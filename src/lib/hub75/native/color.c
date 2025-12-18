#include "color.h"

uint16_t hsv_to_rgb565_kernel(uint8_t hue, uint8_t saturation, uint8_t value) {
    // Grayscale fast path
    if (saturation == 0) {
        return ((uint16_t)(value & 0xF8) << 8) | ((uint16_t)(value & 0xFC) << 3) | (value >> 3);
    }

    // Scale hue to 0-1530 range, then extract sector and fraction
    // This avoids division: sector = hue * 6 / 256, frac = (hue * 6) % 256
    uint16_t scaled_hue = (uint16_t)hue * 6;
    uint8_t hue_sector = scaled_hue >> 8; // 0-5
    uint8_t sector_fraction = scaled_hue & 0xFF; // 0-255 within sector

    // Intermediate values using only multiply and shift
    uint16_t chroma_range = (uint16_t)value * saturation;
    uint8_t min_component = value - (chroma_range >> 8);
    uint8_t descending_component = value - ((uint32_t)chroma_range * sector_fraction >> 16);
    uint8_t ascending_component = value - ((uint32_t)chroma_range * (255 - sector_fraction) >> 16);

    uint8_t r, g, b;

    switch (hue_sector) {
        case 0:  r = value; g = ascending_component; b = min_component; break; // Red -> Yellow
        case 1:  r = descending_component; g = value; b = min_component; break; // Yellow -> Green
        case 2:  r = min_component; g = value; b = ascending_component; break; // Green -> Cyan
        case 3:  r = min_component; g = descending_component; b = value; break; // Cyan -> Blue
        case 4:  r = ascending_component; g = min_component; b = value; break; // Blue -> Magenta
        default: r = value; g = min_component; b = descending_component; break; // Magenta -> Red
    }

    return ((uint16_t)(r & 0xF8) << 8) | ((uint16_t)(g & 0xFC) << 3) | (b >> 3);
}

void hsv_to_rgb_kernel(uint8_t hue, uint8_t saturation, uint8_t value, uint8_t *r, uint8_t *g, uint8_t *b) {
    if (saturation == 0) {
        *r = *g = *b = value;
        return;
    }

    uint16_t scaled_hue = (uint16_t)hue * 6;
    uint8_t hue_sector = scaled_hue >> 8;
    uint8_t sector_fraction = scaled_hue & 0xFF;

    uint16_t chroma_range = (uint16_t)value * saturation;
    uint8_t min_component = value - (chroma_range >> 8);
    uint8_t descending_component = value - ((uint32_t)chroma_range * sector_fraction >> 16);
    uint8_t ascending_component = value - ((uint32_t)chroma_range * (255 - sector_fraction) >> 16);

    switch (hue_sector) {
        case 0:  *r = value; *g = ascending_component; *b = min_component; break;
        case 1:  *r = descending_component; *g = value; *b = min_component; break;
        case 2:  *r = min_component; *g = value; *b = ascending_component; break;
        case 3:  *r = min_component; *g = descending_component; *b = value; break;
        case 4:  *r = ascending_component; *g = min_component; *b = value; break;
        default: *r = value; *g = min_component; *b = descending_component; break;
    }
}
