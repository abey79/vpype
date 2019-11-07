import logging
from typing import Union, Tuple, Sequence

import click
from shapely import affinity
from shapely.geometry import MultiLineString

from .vpype import cli, processor


@cli.command()
@click.argument("offset", nargs=2, type=float, required=True)
@processor
def translate(mls: MultiLineString, offset: Tuple[float, float]):
    """
    Translate the geometries.
    """
    logging.info(f"translating by {offset}")
    return affinity.translate(mls, offset[0], offset[1])


@cli.command()
@click.argument("scale", nargs=2, type=float)
@click.option("-d", "--centroid", is_flag=True, help="Use the centroid as origin instead.")
@click.option("-c", "--center", nargs=2, type=float, help="Use specific origin instead.")
@processor
def scale(
    mls: MultiLineString,
    scale: Sequence[float],
    centroid: bool,
    center: Sequence[float],
):
    """
    Scale the geometries using the bounding box center as origin.
    """
    origin = "center"
    if len(center) == 2:
        origin = center
    if centroid:
        origin = "centroid"

    logging.info(f"scaling by {scale} with {origin} as origin")
    return affinity.scale(mls, scale[0], scale[1], origin=origin)


@cli.command()
@click.argument("angle", required=True, type=float)
@click.option("-r", "--radian", is_flag=True, help="Angle is in radians.")
@click.option("-d", "--centroid", is_flag=True, help="Use the centroid as origin instead.")
@click.option("-c", "--center", nargs=2, type=float, help="Use specific origin instead.")
@processor
def rotate(
    mls: MultiLineString,
    angle: float,
    radian: bool,
    centroid: bool,
    center: Union[None, Tuple[float, float]],
):
    """
    Rotate the geometries using the bounding box center as origin.
    """
    origin = "center"
    if len(center) == 2:
        origin = center
    if centroid:
        origin = "centroid"

    logging.info(f"rotating by {angle} {'rad' if radian else 'deg'} with {origin} as origin")
    return affinity.rotate(mls, angle, origin=origin, use_radians=radian)


@cli.command()
@click.argument("angles", required=True, nargs=2, type=float)
@click.option("-r", "--radian", is_flag=True, help="Angle is in radians.")
@click.option("-d", "--centroid", is_flag=True, help="Use the centroid as origin instead.")
@click.option("-c", "--center", nargs=2, type=float, help="Use specific origin instead.")
@processor
def skew(
    mls: MultiLineString,
    angles: Tuple[float, float],
    radian: bool,
    centroid: bool,
    center: Union[None, Tuple[float, float]],
):
    """
    Skew the geometries using the bounding box center as origin.
    """
    origin = "center"
    if len(center) == 2:
        origin = center
    if centroid:
        origin = "centroid"

    logging.info(f"skewing by {angles} {'rad' if radian else 'deg'} with {origin} as origin")
    return affinity.skew(mls, angles[0], angles[1], origin=origin, use_radians=radian)
