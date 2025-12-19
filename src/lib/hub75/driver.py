import micropython
import rp2
import machine
import uctypes
from array import array
from .constants import COLOR_BIT_DEPTH
from .native import clear, load_rgb888, load_rgb565
from micropython import const
import _thread
import re

DEFAULT_DATA_FREQUENCY = 25_000_000

# Increasing this value non-linearly increases the duty cycle but decreases the refresh rate
# This default value is a good balance between brightness and refresh rate
DEFAULT_ADDRESS_FREQUENCY_DIVIDER = 16

_PIO_PROGRAM_DATA_INDEX = const(0)
_PIO_PROGRAM_BUFFER_SIZE = const(32)

_DEFAULT_PIO_INDEX = const(0)

_DMA_READ_ADDRESS_TRIGGER_INDEX = const(15)

_DMA_8BIT_TRANSFER_SIZE = const(0)
_DMA_16BIT_TRANSFER_SIZE = const(1)
_DMA_32BIT_TRANSFER_SIZE = const(2)

_DMA_UNPACED_TRANSFER_REQUEST = const(0x3F)

_DATA_STATE_MACHINE_OFFSET = const(0)
_ADDRESS_STATE_MACHINE_OFFSET = const(1)
_LATCH_SAFE_IRQ = const(0)
_LATCH_COMPLETE_IRQ = const(1)

# PIO register base addresses (same on RP2040 and RP2350)
_PIO_BASE_ADDRESSES = (
    const(0x50200000),  # PIO0
    const(0x50300000),  # PIO1
    const(0x50400000),  # PIO2 (RP2350 only)
)
_SM_CLKDIV_OFFSET = const(0x0C8)  # SM0_CLKDIV offset from PIO base
_SM_CLKDIV_STRIDE = const(0x18)   # Bytes between each SM's registers

_PIO_DEBUG_FLAGS_OFFSET = const(0x008)

_PIO_TX_FLAG_BASE_INDEX = const(24)

_PIO_INDEX_EXPRESSION = re.compile(r'PIO\((\d)\)')

class Hub75Driver:
    @micropython.native
    def __init__(
            self,
            *,
            address_bit_count: int,
            shift_register_depth: int,
            pio: rp2.PIO | None = None,
            base_address_pin: machine.Pin,
            output_enable_pin: machine.Pin,
            base_data_pin: machine.Pin,
            base_clock_pin: machine.Pin,
            data_frequency: int = DEFAULT_DATA_FREQUENCY,
            address_frequency: int | None = None
        ):

        if address_frequency is None:
            address_frequency = data_frequency // DEFAULT_ADDRESS_FREQUENCY_DIVIDER

        self._address_bit_count = address_bit_count
        self._shift_register_depth = shift_register_depth

        buffer_size = self.row_address_count * shift_register_depth * COLOR_BIT_DEPTH

        self._buffers = [
            bytearray(buffer_size),
            bytearray(buffer_size)
        ]

        self._active_buffer_index = 0

        (address_program, data_program) = self.__class__._create_pio_programs(
            address_bit_count,
            shift_register_depth
        )

        address_program_size = self.__class__._get_pio_program_size(address_program)
        data_program_size = self.__class__._get_pio_program_size(data_program)

        padding_program = self.__class__._create_padding_pio_program(
            _PIO_PROGRAM_BUFFER_SIZE - address_program_size - data_program_size
        )

        self._pio = pio if pio is not None else rp2.PIO(_DEFAULT_PIO_INDEX)
        self._pio_block_id = self.__class__._get_pio_index(self._pio)

        data_state_machine_id = self.__class__._get_absolute_state_machine_id(
            self._pio_block_id, _DATA_STATE_MACHINE_OFFSET
        )
        address_state_machine_id = self.__class__._get_absolute_state_machine_id(
            self._pio_block_id, _ADDRESS_STATE_MACHINE_OFFSET
        )
        
        # Clear ALL programs in this PIO so we're starting from a blank slate
        self._pio.remove_program()

        # PIO programs are loaded from back to front
        # We need address program to be at offset 0 since we use dynamic jumps
        # To force this, we load a padding program first with a calculated size
        # Once this is done, we load 'data', and finally 'address' so it sits at the front

        self._pio.add_program(padding_program)
        self._pio.add_program(data_program)
        self._pio.add_program(address_program)

        self._data_state_machine = rp2.StateMachine(
            data_state_machine_id,
            data_program,
            out_base=base_data_pin,
            sideset_base=base_clock_pin,
            freq=data_frequency * 2 # times 2 since each clock cycle has a rising and falling edge
        )

        self._address_state_machine = rp2.StateMachine(
            address_state_machine_id,
            address_program,
            out_base=base_address_pin,
            sideset_base=output_enable_pin,
            freq=address_frequency
        )

        self._active_buffer_address_pointer = array('I', [uctypes.addressof(self._active_buffer)])

        self._data_state_machine_offset = _DATA_STATE_MACHINE_OFFSET

        self._data_dma = rp2.DMA()
        self._control_flow_dma = rp2.DMA()

        self._data_dma.config(
            ctrl=self._data_dma.pack_ctrl(
                size=_DMA_32BIT_TRANSFER_SIZE,
                inc_read=True,
                inc_write=False,
                chain_to=self._control_flow_dma.channel, # type: ignore
                treq_sel=self.__class__._get_pio_data_request_index(self._pio_block_id, self._data_state_machine_offset),
                irq_quiet=True
            ),
            write=self._data_state_machine,
            read=self._active_buffer,
            count=len(self._active_buffer) // 4 # divide by 4 since '_active_buffer' is in bytes with 32-bit transfers
        )

        self._control_flow_dma.config(
            ctrl=self._control_flow_dma.pack_ctrl(
                size=_DMA_32BIT_TRANSFER_SIZE,
                inc_read=False,
                inc_write=False,
                treq_sel=_DMA_UNPACED_TRANSFER_REQUEST
            ),
            count=1,
            read=self._active_buffer_address_pointer,
            write=self._data_dma.registers[_DMA_READ_ADDRESS_TRIGGER_INDEX:_DMA_READ_ADDRESS_TRIGGER_INDEX+1], # type: ignore
            trigger=True
        )

        self._data_state_machine.active(1)
        self._address_state_machine.active(1)

    @micropython.native
    def deinit(self):
        shutdown_lock = _thread.allocate_lock()
        shutdown_lock.acquire()

        def on_data_dma_complete(_):
            shutdown_lock.release()

        self._data_dma.irq(handler=on_data_dma_complete, hard=True)

        # Cut off the ping-ponged DMAs to stop the loop
        # Graceful stop by cutting chain rather than forcefully stopping means
        # the DMAs are in a clean state when they are done
        self._data_dma.config(
            ctrl=self._data_dma.pack_ctrl(
                size=_DMA_32BIT_TRANSFER_SIZE,
                inc_read=True,
                inc_write=False,
                chain_to=self._data_dma.channel, # type: ignore
                treq_sel=self.__class__._get_pio_data_request_index(self._pio_block_id, self._data_state_machine_offset),
                irq_quiet=False # Atomically enable IRQ to fire only when chain broken
            ),
            write=self._data_state_machine,
            read=self._active_buffer,
            count=len(self._active_buffer) // 4
        )

        # Wait until we're sure the DMA has finished (and is no longer triggering the data DMA)
        shutdown_lock.acquire()

        self._data_dma.close()
        self._control_flow_dma.close()

        pio_base = _PIO_BASE_ADDRESSES[self._pio_block_id]

        tx_flag_index = _PIO_TX_FLAG_BASE_INDEX + self._data_state_machine_offset
        tx_bit_mask = 1 << tx_flag_index

        # Clear any stalled TX flags to ensure we know state machines are freshly stalled
        machine.mem32[pio_base + _PIO_DEBUG_FLAGS_OFFSET] = tx_bit_mask

        while (machine.mem32[pio_base + _PIO_DEBUG_FLAGS_OFFSET] & tx_bit_mask) == 0:
            # Wait until state machine is stalled (has no more data to pull from DMA)
            machine.idle()
            
        # Deactivate the state machines and unload their programs from the PIO block
        self._data_state_machine.active(0)
        self._address_state_machine.active(0)

        self._pio.remove_program()

    @micropython.native
    def load_rgb888(self, rgb888_data: memoryview | bytes | bytearray):
        load_rgb888(rgb888_data, self._inactive_buffer)

    @micropython.native
    def load_rgb565(self, rgb565_data: memoryview | bytes | bytearray):
        load_rgb565(rgb565_data, self._inactive_buffer)

    @micropython.native
    def clear(self):
        clear(self._inactive_buffer)

    @micropython.native
    def flip(self):
        self._active_buffer_index = 1 - self._active_buffer_index
        self._active_buffer_address_pointer[0] = uctypes.addressof(self._active_buffer)

    @micropython.native
    def set_frequency(self, data_frequency=None, address_frequency=None):
        system_frequency = machine.freq()
        pio_base = _PIO_BASE_ADDRESSES[self._pio_block_id]

        if data_frequency is not None:
            clkdiv_address = pio_base + _SM_CLKDIV_OFFSET + (_DATA_STATE_MACHINE_OFFSET * _SM_CLKDIV_STRIDE)
            divider = system_frequency / (data_frequency * 2)
            integer_part = int(divider)
            fractional_part = int((divider - integer_part) * 256)
            machine.mem32[clkdiv_address] = (integer_part << 16) | (fractional_part << 8)

        if address_frequency is not None:
            clkdiv_address = pio_base + _SM_CLKDIV_OFFSET + (_ADDRESS_STATE_MACHINE_OFFSET * _SM_CLKDIV_STRIDE)
            divider = system_frequency / address_frequency
            integer_part = int(divider)
            fractional_part = int((divider - integer_part) * 256)
            machine.mem32[clkdiv_address] = (integer_part << 16) | (fractional_part << 8)

    @property
    @micropython.native
    def address_bit_count(self) -> int:
        return self._address_bit_count
    
    @property
    @micropython.native
    def row_address_count(self) -> int:
        return 1 << self._address_bit_count
    
    @property
    @micropython.native
    def shift_register_depth(self) -> int:
        return self._shift_register_depth

    @staticmethod
    @micropython.native
    def _get_pio_index(pio: rp2.PIO) -> int:
        # Micropython API doesn't expose PIO index as a direct integer, so we need to extract it from its string representation
        match = _PIO_INDEX_EXPRESSION.match(repr(pio))

        if not match:
            raise ValueError(f"Could not determine PIO index: '{pio!r}'")

        return int(match.group(1))

    @staticmethod
    @micropython.native
    def _get_absolute_state_machine_id(pio_block_id: int, state_machine_offset: int) -> int:
        return pio_block_id * 4 + state_machine_offset

    @staticmethod
    @micropython.native
    def _get_pio_data_request_index(pio_block_id: int, state_machine_id: int) -> int:
        return (pio_block_id << 3) | (state_machine_id & 0b11)

    @property
    @micropython.native
    def _active_buffer(self) -> bytearray:
        return self._buffers[self._active_buffer_index]
    
    @property
    @micropython.native
    def _inactive_buffer(self) -> bytearray:
        return self._buffers[1 - self._active_buffer_index]

    @staticmethod
    @micropython.native
    def _create_pio_programs(
        address_bit_count: int,
        shift_register_depth: int
    ) -> tuple[function, function]:
        OE_ASSERTED = const(0b0)
        OE_DEASSERTED = const(0b1)

        @rp2.asm_pio(
            sideset_init=rp2.PIO.OUT_HIGH,
            out_init=[rp2.PIO.OUT_LOW] * address_bit_count
        )
        def address_program():
            # Dynamic jumps to instruction indexes 0-7 creates accumulated exponential delays for bitplane timing
            # For example, when COLOR_BIT_DEPTH is 8:
            # when index is 7 ->                                1 = 1 cycle total delay
            # when index is 6 ->                            1 + 1 = 2 cycles total delay
            # when index is 5 ->                        2 + 1 + 1 = 4 cycles total delay
            # ...
            # when index is 0 -> 64 + 32 + 16 + 8 + 4 + 2 + 1 + 1 = 128 cycles total delay
            jmp("extra_delay_48")                           .side(OE_ASSERTED) [15]
            label("extra_delay_48_exit") # Getting from instruction 0 to here takes 64 cycles total (48 cycle "detour" + 16 cycle main path)
            jmp("extra_delay_16")                           .side(OE_ASSERTED) [15]
            label("extra_delay_16_exit") # Getting from instruction 1 to here takes 32 cycles total (16 cycle "detour" + 16 cycle main path)
            nop()                                           .side(OE_ASSERTED) [15]
            nop()                                           .side(OE_ASSERTED) [7]
            nop()                                           .side(OE_ASSERTED) [3]
            nop()                                           .side(OE_ASSERTED) [1]
            nop()                                           .side(OE_ASSERTED)
            nop()                                           .side(OE_ASSERTED)
            irq(_LATCH_SAFE_IRQ)                            .side(OE_DEASSERTED)
            jmp(x_dec, "write_address")                     .side(OE_DEASSERTED)
            set(x, (0b1 <<  address_bit_count) - 1)         .side(OE_DEASSERTED)
            jmp(y_dec, "write_address")                     .side(OE_DEASSERTED)
            set(y, 7)                                       .side(OE_DEASSERTED)
            label("write_address")
            # We invert the bits here so it counts up from 0 to 15 (to work its way down as addresses increase)
            # (even though the x register itself counts down from 15 to 0)
            mov(pins, invert(x))   .side(OE_DEASSERTED)
            wait(1, irq, _LATCH_COMPLETE_IRQ)               .side(OE_DEASSERTED)
            mov(pc, y)                                      .side(OE_DEASSERTED)
            label("extra_delay_16")
            jmp("extra_delay_16_exit")                      .side(OE_ASSERTED) [15]
            label("extra_delay_48")
            nop()                                           .side(OE_ASSERTED) [15]
            nop()                                           .side(OE_ASSERTED) [15]
            jmp("extra_delay_48_exit")                      .side(OE_ASSERTED) [15]

        CLOCK_ASSERTED = const(0b01)
        LATCH_ASSERTED = const(0b10)
        BOTH_DEASSERTED = const(0b00)

        @rp2.asm_pio(
            sideset_init=[rp2.PIO.OUT_LOW] * 2,
            out_init=[rp2.PIO.OUT_LOW] * 6,
            out_shiftdir=rp2.PIO.SHIFT_RIGHT,
            in_shiftdir=rp2.PIO.SHIFT_RIGHT,
            autopull=True,
            pull_thresh=32
        )
        def data_program():
            # The largest value we can set directly into x register is 0b11111 (31)
            # We use the ISR together with x to build larger values 5 bits at a time and shift them in
            counter_value = shift_register_depth - 1
            right_isr_padding = 32

            while counter_value:
                least_significant_bits = counter_value & 0b11111
                counter_value >>= 5
                right_isr_padding -= 5

                if right_isr_padding < 0:
                    raise ValueError("'shift_register_depth' must fit within 32 bits")

                set(x, least_significant_bits)  .side(BOTH_DEASSERTED)
                in_(x, 5)                       .side(BOTH_DEASSERTED)

            in_(null, right_isr_padding)        .side(BOTH_DEASSERTED)
            wrap_target()
            mov(x, isr)                         .side(BOTH_DEASSERTED)
            label("write_data")
            out(pins, 8)                        .side(BOTH_DEASSERTED)
            jmp(x_dec, "write_data")            .side(CLOCK_ASSERTED)
            wait(1, irq, _LATCH_SAFE_IRQ)       .side(BOTH_DEASSERTED)
            # The latch is triggered on the rising edge, so we can safely say that it has been latched
            # for the IRQ even if the latch hasn't yet been deasserted
            irq(_LATCH_COMPLETE_IRQ)            .side(LATCH_ASSERTED)
            wrap()

        return address_program, data_program
    
    @staticmethod
    @micropython.native
    def _get_pio_program_size(program) -> int:
        return len(program[_PIO_PROGRAM_DATA_INDEX])

    @staticmethod
    @micropython.native
    def _create_padding_pio_program(size: int):

        @rp2.asm_pio()
        def padding_pio():
            for _ in range(size):
                nop()

        return padding_pio