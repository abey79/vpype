import click
from typing import Tuple

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
@click.option(
    "--radii",
    "-r",
    type=vp.LengthType(),
    nargs=4,
    default=(0, 0, 0, 0),
    help="Top-left, top-right, bottom-right and bottom-left corner radii.",
)
@vp.generator
def rect(
    x: float, y: float, width: float, height: float, radii: Tuple[float, float, float, float]
) -> vp.LineCollection:
    """Generate a rectangle.

    The rectangle is defined by its top left corner (X, Y) and its width and height.
    Radius can be specified for each corner with tl, tr, br, bl.
    """
    return vp.LineCollection([vp.rect(x, y, width, height, *radii)])


@cli.command(group="Primitives")
@click.argument("x", type=vp.LengthType())
@click.argument("y", type=vp.LengthType())
@click.argument("rw", type=vp.LengthType())
@click.argument("rh", type=vp.LengthType())
@click.argument("start", type=vp.LengthType())
@click.argument("stop", type=vp.LengthType())
@click.option(
    "-q",
    "--quantization",
    type=vp.LengthType(),
    default="1mm",
    help="Maximum length of segments approximating the circle.",
)
@vp.generator
def arc(
    x: float, y: float, rw: float, rh: float, start: float, stop: float, quantization: float
):
    """Generate lines approximating a circular arc.

    The arc is centered on (X, Y) and has a radius of R and spans counter-clockwise from START
    to STOP angles (in degrees). Angular values of zero refer to east of unit circle and
    positive values extend counter-clockwise.
    """
    return vp.LineCollection([vp.arc(x, y, rw, rh, start, stop, quantization)])


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
    """Generate lines approximating a circle.

    The circle is centered on (X, Y) and has a radius of R.
    """

    return vp.LineCollection([vp.circle(x, y, r, quantization)])


@cli.command(group="Primitives")
@click.argument("x", type=vp.LengthType())
@click.argument("y", type=vp.LengthType())
@click.argument("w", type=vp.LengthType())
@click.argument("h", type=vp.LengthType())
@click.option(
    "-q",
    "--quantization",
    type=vp.LengthType(),
    default="1mm",
    help="Maximum length of segments approximating the ellipse.",
)
@vp.generator
def ellipse(x: float, y: float, w: float, h: float, quantization: float):
    """Generate lines approximating an ellipse.

    The ellipse is centered on (X, Y), with a half-width of W and a half-height of H.
    """

    return vp.LineCollection([vp.ellipse(x, y, w, h, quantization)])
