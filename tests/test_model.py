import pytest
import numpy as np
from shapely.geometry import MultiLineString, LineString, Point

from vpype import LineCollection, VectorData, LinearRing

LINE_COLLECTION_TWO_LINES = [
    LineCollection([[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]]),
    [[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]],
    ([0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]),
    ((0, 1 + 1j), (2 + 2j, 3 + 3j, 4 + 4j)),
    np.array([[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]]),
    MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3), (4, 4)]]),
]

LINE_COLLECTION_LINESTRING_LINEARRING = [
    LineString([(0, 0), (1, 1), (3, 5)]),
    LinearRing([(10, 10), (11, 41), (12, 12), (10, 10)]),
]

EMPTY_LINE_COLLECTION = [
    MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3), (4, 4)]]).intersection(
        Point(50, 50).buffer(1.0)
    ),  # this is an empty geometry
    LineString([(0, 0), (1, 1), (3, 5)]).intersection(Point(50, 50).buffer(1.0)),
    LinearRing([(10, 10), (11, 41), (12, 12), (10, 10)]).intersection(Point(0, 0).buffer(1)),
]


@pytest.mark.parametrize("lines", LINE_COLLECTION_TWO_LINES)
def test_line_collection_creation_two_lines(lines):
    lc = LineCollection(lines)
    assert len(lc) == 2
    assert np.all(lc[0] == np.array([0, 1 + 1j]))
    assert np.all(lc[1] == np.array([2 + 2j, 3 + 3j, 4 + 4j]))


@pytest.mark.parametrize("lines", LINE_COLLECTION_TWO_LINES)
def test_line_collection_extend_two_lines(lines):
    lc = LineCollection([(3, 3j)])
    lc.extend(lines)
    assert len(lc) == 3
    assert np.all(lc[0] == np.array([3, 3j]))
    assert np.all(lc[1] == np.array([0, 1 + 1j]))
    assert np.all(lc[2] == np.array([2 + 2j, 3 + 3j, 4 + 4j]))


@pytest.mark.parametrize("lines", LINE_COLLECTION_LINESTRING_LINEARRING)
def test_line_collection_creation_linestring_linearring(lines):
    lc = LineCollection(lines)
    assert len(lc) == 1


@pytest.mark.parametrize("lines", EMPTY_LINE_COLLECTION)
def test_line_collection_creation_empty(lines):
    lc = LineCollection(lines)
    assert len(lc) == 0


@pytest.mark.parametrize(
    "lines",
    LINE_COLLECTION_TWO_LINES + LINE_COLLECTION_LINESTRING_LINEARRING + EMPTY_LINE_COLLECTION,
)
def test_extend_same_as_init(lines):
    lc1 = LineCollection(lines)
    lc2 = LineCollection()
    lc2.extend(lines)

    assert len(lc1) == len(lc2)
    for l1, l2 in zip(lc1, lc2):
        assert np.all(l1 == l2)


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


@pytest.mark.parametrize(
    "line",
    [
        LinearRing([(4, 3), (5, 0), (10, 10), (0, 5)]),
        LinearRing([(4, 3), (5, 0), (10, 10), (0, 5), (4, 3)]),
    ],
)
def test_line_collection_append_linearring(line):
    lc = LineCollection()
    lc.append(line)
    assert len(lc) == 1
    assert np.all(lc[0] == np.array([4 + 3j, 5, 10 + 10j, 5j, 4 + 3j]))


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
