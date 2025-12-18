#ifndef RENDER_H
#define RENDER_H

#include <stdint.h>

void render_plasma(uint8_t *buffer, uint8_t width, uint8_t height, uint8_t frame_time);

void render_fire(uint8_t *fire_buffer, uint8_t *buffer, uint8_t width, uint8_t height, uint8_t frame_time);

void render_spiral(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *buffer,
    uint16_t pixel_count,
    uint8_t frame_time,
    uint8_t tightness
);

void render_balatro(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *buffer,
    uint8_t width, uint8_t height,
    uint16_t frame_time,
    uint8_t spin_speed,
    uint8_t warp_amount
);

#endif
