import logging

import click
from shapely.geometry import MultiLineString, LinearRing

from .vpype import cli, processor


@cli.command(group="Generators")
@click.option("-o", "--offset", default=0.0)
@processor
def frame(mls: MultiLineString, offset: float):
    """
    Add a frame to the geometry.
    """
    bounds = list(mls.bounds)
    bounds[0] -= offset
    bounds[1] -= offset
    bounds[2] += offset
    bounds[3] += offset

    f = LinearRing(
        [
            (bounds[0], bounds[1]),
            (bounds[2], bounds[1]),
            (bounds[2], bounds[3]),
            (bounds[0], bounds[3]),
        ]
    )

    logging.info(f"adding a frame with coordinates {bounds} (offset {offset})")
    return MultiLineString([ls for ls in mls] + [f])
