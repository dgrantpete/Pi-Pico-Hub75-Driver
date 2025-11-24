def _get_arch():
    import sys

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

    return ARCHES[(sys.implementation._mpy >> 10) & 0b1111]

_arch = _get_arch()

if _arch == 'armv6m':
    from lib.hub75.native.armv6m import load_ppm # type: ignore
elif _arch == 'armv7emsp':
    from lib.hub75.native.armv7emsp import load_ppm # type: ignore
else:
    raise ImportError(f"hub75.native is not supported on architecture: {_arch!r}")

__all__ = ['load_ppm']