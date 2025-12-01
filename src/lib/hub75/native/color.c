#include "color.h"

uint16_t hsv_to_rgb565_impl(uint8_t h, uint8_t s, uint8_t v) {
    // Grayscale fast path
    if (s == 0) {
        return ((uint16_t)(v & 0xF8) << 8) | ((uint16_t)(v & 0xFC) << 3) | (v >> 3);
    }

    // Scale hue to 0-1530 range, then extract sector and fraction
    // This avoids division: sector = h*6/256, frac = (h*6)%256
    uint16_t h6 = (uint16_t)h * 6;
    uint8_t sector = h6 >> 8;       // 0-5
    uint8_t frac = h6 & 0xFF;       // 0-255 within sector

    // Intermediate values using only multiply and shift
    uint16_t vs = (uint16_t)v * s;
    uint8_t p = v - (vs >> 8);                              // min
    uint8_t q = v - ((uint32_t)vs * frac >> 16);            // ramp down
    uint8_t t = v - ((uint32_t)vs * (255 - frac) >> 16);    // ramp up

    uint8_t r, g, b;

    switch (sector) {
        case 0:  r = v; g = t; b = p; break;  // Red -> Yellow
        case 1:  r = q; g = v; b = p; break;  // Yellow -> Green
        case 2:  r = p; g = v; b = t; break;  // Green -> Cyan
        case 3:  r = p; g = q; b = v; break;  // Cyan -> Blue
        case 4:  r = t; g = p; b = v; break;  // Blue -> Magenta
        default: r = v; g = p; b = q; break;  // Magenta -> Red
    }

    // Pack as RGB565: RRRRRGGGGGGBBBBB
    return ((uint16_t)(r & 0xF8) << 8) | ((uint16_t)(g & 0xFC) << 3) | (b >> 3);
}

void hsv_to_rgb888_render(uint8_t h, uint8_t s, uint8_t v,
                          uint8_t *r, uint8_t *g, uint8_t *b) {
    if (s == 0) {
        *r = *g = *b = v;
        return;
    }

    uint16_t h6 = (uint16_t)h * 6;
    uint8_t sector = h6 >> 8;
    uint8_t frac = h6 & 0xFF;

    uint16_t vs = (uint16_t)v * s;
    uint8_t p = v - (vs >> 8);
    uint8_t q = v - ((uint32_t)vs * frac >> 16);
    uint8_t t = v - ((uint32_t)vs * (255 - frac) >> 16);

    switch (sector) {
        case 0:  *r = v; *g = t; *b = p; break;
        case 1:  *r = q; *g = v; *b = p; break;
        case 2:  *r = p; *g = v; *b = t; break;
        case 3:  *r = p; *g = q; *b = v; break;
        case 4:  *r = t; *g = p; *b = v; break;
        default: *r = v; *g = p; *b = q; break;
    }
}
