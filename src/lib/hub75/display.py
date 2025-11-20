from hub75.matrix_frame import MatrixFrame
import rp2

COLOR_BIT_DEPTH = 6

class BitPlanes:
    def __init__(self, data: memoryview, width: int, height: int):
        self._data = data
        self._width = width
        self._height = height
    
    @property
    def width(self) -> int:
        return self._width
    
    @property
    def height(self) -> int:
        return self._height
    
    @classmethod
    @micropython.native
    def from_matrix_frame(cls, frame: MatrixFrame):
        # Single byte holds data for 2 pixels (top and bottom)
        bitplane_size = frame.width * frame.height // 2
        output_size = bitplane_size * COLOR_BIT_DEPTH

        output_data = bytearray(output_size)
        input_size = len(frame.data)

        cls._encode_bitplanes(
            frame.data,
            input_size,
            output_data,
            bitplane_size
        )

        return BitPlanes(memoryview(output_data), frame.width, frame.height)

    @staticmethod
    @micropython.viper
    def _encode_bitplanes(
        input_data: ptr8,
        input_size: int,
        output_data: ptr8,
        bitplane_size: int
    ):
        color_depth = int(COLOR_BIT_DEPTH)

        top_address = input_data
        bottom_offset = input_size // 2

        bottom_address = ptr8(int(top_address) + bottom_offset)
        end_address = bottom_address

        output_address = output_data

        while int(top_address) < int(end_address):
            r1 = top_address[0]
            g1 = top_address[1]
            b1 = top_address[2]

            r2 = bottom_address[0]
            g2 = bottom_address[1]
            b2 = bottom_address[2]

            bitplane_index = 0
            bitplane_address = output_address

            while bitplane_index < color_depth:
                bitplane_address[0] = (
                    (r1 << bitplane_index) & 0b10000000 |
                    (g1 << bitplane_index >> 1) & 0b01000000 |
                    (b1 << bitplane_index >> 2) & 0b00100000 |
                    (r2 << bitplane_index >> 3) & 0b00010000 |
                    (g2 << bitplane_index >> 4) & 0b00001000 |
                    (b2 << bitplane_index >> 5) & 0b00000100
                )

                bitplane_index += 1
                bitplane_address = ptr8(int(bitplane_address) + bitplane_size)

            top_address = ptr8(int(top_address) + 3)
            bottom_address = ptr8(int(bottom_address) + 3)
            output_address = ptr8(int(output_address) + 1)

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