from __future__ import annotations

import svgelements

import vpype as vp


def test_metadata_color():
    assert vp.Color() == vp.Color(red=0, green=0, blue=0, alpha=255)
    assert vp.Color(255, 0, 255) == vp.Color(red=255, green=0, blue=255, alpha=255)
    assert vp.Color(255, 0, 255, 128) == vp.Color(red=255, green=0, blue=255, alpha=128)
    assert vp.Color(vp.Color("red")) == vp.Color(red=255, green=0, blue=0, alpha=255)
    assert vp.Color("blue") == vp.Color(red=0, green=0, blue=255, alpha=255)
    assert vp.Color(svgelements.Color("#0f0")) == vp.Color(red=0, green=255, blue=0, alpha=255)
