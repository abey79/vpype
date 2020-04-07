"""
Implementation of vpype's data model
"""
import math
from typing import Union, Iterable, List, Dict, Tuple, Optional

import numpy as np
import svgpathtools as svg
from shapely.geometry import MultiLineString, LineString, LinearRing

from .utils import convert

LineLike = Union[LineString, LinearRing, Iterable[complex]]

# We accept LineString and LinearRing as line collection because MultiLineString are regularly
# converted to LineString/LinearRing when operation reduce them to single-line construct.
LineCollectionLike = Union[
    Iterable[LineLike], MultiLineString, "LineCollection", LineString, LinearRing
]


def as_vector(a: np.ndarray):
    """Return a view of a complex line array that behaves as an Nx2 real array"""
    return a.view(dtype=float).reshape(len(a), 2)


def read_svg(
    filename: str, quantization: float, simplify: bool = False, return_size: bool = False
) -> Union["LineCollection", Tuple["LineCollection", float, float]]:
    """
    Read a SVG file an return its content as a :class:`LineCollection` instance. All curved
    geometries are chopped in segments no longer than the value of *quantization*.
    Optionally, the geometries are simplified using Shapely, using the value of *quantization*
    as tolerance.

    :param filename: path of the SVG file
    :param quantization: maximum size of segment used to approximate curved geometries
    :param simplify: run Shapely's simplify on loaded geometry
    :param return_size: if True, return a size 3 Tuple containing the geometries and the SVG
        width and height
    :return: imported geometries, and optionally width and height of the SVG
    """

    doc = svg.Document(filename)
    results = doc.flatten_all_paths()
    root = doc.tree.getroot()

    # we must interpret correctly the viewBox, width and height attribs in order to scale
    # the file content to proper pixels

    width = height = None
    if "viewBox" in root.attrib:
        # A view box is defined so we must correctly scale from user coordinates
        # https://css-tricks.com/scale-svg/
        # TODO: we should honor the `preserveAspectRatio` attribute

        viewbox_min_x, viewbox_min_y, viewbox_width, viewbox_height = [
            float(s) for s in root.attrib["viewBox"].split()
        ]

        width = convert(root.attrib.get("width", viewbox_width))
        height = convert(root.attrib.get("height", viewbox_height))

        scale_x = width / viewbox_width
        scale_y = height / viewbox_height
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

    if return_size:
        if width is None or height is None:
            _, _, width, height = lc.bounds()
        return lc, width, height
    else:
        return lc


def interpolate_line(line: np.ndarray, step: float) -> np.ndarray:
    """
    Compute a linearly interpolated version of *line* with segments of *step* length or
    less.
    :param line: 1D array of complex
    :param step: maximum length of interpolated segment
    :return: interpolated 1D array of complex
    """

    diff = np.diff(line)
    curv_absc = np.cumsum(np.hstack([0, np.hypot(diff.real, diff.imag)]))
    max_curv_absc = np.max(curv_absc)
    return np.interp(
        np.linspace(0, max_curv_absc, 1 + math.ceil(max_curv_absc / step)), curv_absc, line
    )


class LineCollection:
    def __init__(self, lines: LineCollectionLike = ()):
        """
        Create a line collection.
        :param lines: iterable of line-like things
        """
        self._lines: List[np.ndarray] = []

        self.extend(lines)

    @property
    def lines(self) -> List[np.ndarray]:
        return self._lines

    def append(self, line: LineLike) -> None:
        if isinstance(line, LineString) or isinstance(line, LinearRing):
            # noinspection PyTypeChecker
            self._lines.append(np.array(line).view(dtype=complex).reshape(-1))
        else:
            self._lines.append(np.array(line, dtype=complex).reshape(-1))

    def extend(self, lines: LineCollectionLike) -> None:
        if hasattr(lines, "geom_type") and lines.is_empty:
            return

        # sometimes, mls end up actually being ls
        if isinstance(lines, LineString) or isinstance(lines, LinearRing):
            lines = [lines]

        for line in lines:
            self.append(line)

    def is_empty(self) -> bool:
        return len(self) == 0

    def __iter__(self):
        return self._lines.__iter__()

    def __len__(self) -> int:
        return len(self._lines)

    def __getitem__(self, item: int):
        return self._lines[item]

    def as_mls(self) -> MultiLineString:
        return MultiLineString([as_vector(line) for line in self.lines])

    def translate(self, dx: float, dy: float) -> None:
        c = complex(dx, dy)
        for line in self._lines:
            line += c

    def scale(self, sx: float, sy: Optional[float] = None) -> None:
        """Scale the geometry
        :param sx: scale factor along x
        :param sy: scale factor along y (if None, then sx is used)
        """
        if sy is None:
            sy = sx

        for line in self._lines:
            line.real *= sx
            line.imag *= sy

    def rotate(self, angle: float) -> None:
        c = complex(math.cos(angle), math.sin(angle))
        for line in self._lines:
            line *= c

    def skew(self, ax: float, ay: float) -> None:
        tx, ty = math.tan(ax), math.tan(ay)
        for line in self._lines:
            line += tx * line.imag + 1j * ty * line.real

    def reloop(self, tolerance: float) -> None:
        """Randomizes the seam of closed paths. Paths are considered closed when their first
        and last point are closer than *tolerance*.
        :param tolerance: tolerance to determine if a path is closed
        """

        for i, line in enumerate(self._lines):
            delta = line[-1] - line[0]
            if np.hypot(delta.real, delta.imag) <= tolerance:
                self._lines[i] = _reloop_line(line)

    def bounds(self) -> Optional[Tuple[float, float, float, float]]:
        if len(self._lines) == 0:
            return None
        else:
            return (
                min((line.real.min() for line in self._lines)),
                min((line.imag.min() for line in self._lines)),
                max((line.real.max() for line in self._lines)),
                max((line.imag.max() for line in self._lines)),
            )

    def width(self) -> float:
        """Returns the total width of the geometries"""
        if len(self._lines) == 0:
            return 0.0
        else:
            return max((line.real.max() for line in self._lines)) - min(
                (line.real.min() for line in self._lines)
            )

    def height(self) -> float:
        """Returns the total height of the geometries"""
        if len(self._lines) == 0:
            return 0.0
        else:
            return max((line.imag.max() for line in self._lines)) - min(
                (line.imag.min() for line in self._lines)
            )

    def length(self) -> float:
        return sum(np.sum(np.abs(np.diff(line))) for line in self._lines)

    def pen_up_length(self) -> Tuple[float, float, float]:
        """Total, mean, median distance to move from one path's end to the next path's start"""
        ends = np.array([line[-1] for line in self.lines[:-1]])
        starts = np.array([line[0] for line in self.lines[1:]])
        dists = np.abs(starts - ends)
        # noinspection PyTypeChecker
        return np.sum(dists), np.mean(dists), np.median(dists)

    def segment_count(self) -> int:
        """Total number of segment across all lines."""
        return sum(max(0, len(line) - 1) for line in self._lines)


class VectorData:
    """This class implements the core of vpype's data model. An empty VectorData is created at
    launch and passed from commands to commands until termination. It models an arbitrary
    number of layers whose label are a positive integer, each consisting of a LineCollection"""

    def __init__(self):
        self._layers: Dict[int, LineCollection] = {}
        # self._current: Union[int, None] = None

    @property
    def layers(self) -> Dict[int, LineCollection]:
        return self._layers

    def ids(self) -> Iterable[int]:
        return self._layers.keys()

    def layers_from_ids(self, layer_ids: Iterable[int]):
        """Returns an generator that yield layers corresponding to the provided IDs, provided
        they exist.
        """
        return (self._layers[lid] for lid in layer_ids if lid in self._layers)

    def exists(self, layer_id: int) -> bool:
        return layer_id in self._layers

    def __getitem__(self, layer_id: int):
        return self._layers.__getitem__(layer_id)

    def __setitem__(self, layer_id: int, value: LineCollectionLike):
        if layer_id < 1:
            raise ValueError(f"expected non-null, positive layer id, got {layer_id} instead")

        if isinstance(value, LineCollection):
            self._layers[layer_id] = value
        else:
            self._layers[layer_id] = LineCollection(value)

    def __contains__(self, layer_id) -> bool:
        return self._layers.__contains__(layer_id)

    def free_id(self) -> int:
        """Returns the lowest free layer id"""
        vid = 1
        while vid in self._layers:
            vid += 1
        return vid

    def add(self, lc: LineCollection, layer_id: Union[None, int] = None) -> None:
        """if layer_id is None, a new layer with lowest possible id is created"""
        if layer_id is None:
            layer_id = 1
            while layer_id in self._layers:
                layer_id += 1

        if layer_id in self._layers:
            self._layers[layer_id].extend(lc)
        else:
            self._layers[layer_id] = lc

    def extend(self, vd: "VectorData"):
        for layer_id, layer in vd.layers.items():
            self.add(layer, layer_id)

    def is_empty(self) -> bool:
        for layer in self.layers.values():
            if not layer.is_empty():
                return False
        return True

    def count(self) -> int:
        return len(self._layers.keys())

    def translate(self, dx: float, dy: float) -> None:
        for layer in self._layers.values():
            layer.translate(dx, dy)

    def bounds(
        self, layer_ids: Union[None, Iterable[int]] = None
    ) -> Tuple[float, float, float, float]:
        """
        Compute bounds of the vector data. If `layer_ids` is provided, bounds are computed only
        the corresponding ids.

        :param layer_ids: layers to consider
        :return: boundaries of the geometries
        """
        if layer_ids is None:
            layer_ids = self.ids()
        a = np.array(
            [
                self._layers[vid].bounds()
                for vid in layer_ids
                if self.exists(vid) and len(self._layers[vid]) > 0
            ]
        )
        return a[:, 0].min(), a[:, 1].min(), a[:, 2].max(), a[:, 3].max()

    def length(self) -> float:
        return sum(layer.length() for layer in self._layers.values())

    def pen_up_length(self) -> float:
        return sum(layer.pen_up_length()[0] for layer in self._layers.values())

    def segment_count(self) -> int:
        return sum(layer.segment_count() for layer in self._layers.values())


def _reloop_line(line: np.ndarray, loc: Optional[int] = None) -> np.ndarray:
    """
    Change the seam of a closed path. Closed-ness is not checked. Beginning and end points are
    averaged to compute a new point. A new seam location can be provided or will be chosen
    randomly.
    :param line: path to reloop
    :param loc: new seam location
    :return: re-seamed path
    """

    if loc is None:
        loc = np.random.randint(len(line) - 1)
    end_point = 0.5 * (line[0] + line[-1])
    line[0] = end_point
    line[-1] = end_point
    return np.hstack([line[loc:], line[1 : min(loc + 1, len(line))]])
