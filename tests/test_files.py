"""Run a bunch of tests on the svg collection."""
import os
import pathlib
import re

import pytest

from vpype_cli import cli

TEST_FILE_DIRECTORY = (pathlib.Path(__file__).parent / "data" / "test_svg").absolute()

TEST_FILES = [
    os.path.join(directory, file)
    for directory, _, filenames in os.walk(TEST_FILE_DIRECTORY)
    for file in filenames
    if file.endswith(".svg")
]


@pytest.mark.parametrize("path", TEST_FILES)
def test_read_must_succeed(runner, path):
    runner.invoke(cli, ["read", path])


@pytest.mark.parametrize("path", TEST_FILES)
def test_read_single_layer_must_succeed(runner, path):
    runner.invoke(cli, ["read", "-m", path])


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
        assert False
