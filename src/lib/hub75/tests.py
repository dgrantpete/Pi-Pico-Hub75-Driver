"""
Basic smoke test for Hub75Driver initialization and startup.
Does not require actual hardware connection - just verifies no exceptions are raised.
"""

from machine import Pin, freq
import rp2
import gc

# Set a reasonable clock speed
freq(125_000_000)

def test_hub75_driver():
    print("=" * 40)
    print("Hub75Driver Smoke Test")
    print("=" * 40)
    
    # Import here so we get clear error messages if import fails
    print("\n[1/6] Importing Hub75Driver...")
    from lib.hub75.driver import Hub75Driver
    print("      OK")
    
    # Define pins (arbitrary but sequential for easy wiring later)
    # These don't need to be connected for this test
    print("\n[2/6] Creating Pin objects...")
    base_data_pin = Pin(0)      # R1, G1, B1, R2, G2, B2 on GPIO 0-5
    base_clock_pin = Pin(6)     # CLK on GPIO6, LAT on GPIO7
    base_address_pin = Pin(8)   # A, B, C, D on GPIO 8-11
    output_enable_pin = Pin(12) # OE on GPIO12
    print("      OK")
    
    # Test instantiation
    print("\n[3/6] Instantiating Hub75Driver (64x32 panel)...")
    driver = Hub75Driver(
        width=64,
        height=32,
        base_data_pin=base_data_pin,
        base_clock_pin=base_clock_pin,
        base_address_pin=base_address_pin,
        output_enable_pin=output_enable_pin,
    )
    print("      OK")
    
    # Verify buffer sizes
    print("\n[4/6] Verifying buffer configuration...")
    expected_size = 64 * 16 * 8  # width * (height/2) * COLOR_BIT_DEPTH
    actual_size = len(driver._buffers[0])
    assert actual_size == expected_size, f"Buffer size mismatch: {actual_size} != {expected_size}"
    assert len(driver._buffers) == 2, "Should have 2 buffers for double buffering"
    print(f"      Buffer size: {actual_size} bytes")
    print(f"      Double buffering: OK")
    
    # Test flip
    print("\n[5/6] Testing buffer flip...")
    initial_index = driver._active_buffer_index
    driver.flip()
    assert driver._active_buffer_index != initial_index, "Buffer index should change after flip"
    driver.flip()
    assert driver._active_buffer_index == initial_index, "Buffer index should return after double flip"
    print("      OK")
    
    # Test starting (activates PIO and DMA)
    print("\n[6/6] Starting driver (PIO + DMA)...")
    driver._address_manager_state_machine.active(1)
    driver._data_clocker_state_machine.active(1)
    driver._data_dma.active(1)
    print("      OK")
    
    # Verify DMA is running
    import time
    time.sleep_ms(10)
    print(f"      Data DMA active: {driver._data_dma.active()}")
    
    # Cleanup
    print("\n" + "-" * 40)
    print("Cleaning up...")
    driver._data_dma.active(0)
    driver._control_flow_dma.active(0)
    driver._address_manager_state_machine.active(0)
    driver._data_clocker_state_machine.active(0)
    print("Done")
    
    print("\n" + "=" * 40)
    print("ALL TESTS PASSED")
    print("=" * 40)
    
    # Memory stats
    gc.collect()
    print(f"\nFree memory: {gc.mem_free()} bytes")

if __name__ == "__main__":
    try:
        test_hub75_driver()
    except Exception as e:
        print(f"\n!!! TEST FAILED !!!")
        print(f"Error: {type(e).__name__}: {e}")
        raise