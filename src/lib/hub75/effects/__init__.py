from ..constants import ARCH

if ARCH == 'armv6m':
    from hub75.effects.armv6m import render_plasma_frame, render_fire_frame, render_spiral_frame, render_balatro_frame  # type: ignore
elif ARCH == 'armv7emsp':
    from hub75.effects.armv7emsp import render_plasma_frame, render_fire_frame, render_spiral_frame, render_balatro_frame  # type: ignore
else:
    raise ImportError(f"Unsupported architecture for effects: {ARCH!r}")

__all__ = ['render_plasma_frame', 'render_fire_frame', 'render_spiral_frame', 'render_balatro_frame']
