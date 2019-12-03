import pytest
import numpy as np
from shapely.geometry import MultiLineString, LineString

from vpype.model import LineCollection, VectorData

LINE_COLLECTION_INIT = [
    LineCollection([[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]]),
    [[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]],
    ([0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]),
    ((0, 1 + 1j), (2 + 2j, 3 + 3j, 4 + 4j)),
    np.array([[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]]),
    MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3), (4, 4)]]),
]


@pytest.mark.parametrize("lines", LINE_COLLECTION_INIT)
def test_line_collection_creation(lines):
    lc = LineCollection(lines)
    assert len(lc) == 2
    assert np.all(lc[0] == np.array([0, 1 + 1j]))
    assert np.all(lc[1] == np.array([2 + 2j, 3 + 3j, 4 + 4j]))


@pytest.mark.parametrize("lines", LINE_COLLECTION_INIT)
def test_line_collection_extend(lines):
    lc = LineCollection([(3, 3j)])
    lc.extend(lines)
    assert len(lc) == 3
    assert np.all(lc[0] == np.array([3, 3j]))
    assert np.all(lc[1] == np.array([0, 1 + 1j]))
    assert np.all(lc[2] == np.array([2 + 2j, 3 + 3j, 4 + 4j]))


@pytest.mark.parametrize(
    "line",
    [
        LineString([(4, 3), (5, 0), (10, 10), (0, 5)]),
        np.array([4 + 3j, 5, 10 + 10j, 5j]),
        [4 + 3j, 5, 10 + 10j, 5j],
    ],
)
def test_line_collection_append(line):
    lc = LineCollection()
    lc.append(line)
    assert len(lc) == 1
    assert np.all(lc[0] == np.array([4 + 3j, 5, 10 + 10j, 5j]))


def test_line_collection_bounds():
    lc = LineCollection([(-10, 10), (-10j, 10j)])
    assert lc.bounds() == (-10, -10, 10, 10)


def test_line_collection_empty_bounds():
    lc = LineCollection()
    assert lc.bounds() is None


def test_line_collection_pen_up_length():
    lc = LineCollection([(0, 10), (10 + 10j, 500 + 500j, 10j), (0, -40)])
    assert lc.pen_up_length()[0] == 20.0


def test_vector_data_lid_iteration():
    lc = LineCollection([(0, 1 + 1j)])
    vd = VectorData()
    vd.add(lc, 1)

    for lc in vd.layers_from_ids([1, 2, 3, 4]):
        lc.append([3, 3 + 3j])

    assert vd.count() == 1
    assert len(vd.layers[1]) == 2


def test_vector_data_bounds():
    vd = VectorData()
    vd.add(LineCollection([(-10, 10), (0, 0)]), 1)
    vd.add(LineCollection([(0, 0), (-10j, 10j)]), 2)
    assert vd.bounds() == (-10, -10, 10, 10)
