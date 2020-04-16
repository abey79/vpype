import click

from vpype import LineCollection, Length, generator, read_svg
from .cli import cli


@cli.command(group="Input")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-q",
    "--quantization",
    type=Length(),
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
@generator
def read(file, quantization: float, no_simplify: bool) -> LineCollection:
    """
    Extract geometries from a SVG file.

    This command only extracts path elements as well as primitives (rectangles, ellipses,
    lines, polylines, polygons). In particular, text and bitmap images are discarded, as well
    as all formatting.

    All curved primitives (e.g. bezier path, ellipses, etc.) are linearized and approximated
    by polylines. The quantization length controls the maximum length of individual segments.

    By default, an implicit line simplification with tolerance set to quantization is executed
    (see `linesimplify` command). This behaviour can be disabled with the `--no-simplify` flag.
    """

    return read_svg(file, quantization=quantization, simplify=not no_simplify)
