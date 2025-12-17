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
    ...

def pack_hsv_to_rgb888(h: int, s: int, v: int) -> int:
    ...

def hsv_to_rgb(h: int, s: int, v: int) -> tuple[int, int, int]:
    ...