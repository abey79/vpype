"""File import/export functions.
"""
from __future__ import annotations

import collections
import copy
import dataclasses
import datetime
import math
import pathlib
import re
from collections.abc import Iterable, Iterator
from typing import Any, List, TextIO, Union, cast
from xml.etree import ElementTree

import click
import numpy as np
import svgelements
import svgwrite
import svgwrite.base
from multiprocess import Pool
from shapely.geometry import LineString
from svgwrite.extensions import Inkscape

from .config import PaperConfig, PlotterConfig, config_manager
from .metadata import (
    METADATA_DEFAULT_COLOR_SCHEME,
    METADATA_FIELD_COLOR,
    METADATA_FIELD_NAME,
    METADATA_FIELD_PEN_WIDTH,
    METADATA_FIELD_SOURCE,
    METADATA_SVG_ATTRIBUTES_WHITELIST,
    METADATA_SVG_NAMESPACES,
    Color,
)
from .model import Document, LineCollection
from .utils import UNITS

__all__ = [
    "read_svg",
    "read_multilayer_svg",
    "read_svg_by_attributes",
    "write_svg",
    "write_hpgl",
]


class _ComplexStack:
    """Complex number stack implemented with a numpy array"""

    def __init__(self):
        self._alloc = 100
        self._stack = np.empty(shape=self._alloc, dtype=complex)
        self._len = 0

    def __len__(self) -> int:
        return self._len

    def _realloc(self, min_free: int = 1) -> None:
        self._alloc = max(self._alloc * 2, self._len + min_free)
        # noinspection PyTypeChecker
        self._stack.resize(self._alloc, refcheck=False)

    def append(self, c: complex) -> None:
        if self._len == self._alloc:
            self._realloc()
        self._stack[self._len] = c
        self._len += 1

    def extend(self, a: np.ndarray) -> None:
        len_a = len(a)
        if self._len + len_a > self._alloc:
            self._realloc(len_a)
        self._stack[self._len : self._len + len_a] = a
        self._len += len_a

    def ends_with(self, c: complex) -> bool:
        return self._stack[self._len - 1] == c if self._len > 0 else False

    def get(self) -> np.ndarray:
        self._alloc = self._len
        # noinspection PyTypeChecker
        self._stack.resize(self._alloc, refcheck=False)
        return self._stack


_PathType = Union[
    # for actual paths and shapes transformed into paths
    svgelements.Path,
    # for the special case of Polygon and Polylines
    list[Union[svgelements.PathSegment, svgelements.Polygon, svgelements.Polyline]],
]
_PathListType = list[_PathType]


_NAMESPACED_PROPERTY_RE = re.compile(r"{([-a-zA-Z0-9@:%._+~#=/]+)}([a-zA-Z_][a-zA-Z0-9\-_.]*)")


def _extract_metadata_from_element(
    elem: svgelements.Shape, layer_system_props: bool = True
) -> dict[str, Any]:
    """Extracts the metadata from a svgelements element.

    svgelements offers 3 levels of metadata:
    - object attributes (e.g. `elem.stroke`) which are guaranteed to exist and are typed
      (e.g. `svgelements.Color` for `elem.stroke`).
    - values (e.g. `elem.values`) which are computed from the group hierarchy (e.g. they are
      inherited from enclosing `<g>` elements)
    - SVG attributes (e.g. `elem.values["attributes"]`) which are

    The strategy is as follows:
    - attributes are mapped directly to system metadata (i.e. "vp_color" and "vp_pen_width" --
      "vp.name" is handled by read_multilayer_svg())
    - values are whitelisted and added as `"svg_"` namespace
    - XML-namespaced values are also added as `svg_` namespace (e.g. `"svg_inkscape:label"`
    - SVG attributes are disregarded
    """

    metadata: dict[str, Any] = {}

    # layer-level system properties
    if layer_system_props:
        metadata.update(
            {
                METADATA_FIELD_COLOR: Color(elem.stroke),
                METADATA_FIELD_PEN_WIDTH: elem.stroke_width,
            }
        )

    # white-listed root SVG properties
    metadata.update(
        {
            "svg_" + k: v
            for k, v in elem.values.items()
            if k in METADATA_SVG_ATTRIBUTES_WHITELIST
        }
    )

    # name-spaced XML properties
    for k, v in elem.values.items():
        mo = _NAMESPACED_PROPERTY_RE.match(k)
        if mo:
            ns = mo[1]
            if ns in METADATA_SVG_NAMESPACES:
                metadata[f"svg_{METADATA_SVG_NAMESPACES[ns]}_{mo[2]}"] = v
            else:
                metadata["svg_" + k] = v

    return metadata


def _intersect_dict(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return dict(a.items() & b.items())


def _merge_metadata(
    base_metadata: dict[str, Any] | None, additional_metadata: dict[str, Any]
) -> dict[str, Any]:
    """Merge two metadata dictionaries with handling of uninitialized base dictionary."""

    if base_metadata is None:
        base_metadata = additional_metadata
    else:
        base_metadata = _intersect_dict(base_metadata, additional_metadata)
    return base_metadata


def _element_to_paths(elem: svgelements.SVGElement) -> _PathType | None:
    """Convert an SVG element into a path object that can be processed by
    :func:`_flattened_paths_to_line_collection`

    Args:
        elem: the element to convert

    Returns:
        the path object or None if the element should be ignored
    """
    if isinstance(elem, svgelements.Path):
        if len(elem) != 0:
            return elem
    elif isinstance(elem, (svgelements.Polyline, svgelements.Polygon)):
        # Here we add a "fake" path containing just the Polyline/Polygon,
        # to be treated specifically by _convert_flattened_paths.
        path = [svgelements.Move(elem.points[0]), elem]
        if isinstance(elem, svgelements.Polygon):
            path.append(svgelements.Close(elem.points[-1], elem.points[0]))
        return path
    elif isinstance(elem, svgelements.Shape):
        e = svgelements.Path(elem)
        e.reify()  # In some cases the shape could not have reified, the path must.
        if len(e) != 0:
            return e

    return None


def _extract_paths(
    group: svgelements.Group, recursive
) -> tuple[_PathListType, dict[str, Any] | None]:
    """Extract everything from the provided SVG group."""

    if recursive:
        everything = group.select()
    else:
        everything = group
    paths = []
    metadata: dict[str, Any] | None = None
    for elem in everything:
        if hasattr(elem, "values") and elem.values.get("visibility", "") in (
            "hidden",
            "collapse",
        ):
            continue

        path = _element_to_paths(elem)
        if path is None:
            continue
        else:
            paths.append(path)

        # apply union on metadata
        metadata = _merge_metadata(metadata, _extract_metadata_from_element(elem))

    return paths, metadata


def _extract_paths_by_attributes(
    group: svgelements.Group, attributes: Iterable[str]
) -> list[tuple[_PathListType, dict[str, Any] | None]]:
    """Extract everything from the provided SVG group, grouped by the specified attributes.

    The paths are grouped by unique combinations of the provided attributes.

    Args:
        group: SVG group from which to extract paths
        attributes: attributes by which to group paths

    Returns:
        list of tuple containing the list of paths and the associated metadata
    """

    @dataclasses.dataclass
    class _LayerDesc:
        paths: _PathListType = dataclasses.field(default_factory=list)
        metadata: dict[str, Any] | None = None

    attributes = tuple(attributes)
    results: dict[tuple, _LayerDesc] = collections.defaultdict(lambda: _LayerDesc())

    for elem in group.select():
        if hasattr(elem, "values") and elem.values.get("visibility", "") in (
            "hidden",
            "collapse",
        ):
            continue

        key = tuple(elem.values.get(attr, None) for attr in attributes)

        path = _element_to_paths(elem)
        if path is None:
            continue
        else:
            results[key].paths.append(path)

        # apply union on metadata
        results[key].metadata = _merge_metadata(
            results[key].metadata, _extract_metadata_from_element(elem)
        )

    return [(desc.paths, desc.metadata) for desc in results.values()]


def _flattened_paths_to_line_collection(
    paths: _PathListType,
    quantization: float,
    simplify: bool,
    parallel: bool,
    metadata: dict[str, Any] | None = None,
) -> LineCollection:
    """Convert a path list to a :class:`LineCollection`.

    The resulting :class:`vpype.LineCollection` instance's metadata contains all properties
    (as extracted with :func:`_extract_metadata_from_element`) whose value is identical for
    every single item within the group.

    Note: group-level properties are not explicitly added to the metadata since they are
    propagated to enclosed elements by svgelements.

    Args:
        paths: paths to process
        quantization: maximum length of linear elements to approximate curve paths
        simplify: should Shapely's simplify be run on curved elements after quantization
        parallel: enable multiprocessing
        metadata: if provided, metadata to include in the returned
            :class:`vpype.LineCollection` instance

    Returns:
        new :class:`LineCollection` instance containing the converted geometries and the
        provided metadata
    """

    def _process_path(path):
        if len(path) == 0:
            return []

        result = []
        point_stack = _ComplexStack()
        for seg in path:
            # handle cases of zero radius Arc
            if isinstance(seg, svgelements.Arc) and (seg.rx == 0 or seg.ry == 0):
                seg = svgelements.Line(start=seg.start, end=seg.end)

            if isinstance(seg, svgelements.Move):
                if len(point_stack) > 0:
                    result.append(point_stack.get())
                    point_stack = _ComplexStack()

                point_stack.append(complex(seg.end))
            elif isinstance(seg, (svgelements.Line, svgelements.Close)):
                start = complex(seg.start)
                end = complex(seg.end)
                if not point_stack.ends_with(start):
                    point_stack.append(start)
                if end != start:
                    point_stack.append(end)
            elif isinstance(seg, (svgelements.Polygon, svgelements.Polyline)):
                line = np.array(seg.points, dtype=float)
                line = line.view(dtype=complex).reshape(len(line))
                if point_stack.ends_with(line[0]):
                    point_stack.extend(line[1:])
                else:
                    point_stack.extend(line)
            else:
                # This is a curved element that we approximate with small segments
                step = max(2, int(math.ceil(seg.length() / quantization)))
                line = seg.npoint(np.linspace(0, 1, step))

                if simplify:
                    line = np.array(LineString(line).simplify(tolerance=quantization))

                line = line.view(dtype=complex).reshape(len(line))

                if point_stack.ends_with(line[0]):
                    point_stack.extend(line[1:])
                else:
                    point_stack.extend(line)

        if len(point_stack) > 0:
            result.append(point_stack.get())

        return result

    # benchmarking indicated that parallel processing only makes sense if simplify is used
    if parallel:
        with Pool() as p:
            results = p.map(_process_path, paths)
    else:
        results = map(_process_path, paths)

    lc = LineCollection(metadata=metadata)
    for res in results:
        lc.extend(res)
    return lc


def _get_source(file: str | TextIO) -> pathlib.Path | None:
    try:
        path = pathlib.Path(file)  # type: ignore
        if path.exists():
            return path.absolute()
    except TypeError:
        pass

    return None


def read_svg(
    file: str | TextIO,
    quantization: float,
    crop: bool = True,
    simplify: bool = False,
    parallel: bool = False,
    default_width: float | None = None,
    default_height: float | None = None,
) -> tuple[LineCollection, float, float]:
    """Read an SVG file and return its content as a :class:`LineCollection` instance.

    All curved geometries are chopped in segments no longer than the value of *quantization*.
    Optionally, the geometries are simplified using Shapely, using the value of *quantization*
    as tolerance.

    The page size is set based on the ``width`` and ``height`` attributes of the ``<svg>`` tag.
    If these attributes are missing or expressed in percent, ``svgelements`` attempts to use
    the ``viewBox`` attribute instead, or reverts to a 1000x1000px page size. This behaviour
    can be overridden by providing values for the ``default_width`` and ``default_height``
    arguments.

    Args:
        file: path of the SVG file or stream object
        quantization: maximum size of segment used to approximate curved geometries
        crop: crop the geometries to the SVG boundaries
        simplify: run Shapely's simplify on loaded geometry
        parallel: enable multiprocessing (only recommended for ``simplify=True`` and SVG with
            many curves)
        default_width: default width if not provided by SVG or if a percent width is provided
        default_height: default height if not provided by SVG or if a percent height is
            provided

    Returns:
        tuple containing a :class:`LineCollection` with the imported geometries as well as the
        width and height of the SVG
    """

    # default width is for SVG with % width/height
    svg = svgelements.SVG.parse(file, width=default_width, height=default_height)
    paths, metadata = _extract_paths(svg, True)
    lc = _flattened_paths_to_line_collection(paths, quantization, simplify, parallel, metadata)

    if crop:
        lc.crop(0, 0, svg.width, svg.height)

    source = _get_source(file)
    if source:
        lc.set_property(METADATA_FIELD_SOURCE, source)

    return lc, svg.width, svg.height


_LID_RE = re.compile(r"\d+")


def _extract_digit_group(label: str) -> str | None:
    """Extract a layer ID from a label.

    The first continuous group of digit, if any, is returned.
    """
    match = _LID_RE.search(label)
    if match is not None:
        return match.group()
    else:
        return None


def read_multilayer_svg(
    file: str | TextIO,
    quantization: float,
    crop: bool = True,
    simplify: bool = False,
    parallel: bool = False,
    default_width: float | None = None,
    default_height: float | None = None,
) -> Document:
    """Read a multilayer SVG file and return its content as a :class:`Document` instance
    retaining the SVG's layer structure and its dimension.

    Each top-level group is considered a layer. All non-group, top-level elements are imported
    in layer 1.

    Groups are matched to layer ID according their `inkscape:label` attribute, their `id`
    attribute or their appearing order, in that order of priority. The first contiguous group
    of digits in the label is used as layer ID. Lacking numeric characters, the appearing order
    is used. If the label is 0, it is changed to 1.

    All curved geometries are chopped in segments no longer than the value of *quantization*.
    Optionally, the geometries are simplified using Shapely, using the value of *quantization*
    as tolerance.

    The page size is set based on the ``width`` and ``height`` attributes of the ``<svg>`` tag.
    If these attributes are missing or expressed in percent, ``svgelements`` attempts to use
    the ``viewBox`` attribute instead, or reverts to a 1000x1000px page size. This behaviour
    can be overridden by providing values for the ``default_width`` and ``default_height``
    arguments.

    Args:
        file: path of the SVG file or stream object
        quantization: maximum size of segment used to approximate curved geometries
        crop: crop the geometries to the SVG boundaries
        simplify: run Shapely's simplify on loaded geometry
        parallel: enable multiprocessing (only recommended for ``simplify=True`` and SVG with
            many curves)
        default_width: default width if not provided by SVG or if a percent width is provided
        default_height: default height if not provided by SVG or if a percent height is
            provided

    Returns:
         :class:`Document` instance with the imported geometries and its page size set the SVG
         dimensions
    """

    svg = svgelements.SVG.parse(file, width=default_width, height=default_height)
    document = Document(metadata=_extract_metadata_from_element(svg, False))

    # non-group top level elements are loaded in layer 1
    paths, metadata = _extract_paths(svg, False)
    lc = _flattened_paths_to_line_collection(paths, quantization, simplify, parallel, metadata)
    if not lc.is_empty():
        document.add(lc, 1)
        document.layers[1].metadata = lc.metadata

    def _find_groups(group: svgelements.Group) -> Iterator[svgelements.Group]:
        for elem in group:
            if isinstance(elem, svgelements.Group):
                yield elem

    for i, g in enumerate(_find_groups(svg)):
        # noinspection HttpUrlsUsage
        layer_name = g.values.get("{http://www.inkscape.org/namespaces/inkscape}label", None)

        # compute a decent layer ID
        lid_str = _extract_digit_group(layer_name or "")
        if not lid_str:
            lid_str = _extract_digit_group(g.values.get("id") or "")
        if lid_str:
            lid = int(lid_str)
            if lid == 0:
                lid = 1
        else:
            lid = i + 1

        paths, metadata = _extract_paths(g, True)
        lc = _flattened_paths_to_line_collection(
            paths, quantization, simplify, parallel, metadata
        )

        if not lc.is_empty():
            # deal with the case of layer 1, which may already be initialized with top-level
            # paths
            if lid in document.layers:
                metadata = _intersect_dict(document.layers[lid].metadata, lc.metadata)
            else:
                metadata = lc.metadata

            document.add(lc, lid)
            document.layers[lid].metadata = metadata
            document.layers[lid].set_property(METADATA_FIELD_NAME, layer_name)

    document.page_size = (svg.width, svg.height)

    if crop:
        document.crop(0, 0, svg.width, svg.height)

    # Because of how svgelements works, all the <svg> level metadata is propagated to every
    # nested tag. As a result, we need to subtract global properties from the layer ones.
    for layer in document.layers.values():
        layer.metadata = dict(layer.metadata.items() - document.metadata.items())

    source = _get_source(file)
    if source:
        document.add_to_sources(source)

    return document


def read_svg_by_attributes(
    file: str | TextIO,
    attributes: Iterable[str],
    quantization: float,
    crop: bool = True,
    simplify: bool = False,
    parallel: bool = False,
    default_width: float | None = None,
    default_height: float | None = None,
) -> Document:
    """Read an SVG file by sorting geometries by unique combination of provided attributes.

    All curved geometries are chopped in segments no longer than the value of *quantization*.
    Optionally, the geometries are simplified using Shapely, using the value of *quantization*
    as tolerance.

    The page size is set based on the ``width`` and ``height`` attributes of the ``<svg>`` tag.
    If these attributes are missing or expressed in percent, ``svgelements`` attempts to use
    the ``viewBox`` attribute instead, or reverts to a 1000x1000px page size. This behaviour
    can be overridden by providing values for the ``default_width`` and ``default_height``
    arguments.

    Args:
        file: path of the SVG file or stream object
        attributes: attributes by which the object should be sorted
        quantization: maximum size of segment used to approximate curved geometries
        crop: crop the geometries to the SVG boundaries
        simplify: run Shapely's simplify on loaded geometry
        parallel: enable multiprocessing (only recommended for ``simplify=True`` and SVG with
            many curves)
        default_width: default width if not provided by SVG or if a percent width is provided
        default_height: default height if not provided by SVG or if a percent height is
            provided

    Returns:
         :class:`Document` instance with the imported geometries and its page size set the SVG
         dimensions
    """

    svg = svgelements.SVG.parse(file, width=default_width, height=default_height)
    document = Document(metadata=_extract_metadata_from_element(svg, False))

    for paths, metadata in _extract_paths_by_attributes(svg, attributes):
        lc = _flattened_paths_to_line_collection(
            paths, quantization, simplify, parallel, metadata
        )

        if not lc.is_empty():
            lid = document.free_id()
            document.add(lc, lid)
            document.layers[lid].metadata = lc.metadata

    document.page_size = (svg.width, svg.height)

    if crop:
        document.crop(0, 0, svg.width, svg.height)

    # Because of how svgelements works, all the <svg> level metadata is propagated to every
    # nested tag. As a result, we need to subtract global properties from the layer ones.
    for layer in document.layers.values():
        layer.metadata = dict(layer.metadata.items() - document.metadata.items())

    source = _get_source(file)
    if source:
        document.add_to_sources(source)

    return document


_WRITE_SVG_RESTORE_EXCLUDE_LIST = (
    "svg_display",
    "svg_visibility",
    "svg_stroke",
    "svg_stroke-width",
    "svg_inkscape_groupmode",  # handled by svgwrite
    "svg_inkscape_label",  # handled by system field
)


def _restore_metadata(elem: svgwrite.base.BaseElement, metadata: dict[str, Any]) -> None:
    for prop, val in metadata.items():
        if prop.startswith("svg_") and prop not in _WRITE_SVG_RESTORE_EXCLUDE_LIST:
            parts = prop[4:].split("_")
            if len(parts) == 2 and parts[0] in METADATA_SVG_NAMESPACES.values():
                elem.attribs[":".join(parts)] = str(val)
            elif len(parts) == 1:
                elem.attribs[parts[0]] = str(val)


# noinspection HttpUrlsUsage
def write_svg(
    output: TextIO,
    document: Document,
    page_size: tuple[float, float] | None = None,
    center: bool = False,
    source_string: str = "",
    layer_label_format: str | None = None,
    show_pen_up: bool = False,
    color_mode: str = "default",
    use_svg_metadata: bool = False,
    set_date: bool = True,
) -> None:
    """Create an SVG from a :py:class:`Document` instance.

    If no page size is provided (or (0, 0) is passed), the SVG generated has bounds tightly
    fitted around the geometries. Otherwise, the provided size (in pixel) is used. The width
    and height is capped to a minimum of 1 pixel.

    By default, no translation is applied on the geometry. If `center=True`, geometries are
    moved to the center of the page.

    No scaling or rotation is applied to geometries.

    Layers are named after the `vp_name` system property if it exists, or with their layer ID
    otherwise. This can be overridden with the  ``layer_label_format`` parameter, which may
    contain a C-style format specifier such as `%d` which will be replaced by the layer number.

    Optionally, metadata properties prefixed with ``svg_`` (typically extracted from an input
    SVG with the :ref:`cmd_read` command) may be used as group attributes with
    ``use_svg_metadata=True``.

    The color of the layer is determined by the ``color_mode`` parameter.

        - ``"default"``: use ``vp_color`` system property and reverts to the default coloring
          scheme
        - ``"none"``: no formatting (black)
        - ``"layer"``: one color per layer based on the default coloring scheme
        - ``"path"``: one color per path based on the default coloring scheme

    The pen width is set to the `vp_pen_width` system property if it exists.

    For previsualisation purposes, pen-up trajectories can be added to the SVG using the
    ``show pen_up`` argument.

    Args:
        output: text-mode IO stream where SVG code will be written
        document: geometries to be written
        page_size: if provided, overrides document.page_size
        center: center geometries on page before export
        source_string: value of the `source` metadata
        layer_label_format: format string for layer label naming
        show_pen_up: add paths for the pen-up trajectories
        color_mode: "default" (system property), "none" (no formatting), "layer" (one color per
            layer), "path" (one color per path)
        use_svg_metadata: apply ``svg_``-prefixed properties as SVG attributes
        set_date: controls whether the current date and time is set in the SVG's metadata
            (disabling it is useful for auto-generated SVG under VCS)
    """

    # compute bounds
    bounds = document.bounds()
    if bounds is None:
        # empty geometry, we provide fake bounds
        bounds = (0, 0, 1, 1)

    if page_size:
        size = page_size
        tight = page_size == (0.0, 0.0)
    elif document.page_size:
        size = document.page_size
        tight = False
    else:
        size = (bounds[2] - bounds[0], bounds[3] - bounds[1])
        tight = True

    if center:
        corrected_doc = copy.deepcopy(document)
        corrected_doc.translate(
            (size[0] - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
            (size[1] - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
        )
    elif tight:
        corrected_doc = copy.deepcopy(document)
        corrected_doc.translate(-bounds[0], -bounds[1])
    else:
        corrected_doc = document

    # output SVG, width/height are capped to 1px
    capped_size = tuple(max(1, s) for s in size)
    size_cm = tuple(f"{round(s / UNITS['cm'], 8)}cm" for s in capped_size)
    dwg = svgwrite.Drawing(size=size_cm, profile="tiny", debug=False)
    inkscape = Inkscape(dwg)
    dwg.attribs.update({"viewBox": f"0 0 {capped_size[0]} {capped_size[1]}"})
    dwg.attribs.update({f"xmlns:{v}": k for k, v in METADATA_SVG_NAMESPACES.items()})

    if use_svg_metadata:
        _restore_metadata(dwg, document.metadata)

    # add metadata
    metadata = ElementTree.Element("rdf:RDF")
    work = ElementTree.SubElement(metadata, "cc:Work")
    fmt = ElementTree.SubElement(work, "dc:format")
    fmt.text = "image/svg+xml"
    source = ElementTree.SubElement(work, "dc:source")
    source.text = source_string
    if set_date:
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

        for layer in corrected_doc.layers.values():
            for line in layer.pen_up_trajectories():
                group.add(
                    dwg.line((line[0].real, line[0].imag), (line[-1].real, line[-1].imag))
                )

        dwg.add(group)

    for layer_id in sorted(corrected_doc.layers.keys()):
        layer = corrected_doc.layers[layer_id]

        if layer_label_format is not None:
            label = layer_label_format % layer_id
        elif layer.property_exists(METADATA_FIELD_NAME):
            label = str(layer.property(METADATA_FIELD_NAME))
        else:
            label = str(layer_id)

        group = inkscape.layer(label=label)
        group.attribs["fill"] = "none"

        color = Color("black")
        if color_mode == "layer" or (
            color_mode == "default" and not layer.property_exists(METADATA_FIELD_COLOR)
        ):
            color = METADATA_DEFAULT_COLOR_SCHEME[
                color_idx % len(METADATA_DEFAULT_COLOR_SCHEME)
            ]
            color_idx += 1
        elif color_mode == "default":
            color = Color(layer.property(METADATA_FIELD_COLOR))

            # we want to avoid a subsequent layer whose color is undefined to have its color
            # affected by whether previous layer have their color defined
            color_idx += 1

        group.attribs["stroke"] = color.as_rgb_hex()
        if color.alpha < 255:
            group.attribs["stroke-opacity"] = f"{color.alpha/255:.3f}"
        group.attribs["style"] = "display:inline"
        group.attribs["id"] = f"layer{layer_id}"
        if layer.property_exists(METADATA_FIELD_PEN_WIDTH):
            group.attribs["stroke-width"] = float(
                cast(float, layer.property(METADATA_FIELD_PEN_WIDTH))
            )

        # dump all svg properties as attribute
        if use_svg_metadata:
            _restore_metadata(group, layer.metadata)

        for line in layer:
            if len(line) <= 1:
                continue

            if len(line) == 2:
                path = dwg.line((line[0].real, line[0].imag), (line[1].real, line[1].imag))
            elif line[0] == line[-1]:
                path = dwg.polygon((c.real, c.imag) for c in line[:-1])
            else:
                path = dwg.polyline((c.real, c.imag) for c in line)

            if color_mode == "path":
                path.attribs["stroke"] = METADATA_DEFAULT_COLOR_SCHEME[
                    color_idx % len(METADATA_DEFAULT_COLOR_SCHEME)
                ]
                color_idx += 1
            group.add(path)

        dwg.add(group)

    dwg.write(output, pretty=True)


def _get_hpgl_config(device: str | None, page_size: str) -> tuple[PlotterConfig, PaperConfig]:
    plotter_config = config_manager.get_plotter_config(device)
    if plotter_config is None:
        raise ValueError(f"no configuration available for plotter '{device}'")
    paper_config = plotter_config.paper_config(page_size)
    if paper_config is None:
        raise ValueError(
            f"no configuration available for paper size '{page_size}' with plotter "
            f"'{device}'"
        )

    return plotter_config, paper_config


def write_hpgl(
    output: TextIO,
    document: Document,
    page_size: str,
    landscape: bool,
    center: bool,
    device: str | None,
    velocity: int | None,
    absolute: bool = False,
    quiet: bool = False,
) -> None:
    """Create an HPGL file from the :class:`Document` instance.

    The ``device``/``page_size`` combination must be defined in the built-in or user-provided
    config files or an exception will be raised.

    By default, no translation is applied on the geometry. If `center=True`, geometries are
    moved to the center of the page.

    No scaling or rotation is applied to geometries.

    Args:
        output: text-mode IO stream where SVG code will be written
        document: geometries to be written
        page_size: page size string (it must be configured for the selected device)
        landscape: if True, the geometries are generated in landscape orientation
        center: center geometries on page before export
        device: name of the device to use (the corresponding config must exist). If not
            provided, a default device must be configured, which will be used.
        velocity: if provided, a VS command will be generated with the corresponding value
        absolute: if True, only use absolute coordinates
        quiet: if True, do not print the plotter/paper info strings
    """

    # empty HPGL is acceptable there are no geometries to plot
    if document.is_empty():
        return

    plotter_config, paper_config = _get_hpgl_config(device, page_size)
    if not quiet:
        if plotter_config.info:
            # use of echo instead of print needed for testability
            # https://github.com/pallets/click/issues/1678
            click.echo(plotter_config.info, err=True)
        if paper_config.info:
            click.echo(paper_config.info, err=True)

    # Handle flex paper size.
    # If paper_size is not provided by the config, the paper size is then assumed to be the
    # same as the current page size. In this case, the config should provide paper_orientation
    # since it may not be the same as the document's page size
    paper_size = paper_config.paper_size
    if paper_size is None:
        if document.page_size is not None:
            paper_size = document.page_size
        else:
            raise ValueError(
                "paper size must be set using `read`, `pagesize`, or `layout` command"
            )

    # Ensure paper orientation is correct.
    if paper_config.paper_orientation is not None and (
        (paper_config.paper_orientation == "portrait" and paper_size[0] > paper_size[1])
        or (paper_config.paper_orientation == "landscape" and paper_size[0] < paper_size[1])
    ):
        paper_size = paper_size[::-1]

    # Handle origin location.
    origin_x, origin_y = paper_config.origin_location
    if paper_config.origin_location_reference not in ["topleft", "botleft"]:
        raise ValueError(
            "incorrect value for origin_location_reference: "
            f"{paper_config.origin_location_reference}"
        )
    if paper_config.origin_location_reference == "botleft":
        origin_y = paper_size[1] - origin_y

    # are plotter coordinate placed in landscape or portrait orientation?
    coords_landscape = paper_size[0] > paper_size[1]

    # document preprocessing:
    # - make a copy
    # - deal with orientation mismatch
    # - optionally center on paper
    # - convert to plotter units
    # - crop to plotter limits
    document = copy.deepcopy(document)

    if landscape != coords_landscape:
        document.rotate(-math.pi / 2)
        document.translate(0, paper_size[1])

    if paper_config.rotate_180:
        document.scale(-1, -1)
        document.translate(*paper_size)

    if center:
        bounds = document.bounds()
        if bounds is not None:
            document.translate(
                (paper_size[0] - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
                (paper_size[1] - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
            )

    document.translate(-origin_x, -origin_y)
    unit_per_pixel = 1 / plotter_config.plotter_unit_length
    document.scale(
        unit_per_pixel, -unit_per_pixel if paper_config.y_axis_up else unit_per_pixel
    )
    if paper_config.x_range is not None and paper_config.y_range is not None:
        document.crop(
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
        output.write(f"VS{int(velocity)};")
    if paper_config.set_ps is not None:
        output.write(f"PS{int(paper_config.set_ps)};")

    first_layer = True
    last_point: complex | None = None
    for layer_id in sorted(document.layers.keys()):
        pen_id = 1 + (layer_id - 1) % plotter_config.pen_count

        # As per #310, we emit a single PU; between layers
        if not first_layer:
            output.write(f"PU;")
        else:
            first_layer = False
        output.write(f"SP{pen_id};")

        for line in document.layers[layer_id]:
            if len(line) < 2:
                continue

            if absolute:
                output.write(
                    f"PU{complex_to_str(line[0])};PD"
                    + ",".join(complex_to_str(p) for p in line[1:])
                    + ";"
                )
            else:
                # snap all points of the line to the HPGL grid, such as to avoid any aliasing
                # when computing the diff between points
                line = np.round(line)

                if last_point is None:
                    output.write(f"PU{complex_to_str(line[0])};PR;")
                else:
                    output.write(f"PU{complex_to_str(line[0] - last_point)};")

                output.write("PD" + ",".join(complex_to_str(p) for p in np.diff(line)) + ";")
                last_point = line[-1]

    if not absolute:
        output.write("PA;")
    output.write(f"PU{paper_config.final_pu_params if paper_config.final_pu_params else ''};")
    output.write("SP0;IN;\n")
    output.flush()
