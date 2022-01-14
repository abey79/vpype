import random

import numpy as np
import pnoise

from .geometry import interpolate
from .model import LineCollection

__all__ = ["squiggles"]


def squiggles(
    lines: LineCollection, ampl: float, period: float, quantization: float
) -> LineCollection:
    """Apply a squiggle filter to a :class:`LineCollection`.

    This filter first densely resample the input lines (based on the ``quantization``
    parameter), and then applies a 2D-Perlin-noise-based displacement to all points.

    For small values of amplitude (~2px) and period (~12px), this filter gives a "shaky-hand"
    style to the lines. Larger values of amplitude (~60px) and period (~400px) result in a
    a smoother, liquid-like effect.

    Args:
        lines: input lines
        ampl: squiggle amplitude (px)
        period: squiggle period (px)
        quantization: quantization (px)

    Returns:
        filtered lines
    """

    # link noise seed to global seed
    noise = pnoise.Noise()
    noise.seed(random.randint(0, 2 ** 16))

    freq = 1.0 / period
    new_lines = lines.clone()
    for line in lines:
        line = interpolate(line, step=quantization)
        perlin_x = noise.perlin(
            freq * line.real, freq * line.imag, np.zeros_like(line.real), grid_mode=False
        )
        perlin_y = noise.perlin(
            freq * line.real, freq * line.imag, 1000 * np.ones_like(line.real), grid_mode=False
        )
        new_lines.append(line + ampl * 2.0 * ((perlin_x - 0.5) + (perlin_y - 0.5) * 1j))

    return new_lines
