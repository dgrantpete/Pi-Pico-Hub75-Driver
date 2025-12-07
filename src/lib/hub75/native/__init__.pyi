def load_rgb888(
    input_data: memoryview | bytes | bytearray,
    output_data: bytearray | memoryview
) -> None: ...

def load_rgb565(
    input_data: memoryview | bytes | bytearray,
    output_data: bytearray | memoryview
) -> None: ...

def clear(buffer: bytearray | memoryview) -> None: ...

def pack_hsv_to_rgb565(h: int, s: int, v: int) -> int:
    """Pack HSV to RGB565 format.

    Args:
        h: Hue (0-255). 0=Red, 43=Yellow, 85=Green, 128=Cyan, 170=Blue, 213=Magenta
        s: Saturation (0-255)
        v: Value/Brightness (0-255)

    Returns:
        RGB565 packed color value
    """
    ...

def pack_hsv_to_rgb888(h: int, s: int, v: int) -> int:
    """Pack HSV to RGB888 as 0x00RRGGBB.

    Args:
        h: Hue (0-255). 0=Red, 43=Yellow, 85=Green, 128=Cyan, 170=Blue, 213=Magenta
        s: Saturation (0-255)
        v: Value/Brightness (0-255)

    Returns:
        RGB888 packed as 0x00RRGGBB
    """
    ...

def hsv_to_rgb(h: int, s: int, v: int) -> tuple[int, int, int]:
    """Convert HSV to RGB tuple.

    Args:
        h: Hue (0-255). 0=Red, 43=Yellow, 85=Green, 128=Cyan, 170=Blue, 213=Magenta
        s: Saturation (0-255)
        v: Value/Brightness (0-255)

    Returns:
        Tuple of (red, green, blue) each 0-255
    """
    ...