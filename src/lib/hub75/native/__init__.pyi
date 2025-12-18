def load_rgb888(
    input_data: memoryview | bytes | bytearray,
    output_data: bytearray | memoryview
) -> None: ...

def load_rgb565(
    input_data: memoryview | bytes | bytearray,
    output_data: bytearray | memoryview
) -> None: ...

def clear(buffer: bytearray | memoryview) -> None: ...

def pack_hsv_to_rgb565(hue: int, saturation: int, value: int) -> int:
    ...

def pack_hsv_to_rgb888(hue: int, saturation: int, value: int) -> int:
    ...

def hsv_to_rgb(hue: int, saturation: int, value: int) -> tuple[int, int, int]:
    ...