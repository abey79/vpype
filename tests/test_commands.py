import itertools
from dataclasses import dataclass

import numpy as np
import pytest

import vpype as vp
from vpype_cli import DebugData, cli, execute

from .utils import TESTS_DIRECTORY, execute_single_line

CM = 96 / 2.54

EXAMPLE_SVG = TESTS_DIRECTORY / "data" / "test_svg" / "svg_width_height" / "percent_size.svg"


@dataclass
class Command:
    command: str
    exit_code_no_layer: int = 0
    exit_code_one_layer: int = 0
    exit_code_two_layers: int = 0
    preserves_metadata: bool = True


MINIMAL_COMMANDS = [
    Command("begin grid 2 2 line 0 0 10 10 end"),
    Command("begin repeat 2 line 0 0 10 10 end"),
    Command("frame"),
    Command("random"),
    Command("line 0 0 1 1"),
    Command("rect 0 0 1 1"),
    Command("arc 0 0 1 1 0 90"),
    Command("circle 0 0 1"),
    Command("ellipse 0 0 2 4"),
    Command(f"read '{EXAMPLE_SVG}'"),
    Command(f"read -m '{EXAMPLE_SVG}'"),
    Command("write -f svg -"),
    Command("write -f hpgl -d hp7475a -p a4 -"),
    Command("rotate 0"),
    Command("scale 1 1"),
    Command("scaleto 10cm 10cm"),
    Command("skew 0 0"),
    Command("translate 0 0"),
    Command("crop 0 0 1 1"),
    Command("linesort"),
    Command("linesort --two-opt"),
    Command("linemerge"),
    Command("linesimplify"),
    Command("multipass"),
    Command("reloop"),
    Command("lmove 1 new", preserves_metadata=False),
    Command("lmove --prob 0. 1 new"),
    Command("lcopy 1 new"),
    Command("ldelete 1", preserves_metadata=False),
    Command("ldelete --prob 0 1"),
    Command("lswap 1 2", exit_code_no_layer=2, exit_code_one_layer=2),
    Command("lreverse 1"),
    Command("line 0 0 10 10 lreverse 1"),
    Command("random -l1 random -l2 lswap 1 2"),
    Command("trim 1mm 1mm"),
    Command("splitall"),
    Command("filter --min-length 1mm"),
    Command("pagesize 10inx15in"),
    Command("stat"),
    Command("snap 1"),
    Command("reverse"),
    Command("layout a4"),
    Command("squiggles"),
    Command("text 'hello wold'"),
    Command("penwidth 0.15mm", preserves_metadata=False),
    Command("metadata vp:name my_name", preserves_metadata=False),
    Command("color red", preserves_metadata=False),
    Command("name my_name", preserves_metadata=False),
]

# noinspection SpellCheckingInspection
LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
)


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_commands_empty_geometry(runner, cmd):
    result = runner.invoke(cli, cmd.command, catch_exceptions=False)
    assert result.exit_code == cmd.exit_code_no_layer


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_commands_single_line(runner, cmd):
    result = runner.invoke(cli, "line 0 0 10 10 " + cmd.command, catch_exceptions=False)
    assert result.exit_code == cmd.exit_code_one_layer


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_commands_degenerate_line(runner, cmd):
    result = runner.invoke(cli, "line 0 0 0 0 " + cmd.command)
    assert result.exit_code == cmd.exit_code_one_layer


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_commands_random_input(runner, cmd):
    result = runner.invoke(cli, "random -n 100 " + cmd.command)
    assert result.exit_code == cmd.exit_code_one_layer


@pytest.mark.parametrize("args", MINIMAL_COMMANDS)
def test_commands_execute(args):
    if args.exit_code_no_layer == 0:
        execute(args.command)


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_commands_must_return_document(runner, cmd):
    @cli.command()
    @vp.global_processor
    def assertdoc(document):
        assert document is not None
        assert type(document) is vp.Document

    result = runner.invoke(cli, "line 0 0 10 10 " + cmd.command + " assertdoc")
    assert result.exit_code == cmd.exit_code_one_layer


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_commands_keeps_page_size(runner, cmd):
    """No command shall "forget" the current page size, unless its `pagesize` of course."""

    args = cmd.command

    if args.split()[0] in ["pagesize", "layout"]:
        return

    page_size = None

    @cli.command()
    @vp.global_processor
    def getpagesize(doc: vp.Document) -> vp.Document:
        nonlocal page_size
        page_size = doc.page_size
        return doc

    result = runner.invoke(
        cli, "random random -l2 pagesize --landscape 5432x4321 " + args + " getpagesize"
    )
    assert result.exit_code == cmd.exit_code_two_layers
    assert page_size == (5432, 4321)


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_command_must_preserve_metadata(cmd):
    if cmd.exit_code_two_layers != 0:
        pytest.skip("command must be compatible with 2-layer pipeline")

    if not cmd.preserves_metadata:
        pytest.skip("command is flagged as not meta-data preserving")

    doc = vp.Document()
    doc.add([], 1)
    doc.add([], 2)

    doc.layers[1].set_property("vp:name", "test_name")
    doc.layers[2].set_property("vp:pen_width", 0.15)

    new_doc = execute(
        "line -l1 0 0 10 10 name -l1 hello line -l2 20 20 30 30 penwidth -l2 0.15 "
        + cmd.command
    )

    assert new_doc.layers[1].metadata == {"vp:name": "hello"}
    assert new_doc.layers[2].metadata == {"vp:pen_width": 0.15}


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


@pytest.mark.parametrize(
    ["opt", "expected"],
    {
        ("--no-flip", 50.0),
        ("", 20.0),
        ("--two-opt", 0.0),
    },
)
def test_linesort_result(runner, opt, expected):
    res = runner.invoke(
        cli,
        "line 20 0 30 0 line 10 0 20 0 line 30 0 40 0 line 0 0 10 0 "
        f"linesort {opt} dbsample dbdump",
    )

    # test situation: four co-linear, single-segment lines in shuffled order
    #
    #    |
    #  0 |  +--4--> +--2--> +--1--> +--3-->
    #    L_____________________________________
    #       0     10      20      30     40

    # the following situation

    data = DebugData.load(res.output)[0]
    assert res.exit_code == 0
    assert data.pen_up_length == pytest.approx(expected)


def test_linesort_reject_bad_opt(runner):
    res = runner.invoke(
        cli,
        "line 0 0 0 10 line 0 10 10 10 line 0 0 10 0 line 10 0 10 10 "
        f"linesort --no-flip dbsample dbdump",
    )

    # in this situation, the greedy optimizer is worse than the starting position, so its
    # result should be discarded

    data = DebugData.load(res.output)[0]
    assert res.exit_code == 0
    assert data.pen_up_length == pytest.approx(14.1, abs=0.1)


def test_linesort_two_opt_debug_output(runner, caplog):
    res = runner.invoke(cli, "-vv -s 0 random -n 100 linesort --two-opt")

    assert res.exit_code == 0
    assert "% done with pass" in caplog.text


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

    assert np.all(line == expected_line for line, expected_line in zip(lc, expected))


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
