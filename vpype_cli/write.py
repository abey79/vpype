import logging
import os
from typing import Optional

import click

from vpype import (
    CONFIG_MANAGER,
    PAGE_FORMATS,
    VectorData,
    convert_page_format,
    global_processor,
    write_hpgl,
    write_svg,
)

from .cli import cli

WRITE_HELP = f"""Save geometries to a file.

The `write` command support two format: SVG and HPGL. The format is determined based on the
file extension used for `OUTPUT` or the `--file-format` option. This is particular useful when
`OUTPUT` is a single dash (`-`), in which case the output is printed to stdout instead of a
file.

When writing to SVG, the file has bounds tightly fitted around the geometries by default.
Optionally, a page format can be provided with the `--page-format FORMAT` option. `FORMAT` may
be one of:

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

When writing to HPGL, a device name must be provided with the `--device` option. The
corresponding device must be configured in the built-in or a user-provided configuration file
(see the documentation for more details). The following devices are currently available:

    {', '.join(CONFIG_MANAGER.get_plotter_list())}

In HPGL mode, because the coordinate system depends on the configuration, the `--page-format`
option is mandatory, and is restricted to the paper formats defined in the corresponding
device's configuration. The plotter may as well need to be specifically configured for the
desired paper format (e.g. for A4 or A3, the HP 7475a's corresponding DIP switch must be set to
metric mode).

The `--landscape` and `--center` options are accepted and honored in HPGL.

Optionally, the HPGL-only `--velocity` can be provided, in which case a `VS` command will be
emitted with the provided value.

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

        vpype [...] write --format SVG -

    Write a A4 page with portrait orientation HPGL file:

        vpype [...] write --device hp7475a --page-format a4 --center
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
    "-l",
    "--landscape",
    is_flag=True,
    help="Use landscape orientation instead of portrait.",
)
@click.option(
    "-c",
    "--center",
    is_flag=True,
    help="Center the geometries within the SVG bounds.",
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
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="[HPGL only] Do not display the plotter configuration or paper loading information.",
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
    device: Optional[str],
    velocity: Optional[int],
    quiet: bool,
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
        page_format_px = convert_page_format(page_format)

        if landscape:
            page_format_px = page_format_px[::-1]

        write_svg(
            output=output,
            vector_data=vector_data,
            page_format=page_format_px,
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
            quiet=quiet,
        )
    else:
        logging.warning(
            f"write: format could not be inferred or format unknown '{file_format}', "
            "no file created"
        )

    return vector_data
