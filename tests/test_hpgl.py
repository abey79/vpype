import sys

import pytest

import vpype as vp
from vpype_cli import cli

HPGL_TEST_CASES = [
    ("line 2 3 6 4", "--absolute -d simple -p simple", "IN;DF;SP1;PU2,3;PD6,4;PU;SP0;IN;"),
    ("line 2 3 6 4", "-d simple -p simple", "IN;DF;SP1;PU2,3;PR;PD4,1;PA;PU;SP0;IN;"),
    ("line 2 3 50 3", "--absolute -d simple -p simple", "IN;DF;SP1;PU2,3;PD10,3;PU;SP0;IN;"),
    ("line 2 3 6 4", "--absolute -d simple -p aka_simple", "IN;DF;SP1;PU2,3;PD6,4;PU;SP0;IN;"),
    (
        "line 2 3 6 4",
        "--absolute -d simple -p simple_ps10",
        "IN;DF;PS10;SP1;PU2,3;PD6,4;PU;SP0;IN;",
    ),
    (
        "line 2 3 6 4",
        "-d simple -p simple_ps10",
        "IN;DF;PS10;SP1;PU2,3;PR;PD4,1;PA;PU;SP0;IN;",
    ),
    (
        "line 2 3 6 4 line -l 2 4 5 2 3",
        "--absolute -d simple -p simple",
        "IN;DF;SP1;PU2,3;PD6,4;PU;SP2;PU4,5;PD2,3;PU;SP0;IN;",
    ),
    (
        "line 2 3 6 4",
        "--absolute -d simple -p simple_landscape",
        "IN;DF;SP1;PU3,8;PD4,4;PU;SP0;IN;",
    ),
    (
        "line 2 3 6 4",
        "--absolute -d simple -p simple_y_up",
        "IN;DF;SP1;PU2,12;PD6,11;PU;SP0;IN;",
    ),
    (
        "line 2 3 6 4",
        "--absolute -d simple -p simple_rotate_180",
        "IN;DF;SP1;PU8,12;PD4,11;PU;SP0;IN;",
    ),
    (
        "line 2 3 6 4",
        "--absolute -d simple -p simple_final_pu",
        "IN;DF;SP1;PU2,3;PD6,4;PU0,0;SP0;IN;",
    ),
    ("line 3 5 4 6", "--absolute -d double -p simple", "IN;DF;SP1;PU6,10;PD8,12;PU;SP0;IN;"),
    (
        "line 1 1 2 4",
        "--absolute -d simple -p simple_botleft",
        "IN;DF;SP1;PU0,13;PD1,10;PU;SP0;IN;",
    ),
    (
        "line 1 1 2 4 pagesize 10x15",
        "--absolute -d simple -p simple_flex_portrait",
        "IN;DF;SP1;PU0,13;PD1,10;PU;SP0;IN;",
    ),
    (
        "line 1 1 2 4 pagesize 10x15",
        "--absolute -d simple -p simple_flex_portrait_implicit",
        "IN;DF;SP1;PU0,13;PD1,10;PU;SP0;IN;",
    ),
    (
        "line 1 1 2 4 pagesize 10x15",
        "--absolute -d simple -p simple_flex_landscape",
        "IN;DF;SP1;PU0,0;PD3,1;PU;SP0;IN;",
    ),
    (
        "line 0 0 2 3 line -l2 5 5 2 3",
        "--absolute -d simple -p simple",
        "IN;DF;SP1;PU0,0;PD2,3;PU;SP2;PU5,5;PD2,3;PU;SP0;IN;",
    ),
    (
        "line 0 0 2 3 line -l2 5 5 2 3",
        "-d simple -p simple",
        "IN;DF;SP1;PU0,0;PR;PD2,3;PU;SP2;PU3,2;PD-3,-2;PA;PU;SP0;IN;",
    ),
]


@pytest.fixture
def simple_printer_config(config_file_factory):
    return config_file_factory(
        """
        [device.simple]
        name = "simple"
        plotter_unit_length = 1
        pen_count = 2
        
        [[device.simple.paper]]
        name = "simple"
        aka_names = ["aka_simple"]
        paper_size = [10, 15]
        x_range = [0, 10]
        y_range = [0, 15]
        y_axis_up = false
        origin_location = [0, 0]
        
        [[device.simple.paper]]
        name = "simple_landscape"
        paper_size = [15, 10]
        x_range = [0, 15]
        y_range = [0, 10]
        y_axis_up = false
        origin_location = [0, 0]
        
        [[device.simple.paper]]
        name = "simple_y_up"
        paper_size = [10, 15]
        x_range = [0, 10]
        y_range = [0, 15]
        y_axis_up = true
        origin_location = [0, 15]
        
        [[device.simple.paper]]
        name = "simple_ps10"
        paper_size = [10, 15]
        x_range = [0, 10]
        y_range = [0, 15]
        y_axis_up = false
        origin_location = [0, 0]
        set_ps = 10
        
        [[device.simple.paper]]
        name = "simple_rotate_180"
        paper_size = [10, 15]
        x_range = [0, 10]
        y_range = [0, 15]
        y_axis_up = false
        origin_location = [0, 0]
        rotate_180 = true
        
        [[device.simple.paper]]
        name = "simple_final_pu"
        paper_size = [10, 15]
        x_range = [0, 10]
        y_range = [0, 15]
        y_axis_up = false
        origin_location = [0, 0]
        final_pu_params = "0,0"
        
        [[device.simple.paper]]
        name = "simple_big"
        paper_size = [20, 30]
        x_range = [0, 20]
        y_range = [0, 30]
        y_axis_up = false
        origin_location = [0, 0]
        
        [[device.simple.paper]]
        name = "simple_botleft"
        paper_size = [10, 15]
        x_range = [0, 8]
        y_range = [0, 13]
        y_axis_up = true
        origin_location = [1, 1]
        origin_location_reference = "botleft"
        
        # test flex paper size
        [[device.simple.paper]]
        name = "simple_flex_portrait"
        paper_orientation = "portrait"
        y_axis_up = true
        origin_location = [1, 1]
        origin_location_reference = "botleft"
        
        [[device.simple.paper]]
        name = "simple_flex_landscape"
        y_axis_up = true
        paper_orientation = "landscape"
        origin_location = [1, 1]
        origin_location_reference = "botleft"
        
        [[device.simple.paper]]
        name = "simple_flex_portrait_implicit"
        y_axis_up = true
        origin_location = [1, 1]
        origin_location_reference = "botleft"
        
        [device.double]
        name = "simple"
        plotter_unit_length = 0.5
        pen_count = 1
        
        [[device.double.paper]]
        name = "simple"
        paper_size = [10, 15]
        x_range = [0, 20]
        y_range = [0, 30]
        y_axis_up = false
        origin_location = [0, 0]
        
        # To test `info`.
        [device.info_device]
        name = "Info Device"
        info = "This is plotter information."
        plotter_unit_length = 0.5
        pen_count = 1
        
        [[device.info_device.paper]]
        name = "simple"
        info = "This is paper information."
        paper_size = [10, 15]
        x_range = [0, 20]
        y_range = [0, 30]
        y_axis_up = false
        origin_location = [0, 0]
        
        # To test failure modes
        [device.defective]
        name = "Defective Device"
        info = "This is plotter information."
        plotter_unit_length = 0.5
        pen_count = 1
        
        [[device.defective.paper]]
        name = "wrong_ref"
        y_axis_up = false
        origin_location = [0, 0]
        origin_location_reference = "middle"
        """
    )


@pytest.mark.parametrize(["commands", "write_opts", "expected"], HPGL_TEST_CASES)
def test_hpgl_simple(runner, simple_printer_config, commands, write_opts, expected):
    # Note: passing a single string to invoke runs it through shlex and removes the windows
    # path back-slash, thus the split.
    res = runner.invoke(
        cli, f"-c {simple_printer_config} {commands} write -f hpgl {write_opts} -".split(" ")
    )

    assert res.exit_code == 0
    assert res.stdout.strip() == expected
    assert res.stderr.strip() == ""


@pytest.mark.parametrize(["commands", "write_opts", "expected"], HPGL_TEST_CASES)
def test_hpgl_file_written(
    runner, simple_printer_config, tmp_path, commands, write_opts, expected
):
    file_path = str(tmp_path / "output.hpgl")

    res = runner.invoke(
        cli,
        f"-c {simple_printer_config} {commands} write -f hpgl {write_opts} {file_path}".split(
            " "
        ),
    )

    assert res.exit_code == 0

    with open(file_path) as fp:
        assert fp.read().strip() == expected


def test_hpgl_info(runner, simple_printer_config):
    res = runner.invoke(
        cli,
        f"-c {simple_printer_config} line 2 3 4 5 "
        "write -f hpgl -d info_device -p simple -".split(" "),
    )

    assert res.stderr == "This is plotter information.\nThis is paper information.\n"


def test_hpgl_info_quiet(runner, simple_printer_config):
    res = runner.invoke(
        cli,
        f"-c {simple_printer_config} line 2 3 4 5 "
        "write -f hpgl -d info_device -p simple --quiet -".split(" "),
    )

    assert res.stderr == ""


@pytest.mark.parametrize(
    ["paper_format", "expected_name"],
    [
        [(10, 15), "simple"],
        [(15, 10), "simple"],
        [(20, 30), "simple_big"],
        [(30, 20), "simple_big"],
        [None, None],
    ],
)
def test_hpgl_paper_config_from_size(simple_printer_config, paper_format, expected_name):
    vp.config_manager.load_config_file(simple_printer_config)
    pc = vp.config_manager.get_plotter_config("simple").paper_config_from_size(paper_format)
    if expected_name is None:
        assert pc is None
    else:
        assert pc.name == expected_name


def test_hpgl_paper_config(simple_printer_config):
    vp.config_manager.load_config_file(simple_printer_config)
    assert vp.config_manager.get_plotter_config("simple").paper_config("simple") is not None
    assert vp.config_manager.get_plotter_config("simple").paper_config("DOESNTEXIST") is None


def test_hpgl_paper_size_inference(runner):
    res = runner.invoke(
        cli, "rect 5cm 5cm 5cm 5cm pagesize a4 write --absolute -f hpgl -d hp7475a -"
    )

    assert res.exit_code == 0
    assert res.stdout.strip() == (
        "IN;DF;PS4;SP1;PU1608,1849;PD3617,1849,3617,3859,1608,3859,1608,1849;PU11040,7721;"
        "SP0;IN;"
    )


def test_hpgl_paper_size_inference_fail(runner):
    res = runner.invoke(cli, "rect 5cm 5cm 5cm 5cm pagesize a6 write -f hpgl -d hp7475a -")

    assert res.exit_code == 0  # this should probably be non-zero, see #131
    assert res.stdout.strip() == ""


def test_hpgl_flex_no_pagesize(simple_printer_config):
    doc = vp.Document()
    doc.add(vp.LineCollection([(1 + 1j, 2 + 4j)]))
    vp.config_manager.load_config_file(simple_printer_config)
    with pytest.raises(ValueError):
        vp.write_hpgl(
            output=sys.stdout,
            document=doc,
            landscape=False,
            center=False,
            device="simple",
            page_size="simple_flex_portrait",
            velocity=None,
        )


def test_hpgl_wrong_ref(simple_printer_config):
    doc = vp.Document()
    doc.add(vp.LineCollection([(1 + 1j, 2 + 4j)]))
    doc.page_size = 10, 15
    vp.config_manager.load_config_file(simple_printer_config)
    with pytest.raises(ValueError):
        vp.write_hpgl(
            output=sys.stdout,
            document=doc,
            landscape=False,
            center=False,
            device="defective",
            page_size="wrong_ref",
            velocity=None,
        )
