"""Visual effects for HUB75 LED matrices.

Example:
    from hub75.driver import Hub75Driver
    from hub75.effects import EffectRunner

    driver = Hub75Driver(...)
    runner = EffectRunner(driver)
    runner.balatro()
    runner.spin_speed = 12
"""
from hub75.constants import ARCH

if ARCH == 'armv6m':
    from hub75.effects.armv6m import plasma_frame, fire_frame, spiral_frame, balatro_frame  # type: ignore
elif ARCH == 'armv7emsp':
    from hub75.effects.armv7emsp import plasma_frame, fire_frame, spiral_frame, balatro_frame  # type: ignore
else:
    raise ImportError(f"Unsupported architecture for effects: {ARCH!r}")

from .runner import EffectRunner

__all__ = ['EffectRunner', 'plasma_frame', 'fire_frame', 'spiral_frame', 'balatro_frame']
