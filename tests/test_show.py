import sys

import matplotlib.pyplot as plt
import pytest

import vpype as vp
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

    res = runner.invoke(cli, f"{commands} show --classic {params}")

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


def test_show_must_return_document(runner, monkeypatch):
    @cli.command()
    @vp.global_processor
    def assertdoc(document):
        assert document is not None
        assert type(document) is vp.Document

    # noinspection PyUnusedLocal
    def new_show(*args, **kwargs):
        # don't do anything, in particular, do not block
        pass

    # make sure neither version of the viewer will block
    monkeypatch.setattr(vpype_viewer, "show", new_show)
    monkeypatch.setattr(plt, "show", new_show)

    result = runner.invoke(cli, "line 0 0 10 10 show assertdoc")
    assert result.exit_code == 0

    result = runner.invoke(cli, "line 0 0 10 10 show --classic assertdoc")
    assert result.exit_code == 0


@pytest.fixture()
def fail_pyside2_import(monkeypatch):
    # noinspection PyTypeChecker
    monkeypatch.setitem(sys.modules, "vpype_viewer", None)


@pytest.mark.skip("stalls CI on windows and mac runners")
def test_show_no_pyside(runner, fail_pyside2_import):
    runner.invoke(cli, "-v show")


def test_show_viewer_mpl_absent(runner, monkeypatch, caplog):
    monkeypatch.setattr(sys.modules["vpype_cli.show"], "_vpype_viewer_ok", False)
    # noinspection PyTypeChecker
    monkeypatch.setitem(sys.modules, "matplotlib", None)

    runner.invoke(cli, "show")
    assert "pip install vpype[all]" in caplog.text
