import math

import click
import numpy as np
from shapely.geometry import MultiLineString, LineString
from svgpathtools import svg2paths, Line

from .utils import Length
from .vpype import cli, generator


@cli.command(group="Input")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-q",
    "--quantization",
    type=Length(),
    default="1mm",
    help="Maximum length used when converting curves to segments.",
)
@generator
def read(file, quantization: float) -> MultiLineString:
    """
    Read geometries from a SVG file.
    """

    paths, _ = svg2paths(file)

    ls_array = []
    for path in paths:
        for elem in path:
            if isinstance(elem, Line):
                coords = np.array([elem.start, elem.end])
            else:
                # This is a curved element that we approximate with small segments
                step = int(math.ceil(elem.length() / quantization))
                coords = np.empty(step + 1, dtype=complex)
                coords[0] = elem.point(0)
                for i in range(step):
                    coords[i + 1] = elem.point((i + 1) / step)

            ls_array.append(LineString(coords.view(dtype=float).reshape(len(coords), 2)))

    return MultiLineString(ls_array)
