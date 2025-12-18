import _thread
import math
import micropython
from time import sleep_ms
from machine import Pin
from hub75.driver import Hub75Driver, DEFAULT_ADDRESS_FREQUENCY_DIVIDER, DEFAULT_DATA_FREQUENCY
from hub75.effects import render_plasma_frame, render_fire_frame, render_spiral_frame, render_balatro_frame

# Display dimensions
WIDTH = 64
HEIGHT = 64

# Demo mode state
_DEMO_BUTTON = Pin(28, Pin.IN, Pin.PULL_UP)
_DEMO_FREQUENCIES = (3_000, 10_000, 50_000, 150_000)
_demo_mode = 0

# Global driver
driver = None

# Effect buffers (allocated on first use)
_rgb_buffer = None
_fire_buffer = None
_spiral_tables = None

# Effect control state
_running = False
_effect_mode = None

# Adjustable parameters (modify these while effects run)
spin_speed = 4
warp_amount = 14


def bit_length(n: int) -> int:
    length = 0
    while n > 0:
        n >>= 1
        length += 1
    return length

def _init():
    global driver
    if driver is not None:
        return

    print("Initializing driver...")
    driver = Hub75Driver(
        address_bit_count=bit_length(HEIGHT // 2 - 1),
        shift_register_depth=WIDTH,
        base_address_pin=Pin(18),
        base_data_pin=Pin(0),
        base_clock_pin=Pin(6),
        output_enable_pin=Pin(12)
    )
    print("Ready!")


def _ensure_buffers():
    global _rgb_buffer, _fire_buffer
    if _rgb_buffer is None:
        _rgb_buffer = bytearray(WIDTH * HEIGHT * 3)
        _fire_buffer = bytearray(WIDTH * HEIGHT)


def _ensure_spiral_tables():
    global _spiral_tables
    if _spiral_tables is not None:
        return

    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    angle_table = bytearray(WIDTH * HEIGHT)
    radius_table = bytearray(WIDTH * HEIGHT)

    max_radius = math.sqrt(center_x * center_x + center_y * center_y)
    two_pi = 2 * math.pi

    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx = x - center_x
            dy = y - center_y
            pixel_index = y * WIDTH + x

            angle = math.atan2(dy, dx)
            angle_table[pixel_index] = int((angle + math.pi) * 255 / two_pi)

            radius = math.sqrt(dx * dx + dy * dy)
            radius_table[pixel_index] = int(radius * 255 / max_radius)

    _spiral_tables = (angle_table, radius_table)


def _init_fire():
    assert _fire_buffer is not None
    for i in range(len(_fire_buffer)):
        _fire_buffer[i] = 0
    for x in range(WIDTH):
        _fire_buffer[(HEIGHT - 1) * WIDTH + x] = 36


@micropython.native
def _effect_loop():
    global _running

    assert driver is not None
    assert _rgb_buffer is not None
    assert _fire_buffer is not None

    rgb_buffer = _rgb_buffer
    fire_buffer = _fire_buffer
    frame_time = 0

    while _running:
        mode = _effect_mode
        current_spin_speed = spin_speed
        current_warp_amount = warp_amount

        if mode == 'balatro':
            assert _spiral_tables is not None
            angle_table, radius_table = _spiral_tables
            render_balatro_frame(angle_table, radius_table, rgb_buffer,
                                 WIDTH, HEIGHT, frame_time, current_spin_speed, current_warp_amount)
        elif mode == 'plasma':
            render_plasma_frame(rgb_buffer, WIDTH, HEIGHT, frame_time & 0xFF)
        elif mode == 'fire':
            render_fire_frame(fire_buffer, rgb_buffer, WIDTH, HEIGHT, frame_time & 0xFF)
        elif mode == 'spiral':
            assert _spiral_tables is not None
            angle_table, radius_table = _spiral_tables
            render_spiral_frame(angle_table, radius_table, rgb_buffer,
                                WIDTH, HEIGHT, frame_time & 0xFF, current_spin_speed)

        driver.load_rgb888(rgb_buffer)
        driver.flip()
        frame_time += 1

    driver.clear()
    driver.flip()


def _start_effect(mode):
    global _running, _effect_mode

    if _running:
        stop()

    _ensure_buffers()
    if mode in ('balatro', 'spiral'):
        _ensure_spiral_tables()
    if mode == 'fire':
        _init_fire()

    _effect_mode = mode
    _running = True
    _thread.start_new_thread(_effect_loop, ())


def balatro():
    _init()
    _start_effect('balatro')
    print("Balatro started. Adjust spin_speed / warp_amount")


def plasma():
    _init()
    _start_effect('plasma')
    print("Plasma started.")


def fire():
    _init()
    _start_effect('fire')
    print("Fire started.")


def spiral():
    _init()
    _start_effect('spiral')
    print("Spiral started. Adjust spin_speed")


def stop():
    global _running
    if not _running:
        return
    _running = False
    sleep_ms(100)
    print("Stopped.")


def _on_demo_button(pin):
    global _demo_mode
    if driver is None:
        return

    _demo_mode = (_demo_mode + 1) % (len(_DEMO_FREQUENCIES) + 1)

    if _demo_mode == 0:
        driver.set_frequency(
            data_frequency=DEFAULT_DATA_FREQUENCY,
            address_frequency=DEFAULT_DATA_FREQUENCY // DEFAULT_ADDRESS_FREQUENCY_DIVIDER
        )
        print("Demo mode: NORMAL")
    else:
        frequency = _DEMO_FREQUENCIES[_demo_mode - 1]
        driver.set_frequency(
            data_frequency=frequency,
            address_frequency=frequency
        )
        print(f"Demo mode: {frequency} Hz")

_DEMO_BUTTON.irq(trigger=Pin.IRQ_FALLING, handler=_on_demo_button)


print("=== HUB75 Interactive Demo ===")
print("Commands: balatro(), plasma(), fire(), spiral(), stop()")
print("Controls: spin_speed, warp_amount")

balatro()
