import micropython
import rp2
from lib.hub75.image import PPMImage
from lib.hub75.native.native import load_ppm
from lib.hub75.constants import COLOR_BIT_DEPTH

class BitPlanes:
    @micropython.native
    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
        self._bitframe_data = bytearray((width * height // 2) * COLOR_BIT_DEPTH)
    
    @property
    def width(self) -> int:
        return self._width
    
    @property
    def height(self) -> int:
        return self._height

    @micropython.native
    def load_ppm(self, ppm: PPMImage):
        if ppm.width != self._width or ppm.height != self._height:
            raise ValueError(f"Unexpected PPM dimensions: expected {(self._width, self._height)}, got {(ppm.width, ppm.height)}")
        
        if ppm.magic_number != 'P6':
            raise ValueError(f"Unsupported PPM format: {ppm.magic_number!r}, only 'P6' is currently supported")
        
        if ppm.max_value is None:
            raise ValueError("PPM max value is not defined")
        
        expected_byte_count = (2 if ppm.max_value >= 256 else 1) * ppm.width * ppm.height * 3

        if len(ppm.image_data) != expected_byte_count:
            raise ValueError(f"Unexpected PPM data byte count: expected {expected_byte_count}, got {len(ppm.image_data)}")

        load_ppm(ppm.image_data, self._bitframe_data, ppm.max_value)

CLOCK_ASSERTED = const(0b10)
LATCH_ASSERTED = const(0b01)
BOTH_DEASSERTED = const(0b00)

OE_ASSERTED = const(0b0)
OE_DEASSERTED = const(0b1)

@micropython.native
def create_pio_programs(
        row_origin_top: bool, 
        latch_safe_irq: int, 
        latch_complete_irq: int
) -> tuple[function, function]:
    
    if latch_safe_irq == latch_complete_irq:
        raise ValueError("'latch_safe_irq' and 'latch_complete_irq' must be different IRQ indexes")

    @rp2.asm_pio(
        sideset_init=rp2.PIO.OUT_HIGH,
        out_init=[rp2.PIO.OUT_LOW] * 4,
    )
    def display_addressing_pio():
        # Dynamic jumps to instructions indexes 0-5 creates accumulated exponential delays for bitplane timing:
        # 5 ->                      1 = 1 cycle
        # 4 ->                  1 + 1 = 2 cycles
        # 3 ->              2 + 1 + 1 = 4 cycles
        # ...
        # 0 -> 16 + 8 + 4 + 2 + 1 + 1 = 32 cycles
        nop()                                           .side(OE_ASSERTED) [15]
        nop()                                           .side(OE_ASSERTED) [7]
        nop()                                           .side(OE_ASSERTED) [3]
        nop()                                           .side(OE_ASSERTED) [1]
        nop()                                           .side(OE_ASSERTED)
        nop()                                           .side(OE_ASSERTED)
        irq(latch_safe_irq)                             .side(OE_DEASSERTED)
        jmp(x_dec, "write_address")                     .side(OE_DEASSERTED)
        set(x, 15)                                      .side(OE_DEASSERTED)
        jmp(y_dec, "write_address")                     .side(OE_DEASSERTED)
        set(y, 5)                                       .side(OE_DEASSERTED)
        label("write_address")
        # We invert the bits here when the row origin is at the top so it counts up from 0 to 15 (to work its way down)
        # (even though the x register itself counts down from 15 to 0)
        mov(pins, invert(x) if row_origin_top else x)   .side(OE_DEASSERTED)
        wait(1, irq, latch_complete_irq)                .side(OE_DEASSERTED)
        mov(pc, y)                                      .side(OE_DEASSERTED)

    @rp2.asm_pio(
        # clock is 0b10, latch is 0b01
        sideset_init=[rp2.PIO.OUT_LOW] * 2,
        out_init=[rp2.PIO.OUT_LOW] * 6,
        out_shiftdir=rp2.PIO.SHIFT_LEFT,
        autopull=True,
        pull_thresh=32,
    )
    def data_output_pio():
        set(x, 31)                  .side(LATCH_ASSERTED)
        irq(latch_complete_irq)     .side(BOTH_DEASSERTED)
        label("write_data")
        out(pins, 8)                .side(BOTH_DEASSERTED)
        jmp(x_dec, "write_data")    .side(CLOCK_ASSERTED)
        wait(1, irq, latch_safe_irq).side(BOTH_DEASSERTED)

    return display_addressing_pio, data_output_pio