import gc
import time
import urandom
import machine
from . import Hub75Driver

def bit_length(n: int) -> int:
    length = 0
    while n > 0:
        n >>= 1
        length += 1
    return length

# ============================================================================
# Synthetic RGB Data Generators
# ============================================================================

def generate_rgb888_data(width, height):
    pixel_count = width * height
    rgb_data = bytearray(pixel_count * 3)
    for i in range(len(rgb_data)):
        rgb_data[i] = urandom.getrandbits(8)

    return rgb_data

def generate_rgb565_data(width, height):
    pixel_count = width * height
    rgb_data = bytearray(pixel_count * 2)
    for i in range(0, len(rgb_data), 2):
        # Generate random 16-bit RGB565 values
        value = urandom.getrandbits(16)
        rgb_data[i] = value & 0xFF
        rgb_data[i + 1] = (value >> 8) & 0xFF

    return rgb_data

# ============================================================================
# Timing and Memory Utilities
# ============================================================================

class BenchmarkTimer:
    def __init__(self):
        self.start_time = 0
        self.elapsed_us = 0

    def __enter__(self):
        self.start_time = time.ticks_us()
        return self

    def __exit__(self, *args):
        self.elapsed_us = time.ticks_diff(time.ticks_us(), self.start_time)

class MemoryTracker:
    def __init__(self):
        self.start_mem = 0
        self.delta = 0

    def __enter__(self):
        gc.collect()
        self.start_mem = gc.mem_alloc()
        return self

    def __exit__(self, *args):
        self.delta = gc.mem_alloc() - self.start_mem

# ============================================================================
# Individual Step Benchmarks
# ============================================================================

def benchmark_rgb888_loading(driver, rgb888_data, iterations):
    timings = []
    memory_deltas = []

    for _ in range(iterations):
        mem_tracker = MemoryTracker()
        timer = BenchmarkTimer()

        with mem_tracker:
            with timer:
                driver.load_rgb888(rgb888_data)

        timings.append(timer.elapsed_us)
        memory_deltas.append(mem_tracker.delta)

    return timings, memory_deltas

def benchmark_rgb565_loading(driver, rgb565_data, iterations):
    timings = []
    memory_deltas = []

    for _ in range(iterations):
        mem_tracker = MemoryTracker()
        timer = BenchmarkTimer()

        with mem_tracker:
            with timer:
                driver.load_rgb565(rgb565_data)

        timings.append(timer.elapsed_us)
        memory_deltas.append(mem_tracker.delta)

    return timings, memory_deltas

def benchmark_flip_operation(driver, iterations):
    timings = []
    memory_deltas = []

    for _ in range(iterations):
        mem_tracker = MemoryTracker()
        timer = BenchmarkTimer()

        with mem_tracker:
            with timer:
                driver.flip()

        timings.append(timer.elapsed_us)
        memory_deltas.append(mem_tracker.delta)

    return timings, memory_deltas

def benchmark_load_and_flip(driver, rgb888_data, rgb565_data, iterations, use_rgb888=True):
    timings = []
    memory_deltas = []

    for _ in range(iterations):
        mem_tracker = MemoryTracker()
        timer = BenchmarkTimer()

        with mem_tracker:
            with timer:
                if use_rgb888:
                    driver.load_rgb888(rgb888_data)
                else:
                    driver.load_rgb565(rgb565_data)
                driver.flip()

        timings.append(timer.elapsed_us)
        memory_deltas.append(mem_tracker.delta)

    return timings, memory_deltas

# ============================================================================
# Statistics Calculation
# ============================================================================

def calculate_stats(values):
    if not values:
        return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}

    sorted_values = sorted(values)
    value_count = len(sorted_values)

    return {
        'min': sorted_values[0],
        'max': sorted_values[-1],
        'avg': sum(sorted_values) / value_count,
        'median': sorted_values[value_count // 2] if value_count % 2 else (sorted_values[value_count // 2 - 1] + sorted_values[value_count // 2]) / 2
    }

# ============================================================================
# Report Formatting
# ============================================================================

def get_datetime_string():
    t = time.localtime()
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"

def format_duration(us):
    if us < 1000:
        return f"{us:.1f} us"
    elif us < 1000000:
        return f"{us / 1000:.2f} ms"
    else:
        return f"{us / 1000000:.2f} s"

def format_memory(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"

def print_step_results(step_name, timing_stats, memory_stats):
    print(f"\n{step_name}:")
    print(f"  Time   - Avg: {format_duration(timing_stats['avg'])}, "
          f"Min: {format_duration(timing_stats['min'])}, "
          f"Max: {format_duration(timing_stats['max'])}, "
          f"Median: {format_duration(timing_stats['median'])}")
    print(f"  Memory - Avg: {format_memory(memory_stats['avg'])}, "
          f"Min: {format_memory(memory_stats['min'])}, "
          f"Max: {format_memory(memory_stats['max'])}")

def print_summary_report(width, height, iterations, results):
    pixel_count = width * height
    datetime_str = get_datetime_string()

    print("=" * 70)
    print("HUB75DRIVER BENCHMARK RESULTS")
    print("=" * 70)
    print(f"\nRun Time: {datetime_str}")
    print(f"\nConfiguration:")
    print(f"  Image Size: {width}x{height} ({pixel_count:,} pixels)")
    print(f"  Iterations: {iterations}")

    # Individual operation results
    print(f"\n{'-' * 70}")
    print("INDIVIDUAL OPERATION PERFORMANCE")
    print('-' * 70)

    print_step_results(
        "1. RGB888 Loading",
        results['rgb888_time'],
        results['rgb888_memory']
    )

    print_step_results(
        "2. RGB565 Loading",
        results['rgb565_time'],
        results['rgb565_memory']
    )

    print_step_results(
        "3. Buffer Flip",
        results['flip_time'],
        results['flip_memory']
    )

    # Combined operation results
    print(f"\n{'-' * 70}")
    print("COMBINED OPERATION PERFORMANCE")
    print('-' * 70)

    print_step_results(
        "RGB888 Load + Flip",
        results['rgb888_flip_time'],
        results['rgb888_flip_memory']
    )

    print_step_results(
        "RGB565 Load + Flip",
        results['rgb565_flip_time'],
        results['rgb565_flip_memory']
    )

    # Throughput metrics
    print(f"\n{'-' * 70}")
    print("THROUGHPUT METRICS")
    print('-' * 70)

    # RGB888 throughput
    avg_rgb888_flip_us = results['rgb888_flip_time']['avg']
    avg_rgb888_flip_s = avg_rgb888_flip_us / 1000000
    fps_rgb888 = 1 / avg_rgb888_flip_s if avg_rgb888_flip_s > 0 else 0
    pixels_per_second_rgb888 = pixel_count / avg_rgb888_flip_s if avg_rgb888_flip_s > 0 else 0

    print(f"\nRGB888 Performance:")
    print(f"  Average Frame Update Time: {format_duration(avg_rgb888_flip_us)}")
    print(f"  Estimated Max FPS: {fps_rgb888:.2f}")
    print(f"  Pixel Throughput: {pixels_per_second_rgb888:,.0f} pixels/second")

    # RGB565 throughput
    avg_rgb565_flip_us = results['rgb565_flip_time']['avg']
    avg_rgb565_flip_s = avg_rgb565_flip_us / 1000000
    fps_rgb565 = 1 / avg_rgb565_flip_s if avg_rgb565_flip_s > 0 else 0
    pixels_per_second_rgb565 = pixel_count / avg_rgb565_flip_s if avg_rgb565_flip_s > 0 else 0

    print(f"\nRGB565 Performance:")
    print(f"  Average Frame Update Time: {format_duration(avg_rgb565_flip_us)}")
    print(f"  Estimated Max FPS: {fps_rgb565:.2f}")
    print(f"  Pixel Throughput: {pixels_per_second_rgb565:,.0f} pixels/second")

    # Memory summary
    print(f"\n{'-' * 70}")
    print("MEMORY SUMMARY")
    print('-' * 70)

    gc.collect()
    print(f"\nCurrent Memory:")
    print(f"  Allocated: {format_memory(gc.mem_alloc())}")
    print(f"  Free: {format_memory(gc.mem_free())}")

    print("\n" + "=" * 70)

def print_compact_report(width, height, iterations, results):
    datetime_str = get_datetime_string()

    print(f"[{datetime_str}] {width}x{height} ({iterations} iterations)")
    print(f"  RGB888 Load:       {results['rgb888_time']['avg'] / 1000:.2f} ms")
    print(f"  RGB565 Load:       {results['rgb565_time']['avg'] / 1000:.2f} ms")
    print(f"  Buffer Flip:       {results['flip_time']['avg'] / 1000:.2f} ms")
    print(f"  RGB888 Load+Flip:  {results['rgb888_flip_time']['avg'] / 1000:.2f} ms ({1000000 / results['rgb888_flip_time']['avg']:.1f} FPS)")
    print(f"  RGB565 Load+Flip:  {results['rgb565_flip_time']['avg'] / 1000:.2f} ms ({1000000 / results['rgb565_flip_time']['avg']:.1f} FPS)")

    gc.collect()
    print(f"  Memory: {format_memory(gc.mem_alloc())} alloc, {format_memory(gc.mem_free())} free")

# ============================================================================
# Main Benchmark Runner
# ============================================================================

def run_benchmark(
    width=64,
    height=64,
    iterations=50,
    verbose=True,
    base_data_pin=0,
    base_clock_pin=6,
    base_address_pin=18,
    output_enable_pin=12
):
    # Calculate address_bit_count from height
    # height = 2 * (2 ** address_bit_count), so address_bit_count = log2(height / 2)
    address_bit_count = bit_length(height // 2) - 1
    if 2 ** address_bit_count != height // 2:
        # height/2 is not a power of 2, round up
        address_bit_count = bit_length(height // 2 - 1)

    # Create Hub75Driver instance
    driver = Hub75Driver(
        address_bit_count=address_bit_count,
        shift_register_depth=width,
        base_data_pin=machine.Pin(base_data_pin),
        base_clock_pin=machine.Pin(base_clock_pin),
        base_address_pin=machine.Pin(base_address_pin),
        output_enable_pin=machine.Pin(output_enable_pin)
    )

    # Generate synthetic data
    rgb888_data = generate_rgb888_data(width, height)
    rgb565_data = generate_rgb565_data(width, height)

    # Run individual operation benchmarks
    rgb888_times, rgb888_mem = benchmark_rgb888_loading(driver, rgb888_data, iterations)
    rgb565_times, rgb565_mem = benchmark_rgb565_loading(driver, rgb565_data, iterations)
    flip_times, flip_mem = benchmark_flip_operation(driver, iterations)

    # Run combined operation benchmarks
    rgb888_flip_times, rgb888_flip_mem = benchmark_load_and_flip(driver, rgb888_data, rgb565_data, iterations, use_rgb888=True)
    rgb565_flip_times, rgb565_flip_mem = benchmark_load_and_flip(driver, rgb888_data, rgb565_data, iterations, use_rgb888=False)

    # Calculate statistics
    results = {
        'rgb888_time': calculate_stats(rgb888_times),
        'rgb888_memory': calculate_stats(rgb888_mem),
        'rgb565_time': calculate_stats(rgb565_times),
        'rgb565_memory': calculate_stats(rgb565_mem),
        'flip_time': calculate_stats(flip_times),
        'flip_memory': calculate_stats(flip_mem),
        'rgb888_flip_time': calculate_stats(rgb888_flip_times),
        'rgb888_flip_memory': calculate_stats(rgb888_flip_mem),
        'rgb565_flip_time': calculate_stats(rgb565_flip_times),
        'rgb565_flip_memory': calculate_stats(rgb565_flip_mem),
    }

    # Print summary report
    if verbose:
        print_summary_report(width, height, iterations, results)
    else:
        print_compact_report(width, height, iterations, results)

    # Cleanup
    driver.deinit()
    del driver, rgb888_data, rgb565_data
    gc.collect()

# ============================================================================
# Quick Test Configurations
# ============================================================================

def quick_test(verbose=True, **pin_config):
    run_benchmark(width=32, height=32, iterations=10, verbose=verbose, **pin_config)

def standard_test(verbose=True, **pin_config):
    run_benchmark(width=64, height=64, iterations=50, verbose=verbose, **pin_config)

def stress_test(verbose=True, **pin_config):
    run_benchmark(width=128, height=64, iterations=100, verbose=verbose, **pin_config)

# ============================================================================
# Module Entry Point
# ============================================================================

if __name__ == '__main__':
    # Run standard test by default
    standard_test()
