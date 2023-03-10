from __future__ import annotations

from typing import Iterable, Literal

from attr import frozen
from matplotlib import pyplot as plt

from vpype.path.segment import Segment


@frozen
class Point(Segment):
    coord: complex

    @property
    def begin(self) -> complex:
        return self.coord

    @property
    def end(self) -> complex:
        return self.coord

    @property
    def length(self) -> float:
        return 0.0

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return self.coord.real, self.coord.imag, self.coord.real, self.coord.imag

    def reverse(self) -> Point:
        return self

    def flip_axes(self) -> Point:
        return Point(complex(self.coord.imag, self.coord.real))

    def crop_x(self, x: float, keep_smaller: bool) -> Iterable[Point]:
        if (self.coord.real < x) == keep_smaller or self.coord.real == x:
            yield self

    def translate(self, offset: complex) -> Point:
        return Point(self.coord + offset)

    def rotate_complex(self: Point, angle: complex) -> Point:
        return Point(self.coord * angle)

    def scale(self: Point, factor: complex) -> Point:
        return Point(complex(self.coord.real * factor.real, self.coord.imag * factor.imag))

    def plot(self, ax: plt.Axes):
        ax.plot(self.coord.real, self.coord.imag, "ro")
