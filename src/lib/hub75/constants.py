import sys

# The values defined here are also passed in as C macros at build time,
# so changing them will require a rebuild.

COLOR_BIT_DEPTH = 8

if sys.implementation.name == 'micropython':
    
    ARCHES = [
        None, 
        'x86', 
        'x64', 
        'armv6', 
        'armv6m', # RP2040
        'armv7m', 
        'armv7em', 
        'armv7emsp', # RP2350
        'armv7emdp',
        'xtensa', 
        'xtensawin', 
        'rv32imc', 
        'rv64imc'
    ]
    
    ARCH = ARCHES[(sys.implementation._mpy >> 10) & 0b1111]