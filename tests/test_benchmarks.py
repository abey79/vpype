import pytest

import vpype as vp
import vpype_cli

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
