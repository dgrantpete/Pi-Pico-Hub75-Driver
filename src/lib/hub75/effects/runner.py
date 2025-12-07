"""High-level effect runner for HUB75 displays."""
import _thread
import math
import micropython
from time import sleep_ms

from . import (
    balatro_frame as _balatro_frame,
    plasma_frame as _plasma_frame,
    fire_frame as _fire_frame,
    spiral_frame as _spiral_frame,
)


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

    def __init__(self, driver):
        """Initialize effect runner.

        Args:
            driver: Hub75Driver instance (must be started)
        """
        self._driver = driver
        self._width = driver.width
        self._height = driver.height

        # Pre-allocate buffers on core 0
        self._rgb_buf = bytearray(self._width * self._height * 3)
        self._fire_buf = bytearray(self._width * self._height)
        self._spiral_tables = None  # Lazy-initialized

        # Control state
        self._running = False
        self._effect_mode = None

        # Adjustable parameters
        self.spin_speed = 4
        self.warp_amount = 14

    @property
    def is_running(self):
        """Whether an effect is currently running."""
        return self._running

    def _ensure_spiral_tables(self):
        """Compute angle/radius tables for spiral effects (once)."""
        if self._spiral_tables is not None:
            return

        cx, cy = self._width // 2, self._height // 2
        angle_table = bytearray(self._width * self._height)
        radius_table = bytearray(self._width * self._height)

        max_radius = math.sqrt(cx * cx + cy * cy)
        two_pi = 2 * math.pi

        for y in range(self._height):
            for x in range(self._width):
                dx, dy = x - cx, y - cy
                idx = y * self._width + x

                angle = math.atan2(dy, dx)
                angle_table[idx] = int((angle + math.pi) * 255 / two_pi)

                radius = math.sqrt(dx * dx + dy * dy)
                radius_table[idx] = int(radius * 255 / max_radius)

        self._spiral_tables = (angle_table, radius_table)

    def _init_fire(self):
        """Initialize fire buffer with heat source at bottom."""
        for i in range(len(self._fire_buf)):
            self._fire_buf[i] = 0
        for x in range(self._width):
            self._fire_buf[(self._height - 1) * self._width + x] = 36

    @micropython.native
    def _effect_loop(self):
        """Main effect loop (runs on core 1)."""
        # Cache for performance
        rgb_buf = self._rgb_buf
        fire_buf = self._fire_buf
        driver = self._driver
        width, height = self._width, self._height
        t = 0

        while self._running:
            mode = self._effect_mode
            spin = self.spin_speed
            warp = self.warp_amount

            if mode == 'balatro':
                angle_table, radius_table = self._spiral_tables
                _balatro_frame(angle_table, radius_table, rgb_buf,
                              width, height, t, spin, warp)
            elif mode == 'plasma':
                _plasma_frame(rgb_buf, width, height, t & 0xFF)
            elif mode == 'fire':
                _fire_frame(fire_buf, rgb_buf, width, height, t & 0xFF)
            elif mode == 'spiral':
                angle_table, radius_table = self._spiral_tables
                _spiral_frame(angle_table, radius_table, rgb_buf,
                             width, height, t & 0xFF, spin)

            driver.load_rgb888(rgb_buf)
            driver.flip()
            t += 1

        # Clear on stop
        driver.clear()
        driver.flip()

    def _start(self, mode):
        """Start an effect (internal)."""
        if self._running:
            self.stop()

        if mode in ('balatro', 'spiral'):
            self._ensure_spiral_tables()
        if mode == 'fire':
            self._init_fire()

        self._effect_mode = mode
        self._running = True
        _thread.start_new_thread(self._effect_loop, ())

    def balatro(self):
        """Start Balatro-style psychedelic spiral effect."""
        self._start('balatro')

    def plasma(self):
        """Start classic plasma effect."""
        self._start('plasma')

    def fire(self):
        """Start Doom-style fire effect."""
        self._start('fire')

    def spiral(self):
        """Start rainbow spiral effect."""
        self._start('spiral')

    def stop(self):
        """Stop the current effect and clear the display."""
        if not self._running:
            return
        self._running = False
        sleep_ms(100)  # Let core 1 clean up

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.stop()
