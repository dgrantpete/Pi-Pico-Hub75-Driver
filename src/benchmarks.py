"""
Parallel benchmark suite for LED matrix image processing
Demonstrates dual-core pipelined processing on RP2040

Core 0: PPM parsing + MatrixFrame creation
Core 1: BitPlanes encoding
"""

import gc
import time
import _thread

try:
    from hub75 import MatrixFrame, BitPlanes, parse_ppm_image
except ImportError:
    pass


# Shared state between cores
class SharedPipeline:
    """Thread-safe pipeline state for producer-consumer pattern"""
    def __init__(self):
        self.lock = _thread.allocate_lock()
        
        # Data slots for double-buffering
        self.matrix_frame = None
        self.matrix_ready = False
        
        # Synchronization flags
        self.producer_done = False
        self.consumer_done = False
        
        # Performance tracking
        self.frames_produced = 0
        self.frames_consumed = 0
    
    def produce_frame(self, matrix_frame):
        """Core 0: Produce a MatrixFrame (blocking if consumer isn't ready)"""
        while True:
            with self.lock:
                if not self.matrix_ready:
                    self.matrix_frame = matrix_frame
                    self.matrix_ready = True
                    self.frames_produced += 1
                    return
            # Consumer busy, yield and retry
            time.sleep_us(10)
    
    def consume_frame(self):
        """Core 1: Consume a MatrixFrame (blocking if producer hasn't produced)"""
        while True:
            with self.lock:
                if self.matrix_ready:
                    frame = self.matrix_frame
                    self.matrix_ready = False
                    self.frames_consumed += 1
                    return frame
                if self.producer_done:
                    return None  # Producer finished
            # No data ready, yield and retry
            time.sleep_us(10)
    
    def signal_producer_done(self):
        """Core 0: Signal that production is complete"""
        with self.lock:
            self.producer_done = True
    
    def signal_consumer_done(self):
        """Core 1: Signal that consumption is complete"""
        with self.lock:
            self.consumer_done = True


def core1_worker(pipeline, iterations):
    """
    Core 1: Bitplane encoder worker
    Continuously consumes MatrixFrames and encodes to BitPlanes
    """
    bitplanes_list = []
    
    for i in range(iterations):
        # Block until frame is available
        matrix_frame = pipeline.consume_frame()
        if matrix_frame is None:
            break
        
        # Do the actual work
        bitplanes = BitPlanes.from_matrix_frame(matrix_frame)
        bitplanes_list.append(bitplanes)
    
    pipeline.signal_consumer_done()
    return bitplanes_list


def generate_synthetic_ppm(width, height, max_value=255):
    """Generate synthetic P6 PPM data in memory"""
    header = f"P6\n{width} {height}\n{max_value}\n".encode()
    
    pixel_data = bytearray(width * height * 3)
    for i in range(0, len(pixel_data), 3):
        pixel_value = (i // 3) % 256
        pixel_data[i] = pixel_value
        pixel_data[i+1] = (pixel_value * 2) % 256
        pixel_data[i+2] = (pixel_value * 3) % 256
    
    return bytes(header + pixel_data)


def benchmark_parallel_pipeline(ppm_data, iterations=10):
    """
    Benchmark with parallel processing:
    Core 0: Parse + MatrixFrame
    Core 1: BitPlanes encoding
    """
    
    pipeline = SharedPipeline()
    
    # Start Core 1 worker
    _thread.start_new_thread(core1_worker, (pipeline, iterations))
    
    # Core 0: Producer (parse + create frames)
    start = time.ticks_us()
    
    for i in range(iterations):
        # Parse and create frame on Core 0
        buffer = memoryview(ppm_data)
        parsed = parse_ppm_image(buffer)
        matrix_frame = MatrixFrame.from_ppm(parsed)
        
        # Hand off to Core 1
        pipeline.produce_frame(matrix_frame)
    
    # Signal we're done producing
    pipeline.signal_producer_done()
    
    # Wait for consumer to finish
    while not pipeline.consumer_done:
        time.sleep_us(100)
    
    end = time.ticks_us()
    total_time = time.ticks_diff(end, start)
    
    return total_time, pipeline.frames_produced, pipeline.frames_consumed


def benchmark_serial_pipeline(ppm_data, iterations=10):
    """
    Benchmark with serial processing (baseline for comparison)
    """
    start = time.ticks_us()
    
    for i in range(iterations):
        buffer = memoryview(ppm_data)
        parsed = parse_ppm_image(buffer)
        matrix_frame = MatrixFrame.from_ppm(parsed)
        bitplanes = BitPlanes.from_matrix_frame(matrix_frame)
    
    end = time.ticks_us()
    return time.ticks_diff(end, start)


def run_parallel_benchmarks(width=64, height=32, iterations=10):
    """Run parallel vs serial comparison"""
    print("\n" + "="*60)
    print(f"Dual-Core Parallel Processing Benchmark")
    print(f"Image size: {width}x{height}")
    print(f"Iterations: {iterations}")
    print("="*60)
    
    # Generate test data
    print("\nGenerating test data...")
    ppm_data = generate_synthetic_ppm(width, height)
    print(f"Generated {len(ppm_data):,} bytes")
    
    # Warmup
    print("\nWarming up...")
    for _ in range(3):
        benchmark_serial_pipeline(ppm_data, iterations=2)
    
    # Serial baseline
    print("\nRunning SERIAL baseline...")
    gc.collect()
    serial_times = []
    for _ in range(5):
        elapsed = benchmark_serial_pipeline(ppm_data, iterations)
        serial_times.append(elapsed)
    
    serial_median = sorted(serial_times)[len(serial_times)//2]
    
    # Parallel benchmark
    print("\nRunning PARALLEL benchmark...")
    gc.collect()
    parallel_times = []
    for _ in range(5):
        elapsed, produced, consumed = benchmark_parallel_pipeline(ppm_data, iterations)
        parallel_times.append(elapsed)
    
    parallel_median = sorted(parallel_times)[len(parallel_times)//2]
    
    # Results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    print(f"\nSerial Pipeline (baseline):")
    print(f"  Median total time: {serial_median/1000:>10.2f} ms")
    print(f"  Per frame:         {serial_median/iterations/1000:>10.2f} ms")
    print(f"  Throughput:        {1000000*iterations/serial_median:>10.1f} frames/sec")
    
    print(f"\nParallel Pipeline (dual-core):")
    print(f"  Median total time: {parallel_median/1000:>10.2f} ms")
    print(f"  Per frame:         {parallel_median/iterations/1000:>10.2f} ms")
    print(f"  Throughput:        {1000000*iterations/parallel_median:>10.1f} frames/sec")
    
    speedup = serial_median / parallel_median
    print(f"\n{'-'*60}")
    print(f"Speedup: {speedup:.2f}x")
    
    if speedup > 1:
        print(f"✓ Parallel is {(speedup-1)*100:.1f}% faster!")
    else:
        print(f"✗ Parallel is {(1-speedup)*100:.1f}% slower (overhead dominates)")
    
    print(f"\nFinal memory free: {gc.mem_free():,} bytes")


if __name__ == "__main__":
    run_parallel_benchmarks(width=64, height=32, iterations=10)