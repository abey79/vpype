import pytest

import vpype as vp

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
