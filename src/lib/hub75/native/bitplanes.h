#ifndef BITPLANES_H
#define BITPLANES_H

#include <stdint.h>
#include <stddef.h>

/**
 * Pack a pair of RGB pixels (top and bottom half of display) into bitplane format.
 *
 * @param r1, g1, b1 Top pixel RGB components
 * @param r2, g2, b2 Bottom pixel RGB components
 * @param initial_bitplane Pointer to first bitplane position for this pixel
 * @param bitplane_size Stride between bitplanes in bytes
 */
void pack_pixel_pair(
    uint8_t r1, uint8_t g1, uint8_t b1,
    uint8_t r2, uint8_t g2, uint8_t b2,
    uint8_t *initial_bitplane,
    size_t bitplane_size
);

/**
 * Convert RGB888 framebuffer to bitplane format for HUB75 display.
 *
 * @param input_data RGB888 source buffer (3 bytes per pixel)
 * @param pixel_count Total number of pixels
 * @param output_data Bitplane destination buffer
 */
void load_rgb888_kernel(
    const uint8_t *input_data,
    size_t pixel_count,
    uint8_t *output_data
);

/**
 * Convert RGB565 framebuffer to bitplane format for HUB75 display.
 *
 * @param input_data RGB565 source buffer (2 bytes per pixel)
 * @param pixel_count Total number of pixels
 * @param output_data Bitplane destination buffer
 */
void load_rgb565_kernel(
    const uint8_t *input_data,
    size_t pixel_count,
    uint8_t *output_data
);

/**
 * Clear a buffer to all zeros.
 *
 * @param data Buffer to clear
 * @param len Length of buffer in bytes
 */
void clear_buffer(uint8_t *data, size_t len);

#endif
