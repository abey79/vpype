import math

import click
import numpy as np
from svgpathtools import Line, Document

from .decorators import generator
from .model import LineCollection
from .utils import Length, convert
from .vpype import cli


@cli.command(group="Input")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-q",
    "--quantization",
    type=Length(),
    default="1mm",
    help="Maximum length of segments approximating curved elements.",
)
@generator
def read(file, quantization: float) -> LineCollection:
    """
    Extract geometries from a SVG file.

    This command only extracts path elements as well as primitives (rectangles, ellipses,
    lines, polylines, polygons). In particular, text and bitmap images are discarded, as well
    as all formatting.

    All curved primitives (e.g. bezier path, ellipses, etc.) are linearized and approximated
    by polylines. The quantization length controls the maximum length of individual segments
    (1mm by default).
    """

    doc = Document(file)
    results = doc.flatten_all_paths()
    root = doc.tree.getroot()

    # we must interpret correctly the viewBox, width and height attribs in order to scale
    # the file content to proper pixels

    if "viewBox" in root.attrib:
        # A view box is defined so we must correctly scale from user coordinates
        # https://css-tricks.com/scale-svg/
        # TODO: we should honor the `preserveAspectRatio` attribute

        viewbox_min_x, viewbox_min_y, viewbox_width, viewbox_height = [
            float(s) for s in root.attrib["viewBox"].split()
        ]

        w = convert(root.attrib.get("width", viewbox_width))
        h = convert(root.attrib.get("height", viewbox_height))

        scale_x = w / viewbox_width
        scale_y = h / viewbox_height
        offset_x = -viewbox_min_x
        offset_y = -viewbox_min_y
    else:
        scale_x = 1
        scale_y = 1
        offset_x = 0
        offset_y = 0

    lc = LineCollection()
    for result in results:
        # Here we load the sub-part of the path element. If such sub-parts are connected,
        # we merge them in a single line (e.g. line string, etc.). If there are disconnection
        # in the path (e.g. multiple "M" commands), we create several lines
        sub_paths = []
        for elem in result.path:
            if isinstance(elem, Line):
                coords = [elem.start, elem.end]
            else:
                # This is a curved element that we approximate with small segments
                step = int(math.ceil(elem.length() / quantization))
                coords = [elem.start]
                coords.extend(elem.point((i + 1) / step) for i in range(step - 1))
                coords.append(elem.end)

            # merge to last sub path if first coordinates match
            if sub_paths:
                if sub_paths[-1][-1] == coords[0]:
                    sub_paths[-1].extend(coords[1:])
                else:
                    sub_paths.append(coords)
            else:
                sub_paths.append(coords)

        for sub_path in sub_paths:
            path = np.array(sub_path)

            # transform
            path += offset_x + 1j * offset_y
            path.real *= scale_x
            path.imag *= scale_y

            lc.append(path)

    return lc
