import logging

import click
import shapely.ops
from shapely.geometry import Polygon, LineString

from .decorators import layer_processor
from .model import LineCollection, as_vector
from .utils import Length
from .vpype import cli


@cli.command(group="Operations")
@click.argument("x", type=Length(), required=True)
@click.argument("y", type=Length(), required=True)
@click.argument("width", type=Length(), required=True)
@click.argument("height", type=Length(), required=True)
@layer_processor
def crop(lines: LineCollection, x: float, y: float, width: float, height: float):
    """
    Crop the geometries.

    The crop area is defined by the (X, Y) top-left corner and the WIDTH and HEIGHT arguments.
    All arguments understand supported units.
    """
    if lines.is_empty():
        return lines

    # Because of this bug, we cannot use shapely at MultiLineString level
    # https://github.com/Toblerity/Shapely/issues/779
    # I should probably implement it directly anyways...
    p = Polygon([(x, y), (x + width, y), (x + width, y + height), (x, y + height)])
    new_lines = LineCollection()
    for line in lines:
        res = LineString(as_vector(line)).intersection(p)
        if res.geom_type == "MultiLineString":
            new_lines.extend(res)
        elif not res.is_empty:
            new_lines.append(res)

    return new_lines


@cli.command(group="Operations")
@layer_processor
def linemerge(lines: LineCollection):
    """
    (BETA) Merge lines whose ending overlap.

    The current implementation relies on `shapely.ops.linemerge()` which as several limitation.
    It ignore nodes where more than 2 lines join and doesn't accept a distance threshold.
    """
    if lines.is_empty():
        return lines

    mls = shapely.ops.linemerge(lines.as_mls())
    new_lines = LineCollection()
    if mls.geom_type == "LineString":
        new_lines.append(mls)
    else:
        new_lines.extend(mls)

    logging.info(f"linemerge: reduced from {len(lines)} lines to {len(new_lines)} lines")

    return new_lines
