from __future__ import annotations

import logging
import math
from typing import Tuple, cast

import click

import vpype as vp

from .cli import cli
from .decorators import global_processor, layer_processor
from .types import AngleType, LayerType, LengthType, multiple_to_layer_ids

__all__ = ("rotate", "scale_relative", "scaleto", "skew", "translate")


def _compute_origin(
    document: vp.Document,
    layer: int | list[int] | None,
    origin_coords: tuple[()] | tuple[float, float] | None,
) -> tuple[tuple[float, float], list[int], tuple[float, float, float, float]]:
    layer_ids = multiple_to_layer_ids(layer, document)
    bounds = document.bounds(layer_ids)

    if not bounds:
        logging.warning("no geometry available, cannot compute origin")
        raise ValueError

    if origin_coords is not None and len(origin_coords) == 2:
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
def translate(lc: vp.LineCollection, offset: tuple[float, float]):
    """
    Translate the geometries. X and Y offsets must be provided. These arguments understand
    supported units.

    Note: negative offsets are possible, but the end-of-options marker `--` must be used to
    disambiguate the minus sign, which would normally be interpreted as a command option (see
    example below).

    Examples:

        Translate layer 2 by 2cm rightward and 3cm downward:

            vpype [...] translate -l 2 2cm 3cm [...]

        The end-of-options marker must be used for negative lateral offsets:

            vpype [...] translate -- -2cm 3cm [...]
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
    document: vp.Document,
    scale: tuple[float, float],
    layer: int | list[int],
    origin_coords: tuple[()] | tuple[float, float],
):
    """Scale the geometries by a factor.

    The origin used is the bounding box center, unless the `--origin` option is used.

    By default, act on all layers. If one or more layer IDs are provided with the `--layer`
    option, only these layers will be affected. In this case, the bounding box is that of the
    listed layers.

    Note: negative scale factors are possible, but the end-of-options marker `--` must be used
    to disambiguate the minus sign, which would normally be interpreted as a command option.

    Example:

        Double the size of the geometries in layer 1, using (0, 0) as origin:

            vpype [...] scale -l 1 -o 0 0 2 2 [...]

    """

    try:
        origin, layer_ids, _ = _compute_origin(document, layer, origin_coords)
    except ValueError:
        return document

    for vid in layer_ids:
        lc = document[vid]
        lc.translate(-origin[0], -origin[1])
        lc.scale(scale[0], scale[1])
        lc.translate(origin[0], origin[1])

    return document


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
    document: vp.Document,
    dim: tuple[float, float],
    layer: int | list[int],
    fit_dimensions: bool,
    origin_coords: tuple[()] | tuple[float, float],
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
        origin, layer_ids, bounds = _compute_origin(document, layer, origin_coords)
    except ValueError:
        return document

    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]

    if width == 0.0 or height == 0.0:
        return document

    factors = dim[0] / width, dim[1] / height
    if not fit_dimensions:
        factors = (min(factors), min(factors))

    for vid in layer_ids:
        lc = document[vid]
        lc.translate(-origin[0], -origin[1])
        lc.scale(factors[0], factors[1])
        lc.translate(origin[0], origin[1])

    return document


# noinspection DuplicatedCode
@cli.command(group="Transforms")
@click.argument("angle", required=True, type=AngleType())
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
def rotate(
    document: vp.Document,
    angle: float,
    layer: int | list[int],
    origin_coords: tuple[()] | tuple[float, float],
):
    """Rotate the geometries (clockwise positive).

    The origin used is the bounding box center, unless the `--origin` option is used.

    ANGLE is in degrees by default, but alternative CSS unit may be provided.

    By default, act on all layers. If one or more layer IDs are provided with the `--layer`
    option, only these layers will be affected. In this case, the bounding box is that of the
    listed layers.

    Note: negative angles are possible, but the end-of-options marker `--` must be used
    to disambiguate the minus sign, which would normally be interpreted as a command option.
    """

    try:
        origin, layer_ids, _ = _compute_origin(document, layer, origin_coords)
    except ValueError:
        return document

    for vid in layer_ids:
        lc = document[vid]
        lc.translate(-origin[0], -origin[1])
        lc.rotate(angle * math.pi / 180.0)
        lc.translate(origin[0], origin[1])

    return document


# noinspection DuplicatedCode
@cli.command(group="Transforms")
@click.argument("angles", required=True, nargs=2, type=AngleType())
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
def skew(
    document: vp.Document,
    layer: int | list[int],
    angles: tuple[float, float],
    origin_coords: tuple[()] | tuple[float, float],
):
    """Skew the geometries.

    The geometries are sheared by the provided angles along X and Y dimensions.

    ANGLE is in degrees by default, but alternative CSS unit may be provided.

    The origin used in the bounding box center, unless the `--centroid` or `--origin` options
    are used.

    Note: negative angles are possible, but the end-of-options marker `--` must be used
    to disambiguate the minus sign, which would normally be interpreted as a command option.
    """

    try:
        origin, layer_ids, _ = _compute_origin(document, layer, origin_coords)
    except ValueError:
        return document

    for vid in layer_ids:
        lc = document[vid]
        lc.translate(-origin[0], -origin[1])
        lc.skew(angles[0] * math.pi / 180.0, angles[1] * math.pi / 180.0)
        lc.translate(origin[0], origin[1])

    return document
