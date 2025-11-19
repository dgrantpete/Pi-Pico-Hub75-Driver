"""
HUB75 LED Matrix Display Driver for MicroPython

A library for driving HUB75 RGB LED matrix panels on Raspberry Pi Pico and
other MicroPython-compatible microcontrollers.

Example usage:
    from hub75 import MatrixFrame, BitPlanes, parse_ppm_image
    import io

    # Parse a PPM image
    with open('image.ppm', 'rb') as f:
        ppm = parse_ppm_image(f)

    # Create a matrix frame
    frame = MatrixFrame.from_ppm(ppm)

    # Encode to bitplanes for display
    bitplanes = BitPlanes.from_matrix_frame(frame)
"""

__version__ = '1.0.0'
__author__ = 'Your Name'

from hub75.display import BitPlanes, COLOR_BIT_DEPTH
from hub75.matrix_frame import MatrixFrame
from hub75.ppm import PPMImage
from hub75.parsing import parse_ppm_image

__all__ = [
    'BitPlanes',
    'MatrixFrame',
    'PPMImage',
    'parse_ppm_image',
    'COLOR_BIT_DEPTH',
]
