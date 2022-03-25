from __future__ import annotations

import click
import numpy as np

import vpype as vp

from .cli import cli
from .decorators import generator
from .types import IntegerType, LengthType

__all__ = ("random",)


@cli.command(group="Generators")
@click.option(
    "-n", "--count", "n", type=IntegerType(), default=10, help="Number of lines to generate."
)
@click.option(
    "-a",
    "--area",
    nargs=2,
    type=LengthType(),
    default=("10mm", "10mm"),
    help="Dimension of the area in which lines are distributed.",
)
@generator
def random(n: int, area: tuple[float, float]):
    """
    Generate random lines.

    By default, 10 lines are randomly placed in a square with corners at (0, 0) and
    (10mm, 10mm). Use the `--area` option to specify the destination area.
    """

    lines = np.random.rand(n, 2) + 1j * np.random.rand(n, 2)
    lines.real *= area[0]
    lines.imag *= area[1]
    return vp.LineCollection(lines)
