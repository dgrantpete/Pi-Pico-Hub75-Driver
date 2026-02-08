#include "py/dynruntime.h"
#include <stdint.h>
#include <stddef.h>

#include "render.h"

static mp_obj_t render_plasma_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t buffer;
    mp_get_buffer_raise(args[0], &buffer, MP_BUFFER_WRITE);

    uint16_t width = (uint16_t)mp_obj_get_int(args[1]);
    uint16_t height = (uint16_t)mp_obj_get_int(args[2]);
    uint8_t frame_time = (uint8_t)mp_obj_get_int(args[3]);

    render_plasma_frame_kernel((uint8_t *)buffer.buf, width, height, frame_time);

    return mp_const_none;
}

static mp_obj_t render_fire_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t fire_buffer;
    mp_buffer_info_t buffer;

    mp_get_buffer_raise(args[0], &fire_buffer, MP_BUFFER_WRITE);
    mp_get_buffer_raise(args[1], &buffer, MP_BUFFER_WRITE);

    uint16_t width = (uint16_t)mp_obj_get_int(args[2]);
    uint16_t height = (uint16_t)mp_obj_get_int(args[3]);
    uint8_t frame_time = (uint8_t)mp_obj_get_int(args[4]);

    render_fire_frame_kernel((uint8_t *)fire_buffer.buf, (uint8_t *)buffer.buf, width, height, frame_time);

    return mp_const_none;
}

static mp_obj_t render_spiral_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t angle_buffer;
    mp_buffer_info_t radius_buffer;
    mp_buffer_info_t buffer;

    mp_get_buffer_raise(args[0], &angle_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[1], &radius_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[2], &buffer, MP_BUFFER_WRITE);

    uint16_t width = (uint16_t)mp_obj_get_int(args[3]);
    uint16_t height = (uint16_t)mp_obj_get_int(args[4]);
    uint8_t frame_time = (uint8_t)mp_obj_get_int(args[5]);
    uint8_t tightness = (uint8_t)mp_obj_get_int(args[6]);

    uint32_t pixel_count = (uint32_t)width * height;

    render_spiral_frame_kernel(
        (const uint8_t *)angle_buffer.buf,
        (const uint8_t *)radius_buffer.buf,
        (uint8_t *)buffer.buf,
        pixel_count,
        frame_time,
        tightness
    );

    return mp_const_none;
}

static mp_obj_t render_balatro_frame(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t angle_buffer;
    mp_buffer_info_t radius_buffer;
    mp_buffer_info_t buffer;

    mp_get_buffer_raise(args[0], &angle_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[1], &radius_buffer, MP_BUFFER_READ);
    mp_get_buffer_raise(args[2], &buffer, MP_BUFFER_WRITE);

    uint16_t width = (uint16_t)mp_obj_get_int(args[3]);
    uint16_t height = (uint16_t)mp_obj_get_int(args[4]);
    uint16_t frame_time = (uint16_t)mp_obj_get_int(args[5]);
    uint8_t spin_speed = (uint8_t)mp_obj_get_int(args[6]);
    uint8_t warp_amount = (uint8_t)mp_obj_get_int(args[7]);

    render_balatro_frame_kernel(
        (const uint8_t *)angle_buffer.buf,
        (const uint8_t *)radius_buffer.buf,
        (uint8_t *)buffer.buf,
        width,
        height,
        frame_time,
        spin_speed,
        warp_amount
    );

    return mp_const_none;
}

static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(render_plasma_frame_obj, 4, 4, render_plasma_frame);
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(render_fire_frame_obj, 5, 5, render_fire_frame);
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(render_spiral_frame_obj, 7, 7, render_spiral_frame);
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(render_balatro_frame_obj, 8, 8, render_balatro_frame);

// IntelliSense stubs for module-specific QSTRs (generated at build time)
#ifdef __INTELLISENSE__
#define MP_QSTR_render_plasma_frame (0)
#define MP_QSTR_render_fire_frame (0)
#define MP_QSTR_render_spiral_frame (0)
#define MP_QSTR_render_balatro_frame (0)
#endif

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY;

    mp_store_global(MP_QSTR_render_plasma_frame, MP_OBJ_FROM_PTR(&render_plasma_frame_obj));
    mp_store_global(MP_QSTR_render_fire_frame, MP_OBJ_FROM_PTR(&render_fire_frame_obj));
    mp_store_global(MP_QSTR_render_spiral_frame, MP_OBJ_FROM_PTR(&render_spiral_frame_obj));
    mp_store_global(MP_QSTR_render_balatro_frame, MP_OBJ_FROM_PTR(&render_balatro_frame_obj));

    MP_DYNRUNTIME_INIT_EXIT;
}
