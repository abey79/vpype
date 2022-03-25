from __future__ import annotations

import pytest

import vpype as vp
import vpype_cli
from vpype_viewer import ViewMode, render_image

from .utils import TEST_FILE_DIRECTORY


@pytest.mark.parametrize(
    "svg_file",
    [
        "benchmark/300_beziers.svg",
        "benchmark/900_quad_beziers.svg",
        "benchmark/500_circles.svg",
        "benchmark/500_polylines.svg",
        "benchmark/bar_nodef_path_polylines.svg",
    ],
)
def test_benchmark_read(benchmark, svg_file):
    path = str(TEST_FILE_DIRECTORY / svg_file)

    # 0.1 px is about 0.02mm
    doc, w, h = benchmark(vp.read_svg, path, 0.1)

    assert doc is not None


def test_benchmark_linesort(benchmark):
    doc = vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / "benchmark/7k_lines.svg"), 0.1)

    pen_up_length, _, _ = doc.layers[1].pen_up_length()
    cnt = len(doc.layers[1])
    doc = benchmark(vpype_cli.execute, "linesort", doc)

    assert pen_up_length > doc.layers[1].pen_up_length()[0]
    assert cnt == len(doc.layers[1])


def test_benchmark_linemerge(benchmark):
    doc = vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / "benchmark/multi_skull.svg"), 0.1)

    cnt = len(doc.layers[1])
    doc = benchmark(vpype_cli.execute, "linemerge", doc)

    assert len(doc.layers[1]) > 0
    assert cnt > len(doc.layers[1])


@pytest.fixture(scope="session")
def doc_for_render():
    return vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / "benchmark/7k_lines.svg"), 0.1)


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"view_mode": ViewMode.OUTLINE}, id="outline"),
        pytest.param(
            {"view_mode": ViewMode.OUTLINE, "show_points": True}, id="outline_points"
        ),
        pytest.param(
            {"view_mode": ViewMode.OUTLINE, "show_pen_up": True}, id="outline_pen_up"
        ),
        pytest.param({"view_mode": ViewMode.OUTLINE_COLORFUL}, id="outline_colorful"),
        pytest.param({"view_mode": ViewMode.PREVIEW}, id="preview"),
    ],
)
def test_benchmark_viewer(request, benchmark, doc_for_render, kwargs):
    if request.config.getoption("--skip-image-similarity"):
        pytest.skip("viewer benchmark skipped (--skip-image-similarity)")

    # noinspection PyArgumentList
    benchmark(render_image, doc_for_render, size=(4096, 4096), **kwargs)
