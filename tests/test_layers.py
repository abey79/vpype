import pytest

from vpype_cli import cli
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
