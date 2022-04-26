import configparser
import os
import numpy as np
import cv2 as cv
import sys

'''

Please go to "config.ini", located in the same directory as this file, to edit basic preferences.


'''

cwd = os.path.dirname(sys.argv[0])

os.chdir(cwd)

read_parser = configparser.ConfigParser()
read_parser.read('config.ini')

try:
    IMAGE_HEIGHT = read_parser.getint('dimensions', 'IMAGE_HEIGHT')
    IMAGE_WIDTH = read_parser.getint('dimensions', 'IMAGE_WIDTH')
    COLOR_MODULATION_MODE = read_parser.get('misc', 'COLOR_MODULATION_MODE')
    WRITE_DIR = read_parser.get('files', 'WRITE_DIR')
    READ_DIR = read_parser.get('files', 'READ_DIR')

except:
    raise ImportError("There was an issue importing data from 'config.ini', ensure neccessary data is there and of correct type.")

os.makedirs(WRITE_DIR, exist_ok=True)

if COLOR_MODULATION_MODE == "high_freq":
    def encode(color_value):
        if color_value > 0:
            index_scalar = 15 / color_value
            true_indices = [int(index_scalar * i) for i in range(color_value)]
            encoded_color = [1 if (i in true_indices) else 0 for i in range(15)]
        else:
            encoded_color = [0] * 15
        return encoded_color

elif COLOR_MODULATION_MODE == "basic":
    def encode(color_value):
        encoded_color = [1 if (color_value > i) else 0 for i in range(15)]
        return encoded_color

else:
    raise ValueError(f"'COLOR_MODULATION_MODE' should be of type 'string' with a value of either 'basic' or 'high_freq', not '{str(COLOR_MODULATION_MODE)}'.")

for image_location in os.listdir(READ_DIR):

    array_image_data = cv.imread(READ_DIR + '/' + image_location)

    resized_image_data = cv.resize(array_image_data, (IMAGE_WIDTH, IMAGE_HEIGHT), interpolation=cv.INTER_AREA).astype(np.int64)

    scaled_colors_data = (resized_image_data//15).astype(np.int8)
   
    y_flipped_data = np.flip(scaled_colors_data, axis=0)

    half_height = IMAGE_HEIGHT // 2

    top_half_data, bottom_half_data = y_flipped_data[:half_height], y_flipped_data[half_height:]

    combined_halves_data = np.block([top_half_data, bottom_half_data])

    encoded_pixel_data = np.vectorize(encode, otypes=[list])(combined_halves_data)

    bin_values = np.array(encoded_pixel_data.tolist(), dtype=bool)
    byte_values_array = np.packbits(bin_values, axis=2, bitorder='little')
    byte_values_reshaped = np.moveaxis(byte_values_array, 3, 0)
    raw_byte_values = byte_values_reshaped.ravel()

    bytes_output = bytes(raw_byte_values)

    with open(WRITE_DIR + '/' + os.path.splitext(image_location)[0] + '.bin', 'wb') as output_file:
        output_file.write(bytes_output)
