import micropython

_DIGITS = {ord('0') + digit for digit in range(10)}
_NEWLINES = {ord(newline) for newline in '\r\n'}
_WHITESPACES = {ord(whitespace) for whitespace in ' \n\r\t\v\f'}

_BITMAP_FORMATS = {'P4'}
_GREYSCALE_FORMATS = {'P5'}
_COLOR_FORMATS = {'P6'}

class PPMImage:
    def __init__(self, *, magic_number, width, height, max_value, image_data):
        self._magic_number = magic_number
        self._width = width
        self._height = height
        self._max_value = max_value
        self._image_data = image_data

    @property
    @micropython.native
    def magic_number(self) -> str:
        return self._magic_number
    
    @property
    @micropython.native
    def width(self) -> int:
        return self._width
    
    @property
    @micropython.native
    def height(self) -> int:
        return self._height
    
    @property
    @micropython.native
    def max_value(self) -> int | None:
        return self._max_value
    
    @property
    @micropython.native
    def image_data(self) -> memoryview:
        return self._image_data
    
    @classmethod
    @micropython.native
    def from_file(cls, file) -> PPMImage:
        cursor = BufferCursor(file)

        magic_number = cls._parse_magic_number(cursor)

        cls._skip_trivia(cursor)
        width = cls._parse_number(cursor)

        cls._skip_trivia(cursor)
        height = cls._parse_number(cursor)

        image_size = width * height

        if magic_number in _BITMAP_FORMATS:
            max_value = None
            expected_byte_count = -(-image_size // 8)
        elif magic_number in _GREYSCALE_FORMATS:
            cls._skip_trivia(cursor)
            max_value = cls._parse_number(cursor)
            expected_byte_count = (2 if max_value >= 256 else 1) * image_size
        elif magic_number in _COLOR_FORMATS:
            cls._skip_trivia(cursor)
            max_value = cls._parse_number(cursor)
            expected_byte_count = (2 if max_value >= 256 else 1) * image_size * 3
        else:
            raise ValueError(f"Unsupported PPM format: {magic_number!r}")

        # Only a single whitespace character should be skipped per the specification
        cls._skip_whitespace(cursor)

        image_data = cursor.read(expected_byte_count)

        if len(image_data) != expected_byte_count:
            raise ValueError(f"PPM image data is incomplete: expected {expected_byte_count} bytes, got {len(image_data)} bytes")

        return cls(
            magic_number=magic_number,
            width=width,
            height=height,
            max_value=max_value,
            image_data=image_data
        )
    
    @classmethod
    @micropython.native
    def _parse_magic_number(cls, cursor: BufferCursor) -> str:
        if cursor.current != ord('P'):
            raise ValueError(cursor.format_error_message("magic number must begin with 'P'"))
        
        cursor.require_next("parsing magic number")

        number = cls._parse_number(cursor)

        return f"P{number}"
    
    @staticmethod
    @micropython.native
    def _parse_number(cursor: BufferCursor) -> int:
        if not cursor.current in _DIGITS:
            raise ValueError(cursor.format_error_message("expected digit while parsing number"))
        
        number = cursor.current - ord('0')

        while cursor.next() and cursor.current in _DIGITS:
            number = (number * 10) + (cursor.current - ord('0'))

        return number

    @classmethod
    @micropython.native
    def _skip_trivia(cls, cursor: BufferCursor):
        trivia_skipped = False

        while True:
            if cursor.current == ord('#'):
                cls._skip_comment(cursor)
                trivia_skipped = True
                continue

            if cursor.current in _WHITESPACES:
                cls._skip_whitespace(cursor)
                trivia_skipped = True
                continue

            break

        if not trivia_skipped:
            raise ValueError("expected trivia to skip (comments or whitespace)")

    @classmethod
    @micropython.native
    def _skip_comment(cls, cursor: BufferCursor):
        if not cursor.current == ord('#'):
            raise ValueError(cursor.format_error_message("expected comment to skip"))

        while not cursor.current in _NEWLINES:
            cursor.require_next("skipping comment")
        
        cls._skip_newline(cursor)

    @classmethod
    @micropython.native
    def _skip_whitespace(cls, cursor: BufferCursor):
        if not cursor.current in _WHITESPACES:
            raise ValueError(cursor.format_error_message("expected whitespace to skip"))

        if cursor.current in _NEWLINES:
            cls._skip_newline(cursor)
            return
        
        cursor.require_next("skipping whitespace")

    @staticmethod
    @micropython.native
    def _skip_newline(cursor: BufferCursor):
        first = cursor.current

        if not first in _NEWLINES:
            raise ValueError(cursor.format_error_message("expected newline to skip"))

        cursor.require_next("skipping newline")

        # Handling case with '\r\n' (Windows newline character)
        if first == ord('\r') and cursor.current == ord('\n'):
            cursor.require_next("skipping newline")

class BufferCursor:
    def __init__(self, buffer):
        self._buffer = buffer
        self._position = 0

    @micropython.native
    def next(self):
        if self._position >= len(self._buffer):
            return False
        
        self._position += 1
        return True
    
    @micropython.native
    def require_next(self, description: str | None = None):
        if not self.next():
            raise IndexError(self.format_error_message("unexpected EOF" if description is None else f"unexpected EOF while {description}"))

        return self.current

    def format_error_message(self, description: str):
        try:
            character_message = f", Character: {chr(self.current)!r}"
        except IndexError:
            character_message = ""

        return f"Error while parsing: {description}{character_message}, Position: {self.position}"

    @micropython.native
    def read(self, byte_count: int | None = None):
        if byte_count is None:
            byte_count = len(self._buffer) - self._position

        try:
            data = self._buffer[self._position:self._position + byte_count]

            self._position += byte_count
            return data
        except IndexError:
            raise IndexError(self.format_error_message("attempted to read past end of buffer"))
    
    @property
    @micropython.native
    def current(self) -> int:
        try:
            return self._buffer[self._position]
        except IndexError:
            raise IndexError(self.format_error_message("attempted to read past end of buffer"))
    
    @property
    @micropython.native
    def position(self):
        return self._position
