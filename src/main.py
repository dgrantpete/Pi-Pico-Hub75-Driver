"""
HUB75 LED Matrix Driver - Interactive Demo

Usage from REPL:
    >>> balatro()          # Start Balatro effect
    >>> plasma()           # Start plasma effect
    >>> fire()             # Start fire effect
    >>> spiral()           # Start rainbow spiral
    >>> stop()             # Stop the effect

Adjust parameters while running:
    >>> runner.spin_speed = 12   # Spiral tightness (2-20)
    >>> runner.warp_amount = 10  # Organic wobble (1-20)
"""

from machine import Pin

from hub75.driver import Hub75Driver
from hub75.effects import EffectRunner

# Display dimensions
WIDTH = 64
HEIGHT = 32

# Global driver and runner
driver = None
runner = None


def _init():
    """Initialize driver and effect runner (called once on first use)."""
    global driver, runner

    if driver is not None:
        return

    print("Initializing driver...")
    driver = Hub75Driver(
        width=WIDTH,
        height=HEIGHT,
        row_origin_top=True,
        base_address_pin=Pin(8),
        base_data_pin=Pin(0),
        base_clock_pin=Pin(6),
        output_enable_pin=Pin(12),
        data_clock_frequency=30_000_000
    )

    runner = EffectRunner(driver)
    print("Ready!")


def balatro():
    """Start Balatro-style psychedelic spiral effect."""
    _init()
    runner.balatro()
    print("Balatro started. Adjust runner.spin_speed / runner.warp_amount")


def plasma():
    """Start classic plasma effect."""
    _init()
    runner.plasma()
    print("Plasma started.")


def fire():
    """Start Doom-style fire effect."""
    _init()
    runner.fire()
    print("Fire started.")


def spiral():
    """Start rainbow spiral effect."""
    _init()
    runner.spiral()
    print("Spiral started. Adjust runner.spin_speed")


def stop():
    """Stop the current effect."""
    if runner is not None:
        runner.stop()
        print("Stopped.")


def load_gradient():
    """Load and display gradient.ppm image."""
    from hub75.image import PPMImage

    _init()
    file_buffer = open('jonathan.ppm', 'rb').read()
    ppm = PPMImage.from_file(file_buffer)

    driver.load_rgb888(ppm.image_data)
    driver.flip()

print("=== HUB75 Interactive Demo ===")
print("Commands: balatro(), plasma(), fire(), spiral(), stop()")
print("Controls: runner.spin_speed, runner.warp_amount")
balatro()