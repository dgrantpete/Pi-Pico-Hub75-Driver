class SRGB:
    """sRGB gamma with linear region per the sRGB specification."""
    pass

class Power:
    """Simple power-function gamma correction."""
    def __init__(self, value: float = 2.2):
        self._value = max(0.0, value)

    @property
    def value(self) -> float:
        return self._value
