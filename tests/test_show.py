import matplotlib.pyplot as plt
import pytest

from vpype_cli import cli

old_show = plt.show


@pytest.mark.mpl_image_compare
@pytest.mark.parametrize(
    "commands",
    [
        "rect 1cm 1cm 10cm 15cm",
        "-s 0 random -a 10cm 10cm -n 100",
        "begin grid -o 3cm 3cm 5 5 circle 0 0 5cm end",
        "circle 15cm 10cm 10cm pagesize -l a4",
    ],
)
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
def test_show(runner, monkeypatch, commands, params):
    fig = None

    def new_show():
        nonlocal fig
        fig = plt.gcf()
        print(fig)

    monkeypatch.setattr(plt, "show", new_show)

    res = runner.invoke(cli, f"{commands} show {params}")

    assert res.exit_code == 0
    return fig
