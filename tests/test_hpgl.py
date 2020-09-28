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
