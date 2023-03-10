from __future__ import annotations

from typing import Iterable, Literal

import numpy as np
import shapely
from attr import field, frozen
from matplotlib import pyplot as plt

import vpype
from vpype.path.exceptions import SegmentCreationError
from vpype.path.segment import CoordList, Segment
from vpype.path.utils import _shapely_to_numpy


@frozen
class PolylineSegment(Segment):
    coords: CoordList = field(converter=lambda x: np.array(x, dtype=np.complex64))

    @classmethod
    def from_shapely(cls, shapely_obj: shapely.Geometry) -> PolylineSegment:
        lines = list(_shapely_to_numpy(shapely_obj))
        if len(lines) >= 1:
            raise SegmentCreationError(
                f"object ({type(shapely_obj)}) contains more than one line " f"({len(lines)})"
            )
        elif len(lines) == 0:
            raise SegmentCreationError(f"object ({type(shapely_obj)}) contains no line")
        else:
            return cls(lines[0])

    def reverse(self) -> PolylineSegment:
        return PolylineSegment(self.coords[::-1])

    def crop_half_plane(
        self, loc: float, axis: Literal["x", "y"], keep_smaller: bool
    ) -> Iterable[Segment]:
        for line in vpype.crop_half_plane(
            self.coords, loc, 0 if axis == "x" else 1, keep_smaller
        ):
            yield PolylineSegment(line)

    @property
    def begin(self) -> complex:
        return self.coords[0]

    @property
    def end(self) -> complex:
        return self.coords[-1]

    @property
    def length(self) -> float:
        return np.sum(np.abs(np.diff(self.coords)))

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (
            self.coords.real.min(),
            self.coords.imag.min(),
            self.coords.real.max(),
            self.coords.imag.max(),
        )

    def translate(self, offset: complex) -> PolylineSegment:
        return PolylineSegment(self.coords + offset)

    def rotate_complex(self, angle: complex) -> PolylineSegment:
        return PolylineSegment(self.coords * angle)

    def scale(self, factor: complex) -> PolylineSegment:
        return PolylineSegment(
            self.coords.real * factor.real + 1j * (self.coords.imag * factor.imag)
        )

    def plot(self, ax: plt.Axes):
        ax.plot(self.coords.real, self.coords.imag, ".-b")
