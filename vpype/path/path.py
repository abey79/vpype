"""
Design decisions:
- Segments and path are immutable
    - caching of computed attributes (cached_property)
    - sets
    - easier to compose transformations
- Segment offers a "low-level" API with emphasis on performance
    - translation, rotation, and scaling expressed in complex
- Path offers more convenience, higher-lever API
- Path has opinionated invariants (continuous, non-empty, if contains a Point, then only one
  and nothing else)

- Compound paths are needed for fill operations.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import shapely
from attr import field, frozen
from matplotlib import pyplot as plt

from vpype.path.exceptions import PathCreationError
from vpype.path.point import Point
from vpype.path.polyline import PolylineSegment
from vpype.path.segment import Segment
from vpype.path.utils import _shapely_to_numpy


@frozen
class Path:
    """Represents a continuous stroke make of one or more segments.

    Since a path is continuous, it may consist of either:
    - a single :class:Point instance
    - one or more segments of types other than :class:Point
    - empty path are not allowed

    TODO:
    - NEED COMPOUND PATH
    - CLOSED FLAG?
    - from_ constructor
    - metadata
    - reloop
    """

    segments: list[Segment] = field(
        default=list, converter=lambda x: list(x)
    )  # using list directly breaks mypy

    @segments.validator
    def _check_segments(self, attribute, value):
        if len(value) == 0:
            raise PathCreationError("empty path not allowed")
        if len(value) > 1 and any(isinstance(seg, Point) for seg in value):
            raise PathCreationError("path may not contain a point and other segments")

    @classmethod
    def from_shapely(cls, shapely_obj: shapely.Geometry) -> Path:
        # TODO: this should enforce the invariants!
        # TODO: this probably returns many paths?
        return cls([PolylineSegment(line) for line in _shapely_to_numpy(shapely_obj)])

    # TODO: add lots of convenience "from" methods (coord list, complex list, shapely, path
    #  list with joining, etc. (CAUTION: enforce invariants!)

    @property
    def continuous(self) -> bool:
        return all(s1.end == s2.begin for s1, s2 in zip(self.segments[:-1], self.segments[1:]))

    @property
    def closed(self) -> bool:
        return self.segments[0].begin == self.segments[-1].end

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        bounds = np.array([seg.bbox for seg in self.segments])

        return bounds[:, 0].min(), bounds[:, 1].min(), bounds[:, 2].max(), bounds[:, 3].max()

    def reverse(self) -> Path:
        return Path([s.reverse() for s in self.segments[::-1]])

    def split(self) -> Iterable[Path]:
        """Split the path into continuous subpaths."""
        sub_path: list[Segment] = []
        for s in self.segments:
            if sub_path and s.begin != sub_path[-1].end:
                yield Path(sub_path)
                sub_path = []
            sub_path.append(s)
        if sub_path:
            yield Path(sub_path)

    def translate(self, offset: complex) -> Path:
        return Path(s.translate(offset) for s in self.segments)

    def show(self):
        fig = plt.figure(tight_layout=True)
        ax = fig.add_subplot(1, 1, 1)
        ax.invert_yaxis()
        ax.set_aspect("equal")
        for seg in self.segments:
            seg.plot(ax)
        ax.grid(True)
        plt.show()


if __name__ == "__main__":

    def main():
        seg = PolylineSegment([1, 1j, 3 + 3j])
        seg.length
        path = Path([seg])
        assert not seg.closed
        assert path.continuous

    main()
