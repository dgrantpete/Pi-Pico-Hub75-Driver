#ifndef RENDER_H
#define RENDER_H

#include <stdint.h>

void render_plasma_frame_kernel(uint8_t *buffer, uint16_t width, uint16_t height, uint8_t frame_time);

void render_fire_frame_kernel(uint8_t *fire_buffer, uint8_t *buffer, uint16_t width, uint16_t height, uint8_t frame_time);

void render_spiral_frame_kernel(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *buffer,
    uint32_t pixel_count,
    uint8_t frame_time,
    uint8_t tightness
);

void render_balatro_frame_kernel(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *buffer,
    uint16_t width, uint16_t height,
    uint16_t frame_time,
    uint8_t spin_speed,
    uint8_t warp_amount
);

#endif
