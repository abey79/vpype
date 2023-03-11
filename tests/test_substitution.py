from __future__ import annotations

import click
import pytest

import vpype as vp
import vpype_cli

# noinspection PyProtectedMember
from vpype_cli.substitution import (
    ExpressionSubstitutionError,
    PropertySubstitutionError,
    _PropertyProxy,
    _substitute_expressions,
)


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


@pytest.fixture
def state_factory():
    def make_state(state_type: str = "default") -> vpype_cli.State:
        if state_type == "default":
            state = vpype_cli.State()
        elif state_type == "inconsistent":
            state = vpype_cli.State()
            state.current_layer_id = 1  # doesn't exists
        elif state_type == "dummy":
            doc = vp.Document()
            doc.set_property("global_prop", 10)
            doc.add([[0, 10, 10j]], 1)
            doc.layers[1].set_property("layer_prop", 1.5)
            state = vpype_cli.State(doc)
            state.current_layer_id = 1
        else:  # pragma: no cover
            raise ValueError(f"unknown state type {state_type}")
        return state

    return make_state


def test_property_proxy(state_factory):
    dummy_state = state_factory("dummy")
    proxy = _PropertyProxy(dummy_state, True, True)
    assert proxy["global_prop"] == proxy.global_prop == 10
    assert proxy["layer_prop"] == proxy.layer_prop == 1.5

    proxy = _PropertyProxy(dummy_state, True, False)
    assert proxy["global_prop"] == proxy.global_prop == 10
    with pytest.raises(KeyError):
        assert proxy["local_prop"]
    with pytest.raises(AttributeError):
        assert proxy.local_prop

    proxy = _PropertyProxy(dummy_state, False, True)
    assert proxy["layer_prop"] == proxy.layer_prop == 1.5
    with pytest.raises(KeyError):
        assert proxy["global_prop"]
    with pytest.raises(AttributeError):
        assert proxy.global_prop


def test_property_proxy_dict(state_factory):
    dummy_state = state_factory("dummy")

    assert dict(_PropertyProxy(dummy_state, True, True)) == {
        "global_prop": 10,
        "layer_prop": 1.5,
    }
    assert dict(_PropertyProxy(dummy_state, True, False)) == {"global_prop": 10}
    assert dict(_PropertyProxy(dummy_state, False, True)) == {"layer_prop": 1.5}


@pytest.fixture
def dumb_interp():
    def interp(text: str) -> str:
        return f"###{text}###"

    return interp


@pytest.fixture
def dumb_prop():
    class _DumbProp(dict):
        def __missing__(self, key):
            return f"$$${key}$$$"

    return lambda x: x.format_map(_DumbProp())


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        # basic properties
        ("{hello}", "$$$hello$$$"),
        ("world{hello}", "world$$$hello$$$"),
        ("{hello}world", "$$$hello$$$world"),
        ("{hello}world{bis}", "$$$hello$$$world$$$bis$$$"),
        ("first{hello}world{bis}last", "first$$$hello$$$world$$$bis$$$last"),
        ("{{hello}}", "{hello}"),
        ("{{hello}}{world}", "{hello}$$$world$$$"),
        ("he%%llo{world}", "he%llo$$$world$$$"),
        ("he%%ll{{}}o{world}", "he%ll{}o$$$world$$$"),
        # basic expression
        ("%%", "%"),
        ("hello", "hello"),
        ("%hello%", "###hello###"),
        ("%hel%%lo%", "###hel%lo###"),
        ("hel%%lo", "hel%lo"),
        ("hel%%lo%world%", "hel%lo###world###"),
        ("hel%%lo%wor%%ld%", "hel%lo###wor%ld###"),
        ("hel%%lo%wor%%ld%bye", "hel%lo###wor%ld###bye"),
        ("hel%%lo%wor%%ld%by%%e", "hel%lo###wor%ld###by%e"),
        # combined
        ("%hello%{world}", "###hello###$$$world$$$"),
        ("%he{ll}o%", "###he{ll}o###"),
        ("{{hello:.1%}}%", "{hello:.1###}}###"),
    ),
)
def test_substitute_expressions(dumb_prop, dumb_interp, text, expected):
    assert _substitute_expressions(text, dumb_prop, dumb_interp) == expected


def test_substitution_percent_property_format(state_factory):
    """Special case where % should be accepted in prop substitution"""
    dummy_state = state_factory("dummy")
    assert dummy_state.substitute("{layer_prop:.2%}") == "150.00%"
    assert dummy_state.substitute("{layer_prop:.2%} %lprop.layer_prop%") == "150.00% 1.5"


@pytest.mark.parametrize(
    "text",
    (
        "%",
        "%%%",
        "%hello",
        "%hel%%lo",
        "%hello%world%",
        "%hello%world%bye",
        "hello%world%bye%",
    ),
)
def test_expression_illegal(text, dumb_interp):
    with pytest.raises(ExpressionSubstitutionError):
        _substitute_expressions(text, lambda x: x, dumb_interp)


@pytest.mark.parametrize(
    "text",
    (
        "{he{{ll}}o}",  # invalid for format
        "{hello}}world",
    ),
)
def test_property_illegal(text, dumb_prop):
    with pytest.raises(PropertySubstitutionError):
        _substitute_expressions(text, dumb_prop, lambda x: x)


def test_expression_get_property(state_factory):
    dummy_state = state_factory("dummy")

    assert dummy_state.substitute("%prop.global_prop%") == "10"
    assert dummy_state.substitute("%prop.layer_prop%") == "1.5"
    assert dummy_state.substitute("%gprop.global_prop%") == "10"
    assert dummy_state.substitute("%lprop.layer_prop%") == "1.5"
    with pytest.raises(click.BadParameter):
        dummy_state.substitute("%lprop.global_prop%")
    with pytest.raises(click.BadParameter):
        dummy_state.substitute("%gprop.layer_prop%")


def test_expression_set_property(state_factory):
    dummy_state = state_factory("dummy")

    dummy_state.substitute("%gprop.new_global_prop='alpha'%")
    assert dummy_state.document.property("new_global_prop") == "alpha"

    dummy_state.substitute("%lprop.new_layer_prop=50%")
    assert dummy_state.document.layers[1].property("new_layer_prop") == 50

    with pytest.raises(click.BadParameter):
        dummy_state.substitute("%prop.new_prop=1%")


@pytest.mark.parametrize("state_type", ("dummy", "default", "inconsistent"))
def test_expression_dict_of_prop(state_factory, state_type):
    state = state_factory(state_type)
    state.substitute("%dict(prop)%")
    state.substitute("%dict(gprop)%")
    state.substitute("%dict(lprop)%")


def test_expression_lid_builtin():
    doc = vpype_cli.execute("random -l 1 random -l 3 name 'layer %lid%'")
    assert {1, 3} == doc.layers.keys()
    assert doc.layers[1].metadata[vp.METADATA_FIELD_NAME] == "layer 1"
    assert doc.layers[3].metadata[vp.METADATA_FIELD_NAME] == "layer 3"
