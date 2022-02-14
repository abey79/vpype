import pytest

import vpype_cli


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
