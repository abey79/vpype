"""
.. module:: vpype

Implementation of vpype's data model
"""
import math
from typing import Union, Iterable, List, Dict, Tuple, Optional

import numpy as np
from shapely.geometry import MultiLineString, LineString, LinearRing

from .geometry import reloop, crop
from .line_index import LineIndex

# REMINDER: anything added here must be added to docs/api.rst
__all__ = [
    "LineCollection",
    "VectorData",
    "LineLike",
    "LineCollectionLike",
    "as_vector",
]

LineLike = Union[LineString, LinearRing, Iterable[complex]]

# We accept LineString and LinearRing as line collection because MultiLineString are regularly
# converted to LineString/LinearRing when operation reduce them to single-line construct.
LineCollectionLike = Union[
    Iterable[LineLike], MultiLineString, "LineCollection", LineString, LinearRing
]


def as_vector(a: np.ndarray):
    """Return a view of a complex line array that behaves as an Nx2 real array"""
    return a.view(dtype=float).reshape(len(a), 2)


class LineCollection:
    """
    :py:class:`LineCollection` encapsulate a list of piecewise linear lines (or paths). Lines
    are implemented as 1D numpy arrays of complex numbers whose real and imaginary parts
    represent the X, respectively Y, coordinates of point in the paths.

    An instance of :py:class:`LineCollection` is used to model a single layer in vpype's
    :ref:`pipeline <fundamentals_pipeline>`. The complete pipeline is modelled by a
    :py:class:`VectorData` instance, which  essentially is a mapping of ``int`` (layer ID) to
    :py:class:`LineCollection`.

    Although the actual ``list`` is stored as private data member in :py:class:`LineCollection`
    instances, the class provides a sequence API similar to ``list``::

        >>> import vpype, numpy as np
        >>> lc = vpype.LineCollection()
        >>> lc.append(np.array([0, 10. + 10.j]))
        >>> lc.append(np.array([10.j, 5. + 5.j]))
        >>> len(lc)
        2
        >>> lc[0]
        array([ 0. +0.j, 10.+10.j])
        >>> for line in lc:
        ...    print(repr(line))
        ...
        array([ 0. +0.j, 10.+10.j])
        array([0.+10.j, 5. +5.j])

    In addition to Numpy arrays, the class accepts paths expressed in a variety of format
    including Python ``list`` or Shapely objects::

        >>> from shapely.geometry import LineString, LinearRing, MultiLineString
        >>> lc = vpype.LineCollection()
        >>> lc.append([5, 5+5j])
        >>> lc.append(LineString([(1, 1), (3, 2)]))
        >>> lc.append(LinearRing([(0, 0), (1, 0), (1, 1), (0, 1)]))
        >>> lc.extend(MultiLineString([[(0, 0), (10, 0)], [(4, 4), (0, 4)]]))
        >>> lc
        LineCollection([array([5.+0.j, 5.+5.j]), array([1.+1.j, 3.+2.j]), array([0.+0.j,
        1.+0.j, 1.+1.j, 0.+1.j, 0.+0.j]), array([ 0.+0.j, 10.+0.j]), array([4.+4.j, 0.+4.j])])

    Instances can also be converted to Shapely's MultiLineString:

        >>> mls = lc.as_mls()
        >>> print(mls)
        MULTILINESTRING ((5 0, 5 5), (1 1, 3 2), (0 0, 1 0, 1 1, 0 1, 0 0), (0 0, 10 0),
        (4 4, 0 4))

    Finally, :py:class:`LineCollection` implements a number of operations such as geometrical
    transformation, cropping, merging, etc. (see member function documentation for details).
    """

    def __init__(self, lines: LineCollectionLike = ()):
        """Create a LineCollection instance from an iterable of lines.

        Args:
            lines (LineCollectionLike): iterable of line (accepts the same input as
                :func:`~LineCollection.append`).
        """
        self._lines: List[np.ndarray] = []

        self.extend(lines)

    @property
    def lines(self) -> List[np.ndarray]:
        """Returns the list of line.

        Returns:
            list of line
        """
        return self._lines

    def append(self, line: LineLike) -> None:
        """Append a single line.

        This function accepts an iterable of complex or a Shapely geometry
        (:py:class:`LineString` or :py:class:`LinearRing`).

        Args:
            line (LineLike): line to append
        """
        if isinstance(line, LineString) or isinstance(line, LinearRing):
            # noinspection PyTypeChecker
            self._lines.append(np.array(line).view(dtype=complex).reshape(-1))
        else:
            line = np.array(line, dtype=complex).reshape(-1)
            if len(line) > 1:
                self._lines.append(line)

    def extend(self, lines: LineCollectionLike) -> None:
        """Append lines from a collection.

        This function accepts an iterable of iterable of complex, another
        :py:class:`LineCollection` instance, or a Shapely geometry
        (:py:class:`MultiLineString`, :py:class:`LineString` or :py:class:`LinearRing`).

        Shapely's LineString and LinearRing are occasionally obtained when a MultiLineString is
        actually expected. As a result, they are accepted as input even though they are not,
        strictly speaking, a line collection.

        Args:
            lines (LineCollectionLike): lines to append
        """

        if hasattr(lines, "geom_type") and lines.is_empty:  # type: ignore
            return

        # sometimes, mls end up actually being ls
        if isinstance(lines, LineString) or isinstance(lines, LinearRing):
            lines = [lines]

        for line in lines:
            self.append(line)

    def is_empty(self) -> bool:
        """Check for emptiness.

        Returns:
            True if the instance does not contain any line, False otherwise.
        """
        return len(self) == 0

    def __iter__(self):
        return self._lines.__iter__()

    def __len__(self) -> int:
        return len(self._lines)

    def __getitem__(self, item: Union[int, slice]):
        return self._lines[item]

    def __repr__(self):
        return f"LineCollection({self._lines})"

    def as_mls(self) -> MultiLineString:
        """Converts the LineCollection to a :py:class:`MultiLineString`.

        Returns:
            a MultiLineString Shapely object
        """
        return MultiLineString([as_vector(line) for line in self.lines])

    def translate(self, dx: float, dy: float) -> None:
        """Translates all line by a given offset.

        Args:
            dx: offset along X axis
            dy: offset along Y axis
        """
        c = complex(dx, dy)
        for line in self._lines:
            line += c

    def scale(self, sx: float, sy: Optional[float] = None) -> None:
        """Scale the geometry.

        The scaling is performed about the coordinates origin (0, 0). To scale around a
        specific location, appropriate translations must be performed before and after the
        scaling::

            >>> import vpype
            >>> lc = vpype.LineCollection([[(-1+1j, 1+1j)]])
            >>> lc.translate(0, -1)
            >>> lc.scale(1.2)
            >>> lc.translate(0, 1)
            >>> lc
            LineCollection([array([-1.2+1.j,  1.2+1.j])])

        Args:
            sx: scale factor along x
            sy: scale factor along y (if None, then sx is used)
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
                self._lines[i] = reloop(line)

    def crop(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Crop all lines to a rectangular area.

        Args:
            x1, y1: first corner of the crop area
            x2, y2: second corner of the crop area
        """

        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        if x1 == x2 or y1 == y2:
            self._lines = []
        else:
            new_lines = []
            for line in self._lines:
                new_lines.extend(crop(line, x1, y1, x2, y2))
            self._lines = new_lines

    def merge(self, tolerance: float, flip: bool = True) -> None:
        """Merge lines whose endings overlap or are very close.

        Args:
            tolerance: max distance between line ending that may be merged
            flip: allow flipping line direction for further merging
        """
        if len(self) < 2:
            return

        index = LineIndex(self.lines, reverse=flip)
        new_lines = LineCollection()

        while len(index) > 0:
            line = index.pop_front()

            # we append to `line` until we dont find anything to add
            while True:
                idx, reverse = index.find_nearest_within(line[-1], tolerance)
                if idx is None and flip:
                    idx, reverse = index.find_nearest_within(line[0], tolerance)
                    line = np.flip(line)
                if idx is None:
                    break
                new_line = index.pop(idx)
                if reverse:
                    new_line = np.flip(new_line)
                line = np.hstack([line, new_line])

            new_lines.append(line)

        self._lines = new_lines._lines

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

    def __init__(self, line_collection: LineCollection = None):
        """Constructor.

        Args:
            line_collection: if provided, used as layer 1
        """
        self._layers: Dict[int, LineCollection] = {}

        if line_collection:
            self.add(line_collection, 1)

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

    def pop(self, layer_id: int) -> LineCollection:
        return self._layers.pop(layer_id)

    def count(self) -> int:
        return len(self._layers.keys())

    def translate(self, dx: float, dy: float) -> None:
        for layer in self._layers.values():
            layer.translate(dx, dy)

    def scale(self, sx: float, sy: Optional[float] = None) -> None:
        for layer in self._layers.values():
            layer.scale(sx, sy)

    def rotate(self, angle: float) -> None:
        for layer in self._layers.values():
            layer.rotate(angle)

    def bounds(
        self, layer_ids: Union[None, Iterable[int]] = None
    ) -> Optional[Tuple[float, float, float, float]]:
        """Compute bounds of the vector data. If `layer_ids` is provided, bounds are computed
        only the corresponding ids.

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
        if len(a) > 0:
            return a[:, 0].min(), a[:, 1].min(), a[:, 2].max(), a[:, 3].max()
        else:
            return None

    def length(self) -> float:
        return sum(layer.length() for layer in self._layers.values())

    def pen_up_length(self) -> float:
        return sum(layer.pen_up_length()[0] for layer in self._layers.values())

    def segment_count(self) -> int:
        return sum(layer.segment_count() for layer in self._layers.values())
