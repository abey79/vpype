import logging

import click
import numpy as np
from shapely.geometry import Polygon, LineString

from vpype import as_vector, LineCollection, Length, layer_processor, LineIndex
from .cli import cli


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
        if res.is_empty:
            continue
        if res.geom_type == "MultiLineString":
            new_lines.extend(res)
        elif res.geom_type == "LineString":
            new_lines.append(res)

    return new_lines


@cli.command(group="Operations")
@click.option(
    "-t",
    "--tolerance",
    type=Length(),
    default="0.05mm",
    help="Maximum distance between two line endings that should be merged.",
)
@click.option(
    "-f", "--no-flip", is_flag=True, help="Disable reversing stroke direction for merging."
)
@layer_processor
def linemerge(lines: LineCollection, tolerance: float, no_flip: bool = True):
    """
    Merge lines whose endings overlap or are very close.

    Stroke direction is preserved by default, so `linemerge` looks at joining a line's end with
    another line's start. With the `--flip` stroke direction will be reversed as required to
    further the merge.

    By default, gaps of maximum 0.05mm are considered for merging. This can be controlled with
    the `--tolerance` option.
    """

    lines.merge(tolerance=tolerance, flip=not no_flip)
    return lines


@cli.command(group="Operations")
@click.option(
    "-f",
    "--no-flip",
    is_flag=True,
    help="Disable reversing stroke direction for optimization.",
)
@layer_processor
def linesort(lines: LineCollection, no_flip: bool = True):
    """
    Sort lines to minimize the pen-up travel distance.

    Note: this process can be lengthy depending on the total number of line. Consider using
    `linemerge` before `linesort` to reduce the total number of line and thus significantly
    optimizing the overall plotting time.
    """
    if len(lines) < 2:
        return lines

    index = LineIndex(lines[1:], reverse=not no_flip)
    new_lines = LineCollection([lines[0]])

    while len(index) > 0:
        idx, reverse = index.find_nearest(new_lines[-1][-1])
        line = index.pop(idx)
        if reverse:
            line = np.flip(line)
        new_lines.append(line)

    logging.info(
        f"optimize: reduced pen-up (distance, mean, median) from {lines.pen_up_length()} to "
        f"{new_lines.pen_up_length()}"
    )

    return new_lines


@cli.command(group="Operations")
@click.option(
    "-t",
    "--tolerance",
    type=Length(),
    default="0.05mm",
    help="Controls how far from the original geometry simplified points may lie.",
)
@layer_processor
def linesimplify(lines: LineCollection, tolerance):
    """
    Reduce the number of segments in the geometries.

    The resulting geometries' points will be at a maximum distance from the original controlled
    by the `--tolerance` parameter (0.05mm by default).
    """
    if len(lines) < 2:
        return lines

    mls = lines.as_mls().simplify(tolerance=tolerance)
    new_lines = LineCollection(mls)

    logging.info(
        f"simplify: reduced segment count from {lines.segment_count()} to "
        f"{new_lines.segment_count()}"
    )

    return new_lines


@cli.command(group="Operations")
@click.option(
    "-t",
    "--tolerance",
    type=Length(),
    default="0.05mm",
    help="Controls how close the path beginning and end must be to consider it closed ("
    "default: 0.05mm).",
)
@layer_processor
def reloop(lines: LineCollection, tolerance):
    """
    Randomize the seam location for closed paths. Paths are considered closed when their
    beginning and end points are closer than the provided tolerance.
    """

    lines.reloop(tolerance=tolerance)
    return lines


@cli.command(group="Operations")
@click.option(
    "-n", "--count", type=int, default=2, help="How many pass for each line (default: 2).",
)
@layer_processor
def multipass(lines: LineCollection, count: int):
    """
    Add multiple passes to each line

    Each line is extended with a mirrored copy of itself, optionally multiple times. This is
    useful for pens that need several passes to ensure a good quality.
    """
    if count < 2:
        return lines

    new_lines = LineCollection()
    for line in lines:
        new_lines.append(
            np.hstack(
                [line] + [line[-2::-1] if i % 2 == 0 else line[1:] for i in range(count - 1)]
            )
        )

    return new_lines
