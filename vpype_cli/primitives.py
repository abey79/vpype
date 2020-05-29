import click

import vpype as vp
from .cli import cli


@cli.command(group="Primitives")
@click.argument("x0", type=vp.LengthType())
@click.argument("y0", type=vp.LengthType())
@click.argument("x1", type=vp.LengthType())
@click.argument("y1", type=vp.LengthType())
@vp.generator
def line(x0: float, y0: float, x1: float, y1: float) -> vp.LineCollection:
    """
    Generate a single line.

    The line starts at (X0, Y0) and ends at (X1, Y1). All arguments understand supported units.
    """
    return vp.LineCollection([vp.line(x0, y0, x1, y1)])


@cli.command(group="Primitives")
@click.argument("x", type=vp.LengthType())
@click.argument("y", type=vp.LengthType())
@click.argument("width", type=vp.LengthType())
@click.argument("height", type=vp.LengthType())
@vp.generator
def rect(x: float, y: float, width: float, height: float) -> vp.LineCollection:
    """
    Generate a rectangle.

    The rectangle is defined by its top left corner (X, Y) and its width and height.
    """
    return vp.LineCollection([vp.rect(x, y, width, height)])


@cli.command(group="Primitives")
@click.argument("x", type=vp.LengthType())
@click.argument("y", type=vp.LengthType())
@click.argument("r", type=vp.LengthType())
@click.option(
    "-q",
    "--quantization",
    type=vp.LengthType(),
    default="1mm",
    help="Maximum length of segments approximating the circle.",
)
@vp.generator
def circle(x: float, y: float, r: float, quantization: float):
    """
    Generate lines approximating a circle.

    The circle is centered on (X, Y) and has a radius of R.
    """

    return vp.LineCollection([vp.circle(x, y, r, quantization)])
