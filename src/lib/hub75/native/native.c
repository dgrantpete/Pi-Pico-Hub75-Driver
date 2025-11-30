#include "py/dynruntime.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Pre-computed sine table: sin(i * 2π / 256) * 127.5 + 127.5
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

// Balatro gradient: transitions go THROUGH DARKNESS, not through intermediate hues
// This avoids the purple/magenta that appears when directly blending red<->blue
// Generated with tools/generate_balatro_gradient.py - RGB888 format for simpler handling
//
// Structure (256 RGB triplets = 768 bytes):
//   0-85:   RED zone (dark->crimson->dark)
//   86-170: BLUE zone (dark->blue->dark)
//   171-255: DARK zone (deep darkness)
//
// Converted from RGB565 using driver-style bit replication to preserve exact colors
static const uint8_t BALATRO_GRADIENT[256 * 3] = {
    // 0-85: RED zone
      8, 20, 24,   24, 16, 16,   33, 16, 16,   49, 16, 16,
     57, 16, 16,   66, 16, 16,   82, 16, 16,   90, 16, 16,
    107, 16,  8,  115, 12,  8,  132, 12,  8,  140, 12,  8,
    140, 12,  8,  148, 16,  8,  156, 16,  8,  165, 16,  8,
    165, 16,  8,  173, 20, 16,  181, 20, 16,  189, 20, 16,
    198, 20, 16,  206, 24, 16,  222, 28, 16,  222, 28, 16,
    231, 28, 24,  231, 32, 24,  239, 32, 24,  239, 32, 24,
    247, 36, 24,  247, 36, 24,  247, 36, 24,  255, 36, 24,
    255, 36, 24,  255, 36, 24,  255, 36, 24,  255, 36, 24,
    255, 36, 24,  255, 36, 24,  255, 36, 24,  255, 36, 24,
    255, 36, 24,  247, 36, 24,  247, 36, 24,  247, 36, 24,
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
    // 86-170: BLUE zone
      8, 20, 24,    8, 20, 33,    8, 24, 33,    8, 28, 41,
      8, 32, 49,    8, 36, 57,    8, 40, 66,    8, 44, 74,
      8, 48, 82,    0, 52, 90,    0, 56, 99,    0, 60, 99,
      0, 65,107,    0, 65,115,    0, 69,123,    0, 73,132,
      0, 77,140,    0, 81,148,    0, 85,156,    0, 89,165,
      0, 89,165,    0, 93,165,    8,101,173,    8,105,181,
     16,113,181,   16,117,189,   16,121,189,   24,125,198,
     24,125,198,   24,130,198,   24,130,198,   24,130,198,
     24,130,198,   24,125,198,   24,125,198,   16,121,189,
     16,117,189,   16,113,181,    8,105,181,    8,101,173,
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
      8, 16, 16,  // Index 255 - was missing, causing black pixels!
};

// Classic Doom fire palette (37 colors): black -> red -> orange -> yellow -> white
// Converted from RGB565 using driver-style bit replication
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

// Stateless hash-based pseudo-random (no .data section needed)
static inline uint32_t fire_hash(uint32_t x, uint32_t y, uint32_t t) {
    uint32_t h = x * 374761393u + y * 668265263u + t * 2654435761u;
    h = (h ^ (h >> 13)) * 1274126177u;
    return h ^ (h >> 16);
}

#ifndef COLOR_BIT_DEPTH
#error "'COLOR_BIT_DEPTH' must be defined"
#endif

// The least significant bits correpond with the lowest pin numbers
// e.g. R1 is connected to pin 0, G1 to pin 1, B1 to pin 2, R2 to pin 3, etc.
enum {
    R1_BIT = 0b000001,
    G1_BIT = 0b000010,
    B1_BIT = 0b000100,
    R2_BIT = 0b001000,
    G2_BIT = 0b010000,
    B2_BIT = 0b100000
};

static void pack_pixel_pair(
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

static void load_rgb888_kernel(
    const uint8_t * restrict input_data,
    size_t pixel_count,
    uint8_t * restrict output_data
) {
    const size_t bitplane_size  = pixel_count / 2;

    for (size_t pixel_index = 0; pixel_index < bitplane_size; pixel_index++) {
        const size_t top_pixel_data_index = pixel_index * 3;
        const size_t bottom_pixel_data_index = (pixel_index + bitplane_size) * 3;
        const uint32_t r1 = input_data[top_pixel_data_index];
        const uint32_t g1 = input_data[top_pixel_data_index + 1];
        const uint32_t b1 = input_data[top_pixel_data_index + 2];

        const uint32_t r2 = input_data[bottom_pixel_data_index];
        const uint32_t g2 = input_data[bottom_pixel_data_index + 1];
        const uint32_t b2 = input_data[bottom_pixel_data_index + 2];

        uint8_t *initial_bitplane = output_data + pixel_index;

        pack_pixel_pair(r1, g1, b1, r2, g2, b2, initial_bitplane, bitplane_size);
    }
}

static void load_rgb565_kernel(
    const uint8_t * restrict input_data,
    size_t pixel_count,
    uint8_t * restrict output_data
) {
    const size_t bitplane_size  = pixel_count / 2;

    for (size_t pixel_index = 0; pixel_index < bitplane_size; pixel_index++) {
        const size_t top_pixel_data_index = pixel_index * 2;
        const size_t bottom_pixel_data_index = (pixel_index + bitplane_size) * 2;

        uint32_t r1 = input_data[top_pixel_data_index + 1] & 0b11111000;
        uint32_t g1 = (input_data[top_pixel_data_index + 1] << 5 | (input_data[top_pixel_data_index] >> 3)) & 0b11111100;
        uint32_t b1 = (input_data[top_pixel_data_index] << 3) & 0b11111000;

        uint32_t r2 = input_data[bottom_pixel_data_index + 1] & 0b11111000;
        uint32_t g2 = (input_data[bottom_pixel_data_index + 1] << 5 | (input_data[bottom_pixel_data_index] >> 3)) & 0b11111100;
        uint32_t b2 = (input_data[bottom_pixel_data_index] << 3) & 0b11111000;

        // Replicating the MSBs to fill the empty LSBs gives us a scaling factor from minimum to maximum brightness at the cost of slight nonlinearity
        r1 |= (r1 >> 5);
        g1 |= (g1 >> 6);
        b1 |= (b1 >> 5);

        r2 |= (r2 >> 5);
        g2 |= (g2 >> 6);
        b2 |= (b2 >> 5);

        uint8_t *initial_bitplane = output_data + pixel_index;

        pack_pixel_pair(r1, g1, b1, r2, g2, b2, initial_bitplane, bitplane_size);
    }
}

static mp_obj_t clear(mp_obj_t buffer_obj) {
    mp_buffer_info_t buffer;

    mp_get_buffer_raise(buffer_obj, &buffer, MP_BUFFER_WRITE);

    uint8_t *data = (uint8_t *)buffer.buf;

    for (size_t index = 0; index < buffer.len; index++) {
        data[index] = 0;
    }
    
    return mp_const_none;
}

static mp_obj_t load_rgb888(mp_obj_t input_obj, mp_obj_t output_obj) {
    mp_buffer_info_t input_buffer;
    mp_buffer_info_t output_buffer;

    mp_get_buffer_raise(input_obj, &input_buffer, MP_BUFFER_READ);

    mp_get_buffer_raise(output_obj, &output_buffer, MP_BUFFER_WRITE);

    const uint8_t *input_data = (const uint8_t *)input_buffer.buf;

    uint8_t *output_data = (uint8_t *)output_buffer.buf;
    size_t output_size = output_buffer.len;

    size_t pixel_count = (output_size / COLOR_BIT_DEPTH) * 2;

    size_t expected_input_size = pixel_count * 3;

    if (input_buffer.len != expected_input_size) {
        mp_raise_ValueError(MP_ERROR_TEXT("Input buffer does not match expected size for RGB888 data"));
    }

    load_rgb888_kernel(input_data, pixel_count, output_data);

    return mp_const_none;
}

static mp_obj_t load_rgb565(mp_obj_t input_obj, mp_obj_t output_obj) {
    mp_buffer_info_t input_buffer;
    mp_buffer_info_t output_buffer;

    mp_get_buffer_raise(input_obj, &input_buffer, MP_BUFFER_READ);

    mp_get_buffer_raise(output_obj, &output_buffer, MP_BUFFER_WRITE);

    const uint8_t *input_data = (const uint8_t *)input_buffer.buf;

    uint8_t *output_data = (uint8_t *)output_buffer.buf;
    size_t output_size = output_buffer.len;

    size_t pixel_count = (output_size / COLOR_BIT_DEPTH) * 2;

    size_t expected_input_size = pixel_count * 2;

    if (input_buffer.len != expected_input_size) {
        mp_raise_ValueError(MP_ERROR_TEXT("Input buffer does not match expected size for RGB565 data"));
    }

    load_rgb565_kernel(input_data, pixel_count, output_data);

    return mp_const_none;
}

/**
 * Convert HSV to RGB565 using division-free math.
 *
 * @param h Hue: 0-255 (full color wheel)
 *          0:   Red
 *          43:  Yellow
 *          85:  Green
 *          128: Cyan
 *          170: Blue
 *          213: Magenta
 *          255: Back toward Red
 * @param s Saturation: 0-255
 * @param v Value/Brightness: 0-255
 * @return RGB565 packed color
 */
static uint16_t hsv_to_rgb565_impl(uint8_t h, uint8_t s, uint8_t v) {
    // Grayscale fast path
    if (s == 0) {
        return ((uint16_t)(v & 0xF8) << 8) | ((uint16_t)(v & 0xFC) << 3) | (v >> 3);
    }

    // Scale hue to 0-1530 range, then extract sector and fraction
    // This avoids division: sector = h*6/256, frac = (h*6)%256
    uint16_t h6 = (uint16_t)h * 6;
    uint8_t sector = h6 >> 8;       // 0-5
    uint8_t frac = h6 & 0xFF;       // 0-255 within sector

    // Intermediate values using only multiply and shift
    uint16_t vs = (uint16_t)v * s;
    uint8_t p = v - (vs >> 8);                              // min
    uint8_t q = v - ((uint32_t)vs * frac >> 16);            // ramp down
    uint8_t t = v - ((uint32_t)vs * (255 - frac) >> 16);    // ramp up

    uint8_t r, g, b;

    switch (sector) {
        case 0:  r = v; g = t; b = p; break;  // Red -> Yellow
        case 1:  r = q; g = v; b = p; break;  // Yellow -> Green
        case 2:  r = p; g = v; b = t; break;  // Green -> Cyan
        case 3:  r = p; g = q; b = v; break;  // Cyan -> Blue
        case 4:  r = t; g = p; b = v; break;  // Blue -> Magenta
        default: r = v; g = p; b = q; break;  // Magenta -> Red
    }

    // Pack as RGB565: RRRRRGGGGGGBBBBB
    return ((uint16_t)(r & 0xF8) << 8) | ((uint16_t)(g & 0xFC) << 3) | (b >> 3);
}

/**
 * Convert HSV to RGB888 for internal render functions.
 * Writes directly to output pointers (no MicroPython object overhead).
 */
static void hsv_to_rgb888_render(uint8_t h, uint8_t s, uint8_t v, uint8_t *r, uint8_t *g, uint8_t *b) {
    if (s == 0) {
        *r = *g = *b = v;
        return;
    }

    uint16_t h6 = (uint16_t)h * 6;
    uint8_t sector = h6 >> 8;
    uint8_t frac = h6 & 0xFF;

    uint16_t vs = (uint16_t)v * s;
    uint8_t p = v - (vs >> 8);
    uint8_t q = v - ((uint32_t)vs * frac >> 16);
    uint8_t t = v - ((uint32_t)vs * (255 - frac) >> 16);

    switch (sector) {
        case 0:  *r = v; *g = t; *b = p; break;
        case 1:  *r = q; *g = v; *b = p; break;
        case 2:  *r = p; *g = v; *b = t; break;
        case 3:  *r = p; *g = q; *b = v; break;
        case 4:  *r = t; *g = p; *b = v; break;
        default: *r = v; *g = p; *b = q; break;
    }
}

static mp_obj_t hsv_to_rgb565(mp_obj_t h_obj, mp_obj_t s_obj, mp_obj_t v_obj) {
    uint8_t h = (uint8_t)mp_obj_get_int(h_obj);
    uint8_t s = (uint8_t)mp_obj_get_int(s_obj);
    uint8_t v = (uint8_t)mp_obj_get_int(v_obj);

    uint16_t result = hsv_to_rgb565_impl(h, s, v);

    return MP_OBJ_NEW_SMALL_INT(result);
}

/**
 * Convert HSV to RGB888 tuple using division-free math.
 * Same algorithm as hsv_to_rgb565 but returns (r, g, b) tuple.
 *
 * @param h Hue: 0-255 (full color wheel)
 * @param s Saturation: 0-255
 * @param v Value/Brightness: 0-255
 * @return Tuple of (r, g, b) each 0-255
 */
static mp_obj_t hsv_to_rgb888(mp_obj_t h_obj, mp_obj_t s_obj, mp_obj_t v_obj) {
    uint8_t h = (uint8_t)mp_obj_get_int(h_obj);
    uint8_t s = (uint8_t)mp_obj_get_int(s_obj);
    uint8_t v = (uint8_t)mp_obj_get_int(v_obj);

    uint8_t r, g, b;

    if (s == 0) {
        r = g = b = v;
    } else {
        // Scale hue to 0-1530 range, then extract sector and fraction
        uint16_t h6 = (uint16_t)h * 6;
        uint8_t sector = h6 >> 8;
        uint8_t frac = h6 & 0xFF;

        uint16_t vs = (uint16_t)v * s;
        uint8_t p = v - (vs >> 8);
        uint8_t q = v - ((uint32_t)vs * frac >> 16);
        uint8_t t = v - ((uint32_t)vs * (255 - frac) >> 16);

        switch (sector) {
            case 0:  r = v; g = t; b = p; break;
            case 1:  r = q; g = v; b = p; break;
            case 2:  r = p; g = v; b = t; break;
            case 3:  r = p; g = q; b = v; break;
            case 4:  r = t; g = p; b = v; break;
            default: r = v; g = p; b = q; break;
        }
    }

    mp_obj_t items[3] = {
        MP_OBJ_NEW_SMALL_INT(r),
        MP_OBJ_NEW_SMALL_INT(g),
        MP_OBJ_NEW_SMALL_INT(b)
    };

    return mp_obj_new_tuple(3, items);
}

/**
 * Render one frame of plasma effect directly to RGB565 buffer.
 *
 * @param buffer RGB565 framebuffer (width * height * 2 bytes)
 * @param width Display width in pixels
 * @param height Display height in pixels
 * @param t Time/frame counter for animation
 */
static void plasma_render(uint8_t *buffer, uint8_t width, uint8_t height, uint8_t t) {
    for (uint8_t y = 0; y < height; y++) {
        for (uint8_t x = 0; x < width; x++) {
            // Combine multiple sine waves for plasma effect
            uint8_t v1 = SIN_TABLE[(x + t) & 0xFF];
            uint8_t v2 = SIN_TABLE[(y + t) & 0xFF];
            uint8_t v3 = SIN_TABLE[((x + y) + t) & 0xFF];
            // Radial component: sqrt approximated by (x²+y²)>>4
            uint8_t v4 = SIN_TABLE[(((x * x + y * y) >> 4) + t) & 0xFF];

            // Average the waves to get hue (0-255)
            uint8_t hue = (v1 + v2 + v3 + v4) >> 2;

            // Convert to RGB888
            uint8_t r, g, b;
            hsv_to_rgb888_render(hue, 255, 255, &r, &g, &b);

            // Write RGB888
            size_t idx = ((size_t)y * width + x) * 3;
            buffer[idx] = r;
            buffer[idx + 1] = g;
            buffer[idx + 2] = b;
        }
    }
}

static mp_obj_t plasma_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t buffer;
    mp_get_buffer_raise(args[0], &buffer, MP_BUFFER_WRITE);

    uint8_t width = (uint8_t)mp_obj_get_int(args[1]);
    uint8_t height = (uint8_t)mp_obj_get_int(args[2]);
    uint8_t t = (uint8_t)mp_obj_get_int(args[3]);

    plasma_render((uint8_t *)buffer.buf, width, height, t);

    return mp_const_none;
}

/**
 * Render one frame of Doom-style fire effect.
 *
 * @param fire_buf Fire intensity buffer (width * height bytes, values 0-36)
 * @param rgb_buf RGB565 output buffer (width * height * 2 bytes)
 * @param width Display width in pixels
 * @param height Display height in pixels
 * @param t Frame counter for animation
 */
static void fire_render(uint8_t *fire_buf, uint8_t *rgb_buf, uint8_t width, uint8_t height, uint8_t t) {
    // Propagate fire upward with cooling and horizontal spread
    for (int y = 0; y < height - 1; y++) {
        for (int x = 0; x < width; x++) {
            // Get pixel below
            int src_idx = (y + 1) * width + x;
            uint8_t src_val = fire_buf[src_idx];

            // Pseudo-random value from position and frame (stateless)
            uint32_t rand = fire_hash(x, y, t);

            // Horizontal drift: -1, 0, +1 based on lower bits
            int dst_x = x - (int)(rand & 1) + (int)((rand >> 1) & 1);
            if (dst_x < 0) dst_x = 0;
            if (dst_x >= width) dst_x = width - 1;

            int decay = ((rand >> 2) & 3);
            int new_val = (int)src_val - decay;
            if (new_val < 0) new_val = 0;

            int dst_idx = y * width + dst_x;
            fire_buf[dst_idx] = (uint8_t)new_val;
        }
    }

    // Convert fire buffer to RGB888
    for (int i = 0; i < width * height; i++) {
        uint8_t intensity = fire_buf[i];
        if (intensity > 36) intensity = 36;
        size_t pal_idx = intensity * 3;
        rgb_buf[i * 3] = FIRE_PALETTE[pal_idx];
        rgb_buf[i * 3 + 1] = FIRE_PALETTE[pal_idx + 1];
        rgb_buf[i * 3 + 2] = FIRE_PALETTE[pal_idx + 2];
    }
}

static mp_obj_t fire_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t fire_buffer;
    mp_buffer_info_t rgb_buffer;

    mp_get_buffer_raise(args[0], &fire_buffer, MP_BUFFER_WRITE);
    mp_get_buffer_raise(args[1], &rgb_buffer, MP_BUFFER_WRITE);

    uint8_t width = (uint8_t)mp_obj_get_int(args[2]);
    uint8_t height = (uint8_t)mp_obj_get_int(args[3]);
    uint8_t t = (uint8_t)mp_obj_get_int(args[4]);

    fire_render((uint8_t *)fire_buffer.buf, (uint8_t *)rgb_buffer.buf, width, height, t);

    return mp_const_none;
}

/**
 * Render one frame of Balatro-style spiral effect.
 *
 * @param angle_table Pre-computed angles (atan2) for each pixel, 0-255
 * @param radius_table Pre-computed radii (sqrt) for each pixel, 0-255
 * @param rgb_buf RGB565 output buffer
 * @param width Display width
 * @param height Display height
 * @param t Frame counter for rotation
 * @param tightness How tight the spiral winds (higher = more arms)
 */
static void spiral_render(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *rgb_buf,
    uint16_t pixel_count,
    uint8_t t,
    uint8_t tightness
) {
    for (uint16_t i = 0; i < pixel_count; i++) {
        // Core spiral formula: hue = angle + radius*tightness + time
        uint8_t hue = angle_table[i] + ((radius_table[i] * tightness) >> 4) + t;

        uint8_t r, g, b;
        hsv_to_rgb888_render(hue, 255, 255, &r, &g, &b);
        rgb_buf[i * 3] = r;
        rgb_buf[i * 3 + 1] = g;
        rgb_buf[i * 3 + 2] = b;
    }
}

static mp_obj_t spiral_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t angle_buffer;
    mp_buffer_info_t radius_buffer;
    mp_buffer_info_t rgb_buffer;

    mp_get_buffer_raise(args[0], &angle_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[1], &radius_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[2], &rgb_buffer, MP_BUFFER_WRITE);

    uint8_t width = (uint8_t)mp_obj_get_int(args[3]);
    uint8_t height = (uint8_t)mp_obj_get_int(args[4]);
    uint8_t t = (uint8_t)mp_obj_get_int(args[5]);
    uint8_t tightness = (uint8_t)mp_obj_get_int(args[6]);

    uint16_t pixel_count = (uint16_t)width * height;

    spiral_render(
        (const uint8_t *)angle_buffer.buf,
        (const uint8_t *)radius_buffer.buf,
        (uint8_t *)rgb_buffer.buf,
        pixel_count, t, tightness
    );

    return mp_const_none;
}

/**
 * Render one frame of Balatro-style psychedelic spiral effect.
 *
 * This replicates the hypnotic background from Balatro using:
 * - Spiral base value from angle + radius creates swirling bands
 * - Domain warping with multiple sine waves for organic wobble
 * - Smooth 256-color gradient (red -> blue -> dark -> red)
 *
 * The key insight is using the SPIRAL VALUE (not distance) for color selection,
 * which creates the characteristic swirling color bands.
 */
static void balatro_render(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *rgb_buf,
    uint8_t width, uint8_t height,
    uint16_t t,
    uint8_t spin_speed,
    uint8_t warp_amount
) {
    for (uint8_t y = 0; y < height; y++) {
        for (uint8_t x = 0; x < width; x++) {
            uint16_t idx = (uint16_t)y * width + x;

            // Get pre-computed angle and radius
            uint8_t angle = angle_table[idx];
            uint8_t radius = radius_table[idx];

            // Create spiral: angle + radius*tightness + time
            // Using >> 2 instead of >> 3 to "zoom out" and show more of the pattern
            int16_t spiral = (int16_t)angle + ((radius * spin_speed) >> 2) - (t >> 1);

            // Domain warping - multiple layers of sine-based distortion
            // This creates the organic, wobbly boundaries between colors
            int16_t warp = 0;

            // Layer 1: Position-based low frequency
            uint8_t w1 = (uint8_t)((x * 5 + y * 7 + (t >> 2)) & 0xFF);
            warp += (int8_t)(SIN_TABLE[w1] - 128);

            // Layer 2: Spiral-based (warps along the spiral bands)
            uint8_t w2 = (uint8_t)((spiral + radius + (t >> 1)) & 0xFF);
            warp += (int8_t)(SIN_TABLE[w2] - 128);

            // Layer 3: High frequency detail
            uint8_t w3 = (uint8_t)((x * 11 - y * 13 + t) & 0xFF);
            warp += (int8_t)(SIN_TABLE[w3] - 128) >> 1;

            // Layer 4: Angle-based swirl
            uint8_t w4 = (uint8_t)((angle * 3 + (t >> 2)) & 0xFF);
            warp += (int8_t)(SIN_TABLE[w4] - 128) >> 1;

            // Layer 5: Radius-based (creates variation from center to edge)
            uint8_t w5 = (uint8_t)((radius * 4 - t) & 0xFF);
            warp += (int8_t)(SIN_TABLE[w5] - 128) >> 2;

            // Apply warp to spiral value
            // warp_amount controls how much organic distortion (1-15)
            int16_t warped_spiral = spiral + ((warp * warp_amount) >> 6);

            // Final band value (wraps 0-255)
            uint8_t band_val = (uint8_t)(warped_spiral & 0xFF);

            // Look up color from smooth gradient table (RGB888)
            size_t grad_idx = band_val * 3;
            rgb_buf[idx * 3] = BALATRO_GRADIENT[grad_idx];
            rgb_buf[idx * 3 + 1] = BALATRO_GRADIENT[grad_idx + 1];
            rgb_buf[idx * 3 + 2] = BALATRO_GRADIENT[grad_idx + 2];
        }
    }
}

static mp_obj_t balatro_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t angle_buffer;
    mp_buffer_info_t radius_buffer;
    mp_buffer_info_t rgb_buffer;

    mp_get_buffer_raise(args[0], &angle_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[1], &radius_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[2], &rgb_buffer, MP_BUFFER_WRITE);

    uint8_t width = (uint8_t)mp_obj_get_int(args[3]);
    uint8_t height = (uint8_t)mp_obj_get_int(args[4]);
    uint16_t t = (uint16_t)mp_obj_get_int(args[5]);
    uint8_t spin_speed = (uint8_t)mp_obj_get_int(args[6]);
    uint8_t contrast = (uint8_t)mp_obj_get_int(args[7]);

    balatro_render(
        (const uint8_t *)angle_buffer.buf,
        (const uint8_t *)radius_buffer.buf,
        (uint8_t *)rgb_buffer.buf,
        width, height, t, spin_speed, contrast
    );

    return mp_const_none;
}

static MP_DEFINE_CONST_FUN_OBJ_2(load_rgb888_obj, load_rgb888);
static MP_DEFINE_CONST_FUN_OBJ_2(load_rgb565_obj, load_rgb565);
static MP_DEFINE_CONST_FUN_OBJ_1(clear_obj, clear);
static MP_DEFINE_CONST_FUN_OBJ_3(hsv_to_rgb565_obj, hsv_to_rgb565);
static MP_DEFINE_CONST_FUN_OBJ_3(hsv_to_rgb888_obj, hsv_to_rgb888);
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(plasma_frame_obj, 4, 4, plasma_frame);
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(fire_frame_obj, 5, 5, fire_frame);
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(spiral_frame_obj, 7, 7, spiral_frame);
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(balatro_frame_obj, 8, 8, balatro_frame);

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY;

    mp_store_global(MP_QSTR_load_rgb888, MP_OBJ_FROM_PTR(&load_rgb888_obj));
    mp_store_global(MP_QSTR_load_rgb565, MP_OBJ_FROM_PTR(&load_rgb565_obj));
    mp_store_global(MP_QSTR_clear, MP_OBJ_FROM_PTR(&clear_obj));
    mp_store_global(MP_QSTR_hsv_to_rgb565, MP_OBJ_FROM_PTR(&hsv_to_rgb565_obj));
    mp_store_global(MP_QSTR_hsv_to_rgb888, MP_OBJ_FROM_PTR(&hsv_to_rgb888_obj));
    mp_store_global(MP_QSTR_plasma_frame, MP_OBJ_FROM_PTR(&plasma_frame_obj));
    mp_store_global(MP_QSTR_fire_frame, MP_OBJ_FROM_PTR(&fire_frame_obj));
    mp_store_global(MP_QSTR_spiral_frame, MP_OBJ_FROM_PTR(&spiral_frame_obj));
    mp_store_global(MP_QSTR_balatro_frame, MP_OBJ_FROM_PTR(&balatro_frame_obj));

    MP_DYNRUNTIME_INIT_EXIT;
}