from __future__ import annotations

import pytest

import vpype as vp


@pytest.mark.parametrize(
    "lf rt".split(),
    [
        ("10cm", "1e-1m"),
        ("10cm", "100mm"),
        ("1km", "1000m"),
        ("1km", "+1e+6mm"),
        ("1km", "100000cm"),
        ("6in", ".5ft"),
        ("-18in", "-.5yd"),
        ("1mi", "63360in"),
        ("69in", "69inch"),
    ],
)
def test_convert_length(lf, rt):
    assert vp.convert_length(lf) == pytest.approx(vp.convert_length(rt))


def test_convert_length_fail():
    with pytest.raises(ValueError):
        vp.convert_length("invalid")

    with pytest.raises(ValueError):
        vp.convert_length("")

    with pytest.raises(ValueError):
        vp.convert_length("3in3")


def test_format_length():
    assert vp.format_length(1_000.12345657, "metric") == "26.461599788414585cm"
    assert vp.format_length(1_000.12345657, "metric", False) == "26.462cm"
    assert vp.format_length(1_000_000.12345657, "metric", False) == "0.265km"
    assert vp.format_length(0.12345657, "metric", False) == "0.03266mm"

    assert vp.format_length(1_000.12345657, "imperial") == "10.417952672604168in"
    assert vp.format_length(1_000_000.12345657, "imperial") == "0.16440448157627216mi"
    assert vp.format_length(10_000.12345657, "imperial") == "2.8935542409056714yd"

    assert vp.format_length(1_000_000.12345657, "mm") == "264583.36599788413mm"


def test_format_length_zero():
    assert vp.format_length(0, "px") == "0.0px"


def test_format_length_fail():
    with pytest.raises(ValueError):
        vp.format_length(50, "au")
