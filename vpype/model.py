"""Implementation of vpype's data model
"""
import logging
import math
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple, Union, cast

import numpy as np
from shapely.geometry import LinearRing, LineString, MultiLineString

from .geometry import crop, reloop
from .line_index import LineIndex

# REMINDER: anything added here must be added to docs/api.rst
__all__ = [
    "LineCollection",
    "Document",
    "LineLike",
    "LineCollectionLike",
    "as_vector",
    # deprecated:
    "VectorData",
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


# noinspection PyShadowingNames
class LineCollection:
    """
    :py:class:`LineCollection` encapsulate a list of piecewise linear lines (or paths). Lines
    are implemented as 1D numpy arrays of complex numbers whose real and imaginary parts
    represent the X, respectively Y, coordinates of point in the paths.

    An instance of :py:class:`LineCollection` is used to model a single layer in vpype's
    :ref:`pipeline <fundamentals_pipeline>`. The complete pipeline is modelled by a
    :py:class:`Document` instance, which  essentially is a mapping of ``int`` (layer ID) to
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

    def reverse(self) -> None:
        """Reverse order of the lines."""
        self._lines = list(reversed(self._lines))

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
            >>> lc = vpype.LineCollection([(-1+1j, 1+1j)])
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
        """Rotates the geometry by ``angle`` amount.

        The angle is expressed in radian. Positive value rotate clockwise.

        The rotation is performed about the coordinates origin (0, 0). To rotate around a
        specific location, appropriate translations must be performed before and after the
        scaling::

            >>> import vpype
            >>> lc = vpype.LineCollection([(-1+1j, 1+1j)])
            >>> lc.translate(0, -1)
            >>> lc.rotate(1.2)
            >>> lc.translate(0, 1)

        Args:
            angle: rotation angle in rad
        """
        c = complex(math.cos(angle), math.sin(angle))
        for line in self._lines:
            line *= c

    def skew(self, ax: float, ay: float) -> None:
        """Skew the geometry by some angular amounts along X and Y axes.

        The angle is expressed in radians.

        The skew is performed about the coordinates origin (0, 0). To rotate around a
        specific location, appropriate translations must be performed before and after the
        scaling::

            >>> import vpype
            >>> lc = vpype.LineCollection([(-1+1j, 1+1j)])
            >>> lc.translate(0, -1)
            >>> lc.skew(0., 1.2)
            >>> lc.translate(0, 1)

        Args:
            ax: skew angle in rad along X axis
            ay: skew angle in rad along Y axis
        """
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

    def filter(self, key: Callable[[np.ndarray], bool]) -> None:
        """Remove lines from the :class:`LineCollection` for which key returns False.

        Args:
            key: filter (returns True if the line should be kept or False otherwise)
        """
        self._lines = [line for line in self._lines if key(line)]

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
                new_line = cast(np.ndarray, index.pop(idx))
                if reverse:
                    new_line = np.flip(new_line)
                line = np.hstack([line, new_line])

            new_lines.append(line)

        self._lines = new_lines._lines

    def bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """Returns the geometries' bounding box.

        Returns:
            tuple (xmin, ymin, xmax, ymax) for the bounding box or None if the LineCollection
            is empty
        """
        if len(self._lines) == 0:
            return None
        else:
            return (
                float(min((line.real.min() for line in self._lines))),
                float(min((line.imag.min() for line in self._lines))),
                float(max((line.real.max() for line in self._lines))),
                float(max((line.imag.max() for line in self._lines))),
            )

    def width(self) -> float:
        """Returns the total width of the geometries.

        Returns:
            the width (xmax - xmin) or 0.0 if the LineCollection is empty
        """

        if self._lines:
            return float(
                max((line.real.max() for line in self._lines))
                - min((line.real.min() for line in self._lines))
            )
        else:
            return 0.0

    def height(self) -> float:
        """Returns the total height of the geometries.

        Returns:
            the width (ymax - ymin) or 0.0 if the LineCollection is empty
        """
        if self._lines:
            return float(
                max((line.imag.max() for line in self._lines))
                - min((line.imag.min() for line in self._lines))
            )
        else:
            return 0.0

    def length(self) -> float:
        """Return the total length of the paths.

        Returns:
            the total length
        """
        return sum(np.sum(np.abs(np.diff(line))) for line in self._lines)

    def pen_up_trajectories(self) -> "LineCollection":
        """Returns a LineCollection containing the pen-up trajectories."""
        return LineCollection(
            ([self._lines[i][-1], self._lines[i + 1][0]] for i in range(len(self._lines) - 1)),
        )

    def pen_up_length(self) -> Tuple[float, float, float]:
        """Returns statistics on the pen-up distance corresponding to the path.

        The total, mean, and median distance are returned. The pen-up distance is the distance
        between a path's end and the next path's beginning.

        Returns:
            tuple (total, mean, median) for the pen-up distances
        """
        if len(self.lines) < 2:
            return 0.0, 0.0, 0.0

        ends = np.array([line[-1] for line in self.lines[:-1]])
        starts = np.array([line[0] for line in self.lines[1:]])
        dists = np.abs(starts - ends)
        # noinspection PyTypeChecker
        return float(np.sum(dists)), float(np.mean(dists)), float(np.median(dists))

    def segment_count(self) -> int:
        """Returns the total number of segment across all lines.

        Returns:
            the total number of segments in the geometries
        """
        return sum(max(0, len(line) - 1) for line in self._lines)


class Document:
    """This class is the core data model of vpype and represent the data that is passed from
    one command to the other. At its core, a Document is a collection of layers identified
    by non-zero positive integers and each represented by a :py:class:`LineCollection`.

    In addition, the Document class maintains a :py:attr:`page_size` attribute which describe
    the physical size of the document. This attribute is not strictly linked to the actual
    Document's content, but can be set based on it.
    """

    def __init__(
        self,
        line_collection: LineCollection = None,
        page_size: Optional[Tuple[float, float]] = None,
    ):
        """Create a Document, optionally providing a :py:class:`LayerCollection` for layer 1.

        Args:
            line_collection: if provided, used as layer 1
        """
        self._layers: Dict[int, LineCollection] = {}
        self._page_size: Optional[Tuple[float, float]] = page_size

        if line_collection:
            self.add(line_collection, 1)

    def empty_copy(self) -> "Document":
        """Create an empty copy of this document with the same page size."""
        return Document(page_size=self.page_size)

    @property
    def layers(self) -> Dict[int, LineCollection]:
        """Returns a reference to the layer dictionary.
        Returns:
            the internal layer dictionary
        """
        return self._layers

    @property
    def page_size(self) -> Optional[Tuple[float, float]]:
        """Returns the page size or None if it hasn't been set."""
        return self._page_size

    @page_size.setter
    def page_size(self, page_size=Optional[Tuple[float, float]]) -> None:
        """Sets the page size to a new value."""
        self._page_size = page_size

    def extend_page_size(self, page_size: Optional[Tuple[float, float]]) -> None:
        """Adjust the  page sized according to the following logic:

            - if ``page_size`` is None, the the page size is unchanged
            - if ``self.page_size`` is None, it is set to ``page_size``
            - if both page sizes are not None, the page size is set to the largest value in
              both direction

        Args:
            page_size: page dimension to use to update ``self.page_size``
        """
        if page_size:
            if self.page_size:
                self.page_size = (
                    max(self.page_size[0], page_size[0]),
                    max(self.page_size[1], page_size[1]),
                )
            else:
                self.page_size = page_size

    def ids(self) -> Iterable[int]:
        """Returns the list of layer IDs"""
        return self._layers.keys()

    def layers_from_ids(self, layer_ids: Iterable[int]) -> Iterator[LineCollection]:
        """Returns an iterator that yield layers corresponding to the provided IDs, provided
        they exist. This is typically used to process a command's layer list option, in
        combination with :py:func:`multiple_to_layer_ids`.

        Non-existent layer IDs in the input are ignored.

        Args:
            layer_ids: iterable of layer IDs

        Returns:
            layer iterator
        """
        return (self._layers[lid] for lid in layer_ids if lid in self._layers)

    def exists(self, layer_id: int) -> bool:
        """Test existence of a layer.

        Note that existence of a layer does not necessarily imply that it isn't empty.

        Args:
            layer_id: layer ID to test

        Returns:
            True if the layer ID exists
        """
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
        """Returns the lowest unused layer id.

        Returns:
            the unused layer ID
        """
        vid = 1
        while vid in self._layers:
            vid += 1
        return vid

    def add(self, lc: LineCollection, layer_id: Union[None, int] = None) -> None:
        """Add a the content of a :py:class:`LineCollection` to a given layer.

        If the given layer is None, the input LineCollection is used to create a new layer
        using the lowest available layer ID.
        """
        if layer_id is None:
            layer_id = 1
            while layer_id in self._layers:
                layer_id += 1

        if layer_id in self._layers:
            self._layers[layer_id].extend(lc)
        else:
            self._layers[layer_id] = lc

    def extend(self, doc: "Document") -> None:
        """Extend a Document with the content of another Document.

        The layer structure of the source Document is maintained and geometries are either
        appended to the destination's corresponding layer or new layers are created, depending
        on if the layer existed or not in the destination Document.

        The :py:attr:`page_size` attribute is adjusted using :meth:`extend_page_size`.

        Args:
            doc: source Document
        """

        self.extend_page_size(doc.page_size)

        for layer_id, layer in doc.layers.items():
            self.add(layer, layer_id)

    def is_empty(self) -> bool:
        """Returns True if all layers are empty.

        Returns:
            True if all layers are empty"""
        for layer in self.layers.values():
            if not layer.is_empty():
                return False
        return True

    def pop(self, layer_id: int) -> LineCollection:
        """Removes a layer from the Document.

        Args:
            layer_id: ID of the layer to be removed

        Returns:
            the :py:class:`LineCollection` corresponding to the removed layer
        """
        return self._layers.pop(layer_id)

    def count(self) -> int:
        """Returns the total number of layers.

        Returns:
            total number of layer"""
        return len(self._layers.keys())

    def translate(self, dx: float, dy: float) -> None:
        """Translates all line by a given offset.

        Args:
            dx: offset along X axis
            dy: offset along Y axis
        """
        for layer in self._layers.values():
            layer.translate(dx, dy)

    def scale(self, sx: float, sy: Optional[float] = None) -> None:
        """Scale the geometry.

        The scaling is performed about the coordinates origin (0, 0). To scale around a
        specific location, appropriate translations must be performed before and after the
        scaling (see :func:`LineCollection.scale`).

        Args:
            sx: scale factor along x
            sy: scale factor along y (if None, then sx is used)
        """
        for layer in self._layers.values():
            layer.scale(sx, sy)

    def rotate(self, angle: float) -> None:
        """Rotate the Document's content..

        The rotation is performed about the coordinates origin (0, 0). To rotate around a
        specific location, appropriate translations must be performed before and after the
        scaling (see :func:`LineCollection.rotate`).

        Args:
            angle: rotation angle (radian)
        """
        for layer in self._layers.values():
            layer.rotate(angle)

    def bounds(
        self, layer_ids: Union[None, Iterable[int]] = None
    ) -> Optional[Tuple[float, float, float, float]]:
        """Compute bounds of the document.

        If layer_ids is provided, bounds are computed only for the corresponding IDs.

        Note: the bounds are computed based on the actual geometries contained in this
        :class:`Document` instance. The document's page size, if any, is not taken into account
        by this calculation.

        Args:
            layer_ids: layers to consider in the bound calculation

        Returns:
            boundaries of the geometries
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

    def crop(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Crop all layers to a rectangular area.

        Args:
            x1, y1: first corner of the crop area
            x2, y2: second corner of the crop area
        """
        for layer in self._layers.values():
            layer.crop(x1, y1, x2, y2)

    def fit_page_size_to_content(self) -> None:
        """Set :py:attr:`page_size` to the current geometries' width and height and move
        the geometries so that their bounds align to (0, 0).
        """
        bounds = self.bounds()
        if not bounds:
            return

        self.translate(-bounds[0], -bounds[1])
        self.page_size = (bounds[2] - bounds[0], bounds[3] - bounds[1])

    def length(self) -> float:
        """Return the total length of the paths.

        Returns:
            the total length
        """
        return sum(layer.length() for layer in self._layers.values())

    def pen_up_length(self) -> float:
        """Returns the total pen-up distance corresponding to the path.

        This function does not account for the pen-up distance between layers.

        Returns:
            total pen-up distances
        """
        return sum(layer.pen_up_length()[0] for layer in self._layers.values())

    def segment_count(self) -> int:
        """Returns the total number of segment across all lines.

        Returns:
            the total number of segments in the geometries
        """
        return sum(layer.segment_count() for layer in self._layers.values())


class VectorData(Document):
    """Deprecated, use Document."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.warning("!!! `vpype.VectorData` is deprecated, use `vpype.Document` instead.")
