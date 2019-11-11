import logging
from typing import Tuple

import click
from shapely import affinity
from shapely.geometry import MultiLineString

from .utils import Length
from .vpype import cli, processor


@cli.command(group="Transforms")
@click.argument("offset", nargs=2, type=Length(), required=True)
@processor
def translate(mls: MultiLineString, offset: Tuple[float, float]):
    """
    Translate the geometries. X and Y offsets must be provided. These arguments understand
    supported units.
    """
    logging.info(f"translating by {offset}")
    return affinity.translate(mls, offset[0], offset[1])


# noinspection PyShadowingNames
@cli.command(group="Transforms")
@click.argument("scale", nargs=2, type=Length())
@click.option(
    "--to",
    "absolute",
    is_flag=True,
    help="Arguments are interpreted as absolute size instead of (relative) factors.",
)
@click.option(
    "-p",
    "--keep-proportions",
    is_flag=True,
    help="[--to only] Maintain the geometries proportions.",
)
@click.option("-d", "--centroid", is_flag=True, help="Use the centroid as origin.")
@click.option(
    "-o", "--origin", "origin_coords", nargs=2, type=float, help="Use a specific origin."
)
@processor
def scale(
    mls: MultiLineString,
    scale: Tuple[float, float],
    absolute: bool,
    keep_proportions: bool,
    centroid: bool,
    origin_coords: Tuple[float, float],
):
    """Scale the geometries.

    The origin used is the bounding box center, unless the `--centroid` or `--origin` options
    are used.

    By default, the arguments are used as relative factors (e.g. `scale 2 2` make the
    geometries twice as big in both dimensions). With `--to`, the arguments are interpreted as
    the final size. In this case, arguments understand the supported units (e.g.
    `scale --to 10cm 10cm`).
    """
    origin = "center"
    if len(origin_coords) == 2:
        origin = origin_coords
    if centroid:
        origin = "centroid"

    if absolute:
        bounds = mls.bounds
        factors = (scale[0] / (bounds[2] - bounds[0]), scale[1] / (bounds[3] - bounds[1]))

        if keep_proportions:
            factors = (min(factors), min(factors))
    else:
        factors = scale

    logging.info(f"scaling by {factors} with {origin} as origin")
    return affinity.scale(mls, factors[0], factors[1], origin=origin)


@cli.command(group="Transforms")
@click.argument("angle", required=True, type=float)
@click.option("-r", "--radian", is_flag=True, help="Angle is in radians.")
@click.option("-d", "--centroid", is_flag=True, help="Use the centroid as origin.")
@click.option(
    "-o", "--origin", "origin_coords", nargs=2, type=float, help="Use a specific origin."
)
@processor
def rotate(
    mls: MultiLineString,
    angle: float,
    radian: bool,
    centroid: bool,
    origin_coords: Tuple[float, float],
):
    """
    Rotate the geometries.

    The origin used is the bounding box center, unless the `--centroid` or `--origin` options
    are used.
    """
    origin = "center"
    if len(origin_coords) == 2:
        origin = origin_coords
    if centroid:
        origin = "centroid"

    logging.info(f"rotating by {angle} {'rad' if radian else 'deg'} with {origin} as origin")
    return affinity.rotate(mls, angle, origin=origin, use_radians=radian)


@cli.command(group="Transforms")
@click.argument("angles", required=True, nargs=2, type=float)
@click.option("-r", "--radian", is_flag=True, help="Angle is in radians.")
@click.option("-d", "--centroid", is_flag=True, help="Use the centroid as origin.")
@click.option(
    "-o", "--origin", "origin_coords", nargs=2, type=float, help="Use a specific origin."
)
@processor
def skew(
    mls: MultiLineString,
    angles: Tuple[float, float],
    radian: bool,
    centroid: bool,
    origin_coords: Tuple[float, float],
):
    """
    Skew the geometries.

    The geometries are sheared by the provided angles along X and Y dimensions.

    The origin used in the bounding box center, unless the `--centroid` or `--origin` options
    are used.
    """
    origin = "center"
    if len(origin_coords) == 2:
        origin = origin_coords
    if centroid:
        origin = "centroid"

    logging.info(f"skewing by {angles} {'rad' if radian else 'deg'} with {origin} as origin")
    return affinity.skew(mls, angles[0], angles[1], origin=origin, use_radians=radian)
