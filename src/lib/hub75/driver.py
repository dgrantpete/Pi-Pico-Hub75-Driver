import micropython
import rp2
import machine
import uctypes
from array import array
from hub75.constants import COLOR_BIT_DEPTH
from hub75.native import clear, load_rgb888, load_rgb565
import _thread
import re

_PIO_PROGRAM_DATA_INDEX = const(0)
_PIO_PROGRAM_BUFFER_SIZE = const(32)

# Increasing this value non-linearly increases the duty cycle but decreases the refresh rate
# This default value is a good balance between brightness and refresh rate
_ADDRESS_MANAGER_CLOCK_DIVIDER = const(16)

_DMA_READ_ADDRESS_TRIGGER_INDEX = const(15)

_DMA_8BIT_TRANSFER_SIZE = const(0)
_DMA_16BIT_TRANSFER_SIZE = const(1)
_DMA_32BIT_TRANSFER_SIZE = const(2)

_DMA_UNPACED_TRANSFER_REQUEST = const(0x3F)

_DATA_STATE_MACHINE_OFFSET = const(0)
_ADDRESS_STATE_MACHINE_OFFSET = const(1)
_LATCH_SAFE_IRQ = const(0)
_LATCH_COMPLETE_IRQ = const(1)

_PIO_INDEX_EXPRESSION = re.compile(r'PIO\((\d)\)')

class Hub75Driver:
    @micropython.native
    def __init__(
            self,
            width: int,
            height: int,
            *,
            pio: rp2.PIO | None = None,
            base_address_pin: machine.Pin,
            output_enable_pin: machine.Pin,
            base_data_pin: machine.Pin,
            base_clock_pin: machine.Pin,
            row_origin_top: bool = True,
            data_clock_frequency: int = 30_000_000
        ):
        self._width = width
        self._height = height
        address_count = height // 2

        self._buffers = [
            bytearray((width * address_count) * COLOR_BIT_DEPTH),
            bytearray((width * address_count) * COLOR_BIT_DEPTH)
        ]

        self._active_buffer_index = 0

        (address_manager_pio, data_clocker_pio) = self.__class__._create_pio_programs(
            row_origin_top,
            address_count,
            clocks_per_address=width
        )

        address_manager_pio_size = self.__class__._get_pio_program_length(address_manager_pio)
        data_clocker_pio_size = self.__class__._get_pio_program_length(data_clocker_pio)

        padding_pio = self.__class__._create_padding_pio_program(
            _PIO_PROGRAM_BUFFER_SIZE - address_manager_pio_size - data_clocker_pio_size
        )

        self._pio = pio if pio is not None else rp2.PIO(0)
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
        # We need 'address_manager' to be at offset 0 since we use dynamic jumps
        # To force this, we load a padding program first with a calculated size
        # Once this is done, we load 'data_clocker', and finally 'address_manager' so it sits at the front

        self._pio.add_program(padding_pio)
        self._pio.add_program(data_clocker_pio)
        self._pio.add_program(address_manager_pio)

        self._data_clocker_state_machine = rp2.StateMachine(
            data_state_machine_id,
            data_clocker_pio,
            out_base=base_data_pin,
            sideset_base=base_clock_pin,
            freq=data_clock_frequency
        )

        self._address_manager_state_machine = rp2.StateMachine(
            address_state_machine_id,
            address_manager_pio,
            out_base=base_address_pin,
            sideset_base=output_enable_pin,
            freq=data_clock_frequency // _ADDRESS_MANAGER_CLOCK_DIVIDER
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
            write=self._data_clocker_state_machine,
            read=self._active_buffer,
            count=len(self._active_buffer) // 4
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

        self._data_clocker_state_machine.active(1)
        self._address_manager_state_machine.active(1)

    @micropython.native
    def deinit(self):
        shutdown_lock = _thread.allocate_lock()
        shutdown_lock.acquire()

        self._data_dma.irq(shutdown_lock.release)

        # Cut off the ping-ponged DMAs to stop the loop
        # Graceful stop by cutting chain rather than forcefully stopping means
        # the DMAs are in a clean state when they are done and FIFOs are emptied
        self._data_dma.config(
            ctrl=self._data_dma.pack_ctrl(
                size=_DMA_32BIT_TRANSFER_SIZE,
                inc_read=True,
                inc_write=False,
                chain_to=self._data_dma.channel, # type: ignore
                treq_sel=self.__class__._get_pio_data_request_index(self._pio_block_id, self._data_state_machine_offset),
                irq_quiet=False # Atomically enable IRQ to fire only when chain broken
            ),
            write=self._data_clocker_state_machine,
            read=self._active_buffer,
            count=len(self._active_buffer) // 4
        )

        # Wait until we're sure the DMA has finished (and is no longer triggering the data DMA)
        shutdown_lock.acquire()

        self._data_dma.close()
        self._control_flow_dma.close()

        # Deactivate the state machines and unload their programs from the PIO block
        self._data_clocker_state_machine.active(0)
        self._address_manager_state_machine.active(0)

        self._pio.remove_program()

    @property
    @micropython.native
    def width(self) -> int:
        return self._width
    
    @property
    @micropython.native
    def height(self) -> int:
        return self._height

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

    @staticmethod
    @micropython.native
    def _get_pio_index(pio: rp2.PIO) -> int:
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
        row_origin_top: bool,
        address_count: int,
        clocks_per_address: int
    ) -> tuple[function, function]:
        OE_ASSERTED = const(0b0)
        OE_DEASSERTED = const(0b1)

        @rp2.asm_pio(
            sideset_init=rp2.PIO.OUT_HIGH,
            out_init=[rp2.PIO.OUT_LOW] * 4
        )
        def address_manager_pio():
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
            set(x, address_count - 1)                       .side(OE_DEASSERTED)
            jmp(y_dec, "write_address")                     .side(OE_DEASSERTED)
            set(y, 7)                                       .side(OE_DEASSERTED)
            label("write_address")
            # We invert the bits here when the row origin is at the top so it counts up from 0 to 15 (to work its way down)
            # (even though the x register itself counts down from 15 to 0)
            mov(pins, invert(x) if row_origin_top else x)   .side(OE_DEASSERTED)
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
            pull_thresh=32,
        )
        def data_clocker_pio():
            # The largest value we can set directly into x register is 0b11111 (31)
            # We use the ISR together with x to build larger values 5 bits at a time and shift them in
            counter_value = clocks_per_address - 1
            right_isr_padding = 32

            while counter_value:
                least_significant_bits = counter_value & 0b11111
                counter_value >>= 5
                right_isr_padding -= 5

                if right_isr_padding < 0:
                    raise ValueError("'clocks_per_row' must fit within 32 bits")

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

        return address_manager_pio, data_clocker_pio
    
    @staticmethod
    @micropython.native
    def _get_pio_program_length(program) -> int:
        return len(program[_PIO_PROGRAM_DATA_INDEX])
    
    @staticmethod
    @micropython.native
    def _create_padding_pio_program(size: int):

        @rp2.asm_pio()
        def padding_pio():
            for _ in range(size):
                nop()

        return padding_pio