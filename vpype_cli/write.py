import logging
import os
from typing import Optional

import click

from vpype import (
    PAGE_FORMATS,
    VectorData,
    global_processor,
    write_hpgl,
    write_svg,
    convert_page_format,
)
from .cli import cli

WRITE_HELP = f"""Save geometries to a SVG file.

By default, the SVG generated has bounds tightly fitted around the geometries. Optionally,
a page format can be provided with the `--page-format FORMAT` option. `FORMAT` may be one
of:

    {', '.join(PAGE_FORMATS.keys())}

Alternatively, a custom format can be specified in the form of `WIDTHxHEIGHT`. `WIDTH` and
`HEIGHT` may include units. If only one has an unit, the other is assumed to have the
same unit. If none have units, both are assumed to be pixels by default. Here are some
examples:

\b
    --page-format 11x14in     # 11in by 14in
    --page-format 1024x768    # 1024px by 768px
    --page-format 13.5inx4cm  # 13.5in by 4cm

When a page format is provided, it will be rotated if the `--landscape` option is used.

By default, when a page format is provided, the geometries are not scaled or translated
even if they lie outside of the page bounds. The `--center` option translates the geometries
to the center of the page.

Layers are labelled with their numbers by default. If an alternative naming is required, a
template pattern can be provided using the `--layer-label` option. The provided pattern must
contain a C-style format specifier such as `%d` which will be replaced by the layer number.

By default, paths will be exported individually. If it is preferable to have a single,
compound path per layer, the `--single-path` flag can be used.

For previsualization purposes, paths are colored by layer in the SVG. This can be controlled
with the `--color-mode` option. Setting it "none" disables coloring and black paths are
generated. Setting it to "path" gives a different color to each path (with a rotation),
which makes it easier to visualize line optimization. Finally, pen-up trajectories can be
generated with the `--pen-up` flag. As most plotting tools will include these paths in the
output, this option should be used for previsualisation only. The Axidraw tools will however
ignore them.

If `OUTPUT` is a single dash (`-`), SVG content is printed to stdout instead of a file.

Examples:

    Write to a tightly fitted SVG:

        vpype [...] write output.svg

    Write to a portrait A4 page:

        vpype [...] write --page-format a4 output.svg 

    Write to a 13x9 inch page and center the geometries:

        vpype [...] write --page-format 13x9in --landscape --center output.svg

    Use custom layer labels:

        vpype [...] write --page-format a4 --layer-label "Pen %d" output.svg

    Write a previsualization SVG:

        vpype [...] write --pen-up --color-mode path output.svg

    Output SVG to stdout:

        vpype [...] write -
"""


@cli.command(group="Output", help=WRITE_HELP)
@click.argument("output", type=click.File("w"))
@click.option(
    "-f",
    "--format",
    "file_format",
    type=click.Choice(["svg", "hpgl"], case_sensitive=False),
    help="Output format (inferred from file extension by default).",
)
@click.option(
    "-p",
    "--page-format",
    type=str,
    default="tight",
    help=(
        "Set the bounds of the SVG to a specific page format. If omitted, the SVG size it set "
        "to the geometry bounding box. May not be omitted for HPGL."
    ),
)
@click.option(
    "-l", "--landscape", is_flag=True, help="Use landscape orientation instead of portrait.",
)
@click.option(
    "-c", "--center", is_flag=True, help="Center the geometries within the SVG bounds.",
)
@click.option(
    "-ll",
    "--layer-label",
    type=str,
    default="%d",
    help="[SVG only] Pattern used to for naming layers.",
)
@click.option("-pu", "--pen-up", is_flag=True, help="[SVG only] Generate pen-up trajectories.")
@click.option(
    "-m",
    "--color-mode",
    type=click.Choice(["none", "layer", "path"]),
    default="layer",
    help="[SVG only] Color mode for paths (default: layer).",
)
@click.option(
    "-s",
    "--single-path",
    is_flag=True,
    help="[SVG only] Generate a single compound path instead of individual paths.",
)
@click.option("-d", "--device", type=str, help="[HPGL only] Type of the plotter device.")
@click.option(
    "-vs",
    "--velocity",
    type=float,
    help="[HPGL only] Emit a VS command with the provided value.",
)
@click.pass_obj  # to obtain the command string
@global_processor
def write(
    vector_data: VectorData,
    cmd_string: Optional[str],
    output,
    file_format: str,
    page_format: str,
    landscape: bool,
    center: bool,
    layer_label: str,
    pen_up: bool,
    color_mode: str,
    single_path: bool,
    device: str,
    velocity: Optional[int],
):
    """Write command."""

    if vector_data.is_empty():
        logging.warning("no geometry to save, no file created")
        return vector_data

    if file_format is None:
        # infer format
        _, ext = os.path.splitext(output.name)
        file_format = ext.lstrip(".").lower()

    if file_format == "svg":
        if landscape:
            page_format = page_format[::-1]

        write_svg(
            output=output,
            vector_data=vector_data,
            page_format=convert_page_format(page_format),
            center=center,
            source_string=cmd_string if cmd_string is not None else "",
            layer_label_format=layer_label,
            single_path=single_path,
            show_pen_up=pen_up,
            color_mode=color_mode,
        )
    elif file_format == "hpgl":
        write_hpgl(
            output=output,
            vector_data=vector_data,
            landscape=landscape,
            center=center,
            device=device,
            page_format=page_format,
            velocity=velocity,
        )
    else:
        logging.warning(
            f"write: format could not be inferred or format unknown '{page_format}', "
            "no file created"
        )

    return vector_data
