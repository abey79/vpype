from __future__ import annotations

import numpy as np
import pytest

import vpype as vp


@pytest.mark.parametrize("quantization", [0.01, 0.1, 1, 10, 100])
def test_circle_quantization(quantization):
    line = vp.circle(0, 0, 10, quantization)

    assert np.max(np.abs(np.diff(line))) < quantization


@pytest.mark.parametrize("quantization", [0.01, 0.1, 1, 10, 100])
def test_rect_quantization(quantization):
    line = vp.rect(0, 0, 300, 400, 3, 3, 3, 3, quantization)

    seg_len = np.abs(np.diff(line))
    assert np.max(seg_len[seg_len < 100]) < quantization


def test_arc():
    vp.arc(0, 0, 4, 47.90087728876629, 60.80551044388678, 0.05)
