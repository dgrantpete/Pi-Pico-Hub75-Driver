"""Type stubs for the effects module."""
from typing import Protocol


def plasma_frame(
    buffer: bytearray | memoryview,
    width: int,
    height: int,
    t: int
) -> None:
    """Render one frame of plasma effect to RGB888 buffer.

    Args:
        buffer: RGB888 framebuffer (width * height * 3 bytes)
        width: Display width in pixels
        height: Display height in pixels
        t: Time/frame counter for animation (0-255)
    """
    ...


def fire_frame(
    fire_buf: bytearray | memoryview,
    rgb_buf: bytearray | memoryview,
    width: int,
    height: int,
    t: int
) -> None:
    """Render one frame of Doom-style fire effect.

    Args:
        fire_buf: Fire intensity buffer (width * height bytes)
        rgb_buf: RGB888 output buffer (width * height * 3 bytes)
        width: Display width in pixels
        height: Display height in pixels
        t: Frame counter for animation
    """
    ...


def spiral_frame(
    angle_table: bytes | bytearray | memoryview,
    radius_table: bytes | bytearray | memoryview,
    rgb_buf: bytearray | memoryview,
    width: int,
    height: int,
    t: int,
    tightness: int
) -> None:
    """Render one frame of rainbow spiral effect.

    Args:
        angle_table: Pre-computed angles for each pixel (0-255)
        radius_table: Pre-computed radii for each pixel (0-255)
        rgb_buf: RGB888 output buffer
        width: Display width in pixels
        height: Display height in pixels
        t: Frame counter for rotation (0-255)
        tightness: How tight the spiral winds (higher = more arms)
    """
    ...


def balatro_frame(
    angle_table: bytes | bytearray | memoryview,
    radius_table: bytes | bytearray | memoryview,
    rgb_buf: bytearray | memoryview,
    width: int,
    height: int,
    t: int,
    spin_speed: int,
    warp_amount: int
) -> None:
    """Render one frame of Balatro-style psychedelic spiral effect.

    Args:
        angle_table: Pre-computed angles for each pixel (0-255)
        radius_table: Pre-computed radii for each pixel (0-255)
        rgb_buf: RGB888 output buffer
        width: Display width
        height: Display height
        t: Frame counter for rotation
        spin_speed: Controls spiral tightness
        warp_amount: Controls organic distortion (1-15)
    """
    ...


class Hub75DriverProtocol(Protocol):
    """Protocol for HUB75 driver interface."""
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    def load_rgb888(self, data: bytearray | memoryview) -> None: ...
    def flip(self) -> None: ...
    def clear(self) -> None: ...


class EffectRunner:
    """Manages visual effects on a HUB75 display.

    Runs effects on core 1, leaving core 0 free for REPL interaction.
    Adjust spin_speed and warp_amount while effects run.

    Example:
        runner = EffectRunner(driver)
        runner.balatro()
        runner.spin_speed = 12
        runner.stop()
    """

    spin_speed: int
    """Controls spiral tightness (4-16 typical, higher = tighter spiral)."""

    warp_amount: int
    """Controls organic distortion amount (1-15 typical, higher = more wobbly)."""

    def __init__(self, driver: Hub75DriverProtocol) -> None:
        """Initialize effect runner.

        Args:
            driver: Hub75Driver instance (must be started)
        """
        ...

    @property
    def is_running(self) -> bool:
        """Whether an effect is currently running."""
        ...

    def balatro(self) -> None:
        """Start Balatro-style psychedelic spiral effect."""
        ...

    def plasma(self) -> None:
        """Start classic plasma effect."""
        ...

    def fire(self) -> None:
        """Start Doom-style fire effect."""
        ...

    def spiral(self) -> None:
        """Start rainbow spiral effect."""
        ...

    def stop(self) -> None:
        """Stop the current effect and clear the display."""
        ...

    def __enter__(self) -> "EffectRunner": ...
    def __exit__(self, *args) -> None: ...
