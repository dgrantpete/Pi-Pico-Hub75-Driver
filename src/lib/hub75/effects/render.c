#include "render.h"
#include <stddef.h>

static inline void hsv_to_rgb_kernel(uint8_t hue, uint8_t saturation, uint8_t value, uint8_t *r, uint8_t *g, uint8_t *b) {
    if (saturation == 0) {
        *r = *g = *b = value;
        return;
    }

    uint16_t scaled_hue = (uint16_t)hue * 6;
    uint8_t hue_sector = scaled_hue >> 8;
    uint8_t sector_fraction = scaled_hue & 0xFF;

    uint16_t chroma_range = (uint16_t)value * saturation;
    uint8_t min_component = value - (chroma_range >> 8);
    uint8_t descending_component = value - ((uint32_t)chroma_range * sector_fraction >> 16);
    uint8_t ascending_component = value - ((uint32_t)chroma_range * (255 - sector_fraction) >> 16);

    switch (hue_sector) {
        case 0:  *r = value; *g = ascending_component; *b = min_component; break;
        case 1:  *r = descending_component; *g = value; *b = min_component; break;
        case 2:  *r = min_component; *g = value; *b = ascending_component; break;
        case 3:  *r = min_component; *g = descending_component; *b = value; break;
        case 4:  *r = ascending_component; *g = min_component; *b = value; break;
        default: *r = value; *g = min_component; *b = descending_component; break;
    }
}

// Pre-computed sine table: (sin(i * 2π / 256) + 1) * 127.5
static const uint8_t SIN_TABLE[256] = {
    128,131,134,137,140,143,146,149,152,155,158,162,165,167,170,173,
    176,179,182,185,188,190,193,196,198,201,203,206,208,211,213,215,
    218,220,222,224,226,228,230,232,234,235,237,238,240,241,243,244,
    245,246,248,249,250,250,251,252,253,253,254,254,254,255,255,255,
    255,255,255,255,254,254,254,253,253,252,251,250,250,249,248,246,
    245,244,243,241,240,238,237,235,234,232,230,228,226,224,222,220,
    218,215,213,211,208,206,203,201,198,196,193,190,188,185,182,179,
    176,173,170,167,165,162,158,155,152,149,146,143,140,137,134,131,
    128,124,121,118,115,112,109,106,103,100, 97, 93, 90, 88, 85, 82,
     79, 76, 73, 70, 67, 65, 62, 59, 57, 54, 52, 49, 47, 44, 42, 40,
     37, 35, 33, 31, 29, 27, 25, 23, 21, 20, 18, 17, 15, 14, 12, 11,
     10,  9,  7,  6,  5,  5,  4,  3,  2,  2,  1,  1,  1,  0,  0,  0,
      0,  0,  0,  0,  1,  1,  1,  2,  2,  3,  4,  5,  5,  6,  7,  9,
     10, 11, 12, 14, 15, 17, 18, 20, 21, 23, 25, 27, 29, 31, 33, 35,
     37, 40, 42, 44, 47, 49, 52, 54, 57, 59, 62, 65, 67, 70, 73, 76,
     79, 82, 85, 88, 90, 93, 97,100,103,106,109,112,115,118,121,124
};

// Structure (256 RGB triplets = 768 bytes):
//   0-85:   RED zone (dark->crimson->dark)
//   86-170: BLUE zone (dark->blue->dark)
//   171-255: DARK zone (deep darkness)
//
static const uint8_t BALATRO_GRADIENT[256 * 3] = {
    8, 20, 24,   24, 16, 16,   33, 16, 16,   49, 16, 16,
    57, 16, 16,   66, 16, 16,   82, 16, 16,   90, 16, 16,
    107, 16,  8,  115, 12,  8,  132, 12,  8,  140, 12,  8,
    140, 12,  8,  148, 16,  8,  156, 16,  8,  165, 16,  8,
    165, 16,  8,  173, 20, 16,  181, 20, 16,  189, 20, 16,
    198, 20, 16,  206, 24, 16,  222, 28, 16,  222, 28, 16,
    231, 28, 24,  231, 32, 24,  239, 32, 24,  239, 38, 30,
    247, 50, 38,  247, 61, 49,  247, 79, 67,  255,102, 90,
    255,127,115,  255,152,140,  255,169,157,  255,176,164,
    255,169,157,  255,152,140,  255,127,115,  255,102, 90,
    255, 79, 67,  247, 61, 49,  247, 50, 38,  247, 42, 30,
    239, 32, 24,  239, 32, 24,  231, 32, 24,  231, 28, 24,
    222, 28, 16,  222, 28, 16,  206, 24, 16,  198, 24, 16,
    189, 20, 16,  189, 20, 16,  181, 20, 16,  181, 20, 16,
    173, 20, 16,  173, 20, 16,  165, 16,  8,  165, 16,  8,
    156, 16,  8,  156, 16,  8,  148, 16,  8,  148, 12,  8,
    140, 12,  8,  140, 12,  8,  132, 12,  8,  123, 12,  8,
    123, 12,  8,  115, 16,  8,  107, 16,  8,   99, 16,  8,
     99, 16, 16,   90, 16, 16,   82, 16, 16,   74, 16, 16,
     66, 16, 16,   66, 16, 16,   57, 16, 16,   49, 16, 16,
     41, 16, 16,   41, 16, 16,   33, 16, 16,   24, 16, 16,
     16, 16, 24,    8, 20, 24,
    // 86-170: BLUE zone (with boosted peak brightness at indices 109-125)
      8, 20, 24,    8, 20, 33,    8, 24, 33,    8, 28, 41,
      8, 32, 49,    8, 36, 57,    8, 40, 66,    8, 44, 74,
      8, 48, 82,    0, 52, 90,    0, 56, 99,    0, 60, 99,
      0, 65,107,    0, 65,115,    0, 69,123,    0, 73,132,
      0, 77,140,    0, 81,148,    0, 85,156,    0, 89,165,
      0, 89,165,    0, 93,165,    8,101,173,   14,111,181,
     30,127,181,   41,142,189,   59,164,189,   90,191,198,
    115,216,198,  140,246,198,  157,255,198,  164,255,198,
    157,255,198,  140,241,198,  115,216,198,   82,187,189,
     59,160,189,   41,138,181,   22,119,181,   14,107,173,
      0, 93,165,    0, 89,165,    0, 89,165,    0, 89,156,
      0, 85,156,    0, 85,156,    0, 85,156,    0, 85,148,
      0, 81,148,    0, 81,148,    0, 81,148,    0, 81,148,
      0, 81,148,    0, 81,148,    0, 81,148,    0, 81,148,
      0, 81,148,    0, 81,148,    0, 81,148,    0, 85,148,
      0, 85,156,    0, 85,156,    0, 85,156,    0, 89,156,
      0, 89,165,    0, 89,165,    0, 85,156,    0, 81,148,
      0, 77,140,    0, 73,132,    0, 69,123,    0, 65,115,
      0, 65,107,    0, 60, 99,    0, 56, 99,    0, 52, 90,
      8, 48, 82,    8, 44, 74,    8, 40, 66,    8, 36, 57,
      8, 32, 49,    8, 28, 41,    8, 24, 33,    8, 20, 33,
      8, 20, 24,
    // 171-255: DARK zone
      8, 16, 16,    8, 16, 16,    8, 16, 16,    8, 16, 16,
      8, 16, 16,    8, 16, 16,    8, 16, 16,    8, 16, 16,
      8, 16, 16,    8, 16, 16,    8, 16, 16,    8, 16, 16,
      8, 16, 24,    8, 16, 24,    8, 16, 24,    8, 16, 24,
      8, 16, 24,    8, 16, 24,    8, 16, 24,    8, 16, 24,
      8, 20, 24,    8, 16, 24,    8, 16, 24,    8, 16, 24,
      8, 16, 24,    8, 16, 24,    8, 16, 24,    8, 16, 24,
      8, 16, 24,    8, 16, 16,    8, 16, 16,    8, 16, 16,
      8, 16, 16,    8, 16, 16,    8, 16, 16,    8, 16, 16,
      8, 16, 16,    8, 16, 16,    8, 16, 16,    8, 16, 16,
      8, 16, 16,    8, 16, 16,    8, 12, 16,    8, 12, 16,
      8, 12, 16,    8, 12, 16,    8, 12, 16,    8, 12, 16,
      8, 12, 16,    8, 12, 16,    8, 12, 16,    8, 12, 16,
      8, 12, 16,    8, 12, 16,    8, 12,  8,    8, 12,  8,
      8, 12,  8,    8, 12,  8,    8, 12,  8,    8, 12,  8,
      8, 12,  8,    8, 12,  8,    8, 12,  8,    8, 12,  8,
      8, 12,  8,    8, 12,  8,    8, 12,  8,    8, 12,  8,
      8, 12,  8,    8, 12,  8,    8, 12, 16,    8, 12, 16,
      8, 12, 16,    8, 12, 16,    8, 12, 16,    8, 12, 16,
      8, 12, 16,    8, 12, 16,    8, 12, 16,    8, 12, 16,
      8, 12, 16,    8, 12, 16,    8, 16, 16,    8, 16, 16,
      8, 16, 16,
};

// Classic Doom fire palette: black -> red -> orange -> yellow -> white
static const uint8_t FIRE_PALETTE[37 * 3] = {
      0,  0,  0,  // 0: black
      8,  0,  0,  16,  0,  0,  24,  0,  0,  33,  0,  0,  // 1-4: dark red
     41,  0,  0,  49,  0,  0,  57,  0,  0,  66,  0,  0,  // 5-8: dark red
     74,  0,  0,  82,  0,  0,  90,  0,  0,  99,  0,  0,  // 9-12: red
    107,  0,  0, 115,  0,  0, 123,  0,  0, 132,  0,  0,  // 13-16: red
    132, 65,  0, 132,130,  0, 132,195,  0, 140,  0,  0,  // 17-20: red-orange
    140, 69,  0, 140,134,  0, 140,203,  0, 148, 12,  0,  // 21-24: red-orange
    148, 81,  0, 148,150,  0, 148,219,  0, 156, 28,  0,  // 25-28: orange
    156, 97,  0, 156,166,  0, 156,235,  0, 165, 44,  0,  // 29-32: orange-yellow
    198,166,  0, 231,231,  0, 255,239,  0, 255,255,  0,  // 33-36: yellow to white
};

static inline uint32_t fire_hash(uint32_t x, uint32_t y, uint32_t frame_time) {
    uint32_t hash_value = x * 374761393u + y * 668265263u + frame_time * 2654435761u;
    hash_value = (hash_value ^ (hash_value >> 13)) * 1274126177u;
    return hash_value ^ (hash_value >> 16);
}

void render_plasma(uint8_t *buffer, uint8_t width, uint8_t height, uint8_t frame_time) {
    for (uint8_t y = 0; y < height; y++) {
        for (uint8_t x = 0; x < width; x++) {
            // Combine multiple sine waves for plasma effect
            uint8_t horizontal_wave = SIN_TABLE[(x + frame_time) & 0xFF];
            uint8_t vertical_wave = SIN_TABLE[(y + frame_time) & 0xFF];
            uint8_t diagonal_wave = SIN_TABLE[((x + y) + frame_time) & 0xFF];
            // Radial component: sqrt approximated by (x^2+y^2)>>4
            uint8_t radial_wave = SIN_TABLE[(((x * x + y * y) >> 4) + frame_time) & 0xFF];

            // Average the waves to get hue (0-255)
            uint8_t hue = (horizontal_wave + vertical_wave + diagonal_wave + radial_wave) >> 2;

            uint8_t r, g, b;
            hsv_to_rgb_kernel(hue, 255, 255, &r, &g, &b);

            size_t buffer_index = ((size_t)y * width + x) * 3;
            buffer[buffer_index] = r;
            buffer[buffer_index + 1] = g;
            buffer[buffer_index + 2] = b;
        }
    }
}

void render_fire(uint8_t *fire_buffer, uint8_t *buffer, uint8_t width, uint8_t height, uint8_t frame_time) {
    // Propagate fire upward with cooling and horizontal spread
    for (int y = 0; y < height - 1; y++) {
        for (int x = 0; x < width; x++) {
            // Get pixel below
            int source_index = (y + 1) * width + x;
            uint8_t source_value = fire_buffer[source_index];

            // Pseudo-random value from position and frame (stateless)
            uint32_t random_value = fire_hash(x, y, frame_time);

            // Horizontal drift: -1, 0, +1 based on lower bits
            int destination_x = x - (int)(random_value & 1) + (int)((random_value >> 1) & 1);
            if (destination_x < 0) destination_x = 0;
            if (destination_x >= width) destination_x = width - 1;

            int decay = ((random_value >> 2) & 3);
            int new_val = (int)source_value - decay;
            if (new_val < 0) new_val = 0;

            int destination_index = y * width + destination_x;
            fire_buffer[destination_index] = (uint8_t)new_val;
        }
    }

    for (int pixel_index = 0; pixel_index < width * height; pixel_index++) {
        uint8_t intensity = fire_buffer[pixel_index];
        if (intensity > 36) intensity = 36;
        size_t palette_index = intensity * 3;
        buffer[pixel_index * 3] = FIRE_PALETTE[palette_index];
        buffer[pixel_index * 3 + 1] = FIRE_PALETTE[palette_index + 1];
        buffer[pixel_index * 3 + 2] = FIRE_PALETTE[palette_index + 2];
    }
}

void render_spiral(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *buffer,
    uint16_t pixel_count,
    uint8_t frame_time,
    uint8_t tightness
) {
    for (uint16_t pixel_index = 0; pixel_index < pixel_count; pixel_index++) {
        // Core spiral formula: hue = angle + radius * tightness + time
        uint8_t hue = angle_table[pixel_index] + ((radius_table[pixel_index] * tightness) >> 4) + frame_time;

        uint8_t r, g, b;
        hsv_to_rgb_kernel(hue, 255, 255, &r, &g, &b);
        buffer[pixel_index * 3] = r;
        buffer[pixel_index * 3 + 1] = g;
        buffer[pixel_index * 3 + 2] = b;
    }
}

void render_balatro(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *buffer,
    uint8_t width, uint8_t height,
    uint16_t frame_time,
    uint8_t spin_speed,
    uint8_t warp_amount
) {
    for (uint8_t y = 0; y < height; y++) {
        for (uint8_t x = 0; x < width; x++) {
            uint16_t pixel_index = (uint16_t)y * width + x;

            // Get pre-computed angle and radius
            uint8_t angle = angle_table[pixel_index];
            uint8_t radius = radius_table[pixel_index];

            // Create spiral: angle + radius * spin_speed + time
            int16_t spiral = (int16_t)angle + ((radius * spin_speed) >> 2) - (frame_time >> 1);

            // Domain warping - multiple layers of sine-based distortion
            // Creates the organic, wobbly boundaries between colors
            int16_t warp = 0;

            // Layer 1: Position-based low frequency
            uint8_t low_frequency_warp = (uint8_t)((x * 5 + y * 7 + (frame_time >> 2)) & 0xFF);
            warp += (int8_t)(SIN_TABLE[low_frequency_warp] - 128);

            // Layer 2: Spiral-based (warps along the spiral bands)
            uint8_t spiral_warp = (uint8_t)((spiral + radius + (frame_time >> 1)) & 0xFF);
            warp += (int8_t)(SIN_TABLE[spiral_warp] - 128);

            // Layer 3: High frequency detail
            uint8_t high_frequency_warp = (uint8_t)((x * 11 - y * 13 + frame_time) & 0xFF);
            warp += (int8_t)(SIN_TABLE[high_frequency_warp] - 128) >> 1;

            // Layer 4: Angle-based swirl
            uint8_t swirl_warp = (uint8_t)((angle * 3 + (frame_time >> 2)) & 0xFF);
            warp += (int8_t)(SIN_TABLE[swirl_warp] - 128) >> 1;

            // Layer 5: Radius-based (creates variation from center to edge)
            uint8_t radial_warp = (uint8_t)((radius * 4 - frame_time) & 0xFF);
            warp += (int8_t)(SIN_TABLE[radial_warp] - 128) >> 2;

            // Apply warp to spiral value
            int16_t warped_spiral = spiral + ((warp * warp_amount) >> 6);

            // Final band value (wraps 0-255)
            uint8_t band_val = (uint8_t)(warped_spiral & 0xFF);

            // Look up color from smooth gradient table (RGB888)
            size_t gradient_index = band_val * 3;
            buffer[pixel_index * 3] = BALATRO_GRADIENT[gradient_index];
            buffer[pixel_index * 3 + 1] = BALATRO_GRADIENT[gradient_index + 1];
            buffer[pixel_index * 3 + 2] = BALATRO_GRADIENT[gradient_index + 2];
        }
    }
}
