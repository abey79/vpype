import math

import click
from shapely.geometry import MultiLineString, LineString, Point, LinearRing

from .utils import Length
from .vpype import cli, generator


@cli.command(group="Primitives")
@click.argument("x0", type=Length())
@click.argument("y0", type=Length())
@click.argument("x1", type=Length())
@click.argument("y1", type=Length())
@generator
def line(x0: float, y0: float, x1: float, y1: float):
    """
    Generate a single line.

    The line starts at (X0, Y0) and ends at (X1, Y1). All arguments understand supported units.
    """

    return MultiLineString([LineString([(x0, y0), (x1, y1)])])


@cli.command(group="Primitives")
@click.argument("x", type=Length())
@click.argument("y", type=Length())
@click.argument("width", type=Length())
@click.argument("height", type=Length())
@generator
def rect(x: float, y: float, width: float, height: float):
    """
    Generate a rectangle.

    The rectangle is defined by its top left corner (X, Y) and its width and height.
    """

    return MultiLineString(
        [LinearRing([(x, y), (x + width, y), (x + width, y + height), (x, y + height)])]
    )


@cli.command(group="Primitives")
@click.argument("x", type=Length())
@click.argument("y", type=Length())
@click.argument("r", type=Length())
@click.option(
    "-q",
    "--quantization",
    type=Length(),
    default="1mm",
    help="Maximum length of segments approximating the circle.",
)
@generator
def circle(x: float, y: float, r: float, quantization: float):
    """
    Generate lines approximating a circle.

    The circle is centered on (X, Y) and has a radius of R.
    """

    n = math.ceil(2 * math.pi * r / quantization)
    return MultiLineString([Point(x, y).buffer(r, resolution=n).boundary])
