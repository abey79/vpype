import numpy as np

from vpype.operations import LineIndex
from vpype.model import LineCollection
from .conftest import random_line


def test_pop_front():
    lines = [random_line(5), random_line(3), random_line(7)]
    lc = LineCollection(lines)
    idx = LineIndex(lc)

    assert np.all(idx.pop_front() == lines[0])
    assert np.all(idx.pop_front() == lines[1])
    assert np.all(idx.pop_front() == lines[2])
    assert len(idx) == 0


def test_pop():
    lines = [random_line(5), random_line(3), random_line(7)]
    lc = LineCollection(lines)
    idx = LineIndex(lc)

    assert np.all(idx.pop(2) == lines[2])
    assert idx.pop(2) is None
    assert np.all(idx.pop(0) == lines[0])
    assert idx.pop(0) is None
    assert np.all(idx.pop(1) == lines[1])
    assert len(idx) == 0


def test_find_nearest_within():
    lines = [[1 + 1j, 10], [1.2 + 1j, 10], [1.3 + 1j, 10]]
    idx = LineIndex(LineCollection(lines))

    assert idx.find_nearest_within(1.05 + 1j, 0.01)[0] is None
    assert idx.find_nearest_within(1.05 + 1j, 0.051) == (0, False)
    assert idx.find_nearest_within(1.05 + 1j, 0.16) == (0, False)
    idx.pop(0)
    assert idx.find_nearest_within(1.05 + 1j, 0.16) == (1, False)
    assert idx.find_nearest_within(1.05 + 1j, 0.051)[0] is None


def test_find_nearest_within_reverse():
    lines = [[10, 0], [20, 10.1]]
    idx = LineIndex(LineCollection(lines))
    ridx = LineIndex(LineCollection(lines), reverse=True)

    assert idx.find_nearest_within(0.1, 0.5)[0] is None
    assert ridx.find_nearest_within(0.1, 0.5) == (0, True)
    assert ridx.find_nearest_within(10.01, 0.5) == (0, False)
    assert ridx.find_nearest_within(10.09, 0.5) == (1, True)
