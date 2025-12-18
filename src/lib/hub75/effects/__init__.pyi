def render_plasma_frame(
    buffer: bytearray | memoryview,
    width: int,
    height: int,
    frame_time: int
) -> None:
    ...

def render_fire_frame(
    fire_buffer: bytearray | memoryview,
    buffer: bytearray | memoryview,
    width: int,
    height: int,
    frame_time: int
) -> None:
    ...

def render_spiral_frame(
    angle_table: bytes | bytearray | memoryview,
    radius_table: bytes | bytearray | memoryview,
    buffer: bytearray | memoryview,
    width: int,
    height: int,
    frame_time: int,
    tightness: int
) -> None:
    ...

def render_balatro_frame(
    angle_table: bytes | bytearray | memoryview,
    radius_table: bytes | bytearray | memoryview,
    buffer: bytearray | memoryview,
    width: int,
    height: int,
    frame_time: int,
    spin_speed: int,
    warp_amount: int
) -> None:
    ...
