"""Run a bunch of tests on the svg collection."""
import difflib
import os
import re

import numpy as np
import pytest

import vpype as vp
from vpype_cli import DebugData, cli

from .utils import TEST_FILE_DIRECTORY


def _write_svg_file(tmp_path, svg) -> str:
    path = str(tmp_path / "file.svg")
    with open(path, "w") as fp:
        fp.write(svg)

    return path


TEST_FILES = [
    os.path.join(directory, file)
    for directory, _, filenames in os.walk(TEST_FILE_DIRECTORY)
    for file in filenames
    if file.endswith(".svg") and not file.startswith("_")
]


@pytest.mark.parametrize("path", TEST_FILES)
def test_read_must_succeed(runner, path):
    result = runner.invoke(cli, ["read", path])
    assert result.exit_code == 0


@pytest.mark.parametrize("path", TEST_FILES)
def test_read_single_layer_must_succeed(runner, path):
    result = runner.invoke(cli, ["read", "-m", path])
    assert result.exit_code == 0


@pytest.mark.parametrize("path", TEST_FILES)
def test_read_svg_should_not_generate_duplicate_points(path):
    line_collection, _, _ = vp.read_svg(path, quantization=1)
    for line in line_collection:
        assert np.all(line[1:] != line[:-1])


METADATA_PATTERN = re.compile(r"<metadata>.*</metadata>", flags=re.DOTALL)


@pytest.mark.skip(reason="Write is currently not idempotent for some reason")
@pytest.mark.parametrize("path", TEST_FILES)
def test_write_is_idempotent(runner, path, tmp_path):  # pragma: no cover
    output1 = tmp_path / "output1.svg"
    output2 = tmp_path / "output2.svg"
    runner.invoke(cli, ["read", path, "write", str(output1)])
    runner.invoke(cli, ["read", str(output1), "write", str(output2)])

    txt1 = METADATA_PATTERN.sub("", output1.read_text())
    txt2 = METADATA_PATTERN.sub("", output2.read_text())

    # avoid using pytest's assert equality, which is very slow
    if txt1 != txt2:
        for line in difflib.unified_diff(txt1.split("\n"), txt2.split("\n"), lineterm=""):
            print(line)
        assert False


@pytest.mark.parametrize(
    ("svg_content", "line_count"),
    [
        ('<circle cx="500" cy="500" r="40"/>', 1),
        ('<circle cx="500" cy="500" r="40" style="visibility:collapse"/>', 0),
        ('<circle cx="500" cy="500" r="40" style="visibility:hidden"/>', 0),
        ('<circle cx="500" cy="500" r="40" style="display:none"/>', 0),
        ('<g style="visibility: hidden"><circle cx="500" cy="500" r="40"/></g>', 0),
        ('<g style="visibility: collapse"><circle cx="500" cy="500" r="40"/></g>', 0),
        (
            """<g style="visibility: collapse">
            <circle cx="500" cy="500" r="40" style="visibility:visible" />
            </g>""",
            1,
        ),
        (
            """<g style="visibility: hidden">
            <circle cx="500" cy="500" r="40" style="visibility:visible" />
            </g>""",
            1,
        ),
        (
            """<g style="display: none">
            <circle cx="500" cy="500" r="40" style="visibility:visible" />
            </g>""",
            0,
        ),
    ],
)
def test_read_svg_visibility(svg_content, line_count, tmp_path):
    svg = f"""<?xml version="1.0"?>
<svg xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.w3.org/2000/svg"
    width="1000" height="1000">
        {svg_content}
</svg>
"""
    path = _write_svg_file(tmp_path, svg)
    lc, _, _ = vp.read_svg(path, 1.0)
    assert len(lc) == line_count


DEFAULT_WIDTH = 666
DEFAULT_HEIGHT = 999


@pytest.mark.parametrize(
    ["params", "expected"],
    [
        ('width="1200" height="2000"', (1200, 2000)),
        ("", (DEFAULT_WIDTH, DEFAULT_HEIGHT)),
        ('width="1200" height="2000" viewBox="0 0 100 200"', (1200, 2000)),
    ],
)
def test_read_svg_width_height(params, expected, tmp_path):
    path = _write_svg_file(
        tmp_path,
        f"""<?xml version="1.0"?>
<svg xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.w3.org/2000/svg"
   {params}>
</svg>
""",
    )

    lc, width, height = vp.read_svg(
        path, quantization=0.1, default_width=DEFAULT_WIDTH, default_height=DEFAULT_HEIGHT
    )
    assert width == expected[0]
    assert height == expected[1]


def test_read_with_viewbox(tmp_path):
    path = _write_svg_file(
        tmp_path,
        f"""<?xml version="1.0"?>
    <svg xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.w3.org/2000/svg"
       width="100" height="100" viewBox="50 50 10 10">
       <line x1="50" y1="50" x2="60" y2="60" />
    </svg>
    """,
    )

    lc, width, height = vp.read_svg(path, quantization=0.1)
    assert width == 100
    assert height == 100
    assert len(lc) == 1
    assert np.all(np.isclose(lc[0], np.array([0, 100 + 100j])))


def test_read_stdin(runner):
    svg = f"""<?xml version="1.0"?>
    <svg xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.w3.org/2000/svg"
        width="1000" height="1000">
      <circle cx="500" cy="500" r="40"/>      
    </svg>
    """

    result = runner.invoke(cli, "read - dbsample dbdump", input=svg)
    data = DebugData.load(result.output)

    assert result.exit_code == 0
    assert data[0].count == 1
