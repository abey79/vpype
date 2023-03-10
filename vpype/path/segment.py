from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Iterable, Literal, TypeVar

import numpy as np
import numpy.typing as npt
from matplotlib import pyplot as plt

CoordList = npt.NDArray[np.complex64]

TSegment = TypeVar("TSegment", bound="Segment")


class Segment(ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def begin(self) -> complex:
        ...

    @property
    @abstractmethod
    def end(self) -> complex:
        ...

    @property
    @abstractmethod
    def length(self) -> float:
        ...

    @property
    @abstractmethod
    def bbox(self) -> tuple[float, float, float, float]:
        ...

    @abstractmethod
    def translate(self: TSegment, offset: complex) -> TSegment:
        """Translate the segment.

        Args:
            offset: translation offset

        Returns:
            translated segment
        """

    @abstractmethod
    def rotate_complex(self: TSegment, angle: complex) -> TSegment:
        """Rotate the segment around the origin.

        Args:
            angle: complex number representing the rotation angle

        Returns:
            rotated segment
        """

    def rotate(self: TSegment, angle: float) -> TSegment:
        """Rotate the segment around the origin.

        Args:
            angle: rotation angle in radians

        Returns:
            rotated segment
        """
        return self.rotate_complex(complex(math.cos(angle), math.sin(angle)))

    @abstractmethod
    def scale(self: TSegment, factor: complex) -> TSegment:
        """Translate the segment around the origin.

        Args:
            factor: complex number representing the scaling factor

        Returns:
            scaled segment
        """

    # shear?

    @abstractmethod
    def reverse(self: TSegment) -> TSegment:
        ...

    @abstractmethod
    def flip_axes(self: TSegment) -> TSegment:
        """Flip the segment along the x=y axis.

        This is used for cropping along the y axis.
        """

    @abstractmethod
    def crop_x(self: TSegment, x: float, keep_smaller: bool) -> Iterable[TSegment]:
        """Crop a segment at the given x coordinate."""

    def crop_y(self: TSegment, y: float, keep_smaller: bool) -> Iterable[TSegment]:
        for q in self.flip_axes().crop_x(y, keep_smaller):
            yield q.flip_axes()

    @abstractmethod
    def to_polyline(self, tolerance: float) -> CoordList:
        """Convert the segment to a polyline.

        The entirety of the polyline must lie within a distance of ``tolerance`` from the
        original segment.

        Args:
            tolerance: maximum distance from the original segment

        Returns:
            the polyline approximating the segment
        """

    @property
    def closed(self) -> bool:
        return self.begin == self.end

    def show(self) -> None:
        fig = plt.figure(tight_layout=True)
        ax = fig.add_subplot(1, 1, 1)
        ax.invert_yaxis()
        ax.set_aspect("equal")
        self.plot(ax)
        ax.set_title(repr(self))
        ax.grid(True)
        plt.show()

    @staticmethod
    def show_many(segs: Iterable[Segment]) -> None:
        fig = plt.figure(tight_layout=True)
        ax = fig.add_subplot(1, 1, 1)
        ax.invert_yaxis()
        ax.set_aspect("equal")
        ax.grid(True)
        for seg in segs:
            seg.plot(ax)
        plt.show()

    @abstractmethod
    def plot(self, ax: plt.Axes):
        pass
