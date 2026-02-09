from sys import path

path.append('lib')

from time import sleep_ms
from machine import Pin
from hub75 import Hub75Driver
from hub75.display import Hub75Display

driver = Hub75Driver(
    address_bit_count=5,
    shift_register_depth=128,
    base_data_pin=Pin(0),
    base_clock_pin=Pin(11),
    output_enable_pin=Pin(13),
    base_address_pin=Pin(6),
    data_frequency=20_000_000
)

display = Hub75Display(driver)

WIDTH = 128
HEIGHT = 64
SQUARE_SIZE = 20

BLACK = 0x0000
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F

RAINBOW = [
    0xF800,  # Red
    0xFBE0,  # Orange
    0xFFE0,  # Yellow
    0x07E0,  # Green
    0x001F,  # Blue
    0x780F,  # Purple
]

def draw_center_square(color):
    display.fill(BLACK)
    x0 = (WIDTH - SQUARE_SIZE) // 2
    y0 = (HEIGHT - SQUARE_SIZE) // 2
    display.fill_rect(x0, y0, SQUARE_SIZE, SQUARE_SIZE, color)
    display.show()

def draw_rainbow_rows():
    display.fill(BLACK)
    for y in range(HEIGHT):
        color = RAINBOW[(y * len(RAINBOW)) // HEIGHT]
        display.hline(0, y, WIDTH, color)
    display.show()

def draw_rainbow_columns():
    display.fill(BLACK)
    for x in range(WIDTH):
        color = RAINBOW[(x * len(RAINBOW)) // WIDTH]
        display.vline(x, 0, HEIGHT, color)
    display.show()

def draw_rainbow_concentric():
    display.fill(BLACK)
    max_depth = min(WIDTH, HEIGHT) // 2
    for d in range(max_depth):
        color = RAINBOW[(d * len(RAINBOW)) // max_depth]
        display.rect(d, d, WIDTH - 2 * d, HEIGHT - 2 * d, color)
    display.show()

NORMAL_REFRESH = 120.0
SLOW_REFRESH = 0.1

while True:
    draw_center_square(RED)
    sleep_ms(5000)
    draw_rainbow_rows()
    sleep_ms(5000)
    driver.set_target_refresh_rate(SLOW_REFRESH)
    sleep_ms(5000)
    driver.set_target_refresh_rate(NORMAL_REFRESH)

    draw_center_square(GREEN)
    sleep_ms(5000)
    draw_rainbow_columns()
    sleep_ms(5000)
    driver.set_target_refresh_rate(SLOW_REFRESH)
    sleep_ms(5000)
    driver.set_target_refresh_rate(NORMAL_REFRESH)

    draw_center_square(BLUE)
    sleep_ms(5000)
    draw_rainbow_concentric()
    sleep_ms(5000)
    driver.set_target_refresh_rate(SLOW_REFRESH)
    sleep_ms(5000)
    driver.set_target_refresh_rate(NORMAL_REFRESH)
