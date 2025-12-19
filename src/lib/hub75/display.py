import micropython
import framebuf
from .driver import Hub75Driver

class Hub75Display:
    @micropython.native
    def __init__(self, driver: Hub75Driver, width=None):
        self._driver = driver

        if width is not None:
            self._width = width
            self._height = (driver.shift_register_depth * driver.row_address_count * 2) // width
        else:
            # Assumes that each address only drives a single row (e.g. 1/32 scan for 64-row panel) if width is not specified
            self._width = driver.shift_register_depth
            self._height = driver.row_address_count * 2

        self._buffer = bytearray(self._width * self._height * 2)
        self._frame_buffer = framebuf.FrameBuffer(
            self._buffer,
            self._width,
            self._height,
            framebuf.RGB565
        )

    @property
    @micropython.native
    def width(self) -> int:
        return self._width
    
    @property
    @micropython.native
    def height(self) -> int:
        return self._height
    
    @property
    @micropython.native
    def frame_buffer(self) -> framebuf.FrameBuffer:
        return self._frame_buffer
    
    @micropython.native
    def show(self) -> None:
        self._driver.load_rgb565(self._buffer)
        self._driver.flip()

    @micropython.native
    def fill(self, color: int) -> None:
        self._frame_buffer.fill(color)

    @micropython.native
    def pixel(self, x: int, y: int, color: int | None = None) -> int | None:
        if color is None:
            return self._frame_buffer.pixel(x, y)
        else:
            self._frame_buffer.pixel(x, y, color)
            return None

    @micropython.native
    def hline(self, x: int, y: int, width: int, color: int) -> None:
        self._frame_buffer.hline(x, y, width, color)

    @micropython.native
    def vline(self, x: int, y: int, height: int, color: int) -> None:
        self._frame_buffer.vline(x, y, height, color)

    @micropython.native
    def line(self, x1: int, y1: int, x2: int, y2: int, color: int) -> None:
        self._frame_buffer.line(x1, y1, x2, y2, color)

    @micropython.native
    def rect(self, x: int, y: int, width: int, height: int, color: int, fill: bool = False) -> None:
        self._frame_buffer.rect(x, y, width, height, color, fill)  # type: ignore (stubs are missing fill parameter)

    @micropython.native
    def fill_rect(self, x: int, y: int, width: int, height: int, color: int) -> None:
        self._frame_buffer.fill_rect(x, y, width, height, color)

    @micropython.native
    def ellipse(self, x: int, y: int, x_radius: int, y_radius: int, color: int, fill: bool = False, quadrants: int = 0xf) -> None:
        self._frame_buffer.ellipse(x, y, x_radius, y_radius, color, fill, quadrants)

    @micropython.native
    def poly(self, x: int, y: int, coords: list | tuple, color: int, fill: bool = False) -> None:
        self._frame_buffer.poly(x, y, coords, color, fill)

    @micropython.native
    def text(self, string: str, x: int, y: int, color: int = 1) -> None:
        self._frame_buffer.text(string, x, y, color)

    @micropython.native
    def scroll(self, delta_x: int, delta_y: int) -> None:
        self._frame_buffer.scroll(delta_x, delta_y)

    @micropython.native
    def blit(self, source_buffer: framebuf.FrameBuffer, x: int, y: int, key: int = -1, palette = None) -> None:
        self._frame_buffer.blit(source_buffer, x, y, key, palette)