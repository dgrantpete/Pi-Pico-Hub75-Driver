#include "bitplanes.h"

#ifndef COLOR_BIT_DEPTH
#error "'COLOR_BIT_DEPTH' must be defined"
#endif

// The least significant bits correspond with the lowest pin numbers
// e.g. R1 is connected to pin 0, G1 to pin 1, B1 to pin 2, R2 to pin 3, etc.
enum {
    R1_BIT = 0b000001,
    G1_BIT = 0b000010,
    B1_BIT = 0b000100,
    R2_BIT = 0b001000,
    G2_BIT = 0b010000,
    B2_BIT = 0b100000
};

void pack_pixel_pair(
    uint8_t r1, uint8_t g1, uint8_t b1,
    uint8_t r2, uint8_t g2, uint8_t b2,
    uint8_t *initial_bitplane,
    size_t bitplane_size
) {
    for (size_t bitplane_index = 0; bitplane_index < COLOR_BIT_DEPTH; bitplane_index++) {
        uint8_t packed_pixel = (
            ((r1 >> bitplane_index) & 1u) * R1_BIT |
            ((g1 >> bitplane_index) & 1u) * G1_BIT |
            ((b1 >> bitplane_index) & 1u) * B1_BIT |
            ((r2 >> bitplane_index) & 1u) * R2_BIT |
            ((g2 >> bitplane_index) & 1u) * G2_BIT |
            ((b2 >> bitplane_index) & 1u) * B2_BIT
        );

        initial_bitplane[bitplane_index * bitplane_size] = packed_pixel;
    }
}

void load_rgb888_kernel(
    const uint8_t *input_data,
    size_t pixel_count,
    uint8_t *output_data,
    const uint8_t *gamma_lut
) {
    const size_t bitplane_size = pixel_count / 2;

    for (size_t pixel_index = 0; pixel_index < bitplane_size; pixel_index++) {
        const size_t top_pixel_data_index = pixel_index * 3;
        const size_t bottom_pixel_data_index = (pixel_index + bitplane_size) * 3;
        const uint32_t r1 = gamma_lut[input_data[top_pixel_data_index]];
        const uint32_t g1 = gamma_lut[input_data[top_pixel_data_index + 1]];
        const uint32_t b1 = gamma_lut[input_data[top_pixel_data_index + 2]];

        const uint32_t r2 = gamma_lut[input_data[bottom_pixel_data_index]];
        const uint32_t g2 = gamma_lut[input_data[bottom_pixel_data_index + 1]];
        const uint32_t b2 = gamma_lut[input_data[bottom_pixel_data_index + 2]];

        uint8_t *initial_bitplane = output_data + pixel_index;

        pack_pixel_pair(r1, g1, b1, r2, g2, b2, initial_bitplane, bitplane_size);
    }
}

void load_rgb565_kernel(
    const uint8_t *input_data,
    size_t pixel_count,
    uint8_t *output_data,
    const uint8_t *gamma_lut
) {
    const size_t bitplane_size = pixel_count / 2;

    for (size_t pixel_index = 0; pixel_index < bitplane_size; pixel_index++) {
        const size_t top_pixel_data_index = pixel_index * 2;
        const size_t bottom_pixel_data_index = (pixel_index + bitplane_size) * 2;

        uint32_t r1 = input_data[top_pixel_data_index + 1] & 0b11111000;
        uint32_t g1 = (input_data[top_pixel_data_index + 1] << 5 | (input_data[top_pixel_data_index] >> 3)) & 0b11111100;
        uint32_t b1 = (input_data[top_pixel_data_index] << 3) & 0b11111000;

        uint32_t r2 = input_data[bottom_pixel_data_index + 1] & 0b11111000;
        uint32_t g2 = (input_data[bottom_pixel_data_index + 1] << 5 | (input_data[bottom_pixel_data_index] >> 3)) & 0b11111100;
        uint32_t b2 = (input_data[bottom_pixel_data_index] << 3) & 0b11111000;

        // Replicating the MSBs to fill the empty LSBs gives us a scaling factor
        // from minimum to maximum brightness at the cost of slight nonlinearity
        r1 |= (r1 >> 5);
        g1 |= (g1 >> 6);
        b1 |= (b1 >> 5);

        r2 |= (r2 >> 5);
        g2 |= (g2 >> 6);
        b2 |= (b2 >> 5);

        // Apply gamma correction after full 8-bit reconstruction
        r1 = gamma_lut[r1];
        g1 = gamma_lut[g1];
        b1 = gamma_lut[b1];

        r2 = gamma_lut[r2];
        g2 = gamma_lut[g2];
        b2 = gamma_lut[b2];

        uint8_t *initial_bitplane = output_data + pixel_index;

        pack_pixel_pair(r1, g1, b1, r2, g2, b2, initial_bitplane, bitplane_size);
    }
}

void clear_buffer(uint8_t *data, size_t size) {
    // Use 'volatile' to prevent compiler from optimizing this into memset (it isn't available in natmod context)
    volatile uint8_t *volatile_data = data;
    for (size_t index = 0; index < size; index++) {
        volatile_data[index] = 0;
    }
}
