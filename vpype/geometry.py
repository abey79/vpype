import math
from typing import List, Optional

import numpy as np

__all__ = ["line_length", "is_closed", "interpolate", "crop_half_plane", "crop", "reloop"]


def line_length(line: np.ndarray) -> float:
    """Compute the length of a line."""
    return float(np.sum(np.abs(np.diff(line))))


def is_closed(line: np.ndarray, tolerance: float) -> bool:
    """Check if a line is closed.

    Args:
        line: the line to test
        tolerance: max distance between starting and ending point to consider a path is_closed

    Returns:
        True if line is is_closed
    """
    return len(line) > 1 and np.abs(line[-1] - line[0]) <= tolerance


def interpolate(line: np.ndarray, step: float) -> np.ndarray:
    """Compute a linearly interpolated version of `line` with segments of `step` length or
    less.

    Args:
        line: 1D array of complex
        step: maximum length of interpolated segment

    Returns:
        interpolated 1D array of complex
    """

    curv_absc = np.cumsum(np.hstack([0, np.abs(np.diff(line))]))
    return np.interp(
        np.linspace(0, curv_absc[-1], 1 + math.ceil(curv_absc[-1] / step)), curv_absc, line
    )


def _interpolate_crop(start: complex, stop: complex, loc: float, axis: int) -> complex:
    """Interpolate between two points at a given coordinates."""

    start_dim, stop_dim = (start.real, stop.real) if axis == 0 else (start.imag, stop.imag)

    diff = stop_dim - start_dim
    if diff == 0:
        raise ValueError("cannot interpolate line parallel to axis")

    r = (loc - start_dim) / diff

    if r < 0.5:
        return start + (stop - start) * r
    else:
        return stop - (stop - start) * (1.0 - r)


def crop_half_plane(
    line: np.ndarray, loc: float, axis: int, keep_smaller: bool
) -> List[np.ndarray]:
    """Crop a path at a axis-aligned location.

    The path is cut at location x=loc for axis=0, and y=loc for axis=1. The argument
    `keep_smaller` controls which part of the path is discarded.

    Args:
        line: path to crop
        loc: coordinate at which the cut is made
        axis: 0 for a cut along x axis, 1 for y axis
        keep_smaller: if True, parts of `line` with coordinates smaller or equal than `loc`
            are kept, and the reverse otherwise

    Returns:
        list of paths
    """

    if axis not in [0, 1]:
        raise ValueError("axis must be either 0 or 1")

    line_test_dim = line.real if axis == 0 else line.imag
    if keep_smaller:
        outside = line_test_dim > loc
    else:
        outside = line_test_dim < loc

    if np.all(outside):
        return []
    elif np.all(~outside):
        return [line]

    diff = np.diff(outside.astype(int))
    (start_idx,) = np.nonzero(diff == -1)
    (stop_idx,) = np.nonzero(diff == 1)

    # The following properties are expected after normalization:
    #   - len(start_idx) == len(stop_idx)
    #   - (start_idx, stop_idx) are streak of points that must be kept
    #   - start_idx == -1 means beginning of line in not to be cropped
    #   - stop_idx == inf means end of line is not to be cropped
    inf = len(line)
    if len(start_idx) == 0:
        start_idx = np.array([-1])
    if len(stop_idx) == 0:
        stop_idx = np.array([inf])
    if start_idx[0] > stop_idx[0]:
        start_idx = np.hstack([-1, start_idx])
    if stop_idx[-1] < start_idx[-1]:
        stop_idx = np.hstack([stop_idx, inf])

    line_arr = []
    for start, stop in zip(start_idx, stop_idx):
        if start == -1:
            sub_line = np.hstack(
                [line[: stop + 1], _interpolate_crop(line[stop], line[stop + 1], loc, axis)]
            )
        elif stop == inf:
            sub_line = np.hstack(
                [
                    _interpolate_crop(line[start], line[start + 1], loc, axis),
                    line[start + 1 :],
                ]
            )
        else:
            sub_line = np.hstack(
                [
                    _interpolate_crop(line[start], line[start + 1], loc, axis),
                    line[start + 1 : stop + 1],
                    _interpolate_crop(line[stop], line[stop + 1], loc, axis),
                ]
            )

        # check cases where coordinate lie on threshold
        sub_start = 1 if sub_line[0] == sub_line[1] else 0
        sub_stop = (len(sub_line) - 1) if sub_line[-1] == sub_line[-2] else len(sub_line)
        if sub_stop >= sub_start + 2:
            line_arr.append(sub_line[sub_start:sub_stop])

    return line_arr


def _crop_half_plane_mult(lines: List[np.ndarray], loc: float, axis: int, keep_smaller: bool):
    new_lines = []
    for line in lines:
        new_lines.extend(crop_half_plane(line, loc=loc, axis=axis, keep_smaller=keep_smaller))
    return new_lines


def crop(line: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> List[np.ndarray]:
    """Crop a polyline to a rectangular area.

    Args:
        line: line to crop
        x1: left coordinate of the crop area
        y1: bottom coordinate of the crop area
        x2: right coordinate of the crop area
        y2: top coordinate of the crop area

    Returns:
        list of lines resulting of the crop (emtpy if x1 > x2 or y1 > y2)
    """
    line_list = _crop_half_plane_mult([line], x1, axis=0, keep_smaller=False)
    line_list = _crop_half_plane_mult(line_list, x2, axis=0, keep_smaller=True)
    line_list = _crop_half_plane_mult(line_list, y1, axis=1, keep_smaller=False)
    return _crop_half_plane_mult(line_list, y2, axis=1, keep_smaller=True)


def reloop(line: np.ndarray, loc: Optional[int] = None) -> np.ndarray:
    """Change the seam of a closed path. Closed-ness is not checked. Beginning and end points
    are averaged to compute a new point. A new seam location can be provided or will be chosen
    randomly.

    Args:
        line: path to reloop
        loc: new seam location

    Returns:
        re-seamed path
    """

    if loc is None:
        loc = np.random.randint(len(line) - 1)
    end_point = 0.5 * (line[0] + line[-1])
    line[0] = end_point
    line[-1] = end_point
    return np.hstack([line[loc:], line[1 : min(loc + 1, len(line))]])
