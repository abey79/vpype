import math

import click
import numpy as np

from vpype import LineCollection, LengthType, generator
from .cli import cli


@cli.command(group="Primitives")
@click.argument("x0", type=LengthType())
@click.argument("y0", type=LengthType())
@click.argument("x1", type=LengthType())
@click.argument("y1", type=LengthType())
@generator
def line(x0: float, y0: float, x1: float, y1: float) -> LineCollection:
    """
    Generate a single line.

    The line starts at (X0, Y0) and ends at (X1, Y1). All arguments understand supported units.
    """
    return LineCollection([(complex(x0, y0), complex(x1, y1))])


@cli.command(group="Primitives")
@click.argument("x", type=LengthType())
@click.argument("y", type=LengthType())
@click.argument("width", type=LengthType())
@click.argument("height", type=LengthType())
@generator
def rect(x: float, y: float, width: float, height: float) -> LineCollection:
    """
    Generate a rectangle.

    The rectangle is defined by its top left corner (X, Y) and its width and height.
    """
    return LineCollection(
        [
            (
                complex(x, y),
                complex(x + width, y),
                complex(x + width, y + height),
                complex(x, y + height),
                complex(x, y),
            )
        ]
    )


@cli.command(group="Primitives")
@click.argument("x", type=LengthType())
@click.argument("y", type=LengthType())
@click.argument("r", type=LengthType())
@click.option(
    "-q",
    "--quantization",
    type=LengthType(),
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
    angle = np.array(list(range(n)) + [0]) / n * 2 * math.pi
    return LineCollection([r * (np.cos(angle) + 1j * np.sin(angle)) + complex(x, y)])
