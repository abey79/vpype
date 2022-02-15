import logging
import pathlib
import sys
from typing import List, Optional, Tuple

import click

import vpype as vp

from .cli import cli
from .decorators import global_processor
from .types import LayerType, LengthType, PageSizeType, PathType, single_to_layer_id

__all__ = ("read",)


@cli.command(group="Input")
@click.argument("file", type=PathType(dir_okay=False, allow_dash=True))
@click.option("-m", "--single-layer", is_flag=True, help="Single layer mode.")
@click.option(
    "-l",
    "--layer",
    type=LayerType(accept_new=True),
    help="Target layer or 'new' (single layer mode only).",
)
@click.option(
    "-a",
    "--attr",
    type=str,
    multiple=True,
    help="Attribute by which geometries should be grouped",
)
@click.option(
    "-q",
    "--quantization",
    type=LengthType(),
    default="0.1mm",
    help="Maximum length of segments approximating curved elements (default: 0.1mm).",
)
@click.option("--no-fail", is_flag=True, help="Do not fail is the target file doesn't exist.")
@click.option(
    "-s",
    "--simplify",
    is_flag=True,
    default=False,
    help="Apply simplification algorithm to curved elements.",
)
@click.option(
    "-p",
    "--parallel",
    is_flag=True,
    default=False,
    help="Enable multiprocessing for SVG conversion.",
)
@click.option(
    "-c",
    "--no-crop",
    is_flag=True,
    default=False,
    help="Do not crop the geometries to the SVG boundaries.",
)
@click.option(
    "-ds",
    "--display-size",
    type=PageSizeType(),
    default="a4",
    help=(
        "Display size to use for SVG with width/height expressed as percentage or missing "
        "altogether (see `write` command for possible format)."
    ),
)
@click.option(
    "-dl",
    "--display-landscape",
    is_flag=True,
    default=False,
    help="Use landscape orientation ofr display size.",
)
@global_processor
def read(
    document: vp.Document,
    file,
    single_layer: bool,
    layer: Optional[int],
    attr: List[str],
    quantization: float,
    no_fail: bool,
    simplify: bool,
    parallel: bool,
    no_crop: bool,
    display_size: Tuple[float, float],
    display_landscape: bool,
) -> vp.Document:
    """Extract geometries from a SVG file.

    FILE may be a file path path or a dash (-) to read from the standard input instead.

    By default, the `read` command attempts to preserve the layer structure of the SVG. In this
    context, top-level groups (<g>) are each considered a layer. If any, all non-group,
    top-level SVG elements are imported into layer 1.

    The following logic is used to determine in which layer each SVG top-level group is
    imported:

        - If a `inkscape:label` attribute is present and contains digit characters, it is \
stripped of non-digit characters the resulting number is used as target layer. If the \
resulting number is 0, layer 1 is used instead.

        - If the previous step fails, the same logic is applied to the `id` attribute.

        - If both previous steps fail, the target layer matches the top-level group's order \
of appearance.

    Alternatively, geometries may be sorted into layers based on their attributes, such as
    color or stroke width. This is enabled by using the `--attr` option with the attribute
    to be considered. Multiple `--attr` options may be passed with different attributes. In
    this case, layers will be created for each unique combination of the provided attributes.

    Using `--single-layer`, the `read` command operates in single-layer mode. In this mode,
    all geometries are in a single layer regardless of the group structure. The current target
    layer is used default and can be specified with the `--layer` option. If the `--layer`
    option is used, `--single-layer` is assumed even if not explicitly provided.

    This command only extracts path elements as well as primitives (rectangles, ellipses,
    lines, polylines, polygons). Other elements such as text and bitmap images are discarded,
    and so is all formatting.

    All curved primitives (e.g. bezier path, ellipses, etc.) are linearized and approximated by
    polylines. The quantization length controls the maximum length of individual segments.

    Optionally, a line simplification with tolerance set to quantization can be applied on the
    SVG's curved element (e.g. circles, ellipses, arcs, bezier curves, etc.). This is enabled
    with the `--simplify` flag. This process reduces significantly the number of segments used
    to approximate the curve while still guaranteeing an accurate conversion, but may increase
    the execution time of this command.

    The `--parallel` option enables multiprocessing for the SVG conversion. This is recommended
    ONLY when using `--simplify` on large SVG files with many curved elements.

    By default, the geometries are cropped to the SVG boundaries defined by its width and
    length attributes. The crop operation can be disabled with the `--no-crop` option.

    In general, SVG boundaries are determined by the `width` and `height` of the top-level
    <svg> tag. However, the some SVG may have their width and/or height specified as percent
    value or even miss them altogether (in which case they are assumed to be set to 100%). In
    these cases, vpype considers by default that 100% corresponds to a A4 page in portrait
    orientation. The options `--display-size FORMAT` and `--display-landscape` can be used
    to specify a different format.

    When importing the SVG, the `read` commands attempts to extract the SVG attributes that
    are common to all paths within a layer. The "stroke", "stroke-width" and "inkscape:label"
    attributes are used to set the layer color, pen width and, respectively, name. The other
    attributes (e.g. "stroke-dasharray", etc.) are stored as layer properties with a `svg_`
    prefix. These properties are ignored by vpype but may be used by plug-ins. Also, the
    `write` command can optionally restore them in the exported SVG.

    Examples:

        Multi-layer SVG import:

            vpype read input_file.svg [...]

        Import SVG, sorting geometries by stroke color:

            vpype read --attr stroke input_file.svg [...]

        Import SVG, sorting geometries by stroke color and width:

            vpype read --attr stroke --attr stroke-width input_file.svg [...]

        Single-layer import:

            vpype read --single-layer input_file.svg [...]

        Single-layer import with target layer:

            vpype read --single-layer --layer 3 input_file.svg [...]

        Multi-layer import with specified quantization and line simplification enabled:

            vpype read --quantization 0.01mm --simplify input_file.svg [...]

        Multi-layer import with cropping disabled:

            vpype read --no-crop input_file.svg [...]
    """

    width, height = display_size
    if display_landscape:
        width, height = height, width

    if file == "-":
        file = sys.stdin
    elif not pathlib.Path(file).is_file():
        if no_fail:
            logging.debug("read: file doesn't exist, ignoring due to `--no-fail`")
            return document
        else:
            raise click.BadParameter(f"file {file!r} does not exist")

    if layer is not None and not single_layer:
        single_layer = True
        logging.info("read: `--layer` provided, assuming single-layer mode")

    if single_layer:
        if len(attr) > 0:
            logging.warning("read: `--attr` is ignored in single-layer mode")

        lc, width, height = vp.read_svg(
            file,
            quantization=quantization,
            crop=not no_crop,
            simplify=simplify,
            parallel=parallel,
            default_width=width,
            default_height=height,
        )

        document.add(lc, single_to_layer_id(layer, document))
        document.extend_page_size((width, height))
    else:
        if len(attr) == 0:
            doc = vp.read_multilayer_svg(
                file,
                quantization=quantization,
                crop=not no_crop,
                simplify=simplify,
                parallel=parallel,
                default_width=width,
                default_height=height,
            )
        else:
            doc = vp.read_svg_by_attributes(
                file,
                attributes=attr,
                quantization=quantization,
                crop=not no_crop,
                simplify=simplify,
                parallel=parallel,
                default_width=width,
                default_height=height,
            )
        document.extend(doc)

    return document
