import copy
import datetime
import logging
import os
from typing import Tuple
from xml.etree import ElementTree

import click
import svgwrite
from svgwrite.extensions import Inkscape

from vpype import global_processor, as_vector, VectorData, PageSizeType, PAGE_FORMATS
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

If `OUTPUT` is a single dash (`-`), SVG content is output on stdout instead of a file.

Examples:

    Write to a tightly fitted SVG:

        vpype [...] write output.svg

    Write to a portrait A4 page:

        vpype [...] write --page-format a4 output.svg 

    Write to a 13x9 inch page and center the geometries:

        vpype [...] write --page-format 13x9in --landscape --center output.svg

    Output SVG to stdout:

        vpype [...] write -
"""


# noinspection PyShadowingBuiltins
@cli.command(group="Output", help=WRITE_HELP)
@click.argument("output", type=click.File("w"))
@click.option(
    "-f",
    "--format",
    type=click.Choice(["svg", "hpgl"], case_sensitive=False),
    help="Output format (inferred from file extension by default).",
)
@click.option(
    "-p",
    "--page-format",
    type=PageSizeType(),
    default="tight",
    help=(
        "Set the bounds of the SVG to a specific page format. If omitted, the SVG size it set "
        "to the geometry bounding box."
    ),
)
@click.option(
    "-l", "--landscape", is_flag=True, help="Use landscape orientation instead of portrait.",
)
@click.option(
    "-c", "--center", is_flag=True, help="Center the geometries within the SVG bounds",
)
@click.option(
    "-s",
    "--single-path",
    is_flag=True,
    help="[SVG only] Generate a single compound path instead of individual paths.",
)
@click.option(
    "--paper-portrait",
    is_flag=True,
    help="[HPGL only] Paper is loaded in portrait orientation instead of landscape.",
)
@click.pass_obj  # to obtain the command string
@global_processor
def write(
    vector_data: VectorData,
    cmd_string: str,
    output,
    format: str,
    page_format: Tuple[float, float],
    landscape: bool,
    paper_portrait: bool,
    center: bool,
    single_path: bool,
):
    """Write command."""

    if vector_data.is_empty():
        logging.warning("no geometry to save, no file created")
        return vector_data

    # translate the geometries to honor the page_format and center argument
    bounds = vector_data.bounds()
    tight = page_format == (0.0, 0.0)
    if not tight:
        size = page_format
        if landscape:
            size = tuple(reversed(size))
    else:
        size = (bounds[2] - bounds[0], bounds[3] - bounds[1])

    if center:
        corrected_vector_data = copy.deepcopy(vector_data)
        corrected_vector_data.translate(
            (size[0] - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
            (size[1] - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
        )
    elif tight:
        corrected_vector_data = copy.deepcopy(vector_data)
        corrected_vector_data.translate(-bounds[0], -bounds[1])
    else:
        corrected_vector_data = vector_data

    # infer format if required
    if format is None:
        # infer format
        _, ext = os.path.splitext(output.name)
        format = ext.lstrip(".").lower()

    if format == "svg":
        write_svg(corrected_vector_data, cmd_string, output, size, single_path)
    elif format == "hpgl":
        write_hpgl(corrected_vector_data, output, size, paper_portrait)
    else:
        logging.warning(
            f"write: format could not be inferred or format unknown '{format}', "
            "no file created"
        )

    return vector_data


def write_svg(
    vector_data: VectorData,
    cmd_string: str,
    output,
    size: Tuple[float, float],
    single_path: bool,
) -> None:
    """
    Export geometries in SVG format
    :param vector_data: geometries to export
    :param cmd_string: full vpype command line to embed in comments/metadata
    :param output: file object to write to
    :param size: size of the page in pixel
    :param single_path: merge all geometries in a single path?
    """
    dwg = svgwrite.Drawing(size=size, profile="tiny", debug=False)
    inkscape = Inkscape(dwg)
    dwg.attribs.update(
        {
            "xmlns:dc": "http://purl.org/dc/elements/1.1/",
            "xmlns:cc": "http://creativecommons.org/ns#",
            "xmlns:rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        }
    )

    # add metadata
    metadata = ElementTree.Element("rdf:RDF")
    work = ElementTree.SubElement(metadata, "cc:Work")
    fmt = ElementTree.SubElement(work, "dc:format")
    fmt.text = "image/svg+xml"
    source = ElementTree.SubElement(work, "dc:source")
    source.text = cmd_string
    date = ElementTree.SubElement(work, "dc:date")
    date.text = datetime.datetime.now().isoformat()
    dwg.set_metadata(metadata)

    for layer_id in sorted(vector_data.layers.keys()):
        layer = vector_data.layers[layer_id]

        group = inkscape.layer(label=str(layer_id))
        group.attribs["fill"] = "none"
        group.attribs["stroke"] = "black"
        group.attribs["style"] = "display:inline"
        group.attribs["id"] = f"layer{layer_id}"

        if single_path:
            group.add(
                dwg.path(
                    " ".join(
                        ("M" + " L".join(f"{x},{y}" for x, y in as_vector(line)))
                        for line in layer
                    ),
                )
            )
        else:
            for line in layer:
                group.add(dwg.path("M" + " L".join(f"{x},{y}" for x, y in as_vector(line)),))

        dwg.add(group)

    dwg.write(output, pretty=True)


def write_hpgl(
    vector_data: VectorData, output, size: Tuple[float, float], paper_portrait: bool
) -> None:
    """
    Export geometries in SVG format
    :param vector_data: geometries to export
    :param output: file object to write to
    :param size: size of the page in pixel
    :param paper_portrait: paper is loaded in portrait orientation instead of landscape
    """
    ##########
    # may need to find out what plotter model and adjust this.
    # find out what other plotters use hpgl and their coord systems and limits
    # for plotters A2 and above we need to offset the coords (LL = -309, -210)
    offset = [-309, -210]

    # convert offset to plotter units
    offset = [int(offset[0] / 0.025), int(offset[1] / 0.025)]

    # convert pvype units (css pixel, 1/96inch) to plotter units
    scale = 1 / 0.025 * 25.4 * 1 / 96

    # function to scale and offset pixels to plotter units
    def pxtoplot(x, y):
        x = int(x * scale) + offset[0]
        y = int(y * scale) + offset[1]
        return x, y

    ##########
    hpgl = "IN;DF;\n"

    # this could be determined by the layer number? layer 1 uses pen 1, layer 2 uses pen 2 etc
    hpgl += "SP1;\n"

    for layer_id in sorted(vector_data.layers.keys()):
        layer = vector_data.layers[layer_id]
        for line in layer:
            # output the first coordinate
            x, y = pxtoplot(as_vector(line)[0][0], as_vector(line)[0][1])
            hpgl += "PU{},{};PD".format(x, y)
            # output second to penulimate coordinates
            for x, y in as_vector(line)[1:-1]:
                x, y = pxtoplot(x, y)
                hpgl += "{},{},".format(x, y)
            # output final coordinate
            x, y = pxtoplot(as_vector(line)[-1][0], as_vector(line)[-1][1])
            hpgl += "{},{}".format(x, y)
            # add semicolon terminator between lines
            hpgl += ";\n"

    # put the pen back and leave the plotter in an initialised state
    hpgl += "SP0;IN;"

    output.write(hpgl)
    output.close()

    # TO BE COMPLETED
    pass
