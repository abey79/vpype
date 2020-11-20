"""File import/export functions.
"""
import contextlib
import copy
import datetime
import math
import re
import time
from typing import List, Optional, TextIO, Tuple, Union
from xml.etree import ElementTree

import click
import numpy as np
import svgelements
import svgwrite
from svgwrite.extensions import Inkscape

from .config import CONFIG_MANAGER, PaperConfig, PlotterConfig
from .model import LineCollection, VectorData, as_vector
from .utils import UNITS

__all__ = ["read_svg", "read_multilayer_svg", "write_svg", "write_hpgl"]


_COLORS = [
    "#00f",
    "#080",
    "#f00",
    "#0cc",
    "#0f0",
    "#c0c",
    "#cc0",
    "black",
]


def _convert_flattened_paths(
    paths: List,
    quantization: float,
    simplify: bool,
) -> "LineCollection":
    """Convert a list of FlattenedPaths to a :class:`LineCollection`.

    Args:
        paths: list of FlattenedPaths
        quantization: maximum length of linear elements to approximate curve paths
        simplify: should Shapely's simplify be run

    Returns:
        new :class:`LineCollection` instance containing the converted geometries
    """

    def _process_path(path: svgelements.Path) -> List[np.ndarray]:
        if len(path) == 0:
            return []

        if isinstance(path[0], svgelements.Move):
            del path[0]

        path_list: List[np.ndarray] = []

        def _append_path(p):
            # convert to numpy array, remove consecutive duplicates and save line
            l = np.hstack(p)
            idx = np.ones(len(l), dtype=bool)
            idx[1:] = l[1:] != l[:-1]
            path_list.append(l[idx])

        segments = []
        for seg in path:
            if isinstance(seg, svgelements.Move):
                if segments:
                    _append_path(segments)
                segments = [seg.end.as_complex()]
            elif isinstance(seg, svgelements.Line) or isinstance(seg, svgelements.Close):
                segments.append((seg.start.as_complex(), seg.end.as_complex()))
            else:
                # This is a curved element that we approximate with small segments
                step = int(math.ceil(seg.length() / quantization))
                segments.append(seg._point_numpy(np.linspace(0, 1, step)))

        if segments:
            _append_path(segments)

        return path_list

    lc = LineCollection()
    for results in map(_process_path, paths):
        lc.extend(results)

    if simplify:
        mls = lc.as_mls()
        lc = LineCollection(mls.simplify(tolerance=quantization))

    return lc


@contextlib.contextmanager
def timer(s):
    start = time.perf_counter()
    yield
    stop = time.perf_counter()
    print(f"Timer task '{s}': {stop - start}s")


def read_svg(
    filename: str,
    quantization: float,
    simplify: bool = False,
    return_size: bool = False,
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

    # TODO: default width/height should be provided in the rare case we get
    # TODO: remove timers
    # % value in there
    with timer("SVG.parse"):
        svg = svgelements.SVG.parse(filename)

    with timer("svg.elements() extraction"):
        paths = []
        for elem in svg.elements():
            if isinstance(elem, svgelements.Shape):
                e = svgelements.Path(elem)
                e.reify()  # In some cases the shape could not have reified, the path must.
                if len(e) != 0:
                    paths.append(e)
            elif isinstance(elem, svgelements.Path):
                if len(elem) != 0:
                    paths.append(elem)

    with timer("path conversion"):
        lc = _convert_flattened_paths(
            paths,
            quantization,
            simplify,
        )

    if return_size:
        width = svg.viewbox.viewbox_width
        height = svg.viewbox.viewbox_height
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

    doc = svgelements.SVG.parse(filename)

    width, height, scale_x, scale_y, offset_x, offset_y = _calculate_page_size(doc.viewport)

    vector_data = VectorData()

    # non-group top level elements are loaded in layer 1
    top_level_elements = doc.paths(group_filter=lambda x: x is doc.root)
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

    for i, g in enumerate(doc.root.iterfind("svg:g", svg.SVG_NAMESPACE)):
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
                doc.paths_from_group(g, g),
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


def _line_to_path(dwg: svgwrite.Drawing, lines: Union[np.ndarray, LineCollection]):
    """Convert a line into a SVG path element.

    Accepts either a single line or a :py:class:`LineCollection`.

    Args:
        lines: line(s) to convert to path

    Returns:
        (svgwrite element): path element

    """

    if isinstance(lines, np.ndarray):
        lines = [lines]

    def single_line_to_path(line: np.ndarray) -> str:
        if line[0] == line[-1] and len(line) > 2:
            closed = True
            line = line[:-1]
        else:
            closed = False
        return (
            "M" + " L".join(f"{x},{y}" for x, y in as_vector(line)) + (" Z" if closed else "")
        )

    return dwg.path(" ".join(single_line_to_path(line) for line in lines))


def write_svg(
    output: TextIO,
    vector_data: VectorData,
    page_format: Tuple[float, float] = (0.0, 0.0),
    center: bool = False,
    source_string: str = "",
    single_path: bool = False,
    layer_label_format: str = "%d",
    show_pen_up: bool = False,
    color_mode: str = "none",
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

    For previsualisation purposes, pen-up trajectories can be added to the SVG and path can
    be colored individually (``color_mode="path"``) or layer-by-layer (``color_mode="layer"``).

    Args:
        output: text-mode IO stream where SVG code will be written
        vector_data: geometries to be written
        page_format: page (width, height) tuple in pixel, or (0, 0) for tight fit
        center: center geometries on page before export
        source_string: value of the `source` metadata
        single_path: export geometries as a single compound path instead of multiple
            individual paths
        layer_label_format: format string for layer label naming
        show_pen_up: add paths for the pen-up trajectories
        color_mode: "none" (no formatting), "layer" (one color per layer), "path" (one color
            per path) (``color_mode="path"`` implies ``single_path=False``)
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

    color_idx = 0
    if show_pen_up:
        group = inkscape.layer(label="% pen up trajectories")
        group.attribs["fill"] = "none"
        group.attribs["stroke"] = "black"
        group.attribs["style"] = "display:inline; stroke-opacity: 50%; stroke-width: 0.5"
        group.attribs["id"] = "pen_up_trajectories"

        for layer in corrected_vector_data.layers.values():
            group.add(_line_to_path(dwg, layer.pen_up_trajectories()))

        dwg.add(group)

    for layer_id in sorted(corrected_vector_data.layers.keys()):
        layer = corrected_vector_data.layers[layer_id]

        group = inkscape.layer(label=str(layer_label_format % layer_id))
        group.attribs["fill"] = "none"
        if color_mode == "layer":
            group.attribs["stroke"] = _COLORS[color_idx % len(_COLORS)]
            color_idx += 1
        else:
            group.attribs["stroke"] = "black"
        group.attribs["style"] = "display:inline"
        group.attribs["id"] = f"layer{layer_id}"

        if single_path and color_mode != "path":
            group.add(_line_to_path(dwg, layer))
        else:
            for line in layer:
                path = _line_to_path(dwg, line)
                if color_mode == "path":
                    path.attribs["stroke"] = _COLORS[color_idx % len(_COLORS)]
                    color_idx += 1
                group.add(path)

        dwg.add(group)

    dwg.write(output, pretty=True)


def _get_hpgl_config(
    device: Optional[str], page_format: str
) -> Tuple[PlotterConfig, PaperConfig]:
    if device is None:
        device = CONFIG_MANAGER.get_command_config("write").get("default_hpgl_device", None)
    plotter_config = CONFIG_MANAGER.get_plotter_config(str(device))
    if plotter_config is None:
        raise ValueError(f"no configuration available for plotter '{device}'")
    paper_config = plotter_config.paper_config(page_format)
    if paper_config is None:
        raise ValueError(
            f"no configuration available for paper size '{page_format}' with plotter "
            f"'{device}'"
        )

    return plotter_config, paper_config


def write_hpgl(
    output: TextIO,
    vector_data: VectorData,
    page_format: str,
    landscape: bool,
    center: bool,
    device: Optional[str],
    velocity: Optional[float],
    quiet: bool = False,
) -> None:
    """Create a HPGL file from the :class:`VectorData` instance.

    The ``device``/``page_format`` combination must be defined in the built-in or user-provided
    config files or an exception will be raised.

    By default, no translation is applied on the geometry. If `center=True`, geometries are
    moved to the center of the page.

    No scaling or rotation is applied to geometries.

    Args:
        output: text-mode IO stream where SVG code will be written
        vector_data: geometries to be written
        page_format: page format string (it must be configured for the selected device)
        landscape: if True, the geometries are generated in landscape orientation
        center: center geometries on page before export
        device: name of the device to use (the corresponding config must exists). If not
            provided, a default device must be configured, which will be used.
        velocity: if provided, a VS command will be generated with the corresponding value
        quiet: if True, do not print the plotter/paper info strings
    """

    # empty HPGL is acceptable there are no geometries to plot
    if vector_data.is_empty():
        return

    plotter_config, paper_config = _get_hpgl_config(device, page_format)
    if not quiet:
        if plotter_config.info:
            # use of echo instead of print needed for testability
            # https://github.com/pallets/click/issues/1678
            click.echo(plotter_config.info, err=True)
        if paper_config.info:
            click.echo(paper_config.info, err=True)

    # are plotter coordinate placed in landscape or portrait orientation?
    coords_landscape = paper_config.paper_size[0] > paper_config.paper_size[1]

    # vector data preprocessing:
    # - make a copy
    # - deal with orientation mismatch
    # - optionally center on paper
    # - convert to plotter units
    # - crop to plotter limits
    vector_data = copy.deepcopy(vector_data)

    if landscape != coords_landscape:
        vector_data.rotate(-math.pi / 2)
        vector_data.translate(0, paper_config.paper_size[1])

    if paper_config.rotate_180:
        vector_data.scale(-1, -1)
        vector_data.translate(*paper_config.paper_size)

    if center:
        bounds = vector_data.bounds()
        if bounds is not None:
            vector_data.translate(
                (paper_config.paper_size[0] - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
                (paper_config.paper_size[1] - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
            )

    vector_data.translate(-paper_config.origin_location[0], -paper_config.origin_location[1])
    unit_per_pixel = 1 / plotter_config.plotter_unit_length
    vector_data.scale(
        unit_per_pixel, -unit_per_pixel if paper_config.y_axis_up else unit_per_pixel
    )
    vector_data.crop(
        paper_config.x_range[0],
        paper_config.y_range[0],
        paper_config.x_range[1],
        paper_config.y_range[1],
    )

    # output HPGL
    def complex_to_str(p: complex) -> str:
        return f"{int(round(p.real))},{int(round(p.imag))}"

    output.write("IN;DF;")
    if velocity is not None:
        output.write(f"VS{velocity};")
    if paper_config.set_ps is not None:
        output.write(f"PS{int(paper_config.set_ps)};")

    for layer_id in sorted(vector_data.layers.keys()):
        pen_id = 1 + (layer_id - 1) % plotter_config.pen_count
        output.write(f"SP{pen_id};")

        for line in vector_data.layers[layer_id]:
            if len(line) < 2:
                continue
            output.write(f"PU{complex_to_str(line[0])};")
            output.write(f"PD")
            output.write(",".join(complex_to_str(p) for p in line[1:]))
            output.write(";")

        output.write(
            f"PU{paper_config.final_pu_params if paper_config.final_pu_params else ''};"
        )

    output.write("SP0;IN;\n")
