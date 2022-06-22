import pytest

import vpype as vp


@pytest.mark.parametrize(
    "lf rt".split(),
    [("10cm", "0.1m"), ("10cm", "100mm"), ("6in", ".5ft")],
)
def test_convert_length(lf, rt):
    assert vp.convert_length(lf) == pytest.approx(vp.convert_length(rt))


def test_convert_length_fail():
    with pytest.raises(ValueError):
        vp.convert_length("invalid")
