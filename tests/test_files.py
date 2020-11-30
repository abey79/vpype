"""Run a bunch of tests on the svg collection."""
import difflib
import os
import pathlib
import re

import numpy as np
import pytest

import vpype as vp
from vpype_cli import cli

TEST_FILE_DIRECTORY = (pathlib.Path(__file__).parent / "data" / "test_svg").absolute()

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
def test_write_is_idempotent(runner, path, tmp_path):
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
    path = str(tmp_path / "file.svg")
    with open(path, "w") as fp:
        fp.write(svg)

    lc, _, _ = vp.read_svg(path, 1.0)
    assert len(lc) == line_count
