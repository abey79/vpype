import logging

import click
import numpy as np
from shapely.geometry import asMultiLineString

from .vpype import cli, generator


@cli.command(group="Generators")
@click.option("-n", "--count", "n", type=int, default=10, help="Number of lines to generate.")
@generator
def random(n: int):
    """
    Generate random lines in [0, 1] x [0, 1] space.
    """
    logging.info(f"generating {n} random lines")
    return asMultiLineString(np.random.rand(n, 2, 2))
