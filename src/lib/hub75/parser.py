from lib.hub75.image import PPMImage
import micropython

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

DIGITS = {ord('0') + digit for digit in range(10)}
NEWLINES = {ord(newline) for newline in '\r\n'}
WHITESPACES = {ord(whitespace) for whitespace in ' \n\r\t\v\f'}

BITMAP_FORMATS = {'P4'}
GREYSCALE_FORMATS = {'P5'}
COLOR_FORMATS = {'P6'}

@micropython.native
def parse_ppm_image(buffer) -> PPMImage:
    cursor = BufferCursor(buffer)

    magic_number = parse_magic_number(cursor)

    skip_trivia(cursor)
    width = parse_number(cursor)

    skip_trivia(cursor)
    height = parse_number(cursor)

    image_size = width * height

    if magic_number in BITMAP_FORMATS:
        max_value = None
        expected_byte_count = -(-image_size // 8)
    elif magic_number in GREYSCALE_FORMATS:
        skip_trivia(cursor)
        max_value = parse_number(cursor)
        expected_byte_count = (2 if max_value >= 256 else 1) * image_size
    elif magic_number in COLOR_FORMATS:
        skip_trivia(cursor)
        max_value = parse_number(cursor)
        expected_byte_count = (2 if max_value >= 256 else 1) * image_size * 3
    else:
        raise ValueError(f"Unsupported PPM format: {magic_number!r}")

    # Only a single whitespace character should be skipped per the specification
    skip_whitespace(cursor)

    image_data = cursor.read(expected_byte_count)

    if len(image_data) != expected_byte_count:
        raise ValueError(f"PPM image data is incomplete: expected {expected_byte_count} bytes, got {len(image_data)} bytes")

    return PPMImage(
        magic_number=magic_number,
        width=width,
        height=height,
        max_value=max_value,
        image_data=image_data
    )

@micropython.native
def parse_magic_number(cursor: BufferCursor) -> str:
    if cursor.current != ord('P'):
        raise ValueError(cursor.format_error_message("magic number must begin with 'P'"))
    
    cursor.require_next("parsing magic number")

    number = parse_number(cursor)

    return f"P{number}"
    
@micropython.native
def parse_number(cursor: BufferCursor) -> int:
    if not cursor.current in DIGITS:
        raise ValueError(cursor.format_error_message("expected digit while parsing number"))
    
    number = cursor.current - ord('0')

    while cursor.next() and cursor.current in DIGITS:
        number = (number * 10) + (cursor.current - ord('0'))

    return number

@micropython.native
def skip_trivia(cursor: BufferCursor):
    trivia_skipped = False

    while True:
        if cursor.current == ord('#'):
            skip_comment(cursor)
            trivia_skipped = True
            continue

        if cursor.current in WHITESPACES:
            skip_whitespace(cursor)
            trivia_skipped = True
            continue

        break

    if not trivia_skipped:
        raise ValueError("expected trivia to skip (comments or whitespace)")

@micropython.native
def skip_comment(cursor: BufferCursor):
    if not cursor.current == ord('#'):
        raise ValueError(cursor.format_error_message("expected comment to skip"))

    while not cursor.current in NEWLINES:
        cursor.require_next("skipping comment")
    
    skip_newline(cursor)

@micropython.native
def skip_whitespace(cursor: BufferCursor):
    if not cursor.current in WHITESPACES:
        raise ValueError(cursor.format_error_message("expected whitespace to skip"))

    if cursor.current in NEWLINES:
        skip_newline(cursor)
        return
    
    cursor.require_next("skipping whitespace")

@micropython.native
def skip_newline(cursor: BufferCursor):
    first = cursor.current

    if not first in NEWLINES:
        raise ValueError(cursor.format_error_message("expected newline to skip"))

    cursor.require_next("skipping newline")

    # Handling case with '\r\n' (Windows newline character)
    if first == ord('\r') and cursor.current == ord('\n'):
        cursor.require_next("skipping newline")
