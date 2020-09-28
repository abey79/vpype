import logging
import math
from typing import List, Optional, Tuple, Union, cast

import click

from vpype import (
    LayerType,
    LengthType,
    LineCollection,
    VectorData,
    global_processor,
    layer_processor,
    multiple_to_layer_ids,
)

from .cli import cli


def _compute_origin(
    vector_data: VectorData,
    layer: Optional[Union[int, List[int]]],
    origin_coords: Union[Tuple[()], Tuple[float, float]],
) -> Tuple[Tuple[float, float], List[int], Tuple[float, float, float, float]]:
    layer_ids = multiple_to_layer_ids(layer, vector_data)
    bounds = vector_data.bounds(layer_ids)

    if not bounds:
        logging.warning("no geometry available, cannot compute origin")
        raise ValueError

    if len(origin_coords) == 2:
        origin = origin_coords
    else:
        origin = (
            0.5 * (bounds[0] + bounds[2]),
            0.5 * (bounds[1] + bounds[3]),
        )

    return cast(Tuple[float, float], origin), layer_ids, bounds


@cli.command(group="Transforms")
@click.argument("offset", nargs=2, type=LengthType(), required=True)
@layer_processor
def translate(lc: LineCollection, offset: Tuple[float, float]):
    """
    Translate the geometries. X and Y offsets must be provided. These arguments understand
    supported units.
    """
    lc.translate(offset[0], offset[1])
    return lc


# noinspection PyShadowingNames
@cli.command(name="scale", group="Transforms")
@click.argument("scale", nargs=2, type=LengthType())
@click.option(
    "-l",
    "--layer",
    type=LayerType(accept_multiple=True),
    default="all",
    help="Target layer(s).",
)
@click.option(
    "-o",
    "--origin",
    "origin_coords",
    nargs=2,
    type=LengthType(),
    help="Use a specific origin.",
)
@global_processor
def scale_relative(
    vector_data: VectorData,
    scale: Tuple[float, float],
    layer: Union[int, List[int]],
    origin_coords: Union[Tuple[()], Tuple[float, float]],
):
    """Scale the geometries by a factor.

    The origin used is the bounding box center, unless the `--origin` option is used.

    By default, act on all layers. If one or more layer IDs are provided with the `--layer`
    option, only these layers will be affected. In this case, the bounding box is that of the
    listed layers.

    Example:

        Double the size of the geometries in layer 1, using (0, 0) as origin:

            vpype [...] scale -l 1 -o 0 0 2 2 [...]

    """

    try:
        origin, layer_ids, _ = _compute_origin(vector_data, layer, origin_coords)
    except ValueError:
        return vector_data

    for vid in layer_ids:
        lc = vector_data[vid]
        lc.translate(-origin[0], -origin[1])
        lc.scale(scale[0], scale[1])
        lc.translate(origin[0], origin[1])

    return vector_data


# noinspection PyShadowingNames
@cli.command(group="Transforms")
@click.argument("dim", nargs=2, type=LengthType())
@click.option(
    "-l",
    "--layer",
    type=LayerType(accept_multiple=True),
    default="all",
    help="Target layer(s).",
)
@click.option(
    "-f",
    "--fit-dimensions",
    is_flag=True,
    help="Exactly fit target dimension, distorting geometries if required.",
)
@click.option(
    "-o",
    "--origin",
    "origin_coords",
    nargs=2,
    type=LengthType(),
    help="Use a specific origin.",
)
@global_processor
def scaleto(
    vector_data: VectorData,
    dim: Tuple[float, float],
    layer: Union[int, List[int]],
    fit_dimensions: bool,
    origin_coords: Union[Tuple[()], Tuple[float, float]],
):
    """Scale the geometries to given dimensions.

    By default, the homogeneous scaling is applied on both X and Y directions, even if the
    geometry proportions are not the same as the target dimensions.  When passing
    `--fit-dimensions`, the geometries are scaled such as to fit exactly the target dimensions,
    distorting them if required.

    The origin used is the bounding box center, unless the `--origin` option is used.

    By default, act on all layers. If one or more layer IDs are provided with the `--layer`
    option, only these layers will be affected. In this case, the bounding box is that of the
    listed layers.

    Example:

        Scale a SVG to a A4 page, accounting for 1cm margin:

            vpype read input.svg scaleto 19cm 27.7cm write -p a4 -c output.svg

    """

    try:
        origin, layer_ids, bounds = _compute_origin(vector_data, layer, origin_coords)
    except ValueError:
        return vector_data

    factors = (dim[0] / (bounds[2] - bounds[0]), dim[1] / (bounds[3] - bounds[1]))
    if not fit_dimensions:
        factors = (min(factors), min(factors))

    for vid in layer_ids:
        lc = vector_data[vid]
        lc.translate(-origin[0], -origin[1])
        lc.scale(factors[0], factors[1])
        lc.translate(origin[0], origin[1])

    return vector_data


# noinspection DuplicatedCode
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
    "-o",
    "--origin",
    "origin_coords",
    nargs=2,
    type=LengthType(),
    help="Use a specific origin.",
)
@global_processor
def rotate(
    vector_data: VectorData,
    angle: float,
    layer: Union[int, List[int]],
    radian: bool,
    origin_coords: Union[Tuple[()], Tuple[float, float]],
):
    """Rotate the geometries (clockwise positive).

    The origin used is the bounding box center, unless the `--origin` option is used.

    By default, act on all layers. If one or more layer IDs are provided with the `--layer`
    option, only these layers will be affected. In this case, the bounding box is that of the
    listed layers.
    """

    if not radian:
        angle *= math.pi / 180.0

    try:
        origin, layer_ids, _ = _compute_origin(vector_data, layer, origin_coords)
    except ValueError:
        return vector_data

    for vid in layer_ids:
        lc = vector_data[vid]
        lc.translate(-origin[0], -origin[1])
        lc.rotate(angle)
        lc.translate(origin[0], origin[1])

    return vector_data


# noinspection DuplicatedCode
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
    "-o",
    "--origin",
    "origin_coords",
    nargs=2,
    type=LengthType(),
    help="Use a specific origin.",
)
@global_processor
def skew(
    vector_data: VectorData,
    layer: Union[int, List[int]],
    angles: Tuple[float, float],
    radian: bool,
    origin_coords: Union[Tuple[()], Tuple[float, float]],
):
    """Skew the geometries.

    The geometries are sheared by the provided angles along X and Y dimensions.

    The origin used in the bounding box center, unless the `--centroid` or `--origin` options
    are used.
    """

    if not radian:
        angles = tuple(a * math.pi / 180.0 for a in angles)  # type: ignore

    try:
        origin, layer_ids, _ = _compute_origin(vector_data, layer, origin_coords)
    except ValueError:
        return vector_data

    for vid in layer_ids:
        lc = vector_data[vid]
        lc.translate(-origin[0], -origin[1])
        lc.skew(angles[0], angles[1])
        lc.translate(origin[0], origin[1])

    return vector_data
