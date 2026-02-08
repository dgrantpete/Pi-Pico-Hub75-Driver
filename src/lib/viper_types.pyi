from typing import TypeAlias, Tuple, TypeVar

Const_T = TypeVar("Const_T", int, float, str, bytes, Tuple)  # constant
T = TypeVar("T")

# ----- Viper pointer pseudo-types -----
ViperPtr: TypeAlias = memoryview | bytearray

ptr8: TypeAlias = ViperPtr
ptr16: TypeAlias = ViperPtr
ptr32: TypeAlias = ViperPtr