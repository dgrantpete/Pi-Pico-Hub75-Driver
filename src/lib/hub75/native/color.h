#ifndef COLOR_H
#define COLOR_H

#include <stdint.h>

/**
 * Convert HSV to RGB565 using division-free math.
 *
 * @param h Hue: 0-255 (full color wheel)
 * @param s Saturation: 0-255
 * @param v Value/Brightness: 0-255
 * @return RGB565 packed color
 */
uint16_t hsv_to_rgb565_kernel(uint8_t h, uint8_t s, uint8_t v);

/**
 * Core HSV to RGB conversion kernel.
 * Computes RGB components from HSV values.
 *
 * @param h Hue: 0-255 (full color wheel)
 * @param s Saturation: 0-255
 * @param v Value/Brightness: 0-255
 * @param r Output red component (0-255)
 * @param g Output green component (0-255)
 * @param b Output blue component (0-255)
 */
void hsv_to_rgb_kernel(uint8_t h, uint8_t s, uint8_t v,
                       uint8_t *r, uint8_t *g, uint8_t *b);

#endif
