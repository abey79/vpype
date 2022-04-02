"""Run a bunch of tests on the svg collection."""
from __future__ import annotations

import difflib
import io
import os
import re

import click
import numpy as np
import pytest

import vpype as vp
import vpype_cli
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


@pytest.mark.parametrize(
    ["svg", "expected_metadata"],
    [
        pytest.param(
            """<?xml version="1.0"?><svg>
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
            </svg>""",
            {1: {"svg_fill": "red"}},
            id="lone_line",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg font="#f00">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
            </svg>""",
            {0: {"svg_font": "#f00"}, 1: {"svg_fill": "red"}},
            id="lone_line_svg_attrib",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
            </svg>""",
            {1: {"svg_fill": "red"}},
            id="lone_line_svg_attrib_conflict",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                <line x1="0" y1="0" x2="10" y2="10" fill="green" />
            </svg>""",
            {1: {"svg_fill": None}},
            id="two_line_inconsistent",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                <g id="1">
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                </g>
            </svg>""",
            {1: {"svg_fill": "red"}},
            id="group_1_with_lone_line_svg_attrib_conflict",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <g id="1">
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                </g>
            </svg>""",
            {1: {"svg_fill": "red"}},
            id="group_1_svg_attrib_conflict",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <g id="1">
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                    <line x1="0" y1="0" x2="10" y2="10" fill="green" />
                </g>
            </svg>""",
            {1: {"svg_fill": None}},
            id="inconsistent_group1",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <g id="1">
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                </g>
                <g fill="blue">
                    <circle cx="0" cy="0" r="10" />
                    <circle cx="0" cy="0" r="10" />
                </g>
                <g fill="green">
                    <circle cx="0" cy="0" r="10" fill="#666"/>
                    <circle cx="0" cy="0" r="10" fill="#666" />
                </g>
            </svg>""",
            {0: {"svg_fill": "blue"}, 1: {"svg_fill": "red"}, 2: {}, 3: {"svg_fill": "#666"}},
            id="multi_layer",
        ),
    ],
)
def test_read_multilayer_metadata(tmp_path, svg, expected_metadata):
    path = _write_svg_file(tmp_path, svg)
    doc = vp.read_multilayer_svg(path, quantization=0.1, crop=False)

    for k, v in expected_metadata.get(0, {}).items():
        if v is None:
            assert k not in doc.metadata
        else:
            assert k in doc.metadata
            assert doc.metadata[k] == v

    for lid in doc.layers:
        layer = doc.layers[lid]

        assert lid in expected_metadata
        for k, v in expected_metadata[lid].items():
            if v is None:
                assert k not in layer.metadata
            else:
                assert k in layer.metadata
                assert layer.metadata[k] == v


@pytest.mark.parametrize(
    ["svg", "expected_metadata"],
    [
        pytest.param(
            """<?xml version="1.0"?><svg>
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
            </svg>""",
            {"svg_fill": "red"},
            id="lone_line",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg stroke="#f00">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
            </svg>""",
            {"svg_fill": "red", "svg_stroke": "#f00"},
            id="lone_line_svg_attrib",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
            </svg>""",
            {"svg_fill": "red"},
            id="lone_line_svg_attrib_conflict",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                <line x1="0" y1="0" x2="10" y2="10" fill="green" />
            </svg>""",
            {"svg_fill": None},
            id="two_line_inconsistent",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                <g id="1">
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                </g>
            </svg>""",
            {"svg_fill": "red"},
            id="group_1_with_lone_line_svg_attrib_conflict",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <g id="1">
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                </g>
            </svg>""",
            {"svg_fill": "red"},
            id="group_1_svg_attrib_conflict",
        ),
        pytest.param(
            """<?xml version="1.0"?><svg fill="blue">
                <g id="1">
                    <line x1="0" y1="0" x2="10" y2="10" fill="red" />
                    <line x1="0" y1="0" x2="10" y2="10" fill="green" />
                </g>
            </svg>""",
            {"svg_fill": None},
            id="inconsistent_group1",
        ),
    ],
)
def test_read_metadata(tmp_path, svg, expected_metadata):
    path = _write_svg_file(tmp_path, svg)
    lc, _, _ = vp.read_svg(path, quantization=0.1, crop=False)

    assert lc.metadata

    for k, v in expected_metadata.items():
        if v is None:
            assert k not in lc.metadata
        else:
            assert k in lc.metadata
            assert lc.metadata[k] == v


def test_read_layer_name(runner):
    res = runner.invoke(
        cli,
        ["read", str(TEST_FILE_DIRECTORY / "misc" / "multilayer_named_layers.svg")]
        + f"propget -l all {vp.METADATA_FIELD_NAME}".split(),
    )

    assert res.exit_code == 0
    assert (
        res.stdout
        == """layer 1 property vp_name: (str) my layer 1
layer 2 property vp_name: (str) my layer 2
layer 3 property vp_name: (str) my layer 3
"""
    )


def test_read_by_attribute():
    def _prop_set(document: vp.Document, prop: str) -> set:
        return {layer.property(prop) for layer in document.layers.values()}

    file = TEST_FILE_DIRECTORY / "misc" / "multilayer_by_attributes.svg"
    doc = vp.read_svg_by_attributes(str(file), ["stroke"], 0.1)
    assert len(doc.layers) == 2
    assert _prop_set(doc, "vp_color") == {vp.Color("#906"), vp.Color("#00f")}

    doc = vp.read_svg_by_attributes(str(file), ["stroke", "stroke-width"], 0.1)
    assert len(doc.layers) == 3
    assert _prop_set(doc, "vp_color") == {vp.Color("#906"), vp.Color("#00f")}
    assert sorted(_prop_set(doc, "vp_pen_width")) == pytest.approx([1, 4])


def test_read_layer_assumes_single_layer(caplog):
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer.svg"
    doc = vpype_cli.execute(f"read --layer 2 '{test_file}'", global_opt="-vv")

    assert "assuming single-layer mode" in caplog.text
    assert len(doc.layers) == 1
    assert 2 in doc.layers


def test_read_single_layer_attr_warning(caplog):
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer_by_attributes.svg"
    doc = vpype_cli.execute(f"read -m -a stroke '{test_file}'")

    assert "`--attr` is ignored in single-layer mode" in caplog.text
    assert len(doc.layers) == 1
    assert 1 in doc.layers


def test_write_svg_svg_props(capsys):
    vpype_cli.execute(
        "line 0 0 10 10 layout a5 propset -l1 svg_stroke-dasharray '1 2' write -r -f svg -"
    )
    assert 'stroke-dasharray="1 2"' in capsys.readouterr().out


def test_write_svg_svg_props_namespace(capsys):
    vpype_cli.execute(
        "line 0 0 10 10 layout a5 propset -g svg_inkscape_version '1.1.0' write -r -f svg -"
    )
    assert 'inkscape:version="1.1.0"' in capsys.readouterr().out


def test_write_svg_svg_props_unknown_namespace(capsys):
    vpype_cli.execute(
        "line 0 0 10 10 layout a5 propset -g svg_unknown_version '1.1.0' write -r -f svg -"
    )
    assert 'unknown:version="1.1.0"' not in capsys.readouterr().out


def test_write_opacity_100pct(capsys):
    vpype_cli.execute("line 0 0 10 10 color red write -f svg -")
    assert 'stroke="#ff0000"' in capsys.readouterr().out


def test_write_opacity_50pct(capsys):
    vpype_cli.execute("line 0 0 10 10 color '#ff00007f' write -f svg -")
    output = capsys.readouterr().out
    assert 'stroke="#ff0000"' in output
    assert 'stroke-opacity="0.498"' in output


def test_read_no_fail():
    with pytest.raises(click.BadParameter):
        vpype_cli.execute("read doesnotexist.svg")
    vpype_cli.execute("read --no-fail doesnotexist.svg")


def test_read_sets_source_properties():
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer.svg"
    doc = vpype_cli.execute(f"read '{test_file}'")
    assert doc.property(vp.METADATA_FIELD_SOURCE) == test_file
    assert doc.property(vp.METADATA_FIELD_SOURCE_LIST) == {test_file}


def test_read_by_attrs_sets_source_properties():
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer.svg"
    doc = vpype_cli.execute(f"read -a fill -a stroke '{test_file}'")
    assert doc.property(vp.METADATA_FIELD_SOURCE) == test_file
    assert doc.property(vp.METADATA_FIELD_SOURCE_LIST) == {test_file}


def test_read_single_layer_sets_source_properties():
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer.svg"
    doc = vpype_cli.execute(f"read --layer 1 '{test_file}'")
    assert doc.property(vp.METADATA_FIELD_SOURCE_LIST) == {test_file}
    assert len(doc.layers) == 1
    assert doc.layers[1].property(vp.METADATA_FIELD_SOURCE) == test_file


def test_read_stdin_sets_source_properties(monkeypatch):
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer.svg"
    monkeypatch.setattr("sys.stdin", io.StringIO(test_file.read_text()))

    doc = vpype_cli.execute(f"read -")
    assert vp.METADATA_FIELD_SOURCE not in doc.metadata
    assert doc.sources == set()


def test_read_single_layer_stdin_sets_source_properties(monkeypatch):
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer.svg"
    monkeypatch.setattr("sys.stdin", io.StringIO(test_file.read_text()))

    doc = vpype_cli.execute(f"read -l1 -")
    assert vp.METADATA_FIELD_SOURCE not in doc.metadata
    assert vp.METADATA_FIELD_SOURCE not in doc.layers[1].metadata
    assert doc.sources == set()


def test_read_by_attr_stdin_sets_source_properties(monkeypatch):
    test_file = TEST_FILE_DIRECTORY / "misc" / "multilayer.svg"
    monkeypatch.setattr("sys.stdin", io.StringIO(test_file.read_text()))

    doc = vpype_cli.execute(f"read -a stroke -a fill -")
    assert vp.METADATA_FIELD_SOURCE not in doc.metadata
    assert doc.sources == set()


def test_write_set_date(capsys):
    vpype_cli.execute("line 0 0 10 10 write -f svg -")
    output = capsys.readouterr().out
    assert "<dc:date>" in output


def test_write_dont_set_date(capsys):
    vpype_cli.execute("line 0 0 10 10 write -f svg --dont-set-date -")
    output = capsys.readouterr().out
    assert "<dc:date>" not in output


_PAGE_SIZE_EXAMPLES = [
    (
        """<?xml version="1.0"?><svg>
            <line x1="0" y1="0" x2="10" y2="10" fill="red" />
        </svg>""",
        (None, None),
        (1000.0, 1000.0),
    ),
    (
        """<?xml version="1.0"?><svg viewBox="0 0 900 800">
            <line x1="0" y1="0" x2="10" y2="10" fill="red" />
        </svg>""",
        (None, None),
        (900.0, 800.0),
    ),
    (
        """<?xml version="1.0"?><svg viewBox="0 0 900 800">
            <line x1="0" y1="0" x2="10" y2="10" fill="red" />
        </svg>""",
        (700, 600),
        (700.0, 600.0),
    ),
    (
        """<?xml version="1.0"?><svg width="500" height="300">
            <line x1="0" y1="0" x2="10" y2="10" fill="red" />
        </svg>""",
        (700, 650),
        (500, 300),
    ),
    (
        """<?xml version="1.0"?><svg width="500" height="300">
            <line x1="0" y1="0" x2="10" y2="10" fill="red" />
        </svg>""",
        (None, None),
        (500, 300),
    ),
    (
        """<?xml version="1.0"?><svg width="500" height="300" viewBox="0 0 600 750">
            <line x1="0" y1="0" x2="10" y2="10" fill="red" />
        </svg>""",
        (700, 600),
        (500, 300),
    ),
    (
        """<?xml version="1.0"?><svg width="500" height="300" viewBox="0 0 600 750">
            <line x1="0" y1="0" x2="10" y2="10" fill="red" />
        </svg>""",
        (None, None),
        (500, 300),
    ),
]


@pytest.mark.parametrize(["svg", "default", "target"], _PAGE_SIZE_EXAMPLES)
def test_read_command_page_size(
    tmp_path, svg: str, default: tuple[float, float], target: tuple[float, float]
):
    path = _write_svg_file(tmp_path, svg)
    args = ""
    if default[0] is not None and default[1] is not None:
        args += f"--display-size {default[0]:.3f}x{default[1]:.3f} "
        if default[0] > default[1]:
            args += f"--display-landscape"
    doc = vpype_cli.execute(f"read {args} {path}")

    assert doc.page_size == pytest.approx(target)


@pytest.mark.parametrize(["svg", "default", "target"], _PAGE_SIZE_EXAMPLES)
def test_read_multilayer_svg_default_page_size(
    tmp_path, svg: str, default: tuple[float, float], target: tuple[float, float]
):
    path = _write_svg_file(tmp_path, svg)
    doc = vp.read_multilayer_svg(
        path, quantization=0.1, default_width=default[0], default_height=default[1]
    )

    assert doc.page_size == pytest.approx(target)


@pytest.mark.parametrize(["svg", "default", "target"], _PAGE_SIZE_EXAMPLES)
def test_read_svg_default_page_size(
    tmp_path, svg: str, default: tuple[float, float], target: tuple[float, float]
):
    path = _write_svg_file(tmp_path, svg)
    _, width, height = vp.read_svg(
        path, quantization=0.1, default_width=default[0], default_height=default[1]
    )

    assert (width, height) == pytest.approx(target)


@pytest.mark.parametrize(["svg", "default", "target"], _PAGE_SIZE_EXAMPLES)
def test_read_svg_by_attributes_default_page_size(
    tmp_path, svg: str, default: tuple[float, float], target: tuple[float, float]
):
    path = _write_svg_file(tmp_path, svg)
    doc = vp.read_svg_by_attributes(
        path,
        quantization=0.1,
        attributes=["fill"],
        default_width=default[0],
        default_height=default[1],
    )

    assert doc.page_size == pytest.approx(target)
