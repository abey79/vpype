"""
.. module:: vpype
"""

from typing import Callable, List

import numpy as np

__all__ = ["union", "min_length", "max_length", "is_closed"]


def _line_length(line: np.ndarray) -> float:
    """Compute the length of a line."""
    return float(np.sum(np.abs(np.diff(line))))


def union(line: np.ndarray, keys: List[Callable[[np.ndarray], bool]]) -> bool:
    """Returns True if every callables in ``keys`` return True (similar to ``all()``.

    Args:
        line: line to test
        keys: list of callables

    Returns:
        True if every callables return True
    """
    for key in keys:
        if not key(line):
            return False
    return True


def min_length(line: np.ndarray, length: float) -> bool:
    """Keeps line whose length is equal or above a threshold.

    Args:
        line: the line to test
        length: threshold length

    Returns:
        True if line has length greater or equal to threshold
        """
    return _line_length(line) >= length


def max_length(line: np.ndarray, length: float) -> bool:
    """Keeps line whose length is shorter or equal to a threshold.

    Args:
        line: the line to test
        length: threshold length

    Returns:
        True if line has length shorter or equal to threshold
        """
    return _line_length(line) <= length


def is_closed(line: np.ndarray, tolerance: float) -> bool:
    """Keeps is_closed lines, where is_closed means that the distance between the starting and
    ending points is shorter than the provided tolerance.

    Args:
        line: the line to test
        tolerance: max distance between starting and ending point to consider a path is_closed

    Returns:
        True if line is is_closed
    """
    return len(line) > 1 and np.abs(line[-1] - line[0]) <= tolerance
