# Pi-Pico-Hub75-Driver

A high-performance MicroPython driver for HUB75 LED matrix panels on Raspberry Pi Pico, featuring PIO state machines and DMA for hardware-accelerated display.

## Features

- **PIO + DMA Hardware Acceleration**: CPU-free display refresh using RP2040 or RP2350's programmable I/O
- **Double Buffering**: Flicker-free updates with atomic buffer swapping
- **Multiple Color Formats**: RGB888 (24-bit) and RGB565 (16-bit) support
- **High Performance**:
    - 24-bit color depth
    - Can process ~800 FPS from RGB888 data on RP2350 with a 64x32 panel
    - PIO can draw entire frame sequence (8 bitplanes) at ~10k FPS (no banding visible even for cameras)
    - PIO and DMA handle all input data transfer and panel driving (CPU is free for other tasks when not transforming pixel data to bitplane format)
- **Multi-Platform**: Supports RP2040 (Pico) and RP2350 (Pico 2)

## Hardware Requirements

- RP2040 or RP2350 microcontroller (e.g., Pi Pico, Pi Pico 2)
- HUB75 LED matrix panel (1/16 scan, e.g., 64x32, 32x32)
- Level shifter recommended (3.3V to 5V) for reliable operation

## Wiring

### Default Pin Configuration

| Pico Pin | HUB75 Signal | Description |
|----------|--------------|-------------|
| GP0 | R1 | Red data (top half) |
| GP1 | G1 | Green data (top half) |
| GP2 | B1 | Blue data (top half) |
| GP3 | R2 | Red data (bottom half) |
| GP4 | G2 | Green data (bottom half) |
| GP5 | B2 | Blue data (bottom half) |
| GP6 | CLK | Pixel clock |
| GP7 | A | Row address bit 0 |
| GP8 | B | Row address bit 1 |
| GP9 | C | Row address bit 2 |
| GP10 | D | Row address bit 3 |
| GP11 | OE | Output enable (active low) |
| GP12 | LAT | Latch signal |
| GND | GND | Ground |

### Pin Configuration Notes

- **Data pins** (R1, G1, B1, R2, G2, B2) must be consecutive GPIO pins starting from `base_data_pin`
- **Address pins** (A, B, C, D) must be consecutive GPIO pins starting from `base_address_pin`
- **Clock and Latch** share a sideset group starting from `base_clock_pin`
- All pin assignments are configurable via the `Hub75Driver` constructor
- The driver requires pins to be grouped consecutively due to PIO constraints

## Installation

1. Copy the `lib/hub75/` directory to your Pico's filesystem
2. Use Thonny, `mpremote`, or your preferred tool to transfer files:

```bash
# Using mpremote
mpremote cp -r src/lib/hub75 :lib/hub75
```

Or in Thonny: Open the files and save them to the Pico under `lib/hub75/`.

### Pre-compiled Modules

For better performance, use the pre-compiled `.mpy` files from the `pico/` directory after running the build script with the `-c=release` flag. These include optimized native C modules for pixel format conversion.

## Quick Start

```python
from lib.hub75.driver import Hub75Driver
import machine

# Initialize the driver
driver = Hub75Driver(
    width=64,
    height=32,
    base_data_pin=machine.Pin(0),
    base_clock_pin=machine.Pin(6),
    base_address_pin=machine.Pin(7),
    output_enable_pin=machine.Pin(11),
)

# Start display output
driver.start()

# Create some test data (red screen)
pixel_count = 64 * 32
rgb_data = bytearray(pixel_count * 3)
for i in range(0, len(rgb_data), 3):
    rgb_data[i] = 255      # Red
    rgb_data[i + 1] = 0    # Green
    rgb_data[i + 2] = 0    # Blue

# Load and display
driver.load_rgb888(rgb_data)
driver.flip()
```

## API Reference

### Hub75Driver

```python
Hub75Driver(
    width: int,
    height: int,
    *,
    base_data_pin: machine.Pin,
    base_clock_pin: machine.Pin,
    base_address_pin: machine.Pin,
    output_enable_pin: machine.Pin,
    data_state_machine_id: int = 0,
    address_state_machine_id: int = 1,
    row_origin_top: bool = True,
    latch_safe_irq: int = 0,
    latch_complete_irq: int = 1,
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | int | required | Panel width in pixels |
| `height` | int | required | Panel height in pixels |
| `base_data_pin` | Pin | required | First GPIO pin for RGB data (uses 6 consecutive pins) |
| `base_clock_pin` | Pin | required | GPIO pin for clock signal (latch is next pin) |
| `base_address_pin` | Pin | required | First GPIO pin for row address (uses 4 consecutive pins) |
| `output_enable_pin` | Pin | required | GPIO pin for output enable signal |
| `data_state_machine_id` | int | 0 | PIO state machine ID for data output (0-7) |
| `address_state_machine_id` | int | 1 | PIO state machine ID for address output (0-7) |
| `row_origin_top` | bool | True | Set False if row 0 is at bottom of panel |
| `latch_safe_irq` | int | 0 | PIO IRQ index for latch timing |
| `latch_complete_irq` | int | 1 | PIO IRQ index for latch completion |

**Note:** Both state machines must be on the same PIO block (0-3 for PIO0, 4-7 for PIO1) to share IRQ signals.

#### Methods

| Method | Description |
|--------|-------------|
| `start()` | Enable the display - activates state machines and DMA |
| `stop()` | Disable the display - stops all hardware |
| `load_rgb888(data)` | Load 24-bit RGB data (3 bytes per pixel: R, G, B) |
| `load_rgb565(data)` | Load 16-bit RGB data (2 bytes per pixel: 5R, 6G, 5B) |
| `flip()` | Swap buffers - displays the most recently loaded frame |

## Performance

Benchmark results for RP2350 on a 64x32 panel (2,048 pixels):

| Operation | Average Time | Estimated FPS |
|-----------|--------------|---------------|
| RGB888 Load | 1.16 ms | - |
| RGB565 Load | 1.33 ms | - |
| Buffer Flip | 109 us | - |
| RGB888 Load + Flip | 1.23 ms | ~812 FPS |
| RGB565 Load + Flip | 1.40 ms | ~713 FPS |

**Memory Usage:**
- Allocated: ~54 KB
- Free: ~392 KB (on RP2350 with 264 KB SRAM)

### Running Benchmarks

These benchmarks are only included in the `debug` build configuration.

```python
from benchmarks import standard_test, quick_test, stress_test

# Quick test (32x32, 10 iterations)
quick_test()

# Standard test (64x32, 50 iterations)
standard_test()

# Stress test (128x64, 100 iterations)
stress_test()
```

## Building from Source

### Prerequisites

- Python 3.x with pip
- ARM GCC toolchain (`arm-none-eabi-gcc`)
- Make utility
- MicroPython source (included as git submodule)

### Setup

```bash
# Clone with submodules
git clone --recursive https://github.com/dgrantpete/Pi-Pico-Hub75-Driver.git

# Or initialize submodules after cloning
git submodule update --init --recursive

# Install Python dependencies
pip install -r requirements.txt
```

### Build

```bash
python tools/build.py
```

This will:
1. Compile native C modules for both RP2040 (armv6m) and RP2350 (armv7emsp)
2. Compile Python files to `.mpy` bytecode
3. Output everything to the `pico/` directory

### Native Module Architecture

The driver includes optimized C code for pixel format conversion. The build system automatically:
- Detects the target architecture at runtime (either armv6m for the RP2040 or armv7emsp for the RP2350)
- Loads the appropriate pre-compiled module

## Troubleshooting

### Panel not lighting up

- Verify all wiring connections, especially GND
- Check that OE (Output Enable) is connected - it's active low
- Ensure the panel is receiving adequate power (5V, often needs separate supply)
- Try calling `driver.start()` after initialization

### Flickering or unstable display

- Add a level shifter between Pico (3.3V) and panel (5V logic)
- Ensure solid ground connection between Pico and panel
- Check for loose wires or poor connections
- Verify the panel scan rate matches (1/16 scan assumed)

### Wrong colors or garbled image

- Verify RGB pin order matches your panel (some panels swap R and B)
- Check that data pins are truly consecutive
- Ensure image dimensions match panel dimensions
- For RGB565, note the byte order is little-endian

### Import errors

- Verify `lib/hub75/` directory exists on the Pico
- Check that all files were copied (driver.py, parser.py, image.py, constants.py, native/)
- Try using `.py` files instead of `.mpy` if architecture doesn't match

### State machine errors

- Both state machines must be on the same PIO block
- IDs 0-3 use PIO0, IDs 4-7 use PIO1
- Don't reuse state machine IDs already in use by other code

## How It Works

### Architecture Overview

The driver leverages the RP2040/RP2350's unique hardware features for efficient LED matrix control:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CPU       │     │   DMA       │     │   PIO       │
│             │     │             │     │             │
│ load_rgb888 │────>│ Auto-stream │────>│ Data SM     │───> RGB pins
│ flip()      │     │ from buffer │     │             │
│             │     │             │     │ Address SM  │───> ABCD + OE
└─────────────┘     └─────────────┘     └─────────────┘
```

### PIO State Machines

**Data Clocker (SM 0):**
- Outputs 6-bit RGB data to panel
- Generates clock signal via sideset
- Generates latch signal
- Synchronized via IRQ with address manager

**Address Manager (SM 1):**
- Outputs 4-bit row address (A, B, C, D)
- Controls Output Enable timing
- Implements exponential delay for bitplane timing (Binary Code Modulation)
- Uses dynamic jumps for variable PWM periods

### Double Buffering

The driver maintains two frame buffers:
- **Active buffer**: Currently being displayed by DMA
- **Inactive buffer**: Where new frame data is written

`flip()` atomically swaps these buffers, ensuring tear-free updates.

### Bitplane Format

Colors are stored in bitplane format for efficient PWM control:
- 8 bitplanes (one per bit of color depth)
- Each pixel pair (top + bottom row) packed into one byte
- Exponential timing per bitplane creates perceived brightness levels

## License

MIT License - see [LICENSE](LICENSE) file for details.
