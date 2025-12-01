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
uint16_t hsv_to_rgb565_impl(uint8_t h, uint8_t s, uint8_t v);

/**
 * Convert HSV to RGB888 for internal render functions.
 * Writes directly to output pointers (no MicroPython object overhead).
 *
 * @param h Hue: 0-255 (full color wheel)
 * @param s Saturation: 0-255
 * @param v Value/Brightness: 0-255
 * @param r Output red component
 * @param g Output green component
 * @param b Output blue component
 */
void hsv_to_rgb888_render(uint8_t h, uint8_t s, uint8_t v,
                          uint8_t *r, uint8_t *g, uint8_t *b);

#endif
