import logging
from typing import Tuple

import click
import numpy as np
from shapely.geometry import asMultiLineString

from .utils import Length
from .vpype import cli, generator


@cli.command(group="Generators")
@click.option("-n", "--count", "n", type=int, default=10, help="Number of lines to generate.")
@click.option(
    "-s",
    "--size",
    nargs=2,
    type=Length(),
    default=("1in", "1in"),
    help="Size of the area in which lines are distributed.",
)
@generator
def random(n: int, size: Tuple[float, float]):
    """
    Generate random lines. By default, lines are distributed in the [0, 1in] square.
    """
    logging.info(f"generating {n} random lines")
    coords = np.random.rand(n, 2, 2)
    coords[:, :, 0] *= size[0]
    coords[:, :, 1] *= size[1]
    return asMultiLineString(coords)
