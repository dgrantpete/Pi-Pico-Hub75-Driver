from machine import Pin

class Direct:
    def __init__(self, base_pin: Pin, bit_count: int):
        self._base_pin = base_pin
        self._bit_count = bit_count

    @property
    def base_pin(self) -> Pin:
        return self._base_pin
    
    @property
    def bit_count(self) -> int:
        return self._bit_count
    
class ShiftRegister:
    def __init__(self, data_pin: Pin, clock_pin: Pin, depth: int):
        self._data_pin = data_pin
        self._clock_pin = clock_pin
        self._depth = depth

    @property
    def data_pin(self) -> Pin:
        return self._data_pin

    @property
    def clock_pin(self) -> Pin:
        return self._clock_pin

    @property
    def depth(self) -> int:
        return self._depth