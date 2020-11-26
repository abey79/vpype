import logging
from typing import List, Optional, Union, cast

import click
import numpy as np

import vpype as vp

from .cli import cli


@cli.command(group="Operations")
@click.argument("x", type=vp.LengthType(), required=True)
@click.argument("y", type=vp.LengthType(), required=True)
@click.argument("width", type=vp.LengthType(), required=True)
@click.argument("height", type=vp.LengthType(), required=True)
@vp.layer_processor
def crop(lines: vp.LineCollection, x: float, y: float, width: float, height: float):
    """Crop the geometries.

    The crop area is defined by the (X, Y) top-left corner and the WIDTH and HEIGHT arguments.
    All arguments understand supported units.
    """

    lines.crop(x, y, x + width, y + height)
    return lines


@cli.command(group="Operations")
@click.argument("margin_x", type=vp.LengthType(), required=True)
@click.argument("margin_y", type=vp.LengthType(), required=True)
@click.option(
    "-l",
    "--layer",
    type=vp.LayerType(accept_multiple=True),
    default="all",
    help="Target layer(s).",
)
@vp.global_processor
def trim(
    document: vp.Document, margin_x: float, margin_y: float, layer: Union[int, List[int]]
) -> vp.Document:
    """Trim the geometries by some margin.

    This command trims the geometries by the provided X and Y margins with respect to the
    current bounding box.

    By default, `trim` acts on all layers. If one or more layer IDs are provided with the
    `--layer` option, only these layers will be affected. In this case, the bounding box is
    that of the listed layers.
    """

    layer_ids = vp.multiple_to_layer_ids(layer, document)
    bounds = document.bounds(layer_ids)

    if not bounds:
        return document

    min_x = bounds[0] + margin_x
    max_x = bounds[2] - margin_x
    min_y = bounds[1] + margin_y
    max_y = bounds[3] - margin_y
    if min_x > max_x:
        min_x = max_x = 0.5 * (min_x + max_x)
    if min_y > max_y:
        min_y = max_y = 0.5 * (min_y + max_y)

    for vid in layer_ids:
        lc = document[vid]
        lc.crop(min_x, min_y, max_x, max_y)

    return document


@cli.command(group="Operations")
@click.option(
    "-t",
    "--tolerance",
    type=vp.LengthType(),
    default="0.05mm",
    help="Maximum distance between two line endings that should be merged.",
)
@click.option(
    "-f", "--no-flip", is_flag=True, help="Disable reversing stroke direction for merging."
)
@vp.layer_processor
def linemerge(lines: vp.LineCollection, tolerance: float, no_flip: bool = True):
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
@vp.layer_processor
def linesort(lines: vp.LineCollection, no_flip: bool = True):
    """
    Sort lines to minimize the pen-up travel distance.

    Note: this process can be lengthy depending on the total number of line. Consider using
    `linemerge` before `linesort` to reduce the total number of line and thus significantly
    optimizing the overall plotting time.
    """
    if len(lines) < 2:
        return lines

    index = vp.LineIndex(lines[1:], reverse=not no_flip)
    new_lines = vp.LineCollection([lines[0]])

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
    type=vp.LengthType(),
    default="0.05mm",
    help="Controls how far from the original geometry simplified points may lie.",
)
@vp.layer_processor
def linesimplify(lines: vp.LineCollection, tolerance):
    """
    Reduce the number of segments in the geometries.

    The resulting geometries' points will be at a maximum distance from the original controlled
    by the `--tolerance` parameter (0.05mm by default).
    """
    if len(lines) < 2:
        return lines

    # Note: preserve_topology must be False, otherwise non-simple (ie intersecting) MLS will
    # not be simplified (see https://github.com/Toblerity/Shapely/issues/911)
    mls = lines.as_mls().simplify(tolerance=tolerance, preserve_topology=False)
    new_lines = vp.LineCollection(mls)

    logging.info(
        f"simplify: reduced segment count from {lines.segment_count()} to "
        f"{new_lines.segment_count()}"
    )

    return new_lines


@cli.command(group="Operations")
@click.option(
    "-t",
    "--tolerance",
    type=vp.LengthType(),
    default="0.05mm",
    help="Controls how close the path beginning and end must be to consider it closed ("
    "default: 0.05mm).",
)
@vp.layer_processor
def reloop(lines: vp.LineCollection, tolerance):
    """Randomize the seam location of closed paths.

    When plotted, closed path may exhibit a visible mark at the seam, i.e. the location where
    the pen begins and ends the stroke. This command randomizes the seam location in order to
    help reduce visual effect of this in plots with regular patterns.

    Paths are considered closed when their beginning and end points are closer than some
    tolerance, which can be set with the `--tolerance` option.
    """

    lines.reloop(tolerance=tolerance)
    return lines


@cli.command(group="Operations")
@click.option(
    "-n", "--count", type=int, default=2, help="How many pass for each line (default: 2)."
)
@vp.layer_processor
def multipass(lines: vp.LineCollection, count: int):
    """
    Add multiple passes to each line

    Each line is extended with a mirrored copy of itself, optionally multiple times. This is
    useful for pens that need several passes to ensure a good quality.
    """
    if count < 2:
        return lines

    new_lines = vp.LineCollection()
    for line in lines:
        new_lines.append(
            np.hstack(
                [line] + [line[-2::-1] if i % 2 == 0 else line[1:] for i in range(count - 1)]
            )
        )

    return new_lines


@cli.command(group="Operations")
@vp.layer_processor
def splitall(lines: vp.LineCollection) -> vp.LineCollection:
    """
    Split all paths into their constituent segments.

    This command may be used together with `linemerge` for cases such as densely-connected
    meshes where the latter cannot optimize well enough by itself.

    Note that since some paths (especially curved ones) can be made of a large number of
    segments, this command may significantly increase the processing time of the pipeline.
    """

    new_lines = vp.LineCollection()
    for line in lines:
        new_lines.extend([line[i : i + 2] for i in range(len(line) - 1)])
    return new_lines


@cli.command(name="filter", group="Operations")
@click.option(
    "--min-length",
    "-m",
    type=vp.LengthType(),
    help="keep lines whose length is no shorter than value",
)
@click.option(
    "--max-length",
    "-M",
    type=vp.LengthType(),
    help="keep lines whose length is no greater than value",
)
@click.option("--closed", "-c", is_flag=True, help="keep closed lines")
@click.option("--not-closed", "-o", is_flag=True, help="reject closed lines")
@click.option(
    "--tolerance",
    "-t",
    type=vp.LengthType(),
    default="0.05mm",
    help="tolerance used to determined if a line is closed or not (default: 0.05mm)",
)
@vp.layer_processor
def filter_command(
    lines: vp.LineCollection,
    min_length: Optional[float],
    max_length: Optional[float],
    closed: bool,
    not_closed: bool,
    tolerance: float,
) -> vp.LineCollection:
    """Filter paths according to specified criterion.

    When an option is provided (e.g. `--min-length 10cm`) the corresponding criterion is
    applied and paths which do not respect the criterion (e.g. a 9cm-long path) are rejected.

    If multiple options are provided, paths will be kept only if they respect every
    corresponding criterion (i.e. logical AND operator).
    """
    keys = []
    if min_length is not None:
        keys.append(lambda line: vp.line_length(line) >= cast(float, min_length))
    if max_length is not None:
        keys.append(lambda line: vp.line_length(line) <= cast(float, max_length))
    if closed:
        keys.append(lambda line: vp.is_closed(line, tolerance))
    if not_closed:
        keys.append(lambda line: not vp.is_closed(line, tolerance))

    if keys:
        lines.filter(lambda line: vp.union(line, keys))
    else:
        logging.warning("filter: no criterion was provided, all geometries are preserved")

    return lines


# noinspection PyShadowingNames
@cli.command(group="Operations")
@click.argument("size", type=vp.PageSizeType(), required=True)
@click.option("-l", "--landscape", is_flag=True, default=False, help="Target layer(s).")
@vp.global_processor
def pagesize(document: vp.Document, size, landscape) -> vp.Document:
    """Change the current page size.

    The page size is set (or modified) by the `read` command and used by the `write` command by
    default. This command can be used to set it to an arbitrary value. See the `write` command
    help section for more information on valid size value (`vpype write --help`).

    Note: this command only changes the current page size and has no effect on the geometries.
    Use the `translate` and `scale` commands to change the position and/or the scale of the
    geometries.

    Examples:

        Set the page size to A4:

            vpype [...] pagesize a4 [...]

        Set the page size to landscape A4:

            vpype [...] pagesize --landscape a4 [...]

        Set the page size to 11x15in:

            vpype [...] pagesize 11inx15in [...]
    """

    document.page_size = size[::-1] if landscape else size
    return document
