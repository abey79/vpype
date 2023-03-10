import cmath
import math

import numpy as np
import pytest

from vpype.path.quad_bezier import QuadraticBezierSegment


def test_quad_bezier_crop_colinear():
    # if the curve is aligned with the crop axis, it is always kept
    q = QuadraticBezierSegment(0, 1, 2)
    assert list(q.crop_y(0, True)) == [q]
    assert list(q.crop_y(0, False)) == [q]
    assert list(q.crop_y(-1, True)) == []
    assert list(q.crop_y(-1, False)) == [q]
    assert list(q.crop_y(1, False)) == []
    assert list(q.crop_y(1, True)) == [q]


@pytest.mark.parametrize(
    ["loc", "axis", "keep_smaller", "expect_empty"],
    [
        (-1, "x", True, True),
        (-1, "x", False, False),
        (0, "x", True, True),
        (0, "x", False, False),
        (2, "x", True, False),
        (2, "x", False, True),
        (3, "x", True, False),
        (3, "x", False, True),
        (-1, "y", True, True),
        (-1, "y", False, False),
        (0, "y", True, True),
        (0, "y", False, False),
        (1.5, "y", True, False),
        (1.5, "y", False, True),
        (2, "y", True, False),
        (2, "y", False, True),
    ],
)
def test_quad_bezier_symmetric_crop_edge_case(loc, axis, keep_smaller, expect_empty):
    """considering a simply symmetric quad bezier, all edge case must correctly handle
    the full curve or nothing at all"""

    if axis == "x":
        crop = QuadraticBezierSegment.crop_x
        crop_inv = QuadraticBezierSegment.crop_y
    else:
        crop = QuadraticBezierSegment.crop_y
        crop_inv = QuadraticBezierSegment.crop_x

    # symmetric, tangent at y = 1.5, which has exact float representation
    q = QuadraticBezierSegment(0, 1 + 3j, 2)
    res = list(crop(q, loc, keep_smaller))
    assert res == ([] if expect_empty else [q])

    # flipped should work as well
    qr = q.reverse()
    assert list(crop(qr, loc, keep_smaller)) == ([] if expect_empty else [qr])

    # mirrored as well
    qm = q.flip_axes()
    assert list(crop_inv(qm, loc, keep_smaller)) == ([] if expect_empty else [qm])


Q = QuadraticBezierSegment(0, 1.5 + 3j, 3 + 1.5j)
P1 = Q.first
P2 = 1 + 1.5j
P3 = 2 + 2j
P4 = Q.last


@pytest.mark.parametrize(
    "loc axis keep_smaller points".split(),
    [
        (-1, "x", True, ()),
        (-1, "x", False, (P1, P4)),
        (0, "x", True, ()),
        (0, "x", False, (P1, P4)),
        (1, "x", True, (P1, P2)),
        (1, "x", False, (P2, P4)),
        (2, "x", True, (P1, P3)),
        (2, "x", False, (P3, P4)),
        (3, "x", True, (P1, P4)),
        (3, "x", False, ()),
        (4, "x", True, (P1, P4)),
        (4, "x", False, ()),
        (-1, "y", True, ()),
        (-1, "y", False, (P1, P4)),
        (0, "y", True, ()),
        (0, "y", False, (P1, P4)),
        (1.5, "y", True, (P1, P2)),
        (1.5, "y", False, (P2, P4)),
        (2, "y", True, (P1, P4)),
        (2, "y", False, ()),
        (3, "y", True, (P1, P4)),
        (3, "y", False, ()),
    ],
)
def test_quad_bezier_asymmetric_crop_edge_case(loc, axis, keep_smaller, points):
    if axis == "x":
        crop = QuadraticBezierSegment.crop_x
    else:
        crop = QuadraticBezierSegment.crop_y

    # noinspection PyShadowingNames
    def _assert_res(res, points):
        res = list(res)
        if points == ():
            assert res == []
        else:
            assert len(res) == 1
            assert res[0].first == pytest.approx(points[0])
            assert res[0].last == pytest.approx(points[1])

    q = QuadraticBezierSegment(0, 1.5 + 3j, 3 + 1.5j)
    _assert_res(crop(q, loc, keep_smaller), points)

    qr = q.reverse()
    _assert_res(crop(qr, loc, keep_smaller), points[::-1])


def test_quad_bezier_crop_single_point():
    q = QuadraticBezierSegment(0, 2 + 2j, 4)
    assert list(q.crop_x(2, True)) == [QuadraticBezierSegment(0, 1 + 1j, 2 + 1j)]
    assert list(q.crop_x(2, False)) == [QuadraticBezierSegment(2 + 1j, 3 + 1j, 4)]


def test_quad_bezier_crop_two_points():
    q = QuadraticBezierSegment(-2j, -2 + 5j, 7)
    begin, end = tuple(q.crop_y(1, True))
    (middle,) = tuple(q.crop_y(1, False))

    assert begin.first == pytest.approx(q.first)
    assert begin.last == pytest.approx(middle.first)
    assert middle.last == pytest.approx(end.first)
    assert end.last == pytest.approx(q.last)


@pytest.mark.parametrize(
    "q bbox".split(),
    [
        (QuadraticBezierSegment(0, 0, 0), (0, 0, 0, 0)),
        (QuadraticBezierSegment(0, 1, 2), (0, 0, 2, 0)),
        (QuadraticBezierSegment(0, 5, 0), (0, 0, 2.5, 0)),
        (QuadraticBezierSegment(0, 1 + 1j, 2 + 2j), (0, 0, 2, 2)),
        (QuadraticBezierSegment(0, 1 - 1j, 2 - 2j), (0, -2, 2, 0)),
        (QuadraticBezierSegment(0, 5 + 5j, 0), (0, 0, 2.5, 2.5)),
    ],
)
def test_quad_bezier_bbox(q, bbox):
    assert q.bbox == bbox
    assert q.flip_axes().bbox == (bbox[1], bbox[0], bbox[3], bbox[2])


@pytest.mark.parametrize("radius", [0.5, 1, 2, 5])
@pytest.mark.parametrize("angle", [n * math.pi for n in [0, 0.25, 0.5, 0.75, 1]])
def test_quad_bezier_bbox_estimate(radius, angle):
    # for various radii and angles, check that the bounding box is correct by converting to
    # a polyline

    q = QuadraticBezierSegment(0, radius * cmath.rect(1, angle), 1)
    bbox = q.bbox

    t = np.linspace(0, 1, 100)
    pts = q.point(t)

    assert bbox[0] == pytest.approx(min(pts.real), rel=1e-3)
    assert bbox[1] == pytest.approx(min(pts.imag), rel=1e-3)
    assert bbox[2] == pytest.approx(max(pts.real), rel=1e-3)
    assert bbox[3] == pytest.approx(max(pts.imag), rel=1e-3)
