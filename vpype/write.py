import copy
import logging
import os
from typing import Tuple

import click
import svgwrite

from .decorators import global_processor
from .model import VectorData, as_vector
from .vpype import cli

# supported page format, size in mm
PAGE_FORMATS = {
    "tight": (0, 0),
    "a5": (148.0, 210.0),
    "a4": (210.0, 297.0),
    "a3": (297.0, 420.0),
    "letter": (215.9, 279.4),
    "legal": (215.9, 355.6),
    "executive": (185.15, 266.7),
    "11x14": (279.4, 355.6),
}


# noinspection PyShadowingBuiltins
@cli.command(group="Output")
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
@click.option(
    "-s",
    "--single-path",
    is_flag=True,
    help=" (SVG only) Generate a single compound path instead of individual paths.",
)
@global_processor
def write(
    vector_data: VectorData,
    output,
    format: str,
    page_format: str,
    landscape: bool,
    center: bool,
    single_path: bool,
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

    # translate the geometries to honor the page_format and center argument
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

    # infer format if required
    if format is None:
        # infer format
        _, ext = os.path.splitext(output.name)
        format = ext.lstrip(".").lower()

    if format == "svg":
        write_svg(corrected_vector_data, output, size, single_path)
    elif format == "hpgl":
        write_hpgl(corrected_vector_data, output, size)
    else:
        logging.warning(
            f"write: format could not be inferred or format unknown '{format}', "
            "no file created"
        )

    return vector_data


def write_svg(
    vector_data: VectorData, output, size: Tuple[float, float], single_path: bool,
) -> None:
    """
    Export geometries in SVG format
    :param vector_data: geometries to export
    :param output: file object to write to
    :param size: size of the page in pixel
    :param single_path: merge all geometries in a single path?
    """
    dwg = svgwrite.Drawing(size=size, profile="tiny", debug=False)
    dwg.attribs["xmlns:inkscape"] = "http://www.inkscape.org/namespaces/inkscape"
    for layer_id in sorted(vector_data.layers.keys()):
        layer = vector_data.layers[layer_id]

        group = dwg.g(style="display:inline", id=f"layer{layer_id}")
        group.attribs["inkscape:groupmode"] = "layer"
        group.attribs["inkscape:label"] = str(layer_id)

        if single_path:
            group.add(
                dwg.path(
                    " ".join(
                        ("M" + " L".join(f"{x},{y}" for x, y in as_vector(line)))
                        for line in layer
                    ),
                    fill="none",
                    stroke="black",
                )
            )
        else:
            for line in layer:
                group.add(
                    dwg.path(
                        "M" + " L".join(f"{x},{y}" for x, y in as_vector(line)),
                        fill="none",
                        stroke="black",
                    )
                )

        dwg.add(group)

    dwg.write(output, pretty=True)


def write_hpgl(vector_data: VectorData, output, size: Tuple[float, float]) -> None:
    """
    Export geometries in SVG format
    :param vector_data: geometries to export
    :param output: file object to write to
    :param size: size of the page in pixel
    """
    # for plotters A2 and above we need to offset the coords (LL = -309, -210)
    offset = [-309, -210]

    # scale offset
    offset = [int(offset[0] / 0.025), int(offset[1] / 0.025)]

    # plotter units in mm
    scale = 0.025

    hpgl = "IN;DF;\n"

    # this could be determined by the layer number? layer 1 uses pen 1, layer 2 uses pen 2 etc
    hpgl += "SP1;\n"

    for layer_id in sorted(vector_data.layers.keys()):
        layer = vector_data.layers[layer_id]
        for line in layer:
            # output the first coordinate
            hpgl += "PU{},{}PD".format(int(as_vector(line)[0][0] / scale) + offset[0], int(as_vector(line)[0][1] / scale) + offset[1])
            # output second to penulimate coordinates
            for x, y in as_vector(line)[1:-1]:
                hpgl+= "{},{},".format(int(x / scale) + offset[0], int(y / scale) + offset[1])
            # output final coordinate
            hpgl += "{},{}\n".format(int(as_vector(line)[-1][0] / scale) + offset[0], int(as_vector(line)[-1][1] / scale) + offset[1])

    # put the pen back and leave the plotter in an initialised state
    hpgl+= "SP0;IN;"

    f = open(output.name, "w+")
    f.write(hpgl)
    f.close()

    # purely for debug purposes
    print(hpgl)

    # TO BE COMPLETED
    pass
