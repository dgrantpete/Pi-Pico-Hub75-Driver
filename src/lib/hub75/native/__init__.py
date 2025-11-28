from hub75.constants import ARCH

if ARCH == 'armv6m':
    from hub75.native.armv6m import load_rgb888, load_rgb565, clear # type: ignore
elif ARCH == 'armv7emsp':
    from hub75.native.armv7emsp import load_rgb888, load_rgb565, clear # type: ignore
else:
    raise ImportError(f"hub75.native is not supported on architecture: {ARCH!r}")

__all__ = ['load_rgb888', 'load_rgb565', 'clear']