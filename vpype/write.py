import logging

import click
import svgwrite
from shapely import affinity
from shapely.geometry import MultiLineString

from .vpype import cli, processor


# supported page format, size in mm
PAGE_FORMATS = {
    "tight": (0, 0),  # this
    "a5": (148.0, 210.0),
    "a4": (210.0, 297.0),
    "a3": (297.0, 420.0),
    "letter": (215.9, 279.4),
    "legal": (215.9, 355.6),
    "executive": (185.15, 266.7),
}


@cli.command(group="Output")
@click.argument("output", type=click.File("w"))
@click.option(
    "-s",
    "--single-path",
    is_flag=True,
    help="Generate a single compound path instead of individual paths.",
)
@click.option(
    "-p",
    "--page-format",
    type=click.Choice(PAGE_FORMATS.keys(), case_sensitive=False),
    default="tight",
    help=(
        "Set the bounds of the SVG to a specific page format. If omitted, the SVG size it set "
        "to the geometry bounding box."
    ),
)
@click.option(
    "-l",
    "--landscape",
    is_flag=True,
    help="[--page-format only] Use landscape orientation instead of portrait.",
)
@click.option(
    "-c",
    "--center",
    is_flag=True,
    help="[--page-format only] Center the geometries within the SVG bounds",
)
@processor
def write(
    mls: MultiLineString,
    output,
    single_path: bool,
    page_format: str,
    landscape: bool,
    center: bool,
):
    """
    Save geometries to a SVG file.

    By default, the SVG generated has bounds tightly fit around the geometries. Optionally,
    a page format can be provided (`--page-format`). In this case, the geometries are not
    scaled or translated by default, even if they lie outside of the page bounds. The
    `--center` option translates the geometries to the center of the page.

    If output path is `-`, SVG content is output on stdout.
    """
    logging.info(f"saving to {output.name}")

    # compute bounds
    bounds = mls.bounds
    if page_format != "tight":
        size = tuple(c * 96.0 / 25.4 for c in PAGE_FORMATS[page_format])
        if landscape:
            size = tuple(reversed(size))
    else:
        size = (bounds[2] - bounds[0], bounds[3] - bounds[1])

    if center:
        corrected_mls = affinity.translate(
            mls,
            (size[0] - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
            (size[1] - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
        )
    elif page_format == "tight":
        # align geometries to (0, 0)
        corrected_mls = affinity.translate(mls, -bounds[0], -bounds[1])
    else:
        corrected_mls = mls

    # output SVG
    dwg = svgwrite.Drawing(size=size, profile="tiny", debug=False)
    if single_path:
        dwg.add(
            dwg.path(
                " ".join(
                    ("M" + " L".join(f"{x},{y}" for x, y in ls.coords)) for ls in corrected_mls
                ),
                fill="none",
                stroke="black",
            )
        )
    else:
        for ls in corrected_mls:
            dwg.add(
                dwg.path(
                    "M" + " L".join(f"{x},{y}" for x, y in ls.coords),
                    fill="none",
                    stroke="black",
                )
            )

    dwg.write(output)
    return mls
