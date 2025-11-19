class PPMImage:
    def __init__(self, *, magic_number, width, height, max_value, image_data):
        self._magic_number = magic_number
        self._width = width
        self._height = height
        self._max_value = max_value
        self._image_data = image_data

    @property
    def magic_number(self) -> str:
        return self._magic_number
    
    @property
    def width(self) -> int:
        return self._width
    
    @property
    def height(self) -> int:
        return self._height
    
    @property
    def max_value(self) -> int | None:
        return self._max_value
    
    @property
    def image_data(self) -> memoryview:
        return self._image_data