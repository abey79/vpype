import pytest

from vpype_cli import cli


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
        """
    )


@pytest.mark.parametrize(
    ["commands", "write_opts", "expected"],
    [
        ("line 2 3 6 4", "-d simple -p simple", "IN;DF;SP1;PU2,3;PD6,4;PU;SP0;IN;"),
        ("line 2 3 50 3", "-d simple -p simple", "IN;DF;SP1;PU2,3;PD10,3;PU;SP0;IN;"),
        ("line 2 3 6 4", "-d simple -p aka_simple", "IN;DF;SP1;PU2,3;PD6,4;PU;SP0;IN;"),
        ("line 2 3 6 4", "-d simple -p simple_ps10", "IN;DF;PS10;SP1;PU2,3;PD6,4;PU;SP0;IN;"),
        (
            "line 2 3 6 4 line -l 2 4 5 2 3",
            "-d simple -p simple",
            "IN;DF;SP1;PU2,3;PD6,4;PU;SP2;PU4,5;PD2,3;PU;SP0;IN;",
        ),
        ("line 2 3 6 4", "-d simple -p simple_landscape", "IN;DF;SP1;PU3,8;PD4,4;PU;SP0;IN;"),
        ("line 2 3 6 4", "-d simple -p simple_y_up", "IN;DF;SP1;PU2,12;PD6,11;PU;SP0;IN;"),
        (
            "line 2 3 6 4",
            "-d simple -p simple_rotate_180",
            "IN;DF;SP1;PU8,12;PD4,11;PU;SP0;IN;",
        ),
        (
            "line 2 3 6 4",
            "-d simple -p simple_final_pu",
            "IN;DF;SP1;PU2,3;PD6,4;PU0,0;SP0;IN;",
        ),
        ("line 3 5 4 6", "-d double -p simple", "IN;DF;SP1;PU6,10;PD8,12;PU;SP0;IN;"),
    ],
)
def test_hpgl_simple(runner, simple_printer_config, commands, write_opts, expected):
    # Note: passing a single string to invoke runs it through shlex and removes the windows
    # path back-slash, thus the split.
    res = runner.invoke(
        cli, f"-c {simple_printer_config} {commands} write -f hpgl {write_opts} -".split(" ")
    )

    assert res.stdout.strip() == expected
    assert res.stderr.strip() == ""


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
