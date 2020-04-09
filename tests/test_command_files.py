import io

import pytest

from vpype_cli.debug import DebugData
from vpype_cli.cli import extract_arguments, cli


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("a b", ["a", "b"]),
        ("a\nb", ["a", "b"]),
        ("\n\n\n\n\na\nb\n\n \n", ["a", "b"]),
        ("   a   \n  b  ", ["a", "b"]),
        ("# comment \na b", ["a", "b"]),
        ("   # comment \na b", ["a", "b"]),
        ("\n\n   # comment \na b", ["a", "b"]),
        ("a 'b c de '", ["a", "b c de "]),
        ('a "b c de "', ["a", "b c de "]),
        ("a  # comment  \n b", ["a", "b"]),
    ],
)
def test_extract_arguments(input_text, expected):
    assert extract_arguments(io.StringIO(input_text)) == expected


def test_include(runner, root_directory):
    result = runner.invoke(cli, f"-I '{root_directory}/tests/data/include.vpy' dbsample dbdump")
    data = DebugData.load(result.output)[0]

    # expecting 4x 100 random lines
    assert result.exit_code == 0
    assert data.count == 400
