from __future__ import annotations

import copy
import math
import random

import click
import numpy as np
import pytest

import vpype as vp
import vpype_cli.cli
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
        ("line 0 0 1 1 lreverse 1", [1]),
        ("lreverse 1", []),  # lreverse doesnt create phantom layers
        ("line -l2 0 0 1 1 lreverse 1", [2]),
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


def test_layer_not_new():
    with pytest.raises(click.exceptions.BadParameter) as exc:
        execute("ldelete new")
    assert "existing" in exc.value.message


def test_lmove(big_doc):
    doc = execute("lmove 1 2", big_doc)

    assert 1 not in doc.layers
    assert len(doc.layers[2]) == 1000


def test_lmove_prob_one(big_doc):
    doc = execute("lmove --prob 1. 1 2", big_doc)

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


def test_lmove_keep_order(make_line_collection, tmp_path_factory):
    lc = make_line_collection(line_count=3)
    doc = vp.Document()
    for i in range(3):
        doc.add(
            vp.LineCollection(lc[i : i + 1], metadata=lc.metadata), i + 1, with_metadata=True
        )

    doc = vpype_cli.execute("lmove all 2", document=doc)

    assert doc.layers[2] == lc


def test_ldelete(big_doc):
    doc = execute("ldelete 1", big_doc)

    assert len(doc.layers) == 0


@pytest.mark.parametrize(
    ["cmd", "resulting_layers"],
    [
        ("random random -l2 ldelete 1", {2}),
        ("random random -l2 ldelete --keep 1", {1}),
        ("random random -l2 ldelete --keep 3", {}),
        ("random random -l2 random -l3 ldelete --keep 1", {1}),
        ("random random -l2 random -l3 ldelete --keep 1,3", {1, 3}),
        ("random random -l2 random -l3 ldelete --keep 1,4,5", {1}),
        ("random random -l2 random -l3 ldelete 1", {2, 3}),
        ("random random -l2 random -l3 ldelete 1,3", {2}),
        ("random random -l2 random -l3 ldelete 1,4,5", {2, 3}),
    ],
)
def test_ldelete_keep(cmd, resulting_layers):
    doc = execute(cmd)
    assert doc.layers.keys() == set(resulting_layers)


def test_ldelete_prob_one(big_doc):
    doc = execute("ldelete --prob 1. 1", big_doc)

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


def test_lcopy_prob_one(big_doc):
    doc = execute("lcopy --prob 1. 1 2", big_doc)

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


def test_lswap():
    doc = execute("line -l1 0 0 10 10 line -l2 20 20 30 30 lswap 1 2")

    assert np.all(doc.layers[1][0] == np.array([20 + 20j, 30 + 30j]))
    assert np.all(doc.layers[2][0] == np.array([0, 10 + 10j]))


def test_lswap_prob_zero():
    doc = execute("line -l1 0 0 10 10 line -l2 20 20 30 30 lswap --prob 0. 1 2")

    assert np.all(doc.layers[2][0] == np.array([20 + 20j, 30 + 30j]))
    assert np.all(doc.layers[1][0] == np.array([0, 10 + 10j]))


def test_lreverse():
    doc = execute("line 0 0 10 10 line 20 20 30 30 lreverse 1")

    assert np.all(doc.layers[1][0] == np.array([20 + 20j, 30 + 30j]))
    assert np.all(doc.layers[1][1] == np.array([0, 10 + 10j]))


def test_lcopy_metadata():
    doc = execute("line 0 0 10 10 propset -l1 test value lcopy 1 2")
    assert len(doc.layers[1]) == 1
    assert len(doc.layers[2]) == 1
    assert ("test", "value") in doc.layers[2].metadata.items()

    doc = execute("line 0 0 10 10 propset -l1 test value lcopy --no-prop 1 2")
    assert len(doc.layers[1]) == 1
    assert len(doc.layers[2]) == 1
    assert "test" in doc.layers[1].metadata
    assert "test" not in doc.layers[2].metadata

    doc = execute("random -n 100 propset -l1 test value lcopy --prob 0.5 1 2")
    assert len(doc.layers[1]) == 100
    assert len(doc.layers[2]) > 0
    assert "test" not in doc.layers[2].metadata.items()

    doc = execute("random -l1 -n100 random -l2 -n100 propset -l1,2 test value lcopy 1,2 3")
    assert len(doc.layers[1]) == 100
    assert len(doc.layers[2]) == 100
    assert len(doc.layers[3]) == 200
    assert "test" not in doc.layers[3].metadata.items()


def test_lmove_metadata():
    doc = execute("line 0 0 10 10 propset -l1 test value lmove 1 2")
    assert 1 not in doc.layers
    assert len(doc.layers[2]) == 1
    assert ("test", "value") in doc.layers[2].metadata.items()

    doc = execute("line 0 0 10 10 propset -l1 test value lmove --no-prop 1 2")
    assert 1 not in doc.layers
    assert len(doc.layers[2]) == 1
    assert "test" not in doc.layers[2].metadata

    doc = execute("random -n 100 propset -l1 test value lmove --prob 0.5 1 2")
    assert len(doc.layers[1]) > 0
    assert len(doc.layers[2]) > 0
    assert "test" not in doc.layers[2].metadata.items()

    doc = execute("random -l1 -n100 random -l2 -n100 propset -l1,2 test value lmove 1,2 3")
    assert 1 not in doc.layers
    assert 2 not in doc.layers
    assert len(doc.layers[3]) == 200
    assert "test" not in doc.layers[3].metadata.items()


def test_lswap_metadata():
    doc = execute(
        "random -l1 -n10 random -l2 -n20 "
        "propset -l1 test val1 propset -l2 test val2 "
        "propset -l1 test1 val1 propset -l2 test2 val2 "
        "lswap 1 2"
    )

    assert len(doc.layers[1]) == 20
    assert len(doc.layers[2]) == 10
    assert ("test", "val2") in doc.layers[1].metadata.items()
    assert ("test2", "val2") in doc.layers[1].metadata.items()
    assert ("test", "val1") in doc.layers[2].metadata.items()
    assert ("test1", "val1") in doc.layers[2].metadata.items()

    doc = execute(
        "random -l1 -n10 random -l2 -n20 "
        "propset -l1 test val1 propset -l2 test val2 "
        "propset -l1 test1 val1 propset -l2 test2 val2 "
        "lswap --no-prop 1 2"
    )

    assert len(doc.layers[1]) == 20
    assert len(doc.layers[2]) == 10
    assert ("test", "val1") in doc.layers[1].metadata.items()
    assert ("test1", "val1") in doc.layers[1].metadata.items()
    assert ("test", "val2") in doc.layers[2].metadata.items()
    assert ("test2", "val2") in doc.layers[2].metadata.items()

    doc = execute(
        "random -l1 -n100 random -l2 -n100 "
        "propset -l1 test val1 propset -l2 test val2 "
        "propset -l1 test1 val1 propset -l2 test2 val2 "
        "lswap --prob 0.5 1 2"
    )

    assert len(doc.layers[1]) > 1
    assert len(doc.layers[2]) > 1
    assert ("test", "val1") in doc.layers[1].metadata.items()
    assert ("test1", "val1") in doc.layers[1].metadata.items()
    assert ("test", "val2") in doc.layers[2].metadata.items()
    assert ("test2", "val2") in doc.layers[2].metadata.items()
