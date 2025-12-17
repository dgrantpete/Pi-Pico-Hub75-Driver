// Minimal MicroPython port config stub for IntelliSense only.
// This file is NOT used in actual builds - the build system generates its own config.
// It provides just the base types needed for MicroPython headers to parse correctly.

#ifndef MPCONFIGPORT_H
#define MPCONFIGPORT_H

#include <stdint.h>

// Core MicroPython types (ARM 32-bit)
typedef uintptr_t mp_uint_t;
typedef intptr_t mp_int_t;
typedef uintptr_t mp_off_t;

// Standard MicroPython QSTR placeholders for IntelliSense
// Exception types
#define MP_QSTR_BaseException (1)
#define MP_QSTR_Exception (2)
#define MP_QSTR_ArithmeticError (3)
#define MP_QSTR_AssertionError (4)
#define MP_QSTR_AttributeError (5)
#define MP_QSTR_EOFError (6)
#define MP_QSTR_GeneratorExit (7)
#define MP_QSTR_ImportError (8)
#define MP_QSTR_IndentationError (9)
#define MP_QSTR_IndexError (10)
#define MP_QSTR_KeyError (11)
#define MP_QSTR_KeyboardInterrupt (12)
#define MP_QSTR_LookupError (13)
#define MP_QSTR_MemoryError (14)
#define MP_QSTR_NameError (15)
#define MP_QSTR_NotImplementedError (16)
#define MP_QSTR_OSError (17)
#define MP_QSTR_OverflowError (18)
#define MP_QSTR_RuntimeError (19)
#define MP_QSTR_StopIteration (20)
#define MP_QSTR_SyntaxError (21)
#define MP_QSTR_SystemExit (22)
#define MP_QSTR_TypeError (23)
#define MP_QSTR_ValueError (24)
#define MP_QSTR_ZeroDivisionError (25)

#endif
