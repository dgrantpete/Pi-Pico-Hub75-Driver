from typing import Any, Iterable, Literal, Set, TypeAlias, Tuple, TypeVar, overload, Final

Const_T = TypeVar("Const_T", int, float, str, bytes, Tuple)  # constant
T = TypeVar("T")

# ----- Viper pointer pseudo-types -----
ViperPtr: TypeAlias = memoryview | bytearray

ptr8: TypeAlias = ViperPtr
ptr16: TypeAlias = ViperPtr
ptr32: TypeAlias = ViperPtr

def const(expr: Const_T) -> Const_T:
    """
    Used to declare that the expression is a constant so that the compiler can
    optimise it.  The use of this function should be as follows::

     from micropython import const

     CONST_X = const(123)
     CONST_Y = const(2 * CONST_X + 1)

    Constants declared this way are still accessible as global variables from
    outside the module they are declared in.  On the other hand, if a constant
    begins with an underscore then it is hidden, it is not available as a global
    variable, and does not take up any memory during execution.

    This `const` function is recognised directly by the MicroPython parser and is
    provided as part of the :mod:`micropython` module mainly so that scripts can be
    written which run under both CPython and MicroPython, by following the above
    pattern.
    """
    ...

class PIOInstruction(PIODelayableInstruction):
    def side(self, value: int) -> PIODelayableInstruction: ...

class PIODelayableInstruction:
    def __getitem__(self, delay: int): ...

# nop instruction
def nop() -> PIOInstruction: ...

# mov instruction
class PIOMoveOperable: ...
class PIOMoveOperated: ...
class PIOMoveTarget: ...

PIOMoveSource = PIOMoveOperable | PIOMoveOperated

def invert(to_invert: PIOMoveOperable) -> PIOMoveOperated: ...

def mov(destination: PIOMoveTarget, source: PIOMoveSource) -> PIOInstruction: ...

# jmp instruction
class PIOJumpCondition: ...
PIOJumpTarget = int | str

@overload
def jmp(target: PIOJumpTarget) -> PIOInstruction: ...

@overload
def jmp(condition: PIOJumpCondition, target: PIOJumpTarget) -> PIOInstruction: ...

# wait instruction
class PIOWaitSource: ...

def wait(polarity: Literal[1] | Literal[0], source: PIOWaitSource, index: int) -> PIOInstruction: ...

# irq instruction
class PIOIRQ(PIOWaitSource): 
    def __call__(self, index: int) -> PIOInstruction: ...

irq: Final[PIOIRQ]

# out instruction
class PIOOutTarget: ...

def out(target: PIOOutTarget, bit_count: int) -> PIOInstruction: ...

# label pseudo-instruction
def label(label: str) -> None: ...

@overload
def set(dest: Any, value: Any) -> PIOInstruction: ...
@overload 
def set() -> Set: ...
@overload
def set(iterable: Iterable[T]) -> Set[T]: ...

# ----- PIO “magic names” (registers / targets) -----
class PIORegister(PIOMoveOperable, PIOMoveTarget): ...

x: Final[PIORegister]
y: Final[PIORegister]

pins: Final[Any]

class PIOProgramCounter(PIOMoveTarget, PIOOutTarget): ...

pc: Final[PIOProgramCounter]

osr: Final[Any]

class PIOInputShiftRegister(PIOOutTarget): ...
isr: Final[PIOInputShiftRegister]

# ----- PIO jmp conditions -----
x_dec: Final[Any]
y_dec: Final[Any]
x_not_y: Final[Any]
pin: Final[Any]
osre: Final[Any]