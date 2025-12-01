#ifndef EFFECTS_H
#define EFFECTS_H

#include <stdint.h>

/**
 * Render one frame of plasma effect directly to RGB888 buffer.
 *
 * @param buffer RGB888 framebuffer (width * height * 3 bytes)
 * @param width Display width in pixels
 * @param height Display height in pixels
 * @param t Time/frame counter for animation
 */
void plasma_render(uint8_t *buffer, uint8_t width, uint8_t height, uint8_t t);

/**
 * Render one frame of Doom-style fire effect.
 *
 * @param fire_buf Fire intensity buffer (width * height bytes, values 0-36)
 * @param rgb_buf RGB888 output buffer (width * height * 3 bytes)
 * @param width Display width in pixels
 * @param height Display height in pixels
 * @param t Frame counter for animation
 */
void fire_render(uint8_t *fire_buf, uint8_t *rgb_buf,
                 uint8_t width, uint8_t height, uint8_t t);

/**
 * Render one frame of rainbow spiral effect.
 *
 * @param angle_table Pre-computed angles (atan2) for each pixel, 0-255
 * @param radius_table Pre-computed radii (sqrt) for each pixel, 0-255
 * @param rgb_buf RGB888 output buffer
 * @param pixel_count Total number of pixels
 * @param t Frame counter for rotation
 * @param tightness How tight the spiral winds (higher = more arms)
 */
void spiral_render(
    const uint8_t *angle_table,
    const uint8_t *radius_table,
    uint8_t *rgb_buf,
    uint16_t pixel_count,
    uint8_t t,
    uint8_t tightness
);

/**
 * Render one frame of Balatro-style psychedelic spiral effect.
 *
 * @param angle_table Pre-computed angles (atan2) for each pixel, 0-255
 * @param radius_table Pre-computed radii (sqrt) for each pixel, 0-255
 * @param rgb_buf RGB888 output buffer
 * @param width Display width
 * @param height Display height
 * @param t Frame counter for rotation
 * @param spin_speed Controls spiral tightness
 * @param warp_amount Controls organic distortion (1-15)
 */
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
