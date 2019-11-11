import math

import click
import numpy as np
from shapely.geometry import MultiLineString, LineString
from svgpathtools import svg2paths, Line

from .utils import Length, convert
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

    paths, _, svg_attr = svg2paths(file, return_svg_attributes=True)

    if "viewBox" in svg_attr:
        # A view box is defined so we must correctly scale from user coordinates
        # https://css-tricks.com/scale-svg/
        # TODO: we should honor the `preserveAspectRatio` attribute

        w = convert(svg_attr["width"])
        h = convert(svg_attr["height"])

        viewbox = [float(s) for s in svg_attr["viewBox"].split()]

        scale_x = w / (viewbox[2] - viewbox[0])
        scale_y = h / (viewbox[3] - viewbox[1])
        offset_x = -viewbox[0]
        offset_y = -viewbox[1]
    else:
        scale_x = 1
        scale_y = 1
        offset_x = 0
        offset_y = 0

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

            # scale and offset according to viewBox
            coords = coords.view(dtype=float).reshape(len(coords), 2)
            final_coords = np.empty_like(coords)
            final_coords[:, 0] = scale_x * (coords[:, 0] + offset_x)
            final_coords[:, 1] = scale_y * (coords[:, 1] + offset_y)

            ls_array.append(LineString(final_coords))

    return MultiLineString(ls_array)
