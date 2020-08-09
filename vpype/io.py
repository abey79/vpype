"""
.. module:: vpype

File import/export functions.
"""
import copy
import datetime
import math
import re
from typing import Tuple, Optional
from typing import Union, List, TextIO
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import numpy as np
import svgpathtools as svg
import svgwrite
from svgpathtools import SVG_NAMESPACE
from svgpathtools.document import flatten_group
from svgwrite.extensions import Inkscape

from .model import LineCollection, as_vector, VectorData
from .utils import UNITS, convert_length

__all__ = ["read_svg", "read_multilayer_svg", "write_svg"]


def _calculate_page_size(
    root: Element,
) -> Tuple[Optional[float], Optional[float], float, float, float, float]:
    """Interpret the viewBox, width and height attribs and compute proper scaling coefficients.

    Args:
        root: SVG's root element

    Returns:
        tuple of width, height, scale X, scale Y, offset X, offset Y
    """
    width = height = None
    if "viewBox" in root.attrib:
        # A view box is defined so we must correctly scale from user coordinates
        # https://css-tricks.com/scale-svg/
        # TODO: we should honor the `preserveAspectRatio` attribute

        viewbox_min_x, viewbox_min_y, viewbox_width, viewbox_height = [
            float(s) for s in root.attrib["viewBox"].split()
        ]

        width = convert_length(root.attrib.get("width", viewbox_width))
        height = convert_length(root.attrib.get("height", viewbox_height))

        scale_x = width / viewbox_width
        scale_y = height / viewbox_height
        offset_x = -viewbox_min_x
        offset_y = -viewbox_min_y
    else:
        scale_x = 1
        scale_y = 1
        offset_x = 0
        offset_y = 0

    return width, height, scale_x, scale_y, offset_x, offset_y


def _convert_flattened_paths(
    paths: List,
    quantization: float,
    scale_x: float,
    scale_y: float,
    offset_x: float,
    offset_y: float,
    simplify: bool,
) -> "LineCollection":
    """Convert a list of FlattenedPaths to a :class:`LineCollection`.

    Args:
        paths: list of FlattenedPaths
        quantization: maximum length of linear elements to approximate curve paths
        scale_x, scale_y: scale factor to apply
        offset_x, offset_y: offset to apply
        simplify: should Shapely's simplify be run

    Returns:
        new :class:`LineCollection` instance containing the converted geometries
    """

    lc = LineCollection()
    for result in paths:
        # Here we load the sub-part of the path element. If such sub-parts are connected,
        # we merge them in a single line (e.g. line string, etc.). If there are disconnection
        # in the path (e.g. multiple "M" commands), we create several lines
        sub_paths: List[List[complex]] = []
        for elem in result.path:
            if isinstance(elem, svg.Line):
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

    if simplify:
        mls = lc.as_mls()
        lc = LineCollection(mls.simplify(tolerance=quantization))

    return lc


def read_svg(
    filename: str, quantization: float, simplify: bool = False, return_size: bool = False
) -> Union["LineCollection", Tuple["LineCollection", float, float]]:
    """Read a SVG file an return its content as a :class:`LineCollection` instance.

    All curved geometries are chopped in segments no longer than the value of *quantization*.
    Optionally, the geometries are simplified using Shapely, using the value of *quantization*
    as tolerance.

    Args:
        filename: path of the SVG file
        quantization: maximum size of segment used to approximate curved geometries
        simplify: run Shapely's simplify on loaded geometry
        return_size: if True, return a size 3 Tuple containing the geometries and the SVG
            width and height

    Returns:
        imported geometries, and optionally width and height of the SVG
    """

    doc = svg.Document(filename)
    width, height, scale_x, scale_y, offset_x, offset_y = _calculate_page_size(doc.root)
    lc = _convert_flattened_paths(
        doc.flatten_all_paths(), quantization, scale_x, scale_y, offset_x, offset_y, simplify,
    )

    if return_size:
        if width is None or height is None:
            _, _, width, height = lc.bounds() or 0, 0, 0, 0
        return lc, width, height
    else:
        return lc


def read_multilayer_svg(
    filename: str, quantization: float, simplify: bool = False, return_size: bool = False
) -> Union["VectorData", Tuple["VectorData", float, float]]:
    """Read a multilayer SVG file and return its content as a :class:`VectorData` instance
    retaining the SVG's layer structure.

    Each top-level group is considered a layer. All non-group, top-level elements are imported
    in layer 1.

    Groups are matched to layer ID according their `inkscape:label` attribute, their `id`
    attribute or their appearing order, in that order of priority. Labels are stripped of
    non-numeric characters and the remaining is used as layer ID. Lacking numeric characters,
    the appearing order is used. If the label is 0, its changed to 1.

    All curved geometries are chopped in segments no longer than the value of *quantization*.
    Optionally, the geometries are simplified using Shapely, using the value of *quantization*
    as tolerance.

    Args:
        filename: path of the SVG file
        quantization: maximum size of segment used to approximate curved geometries
        simplify: run Shapely's simplify on loaded geometry
        return_size: if True, return a size 3 Tuple containing the geometries and the SVG
            width and height

    Returns:
         imported geometries, and optionally width and height of the SVG
    """

    doc = svg.Document(filename)

    width, height, scale_x, scale_y, offset_x, offset_y = _calculate_page_size(doc.root)

    vector_data = VectorData()

    # non-group top level elements are loaded in layer 1
    top_level_elements = doc.flatten_all_paths(group_filter=lambda x: x is doc.root)
    if top_level_elements:
        vector_data.add(
            _convert_flattened_paths(
                top_level_elements,
                quantization,
                scale_x,
                scale_y,
                offset_x,
                offset_y,
                simplify,
            ),
            1,
        )

    for i, g in enumerate(doc.root.iterfind("svg:g", SVG_NAMESPACE)):
        # compute a decent layer ID
        lid_str = re.sub(
            "[^0-9]", "", g.get("{http://www.inkscape.org/namespaces/inkscape}label") or ""
        )
        if not lid_str:
            lid_str = re.sub("[^0-9]", "", g.get("id") or "")
        if lid_str:
            lid = int(lid_str)
            if lid == 0:
                lid = 1
        else:
            lid = i + 1

        vector_data.add(
            _convert_flattened_paths(
                flatten_group(g, g),
                quantization,
                scale_x,
                scale_y,
                offset_x,
                offset_y,
                simplify,
            ),
            lid,
        )

    if return_size:
        if width is None or height is None:
            _, _, width, height = vector_data.bounds() or 0, 0, 0, 0
        return vector_data, width, height
    else:
        return vector_data


def write_svg(
    output: TextIO,
    vector_data: VectorData,
    page_format: Tuple[float, float] = (0.0, 0.0),
    center: bool = False,
    source_string: str = "",
    single_path: bool = False,
    layer_label_format: str = "%d",
) -> None:
    """Create a SVG from a :py:class:`VectorData` instance.

    If no page format is provided (or (0, 0) is passed), the SVG generated has bounds tightly
    fitted around the geometries. Otherwise the provided size (in pixel) is used.

    By default, no translation is applied on the geometry. If `center=True`, geometries are
    moved to the center of the page.

    No scaling or rotation is applied to geometries.

    Layers are named after `layer_label_format`, which may contain a C-style format specifier
    such as `%d` which will be replaced by the layer number.

    If `single_path=True`, a single compound path is written per layer. Otherwise, each path
    is exported individually.

    Args:
        output: text-mode IO stream where SVG code will be written
        vector_data: geometries to be written
        page_format: page (width, height) tuple in pixel, or (0, 0) for tight fit
        center: center geometries on page before export
        source_string: value of the `source` metadata
        single_path: export geometries as a single compound path instead of multiple
            individual paths
        layer_label_format: format string for layer label naming
    """

    # compute bounds
    bounds = vector_data.bounds()
    if bounds is None:
        # empty geometry, we provide fake bounds
        bounds = (0, 0, 1, 1)
    tight = page_format == (0.0, 0.0)
    if not tight:
        size = page_format
    else:
        size = (bounds[2] - bounds[0], bounds[3] - bounds[1])

    if center:
        corrected_vector_data = copy.deepcopy(vector_data)
        corrected_vector_data.translate(
            (size[0] - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
            (size[1] - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
        )
    elif tight:
        corrected_vector_data = copy.deepcopy(vector_data)
        corrected_vector_data.translate(-bounds[0], -bounds[1])
    else:
        corrected_vector_data = vector_data

    # output SVG
    size_cm = tuple(f"{round(s / UNITS['cm'], 8)}cm" for s in size)
    dwg = svgwrite.Drawing(size=size_cm, profile="tiny", debug=False)
    inkscape = Inkscape(dwg)
    dwg.attribs.update(
        {
            "viewBox": f"0 0 {size[0]} {size[1]}",
            "xmlns:dc": "http://purl.org/dc/elements/1.1/",
            "xmlns:cc": "http://creativecommons.org/ns#",
            "xmlns:rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        }
    )

    # add metadata
    metadata = ElementTree.Element("rdf:RDF")
    work = ElementTree.SubElement(metadata, "cc:Work")
    fmt = ElementTree.SubElement(work, "dc:format")
    fmt.text = "image/svg+xml"
    source = ElementTree.SubElement(work, "dc:source")
    source.text = source_string
    date = ElementTree.SubElement(work, "dc:date")
    date.text = datetime.datetime.now().isoformat()
    dwg.set_metadata(metadata)

    for layer_id in sorted(corrected_vector_data.layers.keys()):
        layer = corrected_vector_data.layers[layer_id]

        group = inkscape.layer(label=str(layer_label_format % layer_id))
        group.attribs["fill"] = "none"
        group.attribs["stroke"] = "black"
        group.attribs["style"] = "display:inline"
        group.attribs["id"] = f"layer{layer_id}"

        if single_path:
            group.add(
                dwg.path(
                    " ".join(
                        ("M" + " L".join(f"{x},{y}" for x, y in as_vector(line)))
                        for line in layer
                    ),
                )
            )
        else:
            for line in layer:
                group.add(dwg.path("M" + " L".join(f"{x},{y}" for x, y in as_vector(line)),))

        dwg.add(group)

    dwg.write(output, pretty=True)
