from __future__ import annotations

import logging
import os

import click

import vpype as vp

from .cli import cli
from .decorators import global_processor, pass_state
from .state import State
from .types import FileType, IntegerType, TextType

__all__ = ("write",)

WRITE_HELP = f"""Save geometries to a file.

The `write` command support two format: SVG and HPGL. The format is determined based on the
file extension used for `OUTPUT` or the `--file-format` option. The latter is useful when
`OUTPUT` is a single dash (`-`), in which case the output is printed to stdout instead of a
file.

When writing to SVG, the current page size is used if available. The current page size is
implicitly set by the `read` command and can also be manually changed using the `pagesize`
command. The page size can be overridden using the `--page-size SIZE` option. `SIZE` may
be one of:

    {', '.join(vp.PAGE_SIZES.keys())}

Alternatively, a custom size can be specified in the form of `WIDTHxHEIGHT`. `WIDTH` and
`HEIGHT` may include units. If only one has an unit, the other is assumed to have the
same unit. If none have units, both are assumed to be pixels by default. Here are some
examples:

\b
    --page-size 11x14in     # 11in by 14in
    --page-size 1024x768    # 1024px by 768px
    --page-size 13.5inx4cm  # 13.5in by 4cm

When a page size is provided, it will be rotated if the `--landscape` option is used.

If the current page set has not been set (e.g. because the `read` command has not been used)
and the `--page-size` is not provided, the SVG will have its bounds tightly fit to the
geometries.

By default, the geometries are not scaled or translated even if they lie outside of the page
boundaries. The `--center` option translates the geometries to the center of the page.

Layers are labelled with their numbers by default. If an alternative naming is required, a
template pattern can be provided using the `--layer-label` option. The provided pattern must
contain a C-style format specifier such as `%d` which will be replaced by the layer number.

By default, paths are colored according to the corresponding layer property (as set by the 
`color` or `read` commands). If the color property is not set, a default, per-layer color
scheme is used. Alternative behaviours are available with the `--color-mode` option. Setting it
to "none" disables coloring and black paths are generated. Setting it to "layer" applies the
default color scheme to each layer. Setting it to "path" gives a different color to each path
(with a rotation), which makes it possible to visualize line optimization.

Stroke widths are set according to the corresponding property (as et by the `penwdith`, `pen`,
or `read` commands). If the property is missing, a 1px default is used.

Pen-up trajectories can be generated with the `--pen-up` flag. As most plotting tools will
include these paths in the output, this option should be used for previsualisation only. The
Axidraw tools will however ignore them.

If the `--restore-attribs` option is used, the SVG attributes extracted by the `read` command
are restored in the output SVG. (Note that this is an experimental feature which is unable to
fully recreate an input SVG in all but the simplest cases.)

When writing to HPGL, a device name must be provided with the `--device` option. The
corresponding device must be configured in the built-in or a user-provided configuration file
(see the documentation for more details). The following devices are currently available:

    {', '.join(vp.config_manager.get_plotter_list())}

In HPGL mode, this command will try to infer the paper size to use based on the current page
size (the current page size is set by the `read` command based on the input file and can be
manually set or changed with the `pagesize` or `layout` command). An error will be displayed if
no corresponding paper size if found. Use the `--page-size` option with a format defined in the
device's configuration to manually specify with paper size to use.

The plotter may need to be specifically configured for the desired paper size (e.g. for A4 or
A3, the HP 7475a's corresponding DIP switch must be set to metric mode). A note will be
displayed as a reminder and can be hidden using the `--quiet` option.

The `--landscape` and `--center` options are accepted and honored in HPGL.

By default, relative coordinates are used whenever possible in the HPGL output in order to
reduce file size. If `--absolute` is used, absolute coordinate are used instead.

Optionally, the HPGL-only `--velocity` can be provided, in which case a `VS` command will be
emitted with the provided value.

Examples:

    Write to a SVG using the current page size as set by the `read` command:

        vpype read input.svg [...] write output.svg

    Write to a portrait A4 page:

        vpype [...] write --page-size a4 output.svg

    Write to a 13x9 inch page and center the geometries:

        vpype [...] write --page-size 13x9in --landscape --center output.svg

    Use custom layer labels:

        vpype [...] write --page-size a4 --layer-label "Pen %d" output.svg

    Write a previsualization SVG:

        vpype [...] write --pen-up --color-mode path output.svg

    Output SVG to stdout:

        vpype [...] write --format SVG -

    Write a A4 page with portrait orientation HPGL file:

        vpype [...] write --device hp7475a --page-size a4 --center
"""


@cli.command(group="Output", help=WRITE_HELP)
@click.argument("output", type=FileType("w"))
@click.option(
    "-f",
    "--format",
    "file_format",
    type=click.Choice(["svg", "hpgl"], case_sensitive=False),
    help="Output format (inferred from file extension by default).",
)
@click.option(
    "-p",
    "--page-size",
    type=str,
    help=(
        "Set the bounds of the SVG to a specific page size. If omitted, the SVG size is set "
        "to the current page size (see `read` and `pagesize` commands. May not be omitted for "
        "HPGL."
    ),
)
@click.option(
    "-l", "--landscape", is_flag=True, help="Use landscape orientation instead of portrait."
)
@click.option(
    "-c", "--center", is_flag=True, help="Center the geometries within the SVG bounds."
)
@click.option(
    "-ll",
    "--layer-label",
    type=TextType(),
    help="[SVG only] Pattern used to for naming layers.",
)
@click.option("-pu", "--pen-up", is_flag=True, help="[SVG only] Generate pen-up trajectories.")
@click.option(
    "-m",
    "--color-mode",
    type=click.Choice(["default", "none", "layer", "path"]),
    default="default",
    help="[SVG only] Color mode for paths (default: default).",
)
@click.option(
    "-r",
    "--restore-attribs",
    is_flag=True,
    default=False,
    help="[SVG only] attempt to restore SVG attributes from properties.",
)
@click.option(
    "--dont-set-date",
    is_flag=True,
    help="[SVG only] do not add date metadata (useful for auto-generated SVG under VCS).",
)
@click.option(
    "-d", "--device", type=TextType(), help="[HPGL only] Type of the plotter device."
)
@click.option(
    "-a", "--absolute", is_flag=True, help="[HPGL only] Use absolute coordinates exclusively."
)
@click.option(
    "-vs",
    "--velocity",
    type=IntegerType(),
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
@pass_state
def write(
    state: State,
    document: vp.Document,
    cmd_string: str | None,
    output,
    file_format: str,
    page_size: str,
    landscape: bool,
    center: bool,
    layer_label: str | None,
    restore_attribs: bool,
    dont_set_date: bool,
    pen_up: bool,
    color_mode: str,
    device: str | None,
    absolute: bool,
    velocity: int | None,
    quiet: bool,
):
    """Write command."""

    if document.is_empty():
        logging.warning("no geometry to save, no file created")
        return document

    if file_format is None:
        # infer format
        _, ext = os.path.splitext(output.name)
        file_format = ext.lstrip(".").lower()

    if file_format == "svg":
        page_size_px = None
        if page_size:
            page_size_px = vp.convert_page_size(state.substitute(page_size))
            if landscape:
                page_size_px = page_size_px[::-1]

        vp.write_svg(
            output=output,
            document=document,
            page_size=page_size_px,
            center=center,
            source_string=cmd_string if cmd_string is not None else "",
            layer_label_format=layer_label,
            show_pen_up=pen_up,
            color_mode=color_mode,
            use_svg_metadata=restore_attribs,
            set_date=not dont_set_date,
        )
    elif file_format == "hpgl":
        if not page_size:
            config = vp.config_manager.get_plotter_config(device)
            if config is not None:
                paper_config = config.paper_config_from_size(document.page_size)
            else:
                paper_config = None

            if paper_config and document.page_size is not None:
                page_size = paper_config.name
                landscape = document.page_size[0] > document.page_size[1]
            else:
                logging.error(
                    "write: the plotter page size could not be inferred from the current page "
                    "size (use the `--page-size SIZE` option)"
                )
                return document

        vp.write_hpgl(
            output=output,
            document=document,
            landscape=landscape,
            center=center,
            device=device,
            page_size=page_size,
            absolute=absolute,
            velocity=velocity,
            quiet=quiet,
        )
    else:
        logging.warning(
            f"write: format could not be inferred or format unknown '{file_format}', "
            "no file created (use the `--format` option)"
        )

    return document
