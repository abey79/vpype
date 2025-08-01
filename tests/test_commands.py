from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import pytest

import vpype as vp
import vpype_cli
from vpype_cli import DebugData, cli, execute, global_processor

from .utils import TESTS_DIRECTORY, execute_single_line

CM = 96 / 2.54

EXAMPLE_SVG = TESTS_DIRECTORY / "data" / "test_svg" / "svg_width_height" / "percent_size.svg"
EXAMPLE_SVG_DIR = TESTS_DIRECTORY / "data" / "test_svg" / "misc"


@dataclass
class Command:
    command: str
    exit_code_no_layer: int = 0
    exit_code_one_layer: int = 0
    exit_code_two_layers: int = 0
    preserves_metadata: bool = True
    keeps_page_size: bool = True


MINIMAL_COMMANDS = [
    Command("begin grid 2 2 line 0 0 10 10 end", keeps_page_size=False),
    Command("begin grid 0 0 line 0 0 10 10 end"),  # doesn't update page size
    Command("begin repeat 2 line 0 0 10 10 end"),
    Command("grid 2 2 line 0 0 10 10 end", keeps_page_size=False),  # implicit `begin`
    Command("grid -k 2 2 line 0 0 10 10 end"),  # keep page size option
    Command("grid 2 2 repeat 2 random -n 1 end end", keeps_page_size=False),  # nested block
    Command("frame"),
    Command("random"),
    Command("line 0 0 1 1"),
    Command("rect 0 0 1 1"),
    Command("arc 0 0 1 1 0 90"),
    Command("circle 0 0 1"),
    Command("ellipse 0 0 2 4"),
    Command(f"read '{EXAMPLE_SVG}'", preserves_metadata=False),
    Command(f"read -s '{EXAMPLE_SVG}'", preserves_metadata=False),
    Command(f"read -m '{EXAMPLE_SVG}'", preserves_metadata=False),
    Command(f"read -a stroke '{EXAMPLE_SVG}'", preserves_metadata=False),
    Command("write -f svg -"),
    Command("write -f hpgl -d hp7475a -p a4 -"),
    Command("rotate 0"),
    Command("scale 1 1"),
    Command("scaleto 10cm 10cm"),
    Command("skew 0 0"),
    Command("translate 0 0"),
    Command("crop 0 0 1 1"),
    Command("lineshuffle"),
    Command("linesort"),
    Command("linesort --two-opt"),
    Command("random linesort"),  # make sure there is something sort
    Command("linemerge"),
    Command("linesimplify"),
    Command("multipass"),
    Command("reloop"),
    Command("lmove 1 new", preserves_metadata=False),
    Command("lmove --prob 0. 1 new"),
    Command("lcopy 1 new"),
    Command("ldelete 1", preserves_metadata=False),
    Command("ldelete --prob 0 1"),
    Command(
        "lswap 1 2", preserves_metadata=False, exit_code_no_layer=2, exit_code_one_layer=2
    ),
    Command("lswap --prob 0.5 1 2", exit_code_no_layer=2, exit_code_one_layer=2),
    Command("lreverse 1"),
    Command("line 0 0 10 10 lreverse 1"),
    Command("random -l1 random -l2 lswap 1 2", preserves_metadata=False),
    Command("random -l1 -n100 random -l2 -n100 lswap --prob 0.5 1 2"),
    Command("trim 1mm 1mm"),
    Command("splitall"),
    Command("filter --min-length 1mm"),
    Command("pagesize 10inx15in", keeps_page_size=False),
    Command("stat"),
    Command("snap 1"),
    Command("reverse"),
    Command("reverse --flip"),
    Command("layout a4", keeps_page_size=False),
    Command("layout -m 3cm a4", keeps_page_size=False),
    Command(
        "layout --no-bbox a4",
        keeps_page_size=False,
        exit_code_one_layer=2,
        exit_code_no_layer=2,
        exit_code_two_layers=2,
    ),
    Command("squiggles"),
    Command("text 'hello wold'"),
    Command("penwidth 0.15mm", preserves_metadata=False),
    Command("color red", preserves_metadata=False),
    Command("alpha 0.5", preserves_metadata=False),
    Command("name my_name", preserves_metadata=False),
    Command("propset -g prop:global hello", preserves_metadata=False),
    Command("propset -l 1 prop:local hello", preserves_metadata=False),
    Command("propget -g prop:global"),
    Command("propget -l 1 prop:global"),
    Command("proplist -g"),
    Command("proplist -l 1"),
    Command("propdel -g prop:global", preserves_metadata=False),
    Command("propdel -l 1 prop:layer", preserves_metadata=False),
    Command("propclear -g", preserves_metadata=False, keeps_page_size=False),
    Command("propclear -l 1", preserves_metadata=False),
    Command(
        f"forfile '{EXAMPLE_SVG_DIR / '*.svg'}' text -p 0 %_i*cm% '%_i%/%_n%: %_name%' end"
    ),
    Command("eval x=2 eval %y=3 eval z=4% eval %w=5%"),
    Command("forlayer text '%_lid% (%_i%/%_n%): %_name%' end"),
    Command("pagerotate", keeps_page_size=False),
    Command("splitdist 1cm"),
    Command("circlecrop 0 0 1cm"),
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
    @global_processor
    def assertdoc(document):
        assert document is not None
        assert type(document) is vp.Document

    result = runner.invoke(cli, "line 0 0 10 10 " + cmd.command + " assertdoc")
    assert result.exit_code == cmd.exit_code_one_layer


@pytest.mark.parametrize("cmd", MINIMAL_COMMANDS)
def test_commands_keeps_page_size(runner, cmd):
    """No command shall "forget" the current page size, unless its `pagesize` of course."""

    args = cmd.command

    if not cmd.keeps_page_size:
        pytest.skip(f"command {args.split()[0]} fail this test by design")

    page_size = None

    @cli.command()
    @global_processor
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

    doc.layers[1].set_property(vp.METADATA_FIELD_NAME, "test_name")
    doc.layers[2].set_property(vp.METADATA_FIELD_PEN_WIDTH, 0.15)

    new_doc = execute(
        "line -l1 0 0 10 10 name -l1 hello line -l2 20 20 30 30 penwidth -l2 0.15 "
        + cmd.command
    )

    assert new_doc.layers[1].metadata == {vp.METADATA_FIELD_NAME: "hello"}
    assert new_doc.layers[2].metadata == {vp.METADATA_FIELD_PEN_WIDTH: 0.15}


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
        "linesort --no-flip dbsample dbdump",
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
        ("tight", (0, 0, 1, 1)),
        ("-m 1cm tight", (1, 1, 2, 2)),
    ],
)
def test_layout(args, expected_bounds):
    doc = vpype_cli.execute(f"random -n 100 rect 0 0 1cm 1cm layout {args}")
    assert doc.bounds() == pytest.approx([i * CM for i in expected_bounds])


def test_layout_tight():
    """`layout tight` fits tightly the page size around the geometry, accommodating for margins
    if provided"""

    doc = vpype_cli.execute("rect 5cm 10cm 2cm 3cm layout tight")
    assert doc.bounds() == pytest.approx((0, 0, 2 * CM, 3 * CM))
    assert doc.page_size == pytest.approx((2 * CM, 3 * CM))

    doc = vpype_cli.execute("rect 5cm 10cm 2cm 3cm layout -m 1cm tight")
    assert doc.bounds() == pytest.approx((CM, CM, 3 * CM, 4 * CM))
    assert doc.page_size == pytest.approx((4 * CM, 5 * CM))


def test_layout_no_bbox():
    doc = vpype_cli.execute("pagesize 10x10cm rect 0 0 1cm 1cm layout --no-bbox 30x30cm")
    assert doc.page_size == pytest.approx((30 * CM, 30 * CM))
    assert doc.bounds() == pytest.approx((10 * CM, 10 * CM, 11 * CM, 11 * CM))


def test_layout_empty():
    """page size is set to size provided to layout, unless it's tight, in which case it is
    unchanged"""

    doc = vpype_cli.execute("layout 10x12cm")
    assert doc.page_size == pytest.approx((10 * CM, 12 * CM))

    doc = vpype_cli.execute("pagesize a3 layout 10x12cm")
    assert doc.page_size == pytest.approx((10 * CM, 12 * CM))

    doc = vpype_cli.execute("layout tight")
    assert doc.page_size is None

    doc = vpype_cli.execute("pagesize 10x12cm layout tight")
    assert doc.page_size == pytest.approx((10 * CM, 12 * CM))


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


@pytest.mark.parametrize(
    ("cmd", "expected_output"),
    [
        ("propset -l1 prop val", ""),
        (
            "random propset -l1 -t int prop 1cm propget -l1 prop",
            "layer 1 property prop: (int) 37",
        ),
        ("propset -g prop val", ""),
        ("propget -g prop", "global property prop: n/a"),
        ("line 0 0 1 1 propget -l1 prop", "layer 1 property prop: n/a"),
        (
            "line 0 0 1 1 propset -l1 -t int prop 10 propget -l1 prop",
            "layer 1 property prop: (int) 10",
        ),
        (
            "line 0 0 1 1 propset -l1 -t str prop hello propget -l1 prop",
            "layer 1 property prop: (str) hello",
        ),
        (
            "line 0 0 1 1 propset -l1 -t float prop 10.2 propget -l1 prop",
            "layer 1 property prop: (float) 10.2",
        ),
        (
            "line 0 0 1 1 propset -l1 -t color prop red propget -l1 prop",
            "layer 1 property prop: (color) #ff0000",
        ),
        (
            "pens rgb proplist -l all",
            "listing 2 properties for layer 1\n"
            "  vp_color: (color) #ff0000\n"
            "  vp_name: (str) red\n"
            "listing 2 properties for layer 2\n"
            "  vp_color: (color) #008000\n"
            "  vp_name: (str) green\n"
            "listing 2 properties for layer 3\n"
            "  vp_color: (color) #0000ff\n"
            "  vp_name: (str) blue",
        ),
        (
            "pens rgb propdel -l1 vp_color proplist -l all",
            "listing 1 properties for layer 1\n  vp_name: (str) red\n"
            "listing 2 properties for layer 2\n"
            "  vp_color: (color) #008000\n"
            "  vp_name: (str) green\n"
            "listing 2 properties for layer 3\n"
            "  vp_color: (color) #0000ff\n"
            "  vp_name: (str) blue",
        ),
        (
            "pens rgb propdel -l all vp_color proplist -l all",
            "listing 1 properties for layer 1\n  vp_name: (str) red\n"
            "listing 1 properties for layer 2\n  vp_name: (str) green\n"
            "listing 1 properties for layer 3\n  vp_name: (str) blue",
        ),
        (
            "pens rgb propdel -l all vp_color proplist -l 2",
            "listing 1 properties for layer 2\n  vp_name: (str) green",
        ),
        (
            "pens rgb propclear -l all proplist",
            "listing 0 properties for layer 1\n"
            "listing 0 properties for layer 2\n"
            "listing 0 properties for layer 3\n",
        ),
        (
            "pagesize 400x1200 proplist -g",
            "listing 1 global properties\n  vp_page_size: (tuple) (400.0, 1200.0)",
        ),
        (
            "pagesize 400x1200 propdel -g vp_page_size proplist -g",
            "listing 0 global properties",
        ),
        ("propset -g -t int prop 10 propget -g prop", "global property prop: (int) 10"),
        (
            "propset -g -t float prop 11.2 propget -g prop",
            "global property prop: (float) 11.2",
        ),
        ("propset -g -t str prop hello propget -g prop", "global property prop: (str) hello"),
        (
            "propset -g -t color prop blue propget -g prop",
            "global property prop: (color) #0000ff",
        ),
        (
            "pagesize a4 propset -g prop val propclear -g proplist -g",
            "listing 0 global properties",
        ),
    ],
)
def test_property_commands(runner, cmd, expected_output):
    res = runner.invoke(cli, cmd)
    assert res.exit_code == 0
    assert res.stdout.strip() == expected_output.strip()


def test_pagerotate():
    doc = vpype_cli.execute("random pagesize a4 pagerotate")
    assert doc.page_size == pytest.approx((1122.5196850393702, 793.7007874015749))

    doc = vpype_cli.execute("random pagesize a4 pagerotate -cw")
    assert doc.page_size == pytest.approx((1122.5196850393702, 793.7007874015749))


def test_pagerotate_error(caplog):
    doc = vpype_cli.execute("random pagerotate")
    assert doc.page_size is None
    assert "page size is not defined, page not rotated" in caplog.text


def test_pagerotate_orientation():
    doc = vpype_cli.execute("random pagesize a4 pagerotate -o landscape")
    assert doc.page_size == pytest.approx((1122.5196850393702, 793.7007874015749))

    doc = vpype_cli.execute("random pagesize a4 pagerotate -cw -o landscape")
    assert doc.page_size == pytest.approx((1122.5196850393702, 793.7007874015749))

    doc = vpype_cli.execute("random pagesize --landscape a4 pagerotate -o portrait")
    assert doc.page_size == pytest.approx((793.7007874015749, 1122.5196850393702))

    doc = vpype_cli.execute("random pagesize --landscape a4 pagerotate -cw -o portrait")
    assert doc.page_size == pytest.approx((793.7007874015749, 1122.5196850393702))


def test_pagerotate_orientation_error():
    doc = vpype_cli.execute("random pagesize a4 pagerotate -o portrait")
    assert doc.page_size == pytest.approx((793.7007874015749, 1122.5196850393702))

    doc = vpype_cli.execute("random pagesize --landscape a4 pagerotate -o landscape")
    assert doc.page_size == pytest.approx((1122.5196850393702, 793.7007874015749))


def test_help(runner):
    res = runner.invoke(cli, "--help")

    assert res.exit_code == 0
    assert "Execute the sequence of commands passed in argument." in res.stdout
    assert "multipass" in res.stdout


def test_alpha():
    assert vpype_cli.execute("random alpha 0.5").layers[1].property(
        vp.METADATA_FIELD_COLOR
    ) == vp.Color(0, 0, 0, 127)

    assert vpype_cli.execute("random alpha 1").layers[1].property(
        vp.METADATA_FIELD_COLOR
    ) == vp.Color(0, 0, 0, 255)

    assert vpype_cli.execute("random alpha 0").layers[1].property(
        vp.METADATA_FIELD_COLOR
    ) == vp.Color(0, 0, 0, 0)

    assert vpype_cli.execute("random color red alpha 0.5").layers[1].property(
        vp.METADATA_FIELD_COLOR
    ) == vp.Color(255, 0, 0, 127)


@pytest.mark.parametrize(
    ("lines", "expected_layer_count"),
    [
        ("line 0 0 0 5cm", 1),
        ("line 0 0 0.5cm 0 line 1cm 1cm 1.5cm 1cm", 1),
        ("line 0 0 0 2cm line 0 2cm 2cm 2cm", 2),
        ("line 0 0 0 2cm line -l 2 0 2cm 2cm 2cm", 2),
        ("line 0 0 0 2cm line -l 2 0 2cm 2cm 2cm line -l 2 0 4cm 2cm 4cm", 3),
    ],
)
def test_splitdist(lines, expected_layer_count):
    doc = vpype_cli.execute(lines + " splitdist 1cm")

    assert len(doc.layers) == expected_layer_count


def test_splitdist_ignore_layer():
    doc = vpype_cli.execute("line 0 0 0 2cm line -l 2 0 2cm 2cm 2cm splitdist -l 1 1cm")

    assert len(doc.layers) == 2


def test_splitdist_preserves_metadata():
    doc = vpype_cli.execute(
        "random -n 200 -a 10cm 10cm name hello color red penwidth 5mm splitdist 10cm"
    )

    for layer in doc.layers.values():
        assert layer.metadata[vp.METADATA_FIELD_NAME] == "hello"
        assert layer.metadata[vp.METADATA_FIELD_COLOR] == vp.Color("red")
        assert layer.metadata[vp.METADATA_FIELD_PEN_WIDTH] == pytest.approx(
            vp.convert_length("5mm")
        )
