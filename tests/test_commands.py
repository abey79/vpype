import itertools

import pytest

from vpype import cli
from vpype.debug import DebugData

CM = 96 / 2.54

MINIMAL_COMMANDS = [
    "frame",
    "random",
    "line 0 0 1 1",
    "rect 0 0 1 1",
    "circle 0 0 1",
    "read __ROOT__/examples/bc_template.svg",
    "write -",
    "rotate 0",
    "scale 1 1",
    "skew 0 0",
    "translate 0 0",
    "crop 0 0 1 1",
    "linesort",
    "linemerge",
    "linesimplify",
    "multipass",
]


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_empty_geometry(runner, root_directory, args):
    result = runner.invoke(cli, args.replace("__ROOT__", root_directory))
    assert result.exit_code == 0


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_random_input(runner, root_directory, args):
    result = runner.invoke(
        cli, ["random", "-n", "100", *args.replace("__ROOT__", root_directory).split()]
    )
    assert result.exit_code == 0


def test_frame(runner):
    result = runner.invoke(
        cli,
        (
            "random -n 100 -a 10cm 10cm dbsample frame dbsample frame -o 1cm dbsample dbdump"
        ).split(),
    )
    data = DebugData.load(result.output)

    assert result.exit_code == 0
    assert data[0].bounds == data[1].bounds
    assert data[2].count == data[1].count + 1 == data[0].count + 2


def test_random(runner):
    result = runner.invoke(cli, "random -n 100 -a 10cm 10cm dbsample dbdump")
    data = DebugData.load(result.output)[0]

    assert result.exit_code == 0
    assert data.count == 100
    assert data.bounds_within(0, 0, 10 * CM, 10 * CM)


def test_line(runner):
    result = runner.invoke(cli, "line 0 0 10cm 10cm dbsample dbdump")
    data = DebugData.load(result.output)[0]

    assert result.exit_code == 0
    assert data.count == 1
    assert data.bounds_within(0, 0, 10 * CM, 10 * CM)


def test_rect(runner):
    result = runner.invoke(cli, "rect 0 0 10cm 10cm dbsample dbdump")
    data = DebugData.load(result.output)[0]

    assert result.exit_code == 0
    assert data.count == 1
    assert data.bounds_within(0, 0, 10 * CM, 10 * CM)


def test_circle(runner):
    result = runner.invoke(cli, "circle -q 0.5mm 0 0 10cm dbsample dbdump")
    data = DebugData.load(result.output)[0]

    assert result.exit_code == 0
    assert data.bounds_within(-10 * CM, -10 * CM, 20 * CM, 20 * CM)
    assert data.count == 1


def test_grid(runner):
    result = runner.invoke(
        cli, "begin grid -o 1cm 1cm 2 2 random -n 10 -a 1cm 1cm end dbsample dbdump"
    )
    data = DebugData.load(result.output)

    assert result.exit_code == 0
    assert data[0].count == 40
    assert data[0].bounds_within(0, 0, 2 * CM, 2 * CM)


@pytest.mark.parametrize("args", ["random -n 100 -a 10cm 10cm"])
def test_write_read_identical(runner, args):
    with runner.isolated_filesystem():
        res1 = runner.invoke(cli, args + " dbsample dbdump write output.svg")
        assert res1.exit_code == 0
        res2 = runner.invoke(cli, "read output.svg dbsample dbdump")
        assert res2.exit_code == 0

    data1 = DebugData.load(res1.output)[0]
    data2 = DebugData.load(res2.output)[0]

    assert data1.count == data2.count
    assert (data1.bounds[2] - data1.bounds[0]) == (data2.bounds[2] - data2.bounds[0])
    assert (data1.bounds[3] - data1.bounds[1]) == (data2.bounds[3] - data2.bounds[1])


def test_rotate_360(runner):
    res = runner.invoke(cli, "random -n 100 -a 10cm 10cm dbsample rotate 360 dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0] == data[1]


def test_rotate_origin(runner):
    res = runner.invoke(
        cli, "random -n 100 -a 10cm 10cm dbsample rotate -o 0 0 90 dbsample dbdump"
    )
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[1].bounds_within(-10 * CM, 0, 10 * CM, 10 * CM)


def test_translate(runner):
    res = runner.invoke(
        cli, "random -n 100 -a 10cm 10cm dbsample translate 5cm 5cm dbsample dbdump"
    )
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(0, 0, 10 * CM, 10 * CM)
    assert data[1].bounds_within(5 * CM, 5 * CM, 10 * CM, 10 * CM)


def test_scale_center(runner):
    res = runner.invoke(cli, "random -n 100 -a 10cm 10cm dbsample scale 2 2 dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(0, 0, 10 * CM, 10 * CM)
    assert data[1].bounds_within(-5 * CM, -5 * CM, 20 * CM, 20 * CM)


def test_scale_origin(runner):
    res = runner.invoke(
        cli, "random -n 100 -a 10cm 10cm dbsample scale -o 0 0 2 2 dbsample dbdump"
    )
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(0, 0, 10 * CM, 10 * CM)
    assert data[1].bounds_within(0, 0, 20 * CM, 20 * CM)


def test_crop(runner):
    res = runner.invoke(cli, "random -n 100 -a 10cm 10cm crop 2cm 2cm 8cm 8cm dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(2 * CM, 2 * CM, 8 * CM, 8 * CM)
    assert data[0].count <= 100


def test_crop_line_flush(runner):
    # a line whose end intersect with crop bounds is not kept
    # a line flush with crop bounds is kept
    res = runner.invoke(
        cli, "line 100 0 100 10 line 0 5 100 5 crop 100 0 200 200 dbsample dbdump"
    )
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].count == 1


@pytest.mark.parametrize(
    ("linemerge_args", "expected"),
    [
        ("--no-flip --tolerance 0.05", 3),
        ("--no-flip --tolerance 0.25", 2),
        ("--tolerance 0.05", 3),
        ("--tolerance 0.15", 2),
        ("--tolerance 0.25", 1),
    ],
)
def test_linemerge(runner, linemerge_args, expected):
    res = runner.invoke(
        cli,
        "line 0 0 0 10 line 0 10.2 0 20 line 30 30 0 20.1 "
        f"linemerge {linemerge_args} dbsample dbdump",
    )
    data = DebugData.load(res.output)[0]
    assert res.exit_code == 0
    assert data.count == expected


@pytest.mark.parametrize(
    "lines",
    [
        " ".join(l)
        for l in itertools.permutations(
            ["line 0 0 0 10", "line 0 10 10 10", "line 0 0 10 0", "line 10 0 10 10"]
        )
    ],
)
def test_linesort(runner, lines):
    res = runner.invoke(cli, f"{lines} linesort dbsample dbdump",)
    data = DebugData.load(res.output)[0]
    assert res.exit_code == 0
    assert data.pen_up_length == 0


def test_linesort_no_flip(runner):
    res = runner.invoke(
        cli,
        "line 0 0 0 10 line 0 10 10 10 line 0 0 10 0 line 10 0 10 10 "
        "linesort --no-flip dbsample dbdump",
    )
    # in this situation, an optimal line sorter would have a pen up distance of only 14.14
    # our algo doesnt "see" the second line sequence globally however, thus the added 10 units
    # this would be solved anyway with linemerge
    data = DebugData.load(res.output)[0]
    assert res.exit_code == 0
    assert 24.13 < data.pen_up_length < 24.15
