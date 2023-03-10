import math

import numpy as np
import pytest

from ..arc import ArcSegment


@pytest.mark.parametrize(
    ["seg", "expected_center", "expected_radius"],
    [
        (ArcSegment(0, 1, 0), 0.5, 0.5),
        (ArcSegment(0, 0.5 + 0.5j, 1), 0.5, 0.5),
    ],
)
def test_arc_center_radius(seg, expected_center, expected_radius):
    assert seg.center == pytest.approx(expected_center)
    assert seg.radius == pytest.approx(expected_radius)


PT45_UP = math.sqrt(2) / 2 * (1 - 1j)
PT45_DOWN = math.sqrt(2) / 2 * (1 + 1j)

# arbitrary arcs with their expected angles
ARCS_ANGLES = [
    (ArcSegment(0, 1, 0), math.pi, math.pi * 3),
    (ArcSegment(0, 0.5 + 0.5j, 1), math.pi, 0),
    (ArcSegment(0, 0.5 - 0.5j, 1), math.pi, math.pi * 2),
    (ArcSegment(PT45_UP, PT45_DOWN, -1), 7 * math.pi / 4, 3 * math.pi),
    (ArcSegment(PT45_UP, -1, PT45_DOWN), 7 * math.pi / 4, math.pi / 4),
    (ArcSegment(PT45_DOWN, -1, PT45_UP), math.pi / 4, 7 * math.pi / 4),
    (ArcSegment(PT45_DOWN, PT45_UP, -1), math.pi / 4, -math.pi),
    (ArcSegment(-1, PT45_DOWN, PT45_UP), math.pi, -math.pi / 4),
    (ArcSegment(-1, PT45_UP, PT45_DOWN), math.pi, 9 * math.pi / 4),
    (ArcSegment(PT45_UP, 1, PT45_DOWN), 7 * math.pi / 4, 9 * math.pi / 4),
    (ArcSegment(PT45_DOWN, 1, PT45_UP), math.pi / 4, -math.pi / 4),
]


@pytest.mark.parametrize(["seg", "expected_start_angle", "expected_end_angle"], ARCS_ANGLES)
def test_arc_angles(seg, expected_start_angle, expected_end_angle):
    assert seg.angles == pytest.approx((expected_start_angle, expected_end_angle))


# "round" angles and "random" angles
ANGLES = np.concatenate([np.linspace(-2, 2, 5), np.linspace(-1.9, 1.85, 5)])


@pytest.mark.parametrize(["seg", "expected_start_angle", "expected_end_angle"], ARCS_ANGLES)
@pytest.mark.parametrize("rot", [i * math.pi for i in ANGLES])
def test_arc_angles_rotate(seg, expected_start_angle, expected_end_angle, rot):
    # segment must be centered to origin for this test
    start, end = seg.translate(-seg.center).rotate(rot).angles

    sweep = end - start

    assert 0 <= start < math.tau
    assert sweep == pytest.approx(expected_end_angle - expected_start_angle)

    # correct angle for rotation and normalise
    start -= rot
    while start < 0:
        start += math.tau
    while start >= math.tau:
        start -= math.tau

    assert start == pytest.approx(expected_start_angle)
    assert start + sweep == pytest.approx(expected_end_angle)
