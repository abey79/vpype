import logging
from typing import Optional, cast

import click

from vpype import (
    LayerType,
    LengthType,
    LineCollection,
    VectorData,
    global_processor,
    read_multilayer_svg,
    read_svg,
    single_to_layer_id,
)

from .cli import cli


@cli.command(group="Input")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option("-m", "--single-layer", is_flag=True, help="Single layer mode.")
@click.option(
    "-l",
    "--layer",
    type=LayerType(accept_new=True),
    help="Target layer or 'new' (single layer mode only).",
)
@click.option(
    "-q",
    "--quantization",
    type=LengthType(),
    default="0.1mm",
    help="Maximum length of segments approximating curved elements (default: 0.1mm).",
)
@click.option(
    "-s",
    "--no-simplify",
    is_flag=True,
    default=False,
    help="Do not run the implicit simplify on imported geometries.",
)
@global_processor
def read(
    vector_data: VectorData,
    file,
    single_layer: bool,
    layer: Optional[int],
    quantization: float,
    no_simplify: bool,
) -> VectorData:
    """Extract geometries from a SVG file.

    By default, the `read` command attempts to preserve the layer structure of the SVG. In this
    context, top-level groups (<svg:g>) are each considered a layer. If any, all non-group,
    top-level SVG elements are imported into layer 1.

    The following logic is used to determine in which layer each SVG top-level group is
    imported:

        - If a `inkscape:label` attribute is present and contains digit characters, it is
    stripped of non-digit characters the resulting number is used as target layer. If the
    resulting number is 0, layer 1 is used instead.

        - If the previous step fails, the same logic is applied to the `id` attribute.

        - If both previous steps fail, the target layer matches the top-level group's order of
    appearance.

    Using `--single-layer`, the `read` command operates in single-layer mode. In this mode, all
    geometries are in a single layer regardless of the group structure. The current target
    layer is used default and can be specified with the `--layer` option.

    This command only extracts path elements as well as primitives (rectangles, ellipses,
    lines, polylines, polygons). Other elements such as text and bitmap images are discarded,
    and so is all formatting.

    All curved primitives (e.g. bezier path, ellipses, etc.) are linearized and approximated by
    polylines. The quantization length controls the maximum length of individual segments.

    By default, an implicit line simplification with tolerance set to quantization is executed
    (see `linesimplify` command). This behaviour can be disabled with the `--no-simplify` flag.

    Examples:

        Multi-layer import:

            vpype read input_file.svg [...]

        Single-layer import:

            vpype read --single-layer input_file.svg [...]

        Single-layer import with target layer:

            vpype read --single-layer --layer 3 input_file.svg [...]

        Multi-layer import with specified quantization and line simplification disabled:

            vpype read --quantization 0.01mm --no-simplify input_file.svg [...]
    """

    if single_layer:
        vector_data.add(
            cast(
                LineCollection,
                read_svg(file, quantization=quantization, simplify=not no_simplify),
            ),
            single_to_layer_id(layer, vector_data),
        )
    else:
        if layer is not None:
            logging.warning("read: target layer is ignored in multi-layer mode")
        vector_data.extend(
            cast(
                VectorData,
                read_multilayer_svg(file, quantization=quantization, simplify=not no_simplify),
            ),
        )

    return vector_data
