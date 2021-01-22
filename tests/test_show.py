import matplotlib.pyplot as plt
import pytest

import vpype_viewer
from vpype_cli import cli

TEST_COMMANDS = [
    "rect 1cm 1cm 10cm 15cm",
    "-s 0 random -a 10cm 10cm -n 100",
    "begin grid -o 3cm 3cm 5 5 circle 0 0 5cm end",
    "circle 15cm 10cm 10cm pagesize -l a4",
]


@pytest.mark.mpl_image_compare
@pytest.mark.parametrize("commands", TEST_COMMANDS)
@pytest.mark.parametrize(
    "params",
    [
        "",
        "-ah",
        "-ag",
        "-ag -u cm",
        "-p",
        "-d",
        "-h",
        "-c",
    ],
)
def test_showmpl(runner, monkeypatch, commands, params):
    fig = None

    def new_show():
        nonlocal fig
        fig = plt.gcf()
        print(fig)

    monkeypatch.setattr(plt, "show", new_show)

    res = runner.invoke(cli, f"{commands} showmpl {params}")

    assert res.exit_code == 0
    return fig


@pytest.mark.parametrize("commands", TEST_COMMANDS)
@pytest.mark.parametrize(
    "params",
    [
        "",
        "-o",
        "-c",
        "-p",
        "-d",
    ],
)
def test_show(assert_image_similarity, runner, monkeypatch, commands, params):
    image = None

    def new_show(*args, **kwargs):
        nonlocal image
        image = vpype_viewer.render_image(*args, **kwargs)

    monkeypatch.setattr(vpype_viewer, "show", new_show)

    res = runner.invoke(cli, f"{commands} show {params}")

    assert res.exit_code == 0
    assert_image_similarity(image)
