#include "py/dynruntime.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifndef COLOR_BIT_DEPTH
#error "'COLOR_BIT_DEPTH' must be defined"
#endif

#ifndef SCALE_SHIFT
#define SCALE_SHIFT (24)
#endif

// Fixed-point scaling helper:
// returns floor(v * 255 / max_value) exactly, with at most one correction step.
static inline uint32_t scale_channel(uint32_t v, uint32_t scale, uint32_t max_value) {
    uint32_t q = (v * scale) >> SCALE_SHIFT;  // fast approx
    uint32_t num = v * 255u;                  // true numerator

    if ((q + 1u) * max_value <= num) {
        q += 1u;
    }
    return q; // 0..255
}

static void load_ppm_kernel(
    const uint8_t * restrict input_data,
    size_t input_size,
    uint8_t * restrict output_data,
    size_t output_size,
    uint32_t max_value
) {
    const size_t bottom_offset  = input_size / 2;
    const size_t bitplane_size  = output_size / COLOR_BIT_DEPTH;

    const size_t bytes_per_chan = (max_value < 256) ? 1u : 2u;

    // One-time reciprocal to avoid division in the inner loop.
    const uint32_t scale = (255u << SCALE_SHIFT) / max_value;
    
    // Output bit positions (HUB75 pin packing)
    const uint8_t R1_BIT = 0b10000000;
    const uint8_t G1_BIT = 0b01000000;
    const uint8_t B1_BIT = 0b00100000;
    const uint8_t R2_BIT = 0b00010000;
    const uint8_t G2_BIT = 0b00001000;
    const uint8_t B2_BIT = 0b00000100;

    size_t input_index     = 0;
    size_t bitplane_offset = 0;

    while (input_index < bottom_offset) {

        // ---- 1) Read raw channels for top (1) and bottom (2) pixels ----
        uint32_t r1_raw, g1_raw, b1_raw;
        uint32_t r2_raw, g2_raw, b2_raw;

        if (bytes_per_chan == 1) {
            // 8-bit channels
            r1_raw = input_data[input_index];
            g1_raw = input_data[input_index + 1];
            b1_raw = input_data[input_index + 2];

            r2_raw = input_data[input_index + bottom_offset];
            g2_raw = input_data[input_index + bottom_offset + 1];
            b2_raw = input_data[input_index + bottom_offset + 2];

            input_index += 3;
        } else {
            // 16-bit channels stored big-endian in PPM
            r1_raw = ((uint32_t)input_data[input_index] << 8) |
                     (uint32_t)input_data[input_index + 1];
            g1_raw = ((uint32_t)input_data[input_index + 2] << 8) |
                     (uint32_t)input_data[input_index + 3];
            b1_raw = ((uint32_t)input_data[input_index + 4] << 8) |
                     (uint32_t)input_data[input_index + 5];

            r2_raw = ((uint32_t)input_data[input_index + bottom_offset] << 8) |
                     (uint32_t)input_data[input_index + bottom_offset + 1];
            g2_raw = ((uint32_t)input_data[input_index + bottom_offset + 2] << 8) |
                     (uint32_t)input_data[input_index + bottom_offset + 3];
            b2_raw = ((uint32_t)input_data[input_index + bottom_offset + 4] << 8) |
                     (uint32_t)input_data[input_index + bottom_offset + 5];

            input_index += 6;
        }

        // ---- 2) Scale to 0..255 ----
        const uint32_t r1 = scale_channel(r1_raw, scale, max_value);
        const uint32_t g1 = scale_channel(g1_raw, scale, max_value);
        const uint32_t b1 = scale_channel(b1_raw, scale, max_value);

        const uint32_t r2 = scale_channel(r2_raw, scale, max_value);
        const uint32_t g2 = scale_channel(g2_raw, scale, max_value);
        const uint32_t b2 = scale_channel(b2_raw, scale, max_value);

        uint8_t *out = output_data + bitplane_offset;

        for (size_t p = 0; p < COLOR_BIT_DEPTH; p++) {
            const size_t shift = p + (8 - COLOR_BIT_DEPTH);

            uint8_t packed = 0;
            packed |= ((r1 >> shift) & 1u) * R1_BIT;
            packed |= ((g1 >> shift) & 1u) * G1_BIT;
            packed |= ((b1 >> shift) & 1u) * B1_BIT;
            packed |= ((r2 >> shift) & 1u) * R2_BIT;
            packed |= ((g2 >> shift) & 1u) * G2_BIT;
            packed |= ((b2 >> shift) & 1u) * B2_BIT;

            out[p * bitplane_size] = packed;
        }

        bitplane_offset += 1;
    }
}



static mp_obj_t load_ppm(mp_obj_t input_obj, mp_obj_t output_obj, mp_obj_t max_value_obj) {
    mp_buffer_info_t input_buf;
    mp_buffer_info_t output_buf;

    mp_get_buffer_raise(input_obj, &input_buf, MP_BUFFER_READ);

    mp_get_buffer_raise(output_obj, &output_buf, MP_BUFFER_WRITE);

    const uint8_t *input_data = (const uint8_t *)input_buf.buf;
    size_t input_size = input_buf.len;

    uint8_t *output_data = (uint8_t *)output_buf.buf;
    size_t output_size = output_buf.len;

    mp_int_t max_value_signed = mp_obj_get_int(max_value_obj);

    if (max_value_signed <= 0) {
        mp_raise_ValueError(MP_ERROR_TEXT("'max_value' must be > 0"));
    }
    
    uint32_t max_value = (uint32_t)max_value_signed;

    load_ppm_kernel(input_data, input_size, output_data, output_size, max_value);

    return mp_const_none;
}

static MP_DEFINE_CONST_FUN_OBJ_3(load_ppm_obj, load_ppm);

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY;

    mp_store_global(MP_QSTR_load_ppm, MP_OBJ_FROM_PTR(&load_ppm_obj));

    MP_DYNRUNTIME_INIT_EXIT;
}