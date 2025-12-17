#ifndef RENDER_H
#define RENDER_H

#include <stdint.h>

void plasma_render(uint8_t *buffer, uint8_t width, uint8_t height, uint8_t t);

void fire_render(uint8_t *fire_buf, uint8_t *rgb_buf, uint8_t width, uint8_t height, uint8_t t);

void spiral_render(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *rgb_buf,
    uint16_t pixel_count,
    uint8_t t,
    uint8_t tightness
);

void balatro_render(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *rgb_buf,
    uint8_t width, uint8_t height,
    uint16_t t,
    uint8_t spin_speed,
    uint8_t warp_amount
);

#endif
