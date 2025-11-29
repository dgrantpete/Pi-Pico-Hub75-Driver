#include "py/dynruntime.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

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

static MP_DEFINE_CONST_FUN_OBJ_2(load_rgb888_obj, load_rgb888);
static MP_DEFINE_CONST_FUN_OBJ_2(load_rgb565_obj, load_rgb565);
static MP_DEFINE_CONST_FUN_OBJ_1(clear_obj, clear);

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY;

    mp_store_global(MP_QSTR_load_rgb888, MP_OBJ_FROM_PTR(&load_rgb888_obj));
    mp_store_global(MP_QSTR_load_rgb565, MP_OBJ_FROM_PTR(&load_rgb565_obj));
    mp_store_global(MP_QSTR_clear, MP_OBJ_FROM_PTR(&clear_obj));

    MP_DYNRUNTIME_INIT_EXIT;
}