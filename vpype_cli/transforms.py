import logging
import math
from typing import Tuple, Union, List

import click

from vpype import global_processor, VectorData, LineCollection, Length, layer_processor, \
    LayerType, multiple_to_layer_ids
from .cli import cli


@cli.command(group="Transforms")
@click.argument("offset", nargs=2, type=Length(), required=True)
@layer_processor
def translate(lc: LineCollection, offset: Tuple[float, float]):
    """
    Translate the geometries. X and Y offsets must be provided. These arguments understand
    supported units.
    """
    lc.translate(offset[0], offset[1])
    return lc


# noinspection PyShadowingNames
@cli.command(group="Transforms")
@click.argument("scale", nargs=2, type=Length())
@click.option(
    "-l",
    "--layer",
    type=LayerType(accept_multiple=True),
    default="all",
    help="Target layer(s).",
)
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
@click.option(
    "-o", "--origin", "origin_coords", nargs=2, type=Length(), help="Use a specific origin."
)
@global_processor
def scale(
    vector_data: VectorData,
    scale: Tuple[float, float],
    layer: Union[int, List[int]],
    absolute: bool,
    keep_proportions: bool,
    origin_coords: Tuple[float, float],
):
    """Scale the geometries.

    The origin used is the bounding box center, unless the `--origin` option is used.

    By default, the arguments are used as relative factors (e.g. `scale 2 2` make the
    geometries twice as big in both dimensions). With `--to`, the arguments are interpreted as
    the final size. In this case, arguments understand the supported units (e.g.
    `scale --to 10cm 10cm`).

    By default, act on all layers. If one or more layer IDs are provided with the `--layer`
    option, only these layers will be affected. In this case, the bounding box is that of the
    listed layers.
    """

    if vector_data.is_empty():
        return vector_data

    # these are the layers we want to act on
    layer_ids = multiple_to_layer_ids(layer, vector_data)
    bounds = vector_data.bounds(layer_ids)

    if absolute:
        factors = (scale[0] / (bounds[2] - bounds[0]), scale[1] / (bounds[3] - bounds[1]))

        if keep_proportions:
            factors = (min(factors), min(factors))
    else:
        factors = scale

    if len(origin_coords) == 2:
        origin = origin_coords
    else:
        origin = (
            0.5 * (bounds[0] + bounds[2]),
            0.5 * (bounds[1] + bounds[3]),
        )

    logging.info(f"scaling factors: {factors}, origin: {origin}")

    for vid in layer_ids:
        lc = vector_data[vid]
        lc.translate(-origin[0], -origin[1])
        lc.scale(factors[0], factors[1])
        lc.translate(origin[0], origin[1])

    return vector_data


@cli.command(group="Transforms")
@click.argument("angle", required=True, type=float)
@click.option(
    "-l",
    "--layer",
    type=LayerType(accept_multiple=True),
    default="all",
    help="Target layer(s).",
)
@click.option("-r", "--radian", is_flag=True, help="Angle is in radians.")
@click.option(
    "-o", "--origin", "origin_coords", nargs=2, type=Length(), help="Use a specific origin."
)
@global_processor
def rotate(
    vector_data: VectorData,
    angle: float,
    layer: Union[int, List[int]],
    radian: bool,
    origin_coords: Tuple[float, float],
):
    """
    Rotate the geometries (clockwise positive).

    The origin used is the bounding box center, unless the `--origin` option is used.

    By default, act on all layers. If one or more layer IDs are provided with the `--layer`
    option, only these layers will be affected. In this case, the bounding box is that of the
    listed layers.
    """
    if vector_data.is_empty():
        return vector_data

    if not radian:
        angle *= math.pi / 180.0

    # these are the layers we want to act on
    layer_ids = multiple_to_layer_ids(layer, vector_data)

    bounds = vector_data.bounds(layer_ids)
    if len(origin_coords) == 2:
        origin = origin_coords
    else:
        origin = (
            0.5 * (bounds[0] + bounds[2]),
            0.5 * (bounds[1] + bounds[3]),
        )

    logging.info(f"rotating origin: {origin}")

    for vid in layer_ids:
        lc = vector_data[vid]
        lc.translate(-origin[0], -origin[1])
        lc.rotate(angle)
        lc.translate(origin[0], origin[1])

    return vector_data


@cli.command(group="Transforms")
@click.argument("angles", required=True, nargs=2, type=float)
@click.option(
    "-l",
    "--layer",
    type=LayerType(accept_multiple=True),
    default="all",
    help="Target layer(s).",
)
@click.option("-r", "--radian", is_flag=True, help="Angle is in radians.")
@click.option(
    "-o", "--origin", "origin_coords", nargs=2, type=Length(), help="Use a specific origin."
)
@global_processor
def skew(
    vector_data: VectorData,
    layer: Union[int, List[int]],
    angles: Tuple[float, float],
    radian: bool,
    origin_coords: Tuple[float, float],
):
    """
    Skew the geometries.

    The geometries are sheared by the provided angles along X and Y dimensions.

    The origin used in the bounding box center, unless the `--centroid` or `--origin` options
    are used.
    """
    if vector_data.is_empty():
        return vector_data

    # these are the layers we want to act on
    layer_ids = multiple_to_layer_ids(layer, vector_data)

    bounds = vector_data.bounds(layer_ids)
    if len(origin_coords) == 2:
        origin = origin_coords
    else:
        origin = (
            0.5 * (bounds[0] + bounds[2]),
            0.5 * (bounds[1] + bounds[3]),
        )

    if not radian:
        angles = tuple(a * math.pi / 180.0 for a in angles)

    logging.info(f"skewing origin: {origin}")

    for vid in layer_ids:
        lc = vector_data[vid]
        lc.translate(-origin[0], -origin[1])
        lc.skew(angles[0], angles[1])
        lc.translate(origin[0], origin[1])

    return vector_data
