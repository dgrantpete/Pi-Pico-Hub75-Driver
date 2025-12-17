#ifndef COLOR_H
#define COLOR_H

#include <stdint.h>

uint16_t hsv_to_rgb565_kernel(uint8_t h, uint8_t s, uint8_t v);

void hsv_to_rgb_kernel(uint8_t h, uint8_t s, uint8_t v,
                       uint8_t *r, uint8_t *g, uint8_t *b);

#endif
