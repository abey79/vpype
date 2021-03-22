import itertools

import numpy as np
import pytest

import vpype as vp
from vpype_cli import DebugData, cli, execute

from .utils import TESTS_DIRECTORY, execute_single_line

CM = 96 / 2.54

EXAMPLE_SVG = TESTS_DIRECTORY / "data" / "test_svg" / "svg_width_height" / "percent_size.svg"

MINIMAL_COMMANDS = [
    "begin grid 2 2 line 0 0 10 10 end",
    "begin repeat 2 line 0 0 10 10 end",
    "frame",
    "random",
    "line 0 0 1 1",
    "rect 0 0 1 1",
    "arc 0 0 1 1 0 90",
    "circle 0 0 1",
    "ellipse 0 0 2 4",
    f"read '{EXAMPLE_SVG}'",
    f"read -m '{EXAMPLE_SVG}'",
    "write -f svg -",
    "write -f hpgl -d hp7475a -p a4 -",
    "rotate 0",
    "scale 1 1",
    "scaleto 10cm 10cm",
    "skew 0 0",
    "translate 0 0",
    "crop 0 0 1 1",
    "linesort",
    "linemerge",
    "linesimplify",
    "multipass",
    "reloop",
    "lmove 1 new",
    "lcopy 1 new",
    "ldelete 1",
    "trim 1mm 1mm",
    "splitall",
    "filter --min-length 1mm",
    "pagesize 10inx15in",
    "stat",
    "snap 1",
    "reverse",
    "layout a4",
    "squiggles",
    "text 'hello wold'",
]

# noinspection SpellCheckingInspection
LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
)


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_empty_geometry(runner, args):
    result = runner.invoke(cli, args)
    assert result.exit_code == 0


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_single_line(runner, args):
    result = runner.invoke(cli, "line 0 0 10 10 " + args)
    assert result.exit_code == 0


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_degenerate_line(runner, args):
    result = runner.invoke(cli, "line 0 0 0 0 " + args)
    assert result.exit_code == 0


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_random_input(runner, args):
    result = runner.invoke(cli, "random -n 100 " + args)
    assert result.exit_code == 0


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_execute(args):
    execute(args)


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_must_return_document(runner, args):
    @cli.command()
    @vp.global_processor
    def assertdoc(document):
        assert document is not None
        assert type(document) is vp.Document

    result = runner.invoke(cli, "line 0 0 10 10 " + args + " assertdoc")
    assert result.exit_code == 0


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_keeps_page_size(runner, args):
    """No command shall "forget" the current page size, unless its `pagesize` of course."""
    if args.split()[0] in ["pagesize", "layout"]:
        return

    page_size = None

    @cli.command()
    @vp.global_processor
    def getpagesize(doc: vp.Document) -> vp.Document:
        nonlocal page_size
        page_size = doc.page_size
        return doc

    result = runner.invoke(cli, "pagesize --landscape 5432x4321 " + args + " getpagesize")
    assert result.exit_code == 0
    assert page_size == (5432, 4321)


def test_frame(runner):
    result = runner.invoke(
        cli, "random -n 100 -a 10cm 10cm dbsample frame dbsample frame -o 1cm dbsample dbdump"
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
    assert np.isclose(data1.bounds[2] - data1.bounds[0], data2.bounds[2] - data2.bounds[0])
    assert np.isclose(data1.bounds[3] - data1.bounds[1], data2.bounds[3] - data2.bounds[1])


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


def test_scaleto(runner):
    res = runner.invoke(
        cli, "rect 0 0 10cm 5cm dbsample scaleto -o 0 0 20cm 20cm dbsample dbdump"
    )
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(0, 0, 10 * CM, 5 * CM)
    assert data[1].bounds_within(0, 0, 20 * CM, 10 * CM)


def test_scaleto_fit(runner):
    res = runner.invoke(
        cli,
        "rect 0 0 10cm 5cm dbsample scaleto --fit-dimensions -o 0 0 20cm 20cm dbsample dbdump",
    )
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(0, 0, 10 * CM, 5 * CM)
    assert data[1].bounds_within(0, 0, 20 * CM, 20 * CM)
    assert not data[1].bounds_within(0, 0, 20 * CM, 10 * CM)


def test_crop_cm(runner):
    res = runner.invoke(cli, "random -n 100 -a 10cm 10cm crop 2cm 2cm 8cm 8cm dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(2 * CM, 2 * CM, 8 * CM, 8 * CM)
    assert data[0].count <= 100


def test_crop(runner):
    res = runner.invoke(cli, "random -n 100 -a 10 10 crop 2 2 6 6 dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(2, 2, 6, 6)
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


def test_crop_empty(runner):
    res = runner.invoke(cli, "random -a 10cm 10cm -n 1000 crop 5cm 5cm 0 1cm dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].count == 0


def test_crop_empty2(runner):
    res = runner.invoke(cli, "random -a 10cm 10cm -n 1000 crop 5cm 5cm 0 0 dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].count == 0


def test_trim(runner):
    res = runner.invoke(cli, "random -a 10cm 10cm -n 1000 trim 1cm 2cm dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].bounds_within(CM, 2 * CM, 9 * CM, 8 * CM)


def test_trim_large_margins(runner):
    res = runner.invoke(cli, "random -a 10cm 10cm -n 1000 trim 10cm 2cm dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].count == 0


def test_trim_large_margins2(runner):
    res = runner.invoke(cli, "random -a 10cm 10cm -n 1000 trim 10cm 20cm dbsample dbdump")
    data = DebugData.load(res.output)
    assert res.exit_code == 0
    assert data[0].count == 0


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
        " ".join(s)
        for s in itertools.permutations(
            ["line 0 0 0 10", "line 0 10 10 10", "line 0 0 10 0", "line 10 0 10 10"]
        )
    ],
)
def test_linesort(runner, lines):
    res = runner.invoke(cli, f"{lines} linesort dbsample dbdump")
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


def test_snap():
    line = np.array([0.2, 0.8 + 1.1j, 0.5 + 2.5j])
    lc = execute_single_line("snap 1", line)

    assert len(lc) == 1
    assert np.all(lc[0] == np.array([0, 1 + 1j, 2j]))


def test_filter():
    assert len(execute_single_line("filter --min-length 10", [0, 15])) == 1
    assert len(execute_single_line("filter --min-length 10", [0, 10])) == 1
    assert len(execute_single_line("filter --min-length 10", [0, 5])) == 0
    assert len(execute_single_line("filter --max-length 10", [0, 15])) == 0
    assert len(execute_single_line("filter --max-length 10", [0, 10])) == 1
    assert len(execute_single_line("filter --max-length 10", [0, 5])) == 1
    assert len(execute_single_line("filter --closed", [0, 5, 5j, 0])) == 1
    assert len(execute_single_line("filter --closed", [0, 5, 5j])) == 0
    assert len(execute_single_line("filter --not-closed", [0, 5, 5j, 0])) == 0
    assert len(execute_single_line("filter --not-closed", [0, 5, 5j])) == 1


@pytest.mark.parametrize("pitch", [0.1, 1, 5, 10, 20, 50, 100, 200, 500])
def test_snap_no_duplicate(pitch: float):
    """Snap should return no duplicated points and reject lines that degenerate into a single
    point."""
    lc = execute_single_line(f"snap {pitch}", vp.circle(0, 0, 100, quantization=1))

    if len(lc) == 1:
        assert len(lc[0]) > 1
        assert np.all(lc[0][:-1] != lc[0][1:])
    else:
        assert len(lc) == 0


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ([0, 1 + 2j, 2], [[0, 1 + 2j], [1 + 2j, 2]]),
        ([0, 1 + 2j, 1 + 2j, 2], [[0, 1 + 2j], [1 + 2j, 2]]),
    ],
)
def test_splitall_filter_duplicates(line, expected):
    lc = execute_single_line("splitall", line)

    assert np.all(l == el for l, el in zip(lc, expected))


@pytest.mark.parametrize(
    ("args", "expected_bounds"),
    [
        ("10x10cm", (4.5, 4.5, 5.5, 5.5)),
        ("-h left -v top a4", (0, 0, 1, 1)),
        ("-m 3cm -h left -v top 10x20cm", (3, 3, 7, 7)),
        ("-m 3cm -v bottom 10x20cm", (3, 13, 7, 17)),
        ("-m 3cm -h right 20x10cm", (3, 8, 7, 12)),
        ("-m 3cm -h right 10x20cm", (3, 8, 7, 12)),
        ("-m 3cm -h right -l 20x10cm", (13, 3, 17, 7)),
        ("-m 3cm -h right -l 10x20cm", (13, 3, 17, 7)),
    ],
)
def test_layout(runner, args, expected_bounds):
    document = vp.Document()

    @cli.command()
    @vp.global_processor
    def sample(doc: vp.Document):
        nonlocal document
        document = doc

    res = runner.invoke(cli, f"random -n 100 rect 0 0 1cm 1cm layout {args} sample")
    assert res.exit_code == 0
    bounds = document.bounds()
    assert bounds is not None
    for act, exp in zip(bounds, expected_bounds):
        assert act == pytest.approx(exp * CM)


@pytest.mark.parametrize("font_name", vp.FONT_NAMES)
@pytest.mark.parametrize("options", ["", "-j"])
def test_text_command_wrap(font_name, options):
    doc = execute(f"text -f {font_name} -w 350 {options} '{LOREM}'")

    bounds = doc[1].bounds()
    assert bounds is not None
    assert -2.0 <= bounds[0] <= 3.0
    if options == "-j":
        assert bounds[2] == pytest.approx(350.0)
    else:
        assert bounds[2] <= 350.0


def test_text_command_empty():
    doc = execute("text ''")
    assert doc.is_empty()
