from __future__ import annotations

import math
from functools import lru_cache
from typing import Iterable, Literal

import numpy as np
from attr import frozen
from matplotlib import patches
from matplotlib import pyplot as plt

from vpype.path.exceptions import SegmentCreationError
from vpype.path.segment import Segment


@frozen
class ArcSegment(Segment):
    """A circular arc segment.

    The arc is defined by 3 points. If first and last are the same, the arc is a full circle
    and the mid-point must be opposite.
    """

    first: complex
    mid: complex
    last: complex

    def __attrs_post_init__(self):
        if self.first == self.mid or self.mid == self.last:
            raise SegmentCreationError("arc endpoints must be distinct")

        if self.first != self.last:
            c1 = self.mid - self.first
            c2 = self.last - self.mid
            if c1.real * c2.imag == c1.imag * c2.real:
                raise SegmentCreationError("arc endpoints must not be collinear")

    @classmethod
    def from_center(cls, center: complex, radius: float, start_angle: float, end_angle: float):
        """Create an arc from a center point, radius, start angle and end angle.

        The arc runs from ``start_angle`` in a direction defined by the sign of ``end_angle``.

        Args:
            center: center of the arc
            radius: radius of the arc
            start_angle: start angle of the arc in radians
            end_angle: end angle of the arc in radians

        Returns:
            The arc segment
        """
        return cls(
            first=center + radius * math.e ** (1j * start_angle),
            mid=center + radius * math.e ** (1j * 0.5 * (end_angle - start_angle)),
            last=center + radius * math.e ** (1j * end_angle),
        )

    @property
    def begin(self) -> complex:
        return self.first

    @property
    def end(self) -> complex:
        return self.last

    @property
    def center(self) -> complex:
        # from https://stackoverflow.com/a/28910804/229511

        if self.first == self.last:
            return 0.5 * (self.first + self.mid)

        w = self.last - self.first
        w /= self.mid - self.first
        return self.first - (self.first - self.mid) * (w - abs(w) ** 2) / 2j / w.imag

    @property
    def radius(self) -> float:
        return abs(self.center - self.first)

    @property
    def angles(self) -> tuple[float, float]:
        """Compute the angles of the arc.

        The arc runs from the first angle to the second, in that direction. Angles are in
        radians. The first angle is always in the [0, 2pi) range. The second angle may exceed
        this range depending on the arc direction.

        Returns:
            (start, end) angles in radians
        """

        def norm_0_2pi(x):
            while x < 0:
                x += math.tau
            while x >= math.tau:
                x -= math.tau
            return x

        # noinspection PyTypeChecker
        first_angle = norm_0_2pi(np.angle(self.first - self.center))
        # noinspection PyTypeChecker
        mid_angle = norm_0_2pi(np.angle(self.mid - self.center))
        # noinspection PyTypeChecker
        last_angle = norm_0_2pi(np.angle(self.last - self.center))

        if self.first == self.last:
            return first_angle, first_angle + 2 * math.pi

        if last_angle > first_angle:
            if mid_angle < first_angle or mid_angle > last_angle:
                last_angle -= math.tau
        else:
            if mid_angle > first_angle or mid_angle < last_angle:
                last_angle += math.tau

        return first_angle, last_angle

    @property
    def length(self) -> float:
        a, b = self.angles
        return abs(b - a) * self.radius

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        pass

    def reverse(self) -> ArcSegment:
        return ArcSegment(self.last, self.mid, self.first)

    def translate(self, offset: complex) -> ArcSegment:
        return ArcSegment(self.first + offset, self.mid + offset, self.last + offset)

    def rotate_complex(self, angle: complex) -> ArcSegment:
        return ArcSegment(self.first * angle, self.mid * angle, self.last * angle)

    def scale(self, factor: complex) -> ArcSegment:
        return ArcSegment(
            self.first.real * factor.real + 1j * (self.first.imag * factor.imag),
            self.mid.real * factor.real + 1j * (self.mid.imag * factor.imag),
            self.last.real * factor.real + 1j * (self.last.imag * factor.imag),
        )

    def flip_axes(self) -> ArcSegment:
        return ArcSegment(
            complex(self.first.imag, self.first.real),
            complex(self.mid.imag, self.mid.real),
            complex(self.last.imag, self.last.real),
        )

    def intersect_x(self, x: float) -> Iterable[complex]:
        """Returns angles at which the arc intersects the x axis."""
        c = self.center
        r = self.radius
        d = x - c.real
        start, stop = self.angles

        def _angle_in(a):
            # works for angle in (0, 2pi)
            return (start <= a <= stop) or (start >= a >= stop)

        match d:
            case d if d == -r:
                if _angle_in(math.pi):
                    yield math.pi

            case d if d == r:
                if _angle_in(0.0):  ## STILL WRONG!
                    yield 0.0

            case d if abs(d) < r:
                # circle is intersecting the plane
                angle = abs(math.acos(d / r))
                if _angle_in(angle):
                    yield angle
                if _angle_in(math.tau - angle):
                    yield math.tau - angle

    def divide(self, angle: float) -> tuple[ArcSegment, ArcSegment]:
        """Divide the arc at the given angle.

        This function doesn't check that the angle is within the arc's range.

        Args:
            angle: angle at which to divide the arc in radians

        Returns:
            (left, right) arc segments
        """
        c = self.center
        r = self.radius
        start, stop = self.angles

        mid_point = c + r * math.e ** (1j * angle)

        return (
            ArcSegment(
                self.first,
                c + r * math.e ** (1j * 0.5 * (angle - start)),
                mid_point,
            ),
            ArcSegment(
                mid_point,
                c + r * math.e ** (1j * 0.5 * (stop - angle)),
                self.last,
            ),
        )

    def crop_x(self, x: float, keep_smaller: bool) -> Iterable[ArcSegment]:
        """Crop the at a given x coordinate."""
        t_list = list(self.intersect_x(x))

        c = self.center
        start, stop = self.angles

        if start < stop:
            start_ord, stop_ord = start, stop
        else:
            start_ord, stop_ord = stop, start

        match t_list:
            case []:
                if (self.first.real < x) == keep_smaller:
                    yield self

            case [math.pi]:
                if not (c.real < x) == keep_smaller:
                    yield self

            case [0.0]:
                if (c.real < x) == keep_smaller:
                    yield self

            case [a]:
                sub1, sub2 = self.divide(a)
                if (self.first.real < x) == keep_smaller:
                    yield sub1
                else:
                    yield sub2

            case [start_ord, a]:
                pass

            case [a, stop_ord]:
                pass

            case [a1, a2]:
                pass

    def crop_half_plane(
        self, loc: float, axis: Literal["x", "y"], keep_smaller: bool
    ) -> Iterable[ArcSegment]:
        # FIXME: todo
        c = self.center
        r = self.radius

        c_axis = c.real if axis == "x" else c.imag
        if abs(c_axis - loc) >= r:
            # circle is entirely on one side of the plane
            if (c_axis < loc) == keep_smaller:
                yield self
            else:
                return
        else:
            # circle is intersecting the plane
            pass

    def plot(self, ax: plt.Axes):
        start, stop = self.angles

        # matplotlib want CCW angles (and we have inverted y)
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
            self.first.real,
            self.first.imag,
            "o",
            color="darkgreen",
            ms=7,
            markerfacecolor="none",
        )
        ax.plot(self.mid.real, self.mid.imag, ".", color="darkgreen")
        ax.plot(self.last.real, self.last.imag, "D", color="darkgreen", ms=4)
        ax.plot(self.center.real, self.center.imag, "+", color="darkgreen")
