import micropython
import rp2
from lib.hub75.image import PPMImage

COLOR_BIT_DEPTH = const(6)

class BitPlanes:
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
        
        self._load_ppm(
            ppm.image_data,
            len(ppm.image_data),
            self._bitframe_data,
            len(self._bitframe_data),
            ppm.max_value
        )

    @staticmethod
    @micropython.viper
    def _load_ppm(
        input_data: ptr8,
        input_size: int,
        output_data: ptr8,
        output_size: int,
        max_value: int
    ):
        bitplane_offset: int = 0
        
        bytes_per_channel: int = 1

        if max_value >= 256:
            bytes_per_channel = 2

        bitplane_size: int = output_size // COLOR_BIT_DEPTH

        input_index: int = 0
        bottom_offset: int = input_size // 2

        while input_index < bottom_offset:
            if bytes_per_channel == 1:
                r1 = input_data[input_index]
                g1 = input_data[input_index + 1]
                b1 = input_data[input_index + 2]

                r2 = input_data[input_index + bottom_offset]
                g2 = input_data[input_index + bottom_offset + 1]
                b2 = input_data[input_index + bottom_offset + 2]

                input_index += 3
            else:
                r1 = ((input_data[input_index] << 8) | input_data[input_index + 1]) * 255 // max_value
                g1 = ((input_data[input_index + 2] << 8) | input_data[input_index + 3]) * 255 // max_value
                b1 = ((input_data[input_index + 4] << 8) | input_data[input_index + 5]) * 255 // max_value

                r2 = ((input_data[input_index + bottom_offset] << 8) | input_data[input_index + bottom_offset + 1]) * 255 // max_value
                g2 = ((input_data[input_index + bottom_offset + 2] << 8) | input_data[input_index + bottom_offset + 3]) * 255 // max_value
                b2 = ((input_data[input_index + bottom_offset + 4] << 8) | input_data[input_index + bottom_offset + 5]) * 255 // max_value

                input_index += 6
                
            # Manual loop unrolling provides enough of a speedup here to justify the decreased readability

            # Bitplane 0 (MSB)
            output_data[bitplane_offset] = (
                r1 & 0b10000000 |
                (g1 >> 1) & 0b01000000 |
                (b1 >> 2) & 0b00100000 |
                (r2 >> 3) & 0b00010000 |
                (g2 >> 4) & 0b00001000 |
                (b2 >> 5) & 0b00000100
            )

            # Bitplane 1
            output_data[bitplane_offset + bitplane_size] = (
                (r1 << 1) & 0b10000000 |
                g1 & 0b01000000 |
                (b1 >> 1) & 0b00100000 |
                (r2 >> 2) & 0b00010000 |
                (g2 >> 3) & 0b00001000 |
                (b2 >> 4) & 0b00000100
            )

            # Bitplane 2
            output_data[bitplane_offset + bitplane_size * 2] = (
                (r1 << 2) & 0b10000000 |
                (g1 << 1) & 0b01000000 |
                b1 & 0b00100000 |
                (r2 >> 1) & 0b00010000 |
                (g2 >> 2) & 0b00001000 |
                (b2 >> 3) & 0b00000100
            )

            # Bitplane 3
            output_data[bitplane_offset + bitplane_size * 3] = (
                (r1 << 3) & 0b10000000 |
                (g1 << 2) & 0b01000000 |
                (b1 << 1) & 0b00100000 |
                r2 & 0b00010000 |
                (g2 >> 1) & 0b00001000 |
                (b2 >> 2) & 0b00000100
            )

            # Bitplane 4
            output_data[bitplane_offset + bitplane_size * 4] = (
                (r1 << 4) & 0b10000000 |
                (g1 << 3) & 0b01000000 |
                (b1 << 2) & 0b00100000 |
                (r2 << 1) & 0b00010000 |
                g2 & 0b00001000 |
                (b2 >> 1) & 0b00000100
            )

            # Bitplane 5 (LSB)
            output_data[bitplane_offset + bitplane_size * 5] = (
                (r1 << 5) & 0b10000000 |
                (g1 << 4) & 0b01000000 |
                (b1 << 3) & 0b00100000 |
                (r2 << 2) & 0b00010000 |
                (g2 << 1) & 0b00001000 |
                b2 & 0b00000100
            )

            bitplane_offset += 1

# IRQ 0: Safe to latch data (display not enabled)
# IRQ 1: Data latching complete, safe to enable display

@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_HIGH,
    out_init=[rp2.PIO.OUT_LOW] * 4,
)
def display_addressing_pio():
    nop()                       .side(0) [15]
    nop()                       .side(0) [7]
    nop()                       .side(0) [3]
    nop()                       .side(0) [1]
    nop()                       .side(0)
    nop()                       .side(0)
    irq(0)                      .side(1)
    jmp(x_dec, "write_address") .side(1)
    set(x, 15)                  .side(1)
    jmp(y_dec, "write_address") .side(1)
    set(y, 5)                   .side(1)
    label("write_address")
    mov(pins, x)                .side(1)
    wait(1, irq, 1)             .side(1)
    mov(pc, y)                  .side(1)

@rp2.asm_pio(
    sideset_init=[rp2.PIO.OUT_LOW] * 2, # data clock is 0b10, latch is 0b01
    out_init=[rp2.PIO.OUT_LOW] * 6,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=32,
)
def data_output_pio():
    set(x, 31)                  .side(0b01)
    irq(1)                      .side(0b00)
    label("write_data")
    out(pins, 8)                .side(0b00)
    jmp(x_dec, "write_data")    .side(0b10)
    wait(1, irq, 0)             .side(0b00)