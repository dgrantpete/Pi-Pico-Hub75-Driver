#ifndef COLOR_H
#define COLOR_H

#include <stdint.h>

uint16_t hsv_to_rgb565_kernel(uint8_t hue, uint8_t saturation, uint8_t value);

void hsv_to_rgb_kernel(uint8_t hue, uint8_t saturation, uint8_t value, uint8_t *r, uint8_t *g, uint8_t *b);

#endif
