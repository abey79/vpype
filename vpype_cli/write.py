import copy
import datetime
import logging
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

Layers are labelled with their numbers by default. If an alternative naming is required, a
template pattern can be provided using the `--layer-label` option. The provided pattern must
contain a C-style format specifier such as `%d` which will be replaced by the layer number.

By default, paths will be exported individually. If it is preferable to have a single,
compound path per layer, the `--single-path` flag can be used.

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
    
    Output SVG to stdout:

        vpype [...] write -
"""


@cli.command(group="Output", help=WRITE_HELP)
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
    "-c", "--center", is_flag=True, help="Center the geometries within the SVG bounds.",
)
@click.option(
    "-ll", "--layer-label", type=str, default="%d", help="Pattern used to for naming layers."
)
@click.pass_obj  # to obtain the command string
@global_processor
def write(
    vector_data: VectorData,
    cmd_string: str,
    output,
    single_path: bool,
    page_format: Tuple[float, float],
    landscape: bool,
    center: bool,
    layer_label: str,
):
    """Write command."""

    if vector_data.is_empty():
        logging.warning("no geometry to save, no file created")
        return vector_data

    # compute bounds
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

    # output SVG
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

    for layer_id in sorted(corrected_vector_data.layers.keys()):
        layer = corrected_vector_data.layers[layer_id]

        group = inkscape.layer(label=str(layer_label % layer_id))
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
    return vector_data
