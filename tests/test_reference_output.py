from __future__ import annotations

import pytest

import vpype_cli

from .conftest import set_current_directory
from .utils import TESTS_DIRECTORY

TEST_VPY_DIR = TESTS_DIRECTORY / "data" / "test_vpy"


@pytest.mark.parametrize(
    "cmd",
    [
        "line 0 0 10 10 write '{path}'",
        """pens cmyk grid -o 10cm 10cm 2 2 rect -l new 1cm 1cm 8cm 8cm end
        layout a4 write '{path}'""",
    ],
)
def test_reference_output(reference_svg, runner, cmd):
    with reference_svg() as path:
        res = runner.invoke(vpype_cli.cli, cmd.format(path=path))
        assert res.exit_code == 0


@pytest.mark.xfail
def test_reference_output_fail(reference_svg, runner):
    # ensure that SVG comparison indeed fails when it should
    with reference_svg() as path:
        res = runner.invoke(vpype_cli.cli, f"line 0 0 10 0 write '{path}'")
        assert res.exit_code == 0
        path.write_text(path.read_text().replace("</svg>", "<path d='M0,0 l100,0' /></svg>"))


@pytest.mark.parametrize("vpy_path", TEST_VPY_DIR.glob("*.vpy"))
def test_reference_output_vpy(vpy_path, reference_svg, runner):
    with reference_svg() as path, set_current_directory(TEST_VPY_DIR):
        res = runner.invoke(vpype_cli.cli, f"-I '{vpy_path}' write '{path}'")
        assert res.exit_code == 0
