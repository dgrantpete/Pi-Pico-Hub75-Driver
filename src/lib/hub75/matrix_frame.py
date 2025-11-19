from hub75.ppm import PPMImage

class MatrixFrame:
    def __init__(self, data: memoryview, width: int, height: int):
        # Should have 1 byte per pixel per color (RGB)
        expected_size = width * height * 3

        if expected_size != len(data):
            raise ValueError(f"Expected {expected_size} bytes ({width=} * {height=} * 3), got {len(data)}")
        
        self._data = data
        self._width = width
        self._height = height

    @property
    @micropython.native
    def data(self) -> memoryview:
        return self._data
    
    @property
    @micropython.native
    def width(self) -> int:
        return self._width
    
    @property
    @micropython.native
    def height(self) -> int:
        return self._height

    @classmethod
    @micropython.native
    def from_ppm(cls, ppm: PPMImage):
        if ppm.magic_number == 'P6':
            data = cls._format_p6_data(ppm)
            return cls(data, ppm.width, ppm.height)
        else:
            raise ValueError(f"Format {ppm.magic_number!r} not supported")

    @classmethod
    @micropython.native
    def _format_p6_data(cls, ppm: PPMImage) -> memoryview:
        if ppm.max_value is None:
            raise ValueError("'P6' format requires a 'max_value'")
        
        if ppm.max_value <= 0:
            raise ValueError("'max_value' must be positive")
        
        # PPM spec: 1 byte per channel if max_value < 256, else 2 bytes
        bytes_per_channel = 1 if ppm.max_value < 256 else 2

        output_size = ppm.width * ppm.height * 3
        expected_input_size = output_size * bytes_per_channel

        if expected_input_size != len(ppm.image_data):
            raise ValueError(f"Expected {expected_input_size} bytes ({ppm.width=} * {ppm.height=} * 3 * {bytes_per_channel=}), got {len(ppm.image_data)}")

        output = bytearray(output_size)

        cls._p6_scale_loop(
            ppm.image_data,
            output,
            output_size,
            bytes_per_channel,
            ppm.max_value
        )

        return memoryview(output)

    @staticmethod
    @micropython.viper
    def _p6_scale_loop(
        input_data: ptr8,
        output_data: ptr8,
        output_size: int,
        bytes_per_channel: int,
        max_value: int
    ):
        output_index = 0
        input_index = 0

        while output_index < output_size:
            if bytes_per_channel == 1:
                value = input_data[input_index]
            else:
                value = (input_data[input_index] << 8) | input_data[input_index + 1]

            output_data[output_index] = (value * 255) // max_value

            output_index += 1
            input_index += bytes_per_channel