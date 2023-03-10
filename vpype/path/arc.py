from __future__ import annotations

import math
from typing import Iterable, overload

import numpy as np
import numpy.typing as npt
from attr import evolve, field, frozen, validators
from matplotlib import patches
from matplotlib import pyplot as plt

from vpype.path.exceptions import SegmentCreationError
from vpype.path.segment import CoordList, Segment


def _normalize_angles(angles: Iterable[float]) -> tuple[float, float]:
    """Normalize angles to the definition from :class:`ArcSegment`."""

    try:
        start, stop = angles
    except ValueError:
        raise SegmentCreationError("two values must be provided for angles")

    if abs(stop - start) > math.tau:
        raise SegmentCreationError("arc sweep must be less or equal than 2π")

    start_norm = start % math.tau
    return start_norm, start_norm + stop - start


@frozen
class ArcSegment(Segment):
    """A circular arc segment.

    The arc is defined by a center, a radius, and a tuple of angles. The first angle is in the
    range (0, 2π]. The second angle defines both the direction and the sweep of the arc, and
    my thus exceed this range in either direction. A circle is defined by a2 = a1 ± 2π. The
    circle direction is thus defined by the sign of a2 - a1.

    Angles are normalized to this definition in the constructor.
    """

    center: complex
    radius: float = field(validator=validators.ge(0))
    angles: tuple[float, float] = field(converter=_normalize_angles)

    @classmethod
    def from_sweep(
        cls, center: complex, radius: float, start: float, sweep: float
    ) -> ArcSegment:
        """Create an arc from a center, a radius, and a start angle and a sweep angle.

        The sweep may be in the (-2π, 2π) range. Positive sweep defines a clockwise arc.

        Args:
            center: center of the arc
            radius: radius of the arc
            start: start angle of the arc
            sweep: sweep angle of the arc

        Returns:
            the arc segment
        """
        return cls(center, radius, (start, start + sweep))

    @overload
    def point(self, angle: float) -> complex:
        ...

    @overload
    def point(self, angle: npt.NDArray[np.float64]) -> npt.NDArray[np.complex128]:
        ...

    def point(self, angle):
        return self.center + self.radius * np.exp(1j * angle)

    @property
    def begin(self) -> complex:
        return self.point(self.angles[0])

    @property
    def end(self) -> complex:
        return self.point(self.angles[1])

    @property
    def sweep(self) -> float:
        """Returns the (signed) angular sweep of the arc.

        The sweep is positive if the arc is clockwise, negative otherwise. This is due to
        the y axis down convention.
        """
        return self.angles[1] - self.angles[0]

    @property
    def ccw(self) -> bool:
        """Returns True if the arc is counter-clockwise."""
        return self.sweep < 0

    @property
    def length(self) -> float:
        a, b = self.angles
        return abs(b - a) * self.radius

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        # TODO: this is missing!!
        pass

    def reverse(self) -> ArcSegment:
        return evolve(self, angles=(self.angles[1], self.angles[0]))

    def translate(self, offset: complex) -> ArcSegment:
        return evolve(self, center=self.center + offset)

    def rotate_complex(self, angle: complex) -> ArcSegment:
        # noinspection PyTypeChecker
        angle_rad = np.angle(angle)
        return evolve(
            self,
            center=self.center * angle,
            angles=(self.angles[0] + angle_rad, self.angles[1] + angle_rad),
        )

    def scale(self, factor: complex) -> ArcSegment:
        match factor.real, factor.imag:
            # uniform scaling
            case [k1, k2] if k1 == k2:
                return ArcSegment.from_sweep(
                    self.center * k1,
                    self.radius * abs(k1),
                    self.angles[0] + math.pi if k1 < 0 else self.angles[0],
                    self.sweep,
                )

            # vertical mirror
            case [k1, k2] if k1 == -k2 and k1 > 0:
                return ArcSegment.from_sweep(
                    complex(self.center.real * k1, self.center.imag * k2),
                    self.radius * k1,
                    -self.angles[0],
                    -self.sweep,
                )

            # horizontal mirror
            case [k1, k2] if k1 == -k2 and k1 < 0:
                return ArcSegment.from_sweep(
                    complex(self.center.real * k1, self.center.imag * k2),
                    self.radius * k2,
                    math.pi - self.angles[0],
                    -self.sweep,
                )

            # non-uniform scaling
            case [k1, k2]:
                # TODO – convert to Path with Bezier
                raise ValueError("non-uniform scaling is not yet supported")

    def flip_axes(self) -> ArcSegment:
        new_start = math.pi / 2 - self.angles[0]
        return ArcSegment(
            complex(self.center.imag, self.center.real),
            self.radius,
            (
                new_start,
                new_start - self.sweep,
            ),
        )

    def _angle_inside(self, angle: float) -> float | None:
        """Check if the given angle is within the arc's angle range.

        Returns:
            if the angle is with range, returns the angle such that it is contained in the
            range defined by ``self.angles``. Otherwise, returns None.
        """
        a, b = self.angles
        angle %= math.tau
        if self.ccw:
            if angle > a:
                angle -= math.tau
        elif angle < a:
            angle += math.tau

        return angle if ((a <= angle <= b) or (b <= angle <= a)) else None

    def intersect_x(self, x: float) -> Iterable[complex]:
        """Returns angles at which the arc intersects the x axis.

        Returned angles are inside the range defined by ``self.angles``. This means the
        potential range is [-4π, 4π].
        """
        c = self.center
        r = self.radius
        d = x - c.real

        # noinspection PyShadowingNames
        def _yield_if_inside(angle: float):
            if (angle := self._angle_inside(angle)) is not None:
                yield angle

        match d:
            case d if d == -r:
                yield from _yield_if_inside(math.pi)

            case d if d == r:
                yield from _yield_if_inside(0)

            case d if abs(d) < r:
                # circle is intersecting the plane
                angle = abs(math.acos(d / r))
                yield from _yield_if_inside(angle)
                yield from _yield_if_inside(-angle)

    def divide(self, angle: float) -> tuple[ArcSegment, ArcSegment]:
        """Divide the arc at the given angle.

        This function doesn't check that the angle is within the arc's range.

        Args:
            angle: angle at which to divide the arc in radians

        Returns:
            tuple of arc segments
        """

        start, stop = self.angles
        angle = self._angle_inside(angle)

        if angle is None:
            raise ValueError("angle is not within the arc's range")

        return evolve(self, angles=(start, angle)), evolve(self, angles=(angle, stop))

    def crop_x(self, x: float, keep_smaller: bool) -> Iterable[ArcSegment]:
        """Crop the at a given x coordinate."""
        t_list = list(self.intersect_x(x))

        c = self.center
        start, stop = self.angles

        match t_list:
            case []:
                if (c.real < x) == keep_smaller:
                    yield self

            case [a] if (a % math.tau) == 0:
                if (c.real < x) == keep_smaller:
                    yield self

            case [a] if (a % math.tau) == math.pi:
                if (c.real > x) == (not keep_smaller):
                    yield self

            case [a]:
                sub1, sub2 = self.divide(a)
                if (self.begin.real < x) == keep_smaller:
                    yield sub1
                else:
                    yield sub2

            case [a1, a2] if a1 == start:
                sub1, sub2 = self.divide(a2)
                if (self.begin.real < x) == keep_smaller:
                    yield sub1
                else:
                    yield sub2

            case [a1, a2] if a2 == stop:
                sub1, sub2 = self.divide(a1)
                if (self.begin.real < x) == keep_smaller:
                    yield sub2
                else:
                    yield sub1

            case [a1, a2]:
                if (a1 > a2) == (start < stop):
                    a1, a2 = a2, a1
                sub1, sub2 = self.divide(a1)
                sub2a, sub2b = sub2.divide(a2)
                if (self.begin.real < x) == keep_smaller:
                    yield sub1
                    yield sub2b
                else:
                    yield sub2a

    def to_polyline(self, tolerance: float) -> CoordList:
        if tolerance > self.radius:
            tolerance = self.radius
        angle_step = math.acos(1 - tolerance / self.radius)
        angles = np.linspace(
            self.angles[0], self.angles[1], math.ceil(abs(self.sweep) / angle_step)
        )
        return self.point(angles)

    def plot(self, ax: plt.Axes):

        # matplotlib want CCW angles (and we have inverted y)
        start, stop = self.angles
        if start > stop:
            start, stop = stop, start
        arc = patches.Arc(
            (self.center.real, self.center.imag),
            self.radius * 2,
            self.radius * 2,
            theta1=math.degrees(start),
            theta2=math.degrees(stop),
            edgecolor="darkgreen",
            facecolor="none",
        )
        ax.add_patch(arc)
        ax.plot(
            self.begin.real,
            self.begin.imag,
            "o",
            color="darkgreen",
            ms=7,
            markerfacecolor="none",
        )
        ax.plot(self.end.real, self.end.imag, "D", color="darkgreen", ms=4)
        ax.plot(self.center.real, self.center.imag, "+", color="darkgreen")


# if __name__ == "__main__":
#     arc = ArcSegment(1 + 2j, 0.5, [0.1, math.tau - 0.3])
#
#     fig = plt.figure(tight_layout=True)
#     ax = fig.add_subplot(1, 1, 1)
#     ax.invert_yaxis()
#     ax.set_aspect("equal")
#     arc.plot(ax)
#     arc.scale(-2 - 2j).plot(ax)
#     ax.grid(True)
#     fig.show()
