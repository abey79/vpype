import pytest

import vpype_cli


@pytest.mark.parametrize(
    ("value", "field", "expected"),
    [
        (3, "", "3"),
        (3, "03", "003"),
        (1.2, "", "1.2"),
        (1.2, ".2f", "1.20"),
        (1.2, "06.2f", "001.20"),
        ("hello", "", "hello"),
    ],
)
def test_property_substitution(runner, value, field, expected):
    res = runner.invoke(
        vpype_cli.cli,
        f"propset -t {type(value).__name__} -g base_prop {value} "
        f"propset -g result_prop {{base_prop:{field}}} "
        "propget -g result_prop",
    )
    assert res.exit_code == 0
    assert res.output.strip().split(" ")[-1] == expected


def test_property_substitution_layer(runner):
    res = runner.invoke(vpype_cli.cli, "random -l1 propset -l 1 hello world text {hello}")
    assert res.exit_code == 0


def test_property_substitution_global(runner):
    res = runner.invoke(vpype_cli.cli, "propset -g hello world text {hello}")
    assert res.exit_code == 0


def test_property_substitution_missing(runner):
    res = runner.invoke(vpype_cli.cli, "propset -g hello world text {missing}")
    assert res.exit_code == 2
    assert "Error" in res.stderr


def test_property_substitution_invalid(runner):
    res = runner.invoke(vpype_cli.cli, "propset -g hello world text {hello:.2f}")
    assert res.exit_code == 2
    assert "Error" in res.stderr


def test_property_substitution_int():
    doc = vpype_cli.execute("propset -g -t int num 2 repeat 2 random -l new end")
    assert {1, 2} == doc.layers.keys()


def test_property_substitution_empty_layer():
    # property substitution should work even if the layer is empty
    doc = vpype_cli.execute("pens rgb text {vp_name}")
    assert len(doc.layers[1]) > 0
