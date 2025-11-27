# HUB75 Driver Performance Characteristics

## Display Specifications

- **Panel Configuration**: 16 rows (1/16 scan)
- **Color Bit Depth**: 6 bits per channel (RGB)
- **Color Resolution**: 64 levels per channel (262,144 total colors)

## PIO State Machine Performance

### Timing at 150 MHz

- **Cycles per Frame**: 1,501 cycles
- **Frame Display Time**: 57.4 microseconds
- **Refresh Rate**: 17.4 kHz
- **Duty Cycle**: 67.2%

### Breakdown
- **ON cycles** (LEDs lit): 1,008 cycles
- **OFF cycles** (addressing/data transfer): 493 cycles

## CPU Performance

### Bitplane Transformation
- **PPM to Bitplanes**: 1.27 ms per frame
- **CPU Core Usage**: Single core for transformation
- **Optimization Level**: `-O2 -funroll-loops` (best performance observed)

## System Architecture

### Data Flow
1. **CPU Core 0**: Video decode / effect computation / source data preparation
2. **CPU Core 1**: Bitplane transformation (1.27ms per frame)
3. **DMA**: Autonomous transfer of bitplanes to PIO FIFOs (zero CPU overhead)
4. **PIO**: Autonomous HUB75 signal generation (zero CPU overhead)

### Memory Bandwidth
- **Bitplane Buffer Size**: `(width × height / 2) × 6` bytes
- **DMA Transfer**: Overlapped with display refresh (non-blocking)

## Optimization Findings

### Compiler Flags Performance
Tested optimization levels for bitplane transformation:

| Flags | Performance | Ranking |
|-------|-------------|---------|
| `-O3` | 5.0 ms | Worst |
| None | 4.5 ms | Better |
| `-O2` | 4.2 ms | Good |
| `-O2 -funroll-loops` | 3.8 ms | Better |
| **Current optimized** | **1.27 ms** | Best |

The RP2040's 16KB instruction cache favors `-O2` over `-O3` due to better code size management.

## Real-Time Capabilities

### Achievable Use Cases
- 60 FPS procedural effects (plasma, fire, particles)
- 60 FPS animations and transitions
- 30 FPS pre-decoded video playback
- 30 FPS video with real-time effects/filters
- Audio visualizations
- Game rendering
- Live camera processing (with appropriate codec)

### System Bottlenecks
1. **Memory bandwidth**: Reading source data from SD/flash
2. **Video decode complexity**: Codec-dependent
3. **Effect computation**: Algorithm-dependent

The display pipeline itself (transformation + refresh) is **not** a bottleneck.

## Summary

With only 1.27ms of CPU time required per frame for bitplane transformation and autonomous DMA+PIO operation, the system has exceptional headroom for real-time video playback and effects at both 30 FPS and 60 FPS. The 17.4 kHz refresh rate with 67.2% duty cycle ensures a bright, flicker-free display ideal for video content.
