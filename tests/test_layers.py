import copy
import math
import random

import pytest

import vpype as vp
from vpype_cli import cli, execute
from vpype_cli.debug import DebugData


@pytest.mark.parametrize(
    ("command", "layers"),
    [
        ("line 0 0 1 1", [1]),
        ("line -l 2 0 0 1 1", [2]),
        ("line 0 0 1 1 line 2 2 3 3", [1]),
        ("line -l 2 0 0 1 1 line 2 2 3 3", [2]),
        ("line -l 2 0 0 1 1 line -l 3 2 2 3 3", [2, 3]),
        ("line -l 2 0 0 1 1 line -l 3 2 2 3 3 line 4 4 5 5", [2, 3]),
        ("line -l new 0 0 1 1 line -l new 2 2 3 3 line 4 4 5 5", [1, 2]),
        ("line -l 3 0 0 1 1 line -l new 2 2 3 3 line 4 4 5 5", [1, 3]),
        ("line -l new 0 0 1 1 line -l new 2 2 3 3 line -l new 4 4 5 5", [1, 2, 3]),
        ("line 0 0 1 1 ldelete 1", []),
        ("line 0 0 1 1 lcopy all new", [1, 2]),
        ("line 0 0 1 1 lcopy all new ldelete 1", [2]),
        ("line 0 0 1 1 lcopy all new ldelete all", []),
        ("line 0 0 1 1 lmove all new", [2]),
        ("line 0 0 1 1 line -l new 0 0 1 1 lmove all 2", [2]),
        ("line 0 0 1 1 line -l new 0 0 1 1 lmove all 3", [3]),
    ],
)
def test_layer_creation(runner, command, layers):
    result = runner.invoke(cli, command + " dbsample dbdump")
    data = DebugData.load(result.output)[0]

    assert result.exit_code == 0
    assert data.has_layers_only(layers)


@pytest.mark.parametrize(
    ("command", "bounds_offset"),
    [
        ("", [0, 0, 0]),
        ("translate 1 1", [1, 1, 1]),
        ("translate -l all 1 1", [1, 1, 1]),
        ("translate -l 1 1 1", [1, 0, 0]),
        ("translate -l 2 1 1", [0, 1, 0]),
        ("translate -l 3 1 1", [0, 0, 1]),
    ],
)
def test_layer_processors(runner, command, bounds_offset):
    result = runner.invoke(
        cli, f"line -l 1 0 0 1 1 line -l 2 0 0 1 1 line -l 3 0 0 1 1 {command} dbsample dbdump"
    )
    data = DebugData.load(result.output)[0]

    assert result.exit_code == 0
    for i in range(3):
        assert data.document[i + 1].bounds() == (
            bounds_offset[i],
            bounds_offset[i],
            bounds_offset[i] + 1,
            bounds_offset[i] + 1,
        )


@pytest.fixture
def big_doc():
    random.seed(0)
    doc = vp.Document()
    doc.add(
        vp.LineCollection(
            [
                (
                    random.uniform(0, 100) + random.uniform(0, 100) * 1j,
                    random.uniform(0, 100) + random.uniform(0, 100) * 1j,
                )
                for _ in range(1000)
            ]
        )
    )
    return doc


def test_lmove(big_doc):
    doc = execute("lmove 1 2", big_doc)

    assert 1 not in doc.layers
    assert len(doc.layers[2]) == 1000


def test_lmove_prob(big_doc):
    # test for a bunch of seeds without making the test fragile
    for seed in range(100):
        random.seed(seed)

        doc = copy.deepcopy(big_doc)
        doc = execute("lmove --prob 0.5 1 2", doc)

        assert math.isclose(len(doc.layers[1]) / 1000, 0.5, abs_tol=0.1)
        assert math.isclose(len(doc.layers[2]) / 1000, 0.5, abs_tol=0.1)


def test_lmove_prob_zero(big_doc):
    doc = execute("lmove --prob 0. 1 2", big_doc)

    assert 2 not in doc.layers
    assert len(doc.layers[1]) == 1000


def test_ldelete(big_doc):
    doc = execute("ldelete 1", big_doc)

    assert len(doc.layers) == 0


def test_ldelete_prob(big_doc):
    # test for a bunch of seeds without making the test fragile
    for seed in range(100):
        random.seed(seed)

        doc = copy.deepcopy(big_doc)
        doc = execute("ldelete --prob 0.5 1", doc)

        assert math.isclose(len(doc.layers[1]) / 1000, 0.5, abs_tol=0.1)


def test_ldelete_prob_zero(big_doc):
    doc = execute("ldelete --prob 0. 1", big_doc)

    assert len(doc.layers[1]) == 1000


def test_lcopy(big_doc):
    doc = execute("lcopy 1 2", big_doc)

    assert len(doc.layers[1]) == 1000
    assert len(doc.layers[2]) == 1000


def test_lcopy_prob(big_doc):
    # test for a bunch of seeds without making the test fragile
    for seed in range(100):
        random.seed(seed)

        doc = copy.deepcopy(big_doc)
        doc = execute("lcopy --prob 0.5 1 2", doc)

        assert len(doc.layers[1]) == 1000
        assert math.isclose(len(doc.layers[2]) / 1000, 0.5, abs_tol=0.1)


def test_lcopy_prob_zero(big_doc):
    doc = execute("lcopy --prob 0. 1 2", big_doc)

    assert len(doc.layers[1]) == 1000
    assert 2 not in doc.layers
