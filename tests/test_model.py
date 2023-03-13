from __future__ import annotations

import copy
import sys
from collections.abc import Iterable, Sequence

import numpy as np
import pytest
from shapely.geometry import LinearRing, LineString, MultiLineString, Point

import vpype as vp
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


def _line_set_unoriented(lc: Iterable[Sequence[complex]]) -> set[tuple[complex, ...]]:
    """Set of lines with consistent flipping to ignore direction in comparison"""
    return {tuple(line if abs(line[0]) > abs(line[-1]) else reversed(line)) for line in lc}


def _line_set_oriented(lc: Iterable[Sequence[complex]]) -> set[tuple[complex, ...]]:
    """Set of lines without flipping"""
    return {tuple(line) for line in lc}


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


def test_line_collection_clone_with_data():
    metadata = {"line_width": 0.3}
    lc = LineCollection(([0, 1, 10 + 10j], [0, 10]), metadata=metadata)
    cloned = lc.clone([(100, 100j + 200)])
    assert len(cloned) == 1
    assert np.all(cloned[0] == np.array((100, 100j + 200)))
    assert cloned.metadata == metadata


def test_line_collection_property():
    lc = LineCollection()

    lc.metadata["name"] = "Hello world"
    assert lc.property("name") == "Hello world"
    assert lc.property("missing") is None


def test_line_collection_set_property():
    lc = LineCollection()

    lc.set_property(vp.METADATA_FIELD_PEN_WIDTH, 0.1)
    assert lc.metadata[vp.METADATA_FIELD_PEN_WIDTH] == 0.1

    lc.set_property(vp.METADATA_FIELD_PEN_WIDTH, "0.2")
    assert lc.metadata[vp.METADATA_FIELD_PEN_WIDTH] == 0.2

    with pytest.raises(ValueError):
        lc.set_property(vp.METADATA_FIELD_PEN_WIDTH, "should fail")


def test_document_replace():
    doc = Document()
    doc.add([(0, 10 + 10j)], 1)
    doc.layers[1].set_property(vp.METADATA_FIELD_NAME, "test value")

    doc.replace([(10, 100j)], 1)

    assert np.all(doc.layers[1][0] == np.array([10, 100j]))
    assert doc.layers[1].metadata == {vp.METADATA_FIELD_NAME: "test value"}


def test_document_replace_bad_layer_id():
    doc = Document()
    with pytest.raises(ValueError):
        doc.replace([(0, 10j)], 1)


def test_document_swap_content():
    doc = Document()
    doc.add([(0, 1)], 1)
    doc.add([(0, 10)], 2)
    doc.layers[1].set_property(vp.METADATA_FIELD_NAME, "hello")
    doc.layers[2].set_property(vp.METADATA_FIELD_PEN_WIDTH, 0.15)

    doc.swap_content(1, 2)

    assert np.all(doc.layers[1][0] == np.array([0, 10]))
    assert np.all(doc.layers[2][0] == np.array([0, 1]))
    assert doc.layers[1].metadata == {vp.METADATA_FIELD_NAME: "hello"}
    assert doc.layers[2].metadata == {vp.METADATA_FIELD_PEN_WIDTH: 0.15}


def test_document_swap_content_bad_layer_id():
    doc = Document()

    with pytest.raises(ValueError):
        doc.swap_content(1, 2)

    doc.add([(0, 1)], 1)

    with pytest.raises(ValueError):
        doc.swap_content(1, 2)

    with pytest.raises(ValueError):
        doc.swap_content(2, 1)


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

    assert _line_set_unoriented(lc) == _line_set_unoriented(merge_lines)


@pytest.mark.parametrize(
    ["lines", "merge_lines"],
    [
        (
            [(0, 100), (100, 200 + 100j)],
            [(0, 100, 100, 200 + 100j)],
        ),
        (
            [(100, 200 + 100j), (0, 100)],
            [(0, 100, 100, 200 + 100j)],
        ),
        (  # first line needs flipping to match
            [(100, 0), (100, 200 + 100j)],
            [(100, 0), (100, 200 + 100j)],
        ),
        (
            [(100, 200 + 100j), (100, 0)],
            [(100, 0), (100, 200 + 100j)],
        ),
    ],
)
def test_line_collection_merge_no_flip(lines, merge_lines):
    lc = LineCollection(lines)
    lc.merge(0.1, flip=False)

    assert _line_set_oriented(lc) == _line_set_oriented(merge_lines)


def test_document_clone():
    doc = Document()
    doc.add(LineCollection([(0, 1)]), 1)
    doc.page_size = 3, 4

    new_doc = doc.clone()
    assert len(new_doc.layers) == 0
    assert new_doc.page_size == (3, 4)


def test_document_exists_none():
    doc = Document()
    doc.add(LineCollection([[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]]), 1)

    assert doc.exists(1)
    assert not doc.exists(2)
    assert not doc.exists(None)


def test_document_add_to_sources(tmp_path):
    path = tmp_path / "some_file.txt"
    path.touch()

    doc = Document()
    doc.add(LineCollection([[0, 1 + 1j], [2 + 2j, 3 + 3j, 4 + 4j]]), 1)

    doc.add_to_sources(path)
    assert path in doc.property(vp.METADATA_FIELD_SOURCE_LIST)
    assert path == doc.property(vp.METADATA_FIELD_SOURCE)

    path2 = tmp_path / "doest_exist.txt"
    doc.add_to_sources(path2)
    assert path2 not in doc.property(vp.METADATA_FIELD_SOURCE_LIST)
    assert path2 != doc.property(vp.METADATA_FIELD_SOURCE)

    with pytest.raises(Exception):
        doc.add_to_sources(sys.stdin)


def test_line_collection_equality(make_line_collection):
    lc = make_line_collection()
    assert lc == lc
    assert lc == copy.deepcopy(lc)

    lc_clone = lc.clone()
    lc_clone.extend(lc)
    assert lc == lc_clone

    lc_no_metadata = copy.deepcopy(lc)
    lc_no_metadata.metadata = {}
    assert lc != lc_no_metadata

    lc_new_metadata = copy.deepcopy(lc)
    lc_new_metadata.set_property("test_line_collection_equality_prop", "hello")
    assert lc != lc_new_metadata

    lc_miss_one_line = lc.clone()
    lc_miss_one_line.extend(lc[:-1])
    assert lc != lc_miss_one_line

    lc_one_more_line = copy.deepcopy(lc)
    lc_one_more_line.append(np.array([0, 100, 100j]))
    assert lc != lc_one_more_line

    assert lc != "wrong type"


def test_document_equality(make_document, make_line_collection):
    doc = make_document()

    assert doc == doc
    assert doc == copy.deepcopy(doc)

    doc_clone = doc.clone()
    for lid, layer in doc.layers.items():
        doc_clone.add(copy.deepcopy(layer), lid, with_metadata=True)
    assert doc == doc_clone

    doc_no_metadata = copy.deepcopy(doc)
    doc.metadata = {}
    assert doc != doc_no_metadata

    doc_new_metadata = copy.deepcopy(doc)
    doc_new_metadata.set_property("test_document_equality_prop", "hello")
    assert doc != doc_new_metadata

    doc_miss_one_layer = copy.deepcopy(doc)
    del doc_miss_one_layer.layers[1]
    assert doc != doc_miss_one_layer

    doc_one_more_layer = copy.deepcopy(doc)
    doc_one_more_layer.add(make_line_collection())
    assert doc != doc_one_more_layer

    doc_one_more_line = copy.deepcopy(doc)
    doc_one_more_line.layers[1].append(np.array([0, 100, 100j]))
    assert doc != doc_one_more_line

    assert doc != "wrong type"
