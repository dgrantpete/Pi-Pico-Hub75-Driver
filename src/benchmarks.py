"""
Hub75 Pipeline Benchmark Suite

Comprehensive benchmarking for the Hub75 display driver pipeline.
Tests synthetic PPM data through parsing and BitPlane loading with buffer reuse.
"""

import gc
import time
import urandom
from lib.hub75.parser import parse_ppm_image
from lib.hub75.display import BitPlanes


# ============================================================================
# Synthetic PPM Data Generator
# ============================================================================

def generate_ppm_data(width, height):
    """
    Generate synthetic PPM P6 format data in memory.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        bytes: Binary PPM data ready for parsing
    """
    header = f"P6\n{width} {height}\n255\n".encode('ascii')

    # Generate random RGB data
    pixel_count = width * height
    rgb_data = bytearray(pixel_count * 3)
    for i in range(len(rgb_data)):
        rgb_data[i] = urandom.getrandbits(8)

    return bytes(header + rgb_data)


# ============================================================================
# Timing and Memory Utilities
# ============================================================================

class BenchmarkTimer:
    """Context manager for timing code blocks with microsecond precision."""

    def __init__(self):
        self.start_time = 0
        self.elapsed_us = 0

    def __enter__(self):
        self.start_time = time.ticks_us()
        return self

    def __exit__(self, *args):
        self.elapsed_us = time.ticks_diff(time.ticks_us(), self.start_time)


class MemoryTracker:
    """Track memory allocation changes."""

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

def benchmark_ppm_parsing(ppm_data, iterations):
    """
    Benchmark PPM parsing step.

    Args:
        ppm_data: Binary PPM data
        iterations: Number of test iterations

    Returns:
        tuple: (timings_us, memory_deltas, last_result)
    """
    timings = []
    memory_deltas = []
    result = None

    for _ in range(iterations):
        mem_tracker = MemoryTracker()
        timer = BenchmarkTimer()

        with mem_tracker:
            with timer:
                result = parse_ppm_image(ppm_data)

        timings.append(timer.elapsed_us)
        memory_deltas.append(mem_tracker.delta)

        # Clean up for next iteration
        del result
        gc.collect()

    # Keep last result for pipeline continuity
    result = parse_ppm_image(ppm_data)
    return timings, memory_deltas, result


def benchmark_bitplane_loading(ppm_image, iterations):
    """
    Benchmark BitPlane loading with buffer reuse (includes color scaling and encoding).

    Creates a single BitPlanes object and reuses it for all iterations,
    measuring the performance of the in-place load_ppm() operation.

    Args:
        ppm_image: PPMImage object
        iterations: Number of test iterations

    Returns:
        tuple: (timings_us, memory_deltas, bitplanes_object)
    """
    timings = []
    memory_deltas = []

    # Create BitPlanes once - this is the buffer reuse pattern
    bitplanes = BitPlanes(ppm_image.width, ppm_image.height)

    for _ in range(iterations):
        mem_tracker = MemoryTracker()
        timer = BenchmarkTimer()

        with mem_tracker:
            with timer:
                bitplanes.load_ppm(ppm_image)

        timings.append(timer.elapsed_us)
        memory_deltas.append(mem_tracker.delta)

    return timings, memory_deltas, bitplanes


# ============================================================================
# Full Pipeline Benchmark
# ============================================================================

def benchmark_full_pipeline(ppm_data, width, height, iterations):
    """
    Benchmark complete pipeline: PPM bytes -> BitPlanes with buffer reuse.

    Creates BitPlanes once and reuses it for all iterations to demonstrate
    the performance benefit of buffer reuse.

    Args:
        ppm_data: Binary PPM data
        width: Image width
        height: Image height
        iterations: Number of test iterations

    Returns:
        tuple: (timings_us, memory_deltas)
    """
    timings = []
    memory_deltas = []

    # Create BitPlanes once for buffer reuse
    bitplanes = BitPlanes(width, height)

    for _ in range(iterations):
        mem_tracker = MemoryTracker()
        timer = BenchmarkTimer()

        with mem_tracker:
            with timer:
                ppm_image = parse_ppm_image(ppm_data)
                bitplanes.load_ppm(ppm_image)

        timings.append(timer.elapsed_us)
        memory_deltas.append(mem_tracker.delta)

        # Clean up PPM image for next iteration
        del ppm_image
        gc.collect()

    return timings, memory_deltas


# ============================================================================
# Statistics Calculation
# ============================================================================

def calculate_stats(values):
    """
    Calculate min, max, average, and median from a list of values.

    Args:
        values: List of numeric values

    Returns:
        dict: Statistics dictionary
    """
    if not values:
        return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}

    sorted_values = sorted(values)
    n = len(sorted_values)

    return {
        'min': sorted_values[0],
        'max': sorted_values[-1],
        'avg': sum(sorted_values) / n,
        'median': sorted_values[n // 2] if n % 2 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    }


# ============================================================================
# Report Formatting
# ============================================================================

def get_datetime_string():
    """Get current datetime as formatted string."""
    t = time.localtime()
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"


def format_duration(us):
    """Format microseconds as human-readable string."""
    if us < 1000:
        return f"{us:.1f} us"
    elif us < 1000000:
        return f"{us / 1000:.2f} ms"
    else:
        return f"{us / 1000000:.2f} s"


def format_memory(bytes_val):
    """Format bytes as human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"


def print_step_results(step_name, timing_stats, memory_stats):
    """Print results for a single benchmark step."""
    print(f"\n{step_name}:")
    print(f"  Time   - Avg: {format_duration(timing_stats['avg'])}, "
          f"Min: {format_duration(timing_stats['min'])}, "
          f"Max: {format_duration(timing_stats['max'])}, "
          f"Median: {format_duration(timing_stats['median'])}")
    print(f"  Memory - Avg: {format_memory(memory_stats['avg'])}, "
          f"Min: {format_memory(memory_stats['min'])}, "
          f"Max: {format_memory(memory_stats['max'])}")


def print_summary_report(width, height, iterations, results):
    """
    Print comprehensive benchmark summary report.

    Args:
        width: Image width
        height: Image height
        iterations: Number of iterations run
        results: Dictionary of benchmark results
    """
    pixel_count = width * height
    datetime_str = get_datetime_string()

    print("=" * 70)
    print("HUB75 PIPELINE BENCHMARK RESULTS")
    print("=" * 70)
    print(f"\nRun Time: {datetime_str}")
    print(f"\nConfiguration:")
    print(f"  Image Size: {width}x{height} ({pixel_count:,} pixels)")
    print(f"  Iterations: {iterations}")

    # Individual step results
    print(f"\n{'-' * 70}")
    print("INDIVIDUAL STEP PERFORMANCE")
    print('-' * 70)

    print_step_results("1. PPM Parsing",
                      results['parsing_time'],
                      results['parsing_memory'])

    print_step_results("2. BitPlane Loading (with buffer reuse)",
                      results['bitplane_time'],
                      results['bitplane_memory'])

    # Full pipeline results
    print(f"\n{'-' * 70}")
    print("FULL PIPELINE PERFORMANCE")
    print('-' * 70)

    print_step_results("Complete Pipeline (PPM -> BitPlanes)",
                      results['pipeline_time'],
                      results['pipeline_memory'])

    # Throughput metrics
    print(f"\n{'-' * 70}")
    print("THROUGHPUT METRICS")
    print('-' * 70)

    avg_pipeline_us = results['pipeline_time']['avg']
    avg_pipeline_s = avg_pipeline_us / 1000000
    fps = 1 / avg_pipeline_s if avg_pipeline_s > 0 else 0
    pixels_per_second = pixel_count / avg_pipeline_s if avg_pipeline_s > 0 else 0

    print(f"\nAverage Frame Processing Time: {format_duration(avg_pipeline_us)}")
    print(f"Estimated Max FPS: {fps:.2f}")
    print(f"Pixel Throughput: {pixels_per_second:,.0f} pixels/second")

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
    """
    Print compact benchmark summary report.

    Args:
        width: Image width
        height: Image height
        iterations: Number of iterations run
        results: Dictionary of benchmark results
    """
    pixel_count = width * height
    datetime_str = get_datetime_string()

    print(f"[{datetime_str}] {width}x{height} ({iterations} iterations)")
    print(f"  PPM Parsing:       {results['parsing_time']['avg'] / 1000:.2f} ms")
    print(f"  BitPlane Loading:  {results['bitplane_time']['avg'] / 1000:.2f} ms")
    print(f"  Full Pipeline:     {results['pipeline_time']['avg'] / 1000:.2f} ms")

    gc.collect()
    print(f"  Memory: {format_memory(gc.mem_alloc())} alloc, {format_memory(gc.mem_free())} free")


# ============================================================================
# Main Benchmark Runner
# ============================================================================

def run_benchmark(width=64, height=32, iterations=50, verbose=True):
    """
    Run complete benchmark suite for Hub75 pipeline.

    Args:
        width: Image width in pixels (default: 64)
        height: Image height in pixels (default: 32)
        iterations: Number of iterations per test (default: 50)
        verbose: Show detailed report (True) or compact report (False) (default: True)

    Example:
        >>> run_benchmark(width=64, height=32, iterations=100)
        >>> run_benchmark(width=128, height=64, iterations=50, verbose=False)
    """
    # Generate synthetic data
    ppm_data = generate_ppm_data(width, height)

    # Run individual step benchmarks
    parsing_times, parsing_mem, ppm_image = benchmark_ppm_parsing(ppm_data, iterations)
    bitplane_times, bitplane_mem, bitplanes = benchmark_bitplane_loading(ppm_image, iterations)

    # Run full pipeline benchmark
    pipeline_times, pipeline_mem = benchmark_full_pipeline(ppm_data, width, height, iterations)

    # Calculate statistics
    results = {
        'parsing_time': calculate_stats(parsing_times),
        'parsing_memory': calculate_stats(parsing_mem),
        'bitplane_time': calculate_stats(bitplane_times),
        'bitplane_memory': calculate_stats(bitplane_mem),
        'pipeline_time': calculate_stats(pipeline_times),
        'pipeline_memory': calculate_stats(pipeline_mem),
    }

    # Print summary report
    if verbose:
        print_summary_report(width, height, iterations, results)
    else:
        print_compact_report(width, height, iterations, results)

    # Cleanup
    del ppm_data, ppm_image, bitplanes
    gc.collect()


# ============================================================================
# Quick Test Configurations
# ============================================================================

def quick_test(verbose=True):
    """Quick benchmark with small image and few iterations."""
    run_benchmark(width=32, height=32, iterations=10, verbose=verbose)


def standard_test(verbose=True):
    """Standard benchmark with typical HUB75 panel size."""
    run_benchmark(width=64, height=32, iterations=50, verbose=verbose)


def stress_test(verbose=True):
    """Stress test with large image and many iterations."""
    run_benchmark(width=128, height=64, iterations=100, verbose=verbose)


# ============================================================================
# Module Entry Point
# ============================================================================

if __name__ == '__main__':
    # Run standard test by default
    standard_test()
