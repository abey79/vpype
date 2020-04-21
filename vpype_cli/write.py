import copy
import datetime
import logging
from xml.etree import ElementTree

import click
import svgwrite
from svgwrite.extensions import Inkscape

from vpype import global_processor, as_vector, VectorData
from .cli import cli

# supported page format, size in mm
PAGE_FORMATS = {
    "tight": (0, 0),
    "a6": (105.0, 148.0),
    "a5": (148.0, 210.0),
    "a4": (210.0, 297.0),
    "a3": (297.0, 420.0),
    "letter": (215.9, 279.4),
    "legal": (215.9, 355.6),
    "executive": (185.15, 266.7),
    "11x14": (279.4, 355.6),
    "12x9": (304.8, 228.6),
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
@click.pass_obj  # to obtain the command string
@global_processor
def write(
    vector_data: VectorData,
    cmd_string: str,
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

    if vector_data.is_empty():
        logging.warning("no geometry to save, no file created")
        return vector_data

    # compute bounds
    bounds = vector_data.bounds()
    if page_format != "tight":
        size = tuple(c * 96.0 / 25.4 for c in PAGE_FORMATS[page_format])
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
    elif page_format == "tight":
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
    return vector_data
