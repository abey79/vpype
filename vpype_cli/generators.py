from typing import Tuple

import click
import numpy as np

from vpype import LengthType, LineCollection, generator

from .cli import cli

__all__ = ("random",)


@cli.command(group="Generators")
@click.option("-n", "--count", "n", type=int, default=10, help="Number of lines to generate.")
@click.option(
    "-a",
    "--area",
    nargs=2,
    type=LengthType(),
    default=("10mm", "10mm"),
    help="Dimension of the area in which lines are distributed.",
)
@generator
def random(n: int, area: Tuple[float, float]):
    """
    Generate random lines.

    By default, 10 lines are randomly placed in a square with corners at (0, 0) and
    (10mm, 10mm). Use the `--area` option to specify the destination area.
    """

    lines = np.random.rand(n, 2) + 1j * np.random.rand(n, 2)
    lines[:, 0] *= area[0]
    lines[:, 1] *= area[1]
    return LineCollection(lines)
