from __future__ import annotations

import math
from typing import Iterable, Literal, overload

import numpy as np
import numpy.typing as npt
from attr import frozen
from matplotlib import patches
from matplotlib import path as mpath
from matplotlib import pyplot as plt

from vpype.path.segment import Segment
from vpype.path.utils import cmax, cmin, lerp


@frozen
class QuadraticBezierSegment(Segment):
    first: complex
    control: complex
    last: complex

    @property
    def begin(self) -> complex:
        return self.first

    @property
    def end(self) -> complex:
        return self.last

    @property
    def length(self) -> float:
        pass

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """Return the bounding box of the segment.

        Based on https://iquilezles.org/articles/bezierbbox/
        """

        def _bbox_1d(a: float, b: float, c: float) -> list[float]:
            mi = min(a, c)
            ma = max(a, c)
            if b < mi or b > ma:
                return [(a - b) / (a - 2 * b + c)]
            else:
                return []

        mi = cmin(self.first, self.last)
        ma = cmax(self.first, self.last)

        t_list = _bbox_1d(self.first.real, self.control.real, self.last.real) + _bbox_1d(
            self.first.imag, self.control.imag, self.last.imag
        )

        for t in t_list:
            if 0 <= t <= 1:
                p = self.point(t)
                mi = cmin(mi, p)
                ma = cmax(ma, p)

        return mi.real, mi.imag, ma.real, ma.imag

    def reverse(self) -> QuadraticBezierSegment:
        return QuadraticBezierSegment(self.last, self.control, self.first)

    @overload
    def point(self, t: float) -> complex:
        ...

    @overload
    def point(self, t: npt.NDArray[np.float64]) -> npt.NDArray[np.complex128]:
        ...

    def point(self, t):
        return (1 - t) ** 2 * self.first + 2 * (1 - t) * t * self.control + t**2 * self.last

    def divide(self, t: float) -> tuple[QuadraticBezierSegment, QuadraticBezierSegment]:
        p1 = lerp(self.first, self.control, t)
        p2 = lerp(self.control, self.last, t)
        p3 = lerp(p1, p2, t)

        return (
            QuadraticBezierSegment(self.first, p1, p3),
            QuadraticBezierSegment(p3, p2, self.last),
        )

    def flip_axes(self) -> QuadraticBezierSegment:
        return QuadraticBezierSegment(
            complex(self.first.imag, self.first.real),
            complex(self.control.imag, self.control.real),
            complex(self.last.imag, self.last.real),
        )

    def intersect_x(self, x: float) -> Iterable[float]:
        """Yields a list t values corresponding to intersection points

        If the whole curve intersects, returns. If multiple intersections
        are found, the t values are sorted in ascending order.
        """

        a, b, c = self.first.real, self.control.real, self.last.real

        if a == b == c:
            if a == x:
                yield float("nan")
        elif a + c == 2 * b:
            # curve is symmetric, a single root is possible
            t = (a - x) / 2 / (a - b)
            yield t
        else:
            # two intersections are possible
            inside = -a * c + a * x + b**2 - 2 * b * x + c * x
            if inside >= 0:
                sq = math.sqrt(inside)
                denom = 1 / (-a + 2 * b - c)
                t1 = (sq - a + b) * denom
                t2 = (-sq - a + b) * denom
                if t1 > t2:
                    t1, t2 = t2, t1
                yield t1
                if t2 != t1:
                    yield t2

    def intersect_y(self, y: float) -> Iterable[float]:
        yield from self.flip_axes().intersect_x(y)

    def crop_x(self, x: float, keep_smaller: bool) -> Iterable[QuadraticBezierSegment]:
        t_list = list(self.intersect_x(x))

        first_in = (self.first.real < x) == keep_smaller
        last_in = (self.last.real < x) == keep_smaller

        match t_list:
            case []:
                if first_in or self.first.real == x:
                    yield self

            # along crop line
            case [t] if math.isnan(t):
                yield self

            case [t]:
                # t out or on bounds
                if (t <= 0 and last_in) or (t >= 1 and first_in):
                    yield self
                # t strictly in bounds
                elif 0 < t < 1:
                    if first_in and last_in:
                        # tangent case
                        yield self
                    else:
                        sub1, sub2 = self.divide(t)
                        if first_in:
                            yield sub1
                        if last_in:
                            yield sub2

            # both are strictly out of range
            case [t1, t2] if not (0 <= t1 <= 1) and not (0 <= t2 <= 1):
                if first_in:
                    yield self

            # (0, 1)
            case [t1, t2] if t1 <= 0 and t2 >= 1:
                if (self.control.real < x) == keep_smaller:
                    yield self

            # (0, t)
            case [t1, t2] if t1 <= 0:
                sub1, sub2 = self.divide(t2)
                yield sub1 if first_in else sub2

            # (t, 1)
            case [t1, t2] if t2 >= 1:
                sub1, sub2 = self.divide(t1)
                yield sub2 if last_in else sub1

            # (t1, t2)
            case [t1, t2]:
                sub1, sub2 = self.divide(t1)
                sub2a, sub2b = sub2.divide((t2 - t1) / (1 - t1))
                if first_in:
                    yield sub1
                    yield sub2b
                else:
                    yield sub2a

    # def crop_half_plane(
    #     self, loc: float, axis: Literal["x", "y"], keep_smaller: bool
    # ) -> Iterable[QuadraticBezierSegment]:
    #     """Crop the segment with a half-plane.
    #
    #     Edge cases are handled such as "empty" bezier are not returned, unless this is already
    #     an empty bezier.
    #
    #     Derivation based on https://tinyurl.com/3bywmz9e
    #     """
    #     if axis == "x":
    #         a, b, c = self.first.real, self.control.real, self.last.real
    #     else:
    #         a, b, c = self.first.imag, self.control.imag, self.last.imag
    #
    #     keep_a = (a < loc) == keep_smaller
    #     keep_c = (c < loc) == keep_smaller
    #
    #     # noinspection PyShadowingNames
    #     def _crop_at_single_t(t: float) -> Iterable[QuadraticBezierSegment]:
    #         # careful with edge cases as we don't want to keep a
    #         # (a, a, a) or (c, c, c) degenerate curve
    #         if (t <= 0 and keep_c) or (t >= 1 and keep_a):
    #             yield self
    #         elif 0 < t < 1:
    #             if keep_a and keep_c:
    #                 # tangent case
    #                 yield self
    #             else:
    #                 sub1, sub2 = self.divide(t)
    #                 if keep_a:
    #                     yield sub1
    #                 if keep_c:
    #                     yield sub2
    #
    #     # find the roots of the quadratic equation
    #     if a == b == c:
    #         if keep_a or a == loc:
    #             yield self
    #     elif a + c == 2 * b:
    #         # curve is symmetric, a single root is possible
    #         t = (a - loc) / 2 / (a - b)
    #         yield from _crop_at_single_t(t)
    #     else:
    #         # two intersections are possible
    #         inside = -a * c + a * loc + b**2 - 2 * b * loc + c * loc
    #         if inside < 0:
    #             # no intersection
    #             if keep_a:
    #                 yield self
    #         else:
    #             sq = math.sqrt(inside)
    #             t1 = (sq - a + b) / (-a + 2 * b - c)
    #             t2 = (-sq - a + b) / (-a + 2 * b - c)
    #             if t1 > t2:
    #                 t1, t2 = t2, t1
    #
    #             if not (0 <= t1 <= 1) and not (0 <= t2 <= 1):
    #                 if keep_a:
    #                     yield self
    #             else:
    #                 # either or both of t1 and t2 are in (0, 1)
    #                 if t1 < 0:
    #                     t1 = 0
    #                 if t2 > 1:
    #                     t2 = 1
    #
    #                 match t1, t2:
    #                     case t1, t2 if t1 == t2:
    #                         yield from _crop_at_single_t(t1)
    #                     case 0, 1:
    #                         if (b < loc) == keep_smaller:
    #                             yield self
    #                     case 0, t2:
    #                         sub1, sub2 = self.divide(t2)
    #                         yield sub1 if keep_a else sub2
    #                     case t1, 1:
    #                         sub1, sub2 = self.divide(t1)
    #                         yield sub2 if keep_c else sub1
    #                     case t1, t2:
    #                         sub1, sub2 = self.divide(t1)
    #                         sub2a, sub2b = sub2.divide((t2 - t1) / (1 - t1))
    #                         if keep_a:
    #                             yield sub1
    #                             yield sub2b
    #                         else:
    #                             yield sub2a

    def translate(self, offset: complex) -> QuadraticBezierSegment:
        return QuadraticBezierSegment(
            self.first + offset, self.control + offset, self.last + offset
        )

    def rotate_complex(self, angle: complex) -> QuadraticBezierSegment:
        return QuadraticBezierSegment(
            self.first * angle, self.control * angle, self.last * angle
        )

    def scale(self, factor: complex) -> QuadraticBezierSegment:
        return QuadraticBezierSegment(
            complex(self.first.real * factor.real, self.first.imag * factor.imag),
            complex(self.control.real * factor.real, self.control.imag * factor.imag),
            complex(self.last.real * factor.real, self.last.imag * factor.imag),
        )

    def plot(self, ax: plt.Axes):
        color = "darkorange"

        bbox = self.bbox
        ax.plot(
            [bbox[0], bbox[2], bbox[2], bbox[0], bbox[0]],
            [bbox[1], bbox[1], bbox[3], bbox[3], bbox[1]],
            "-",
            color="orange",
            lw=".5",
        )

        # noinspection PyTypeChecker
        patch = patches.PathPatch(
            mpath.Path(
                (
                    (self.first.real, self.first.imag),
                    (self.control.real, self.control.imag),
                    (self.last.real, self.last.imag),
                ),
                [mpath.Path.MOVETO, mpath.Path.CURVE3, mpath.Path.CURVE3],
            ),
            facecolor="none",
            edgecolor=color,
        )

        pts = np.array([self.first, self.control, self.last])
        ax.plot(pts.real, pts.imag, lw=0.5, color="lightgrey")
        ax.add_patch(patch)
        ax.plot(
            self.first.real,
            self.first.imag,
            "o",
            color=color,
            ms=7,
            markerfacecolor="none",
        )
        ax.plot(self.control.real, self.control.imag, ".", color=color)
        ax.plot(self.last.real, self.last.imag, "D", color=color, ms=4)


if __name__ == "__main__":
    pass
    # q = QuadraticBezierSegment(0, 2 + 4j, 4 - 2j)
    #
    # # t = np.linspace(0, 1, 21)
    # # fig = plt.figure(tight_layout=True)
    # # ax = fig.add_subplot(1, 1, 1)
    # # ax.invert_yaxis()
    # # ax.set_aspect("equal")
    # # q.plot(ax)
    # # ax.grid(True)
    # #
    # # pts = np.array([q.point(t) for t in t])
    # # plt.plot(pts.real, pts.imag, "o", color="red")
    # # plt.show()
    #
    # # print(pts[10])
    # # print(pts[15])
    #
    # # q.show()
    #
    # res = list(q.crop_half_plane(1, "y", True))
    # print(res)
    # Segment.show_many(res + [q])
