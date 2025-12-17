from ..constants import ARCH

if ARCH == 'armv6m':
    from .armv6m import load_rgb888, load_rgb565, clear, pack_hsv_to_rgb565, pack_hsv_to_rgb888, hsv_to_rgb  # type: ignore
elif ARCH == 'armv7emsp':
    from .armv7emsp import load_rgb888, load_rgb565, clear, pack_hsv_to_rgb565, pack_hsv_to_rgb888, hsv_to_rgb  # type: ignore
else:
    raise ImportError(f"Native code is not supported on architecture: {ARCH!r}")

__all__ = ['load_rgb888', 'load_rgb565', 'clear', 'pack_hsv_to_rgb565', 'pack_hsv_to_rgb888', 'hsv_to_rgb']