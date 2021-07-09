from typing import Iterable, Sequence, Set, Tuple

import numpy as np
import pytest
from shapely.geometry import LinearRing, LineString, MultiLineString, Point

from vpype import Document, LineCollection

from .utils import line_collection_contains

LINE_COLLECTION_TWO_LINES = [
    LineCollection([[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]]),
    [[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]],
    ([0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]),
    ((0, 1 + 1j), (2 + 2j, 3 + 3j, 4 + 4j)),
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


def _line_set(lc: Iterable[Sequence[complex]]) -> Set[Tuple[complex, ...]]:
    return {tuple(line if abs(line[0]) > abs(line[-1]) else reversed(line)) for line in lc}


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


# noinspection PyTypeChecker
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
    assert lc.width() == 20
    assert lc.height() == 20
    assert lc.bounds() == (-10, -10, 10, 10)


def test_line_collection_empty_bounds():
    lc = LineCollection()
    assert lc.bounds() is None


def test_line_collection_pen_up_length():
    lc = LineCollection([(0, 10), (10 + 10j, 500 + 500j, 10j), (0, -40)])
    assert lc.pen_up_length()[0] == 20.0


def test_line_collection_pen_up_trajectories():
    lc = LineCollection([(0, 100j, 1000, 10), (5j, 3, 25j), (3 + 3j, 100, 10j)])
    pen_up = lc.pen_up_trajectories()
    assert len(pen_up) == 2
    assert line_collection_contains(pen_up, [10, 5j])
    assert line_collection_contains(pen_up, [25j, 3 + 3j])


def test_line_collection_reverse():
    line_arr = [(0, 100j, 1000, 10), (5j, 3, 25j), (3 + 3j, 100, 10j)]
    lc = LineCollection(line_arr)
    lc.reverse()
    for i, line in enumerate(reversed(line_arr)):
        assert np.all(lc[i] == np.array(line))


def test_line_collection_clone():
    metadata = {"line_width": 0.3}
    lc = LineCollection(([0, 1, 10 + 10j], [0, 10]), metadata=metadata)
    cloned = lc.clone()
    assert len(cloned) == 0
    assert cloned.metadata == metadata


def test_document_lid_iteration():
    lc = LineCollection([(0, 1 + 1j)])
    doc = Document()
    doc.add(lc, 1)

    for lc in doc.layers_from_ids([1, 2, 3, 4]):
        lc.append([3, 3 + 3j])

    assert doc.count() == 1
    assert len(doc.layers[1]) == 2


def test_document_bounds():
    doc = Document()
    doc.add(LineCollection([(-10, 10), (0, 0)]), 1)
    doc.add(LineCollection([(0, 0), (-10j, 10j)]), 2)
    assert doc.bounds() == (-10, -10, 10, 10)


def test_document_bounds_empty_layer():
    doc = Document()

    doc.add(LineCollection([(0, 10 + 10j)]), 1)
    doc.add(LineCollection())

    assert doc.bounds() == (0, 0, 10, 10)


def _all_line_collection_ops(lc: LineCollection):
    lc.merge(1)
    lc.scale(2, 2)
    lc.translate(2, 2)
    lc.rotate(10)
    lc.reloop(1)
    lc.skew(4, 4)
    lc.bounds()
    # to be continued...


def test_ops_on_empty_line_collection():
    lc = LineCollection()
    _all_line_collection_ops(lc)


def test_ops_on_degenerate_line_collection():
    lc = LineCollection([np.array([], dtype=complex).reshape(-1)])
    _all_line_collection_ops(lc)

    lc = LineCollection([np.array([complex(1, 1)])])
    _all_line_collection_ops(lc)


def _all_document_ops(doc: Document):
    doc.bounds()
    doc.length()
    doc.segment_count()
    # to be completed..


def test_ops_on_emtpy_document():
    doc = Document()
    _all_document_ops(doc)


def test_ops_on_document_with_emtpy_layer():
    doc = Document()
    lc = LineCollection()
    doc.add(lc, 1)
    _all_document_ops(doc)


@pytest.mark.parametrize(
    ["lines", "merge_lines"],
    [
        ([[0, 10], [30, 40]], [[0, 10], [30, 40]]),
        ([[0, 10], [10, 20], [30, 40]], [[0, 10, 10, 20], [30, 40]]),
        ([[10, 0], [20, 10], [40, 30]], [[0, 10, 10, 20], [30, 40]]),
    ],
)
def test_line_collection_merge(lines, merge_lines):
    lc = LineCollection(lines)
    lc.merge(0.1)

    assert _line_set(lc) == _line_set(merge_lines)


def test_document_empty_copy():
    doc = Document()
    doc.add(LineCollection([(0, 1)]), 1)
    doc.page_size = 3, 4

    new_doc = doc.empty_copy()
    assert len(new_doc.layers) == 0
    assert new_doc.page_size == (3, 4)
