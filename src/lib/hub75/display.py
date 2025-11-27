import micropython
import framebuf
from lib.hub75.driver import Hub75Driver

class Hub75Display:
    @micropython.native
    def __init__(self, driver: Hub75Driver):
        self._driver = driver

        self._width = driver.width
        self._height = driver.height
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
        return self._driver.width
    
    @property
    @micropython.native
    def height(self) -> int:
        return self._driver.height
    
    @property
    @micropython.native
    def frame_buffer(self) -> framebuf.FrameBuffer:
        return self._frame_buffer
    
    @micropython.native
    def show(self) -> None:
        """Display the current framebuffer contents on the LED panel."""
        self._driver.load_rgb565(self._buffer)
        self._driver.flip()

    @micropython.native
    def fill(self, color: int) -> None:
        """Fill the entire display with the specified color."""
        self._frame_buffer.fill(color)

    @micropython.native
    def pixel(self, x: int, y: int, color: int | None = None) -> int | None:
        """Get or set the color of a pixel at (x, y)."""
        if color is None:
            return self._frame_buffer.pixel(x, y)
        else:
            self._frame_buffer.pixel(x, y, color)
            return None

    @micropython.native
    def hline(self, x: int, y: int, width: int, color: int) -> None:
        """Draw a horizontal line starting at (x, y) with the specified width."""
        self._frame_buffer.hline(x, y, width, color)

    @micropython.native
    def vline(self, x: int, y: int, height: int, color: int) -> None:
        """Draw a vertical line starting at (x, y) with the specified height."""
        self._frame_buffer.vline(x, y, height, color)

    @micropython.native
    def line(self, x1: int, y1: int, x2: int, y2: int, color: int) -> None:
        """Draw a line from (x1, y1) to (x2, y2)."""
        self._frame_buffer.line(x1, y1, x2, y2, color)

    @micropython.native
    def rect(self, x: int, y: int, width: int, height: int, color: int, fill: bool = False) -> None:
        """Draw a rectangle at (x, y) with the specified width and height."""
        self._frame_buffer.rect(x, y, width, height, color, fill)

    @micropython.native
    def fill_rect(self, x: int, y: int, width: int, height: int, color: int) -> None:
        """Draw a filled rectangle at (x, y) with the specified width and height."""
        self._frame_buffer.fill_rect(x, y, width, height, color)

    @micropython.native
    def ellipse(self, x: int, y: int, x_radius: int, y_radius: int, color: int, fill: bool = False, quadrants: int = 0xf) -> None:
        """Draw an ellipse at (x, y) with the specified radii. Quadrants is a bitmask (0-15) controlling which quadrants to draw."""
        self._frame_buffer.ellipse(x, y, x_radius, y_radius, color, fill, quadrants)

    @micropython.native
    def poly(self, x: int, y: int, coords: list | tuple, color: int, fill: bool = False) -> None:
        """Draw a polygon with vertices at coords (list of (x,y) tuples), offset by (x, y)."""
        self._frame_buffer.poly(x, y, coords, color, fill)

    @micropython.native
    def text(self, string: str, x: int, y: int, color: int = 1) -> None:
        """Draw text at position (x, y)."""
        self._frame_buffer.text(string, x, y, color)

    @micropython.native
    def scroll(self, delta_x: int, delta_y: int) -> None:
        """Scroll the framebuffer by delta_x pixels horizontally and delta_y pixels vertically."""
        self._frame_buffer.scroll(delta_x, delta_y)

    @micropython.native
    def blit(self, source_buffer: framebuf.FrameBuffer, x: int, y: int, key: int = -1, palette = None) -> None:
        """Blit another framebuffer onto this one at position (x, y). Key is the transparency color (-1 for none)."""
        self._frame_buffer.blit(source_buffer, x, y, key, palette)