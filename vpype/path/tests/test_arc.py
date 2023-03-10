import itertools
import math

import numpy as np
import pytest

import vpype
from vpype.path.arc import ArcSegment
from vpype.path.exceptions import SegmentCreationError


def _assert_arc_equal(arc1, arc2):
    assert arc1.center == pytest.approx(arc2.center)
    assert arc1.radius == pytest.approx(arc2.radius)
    assert arc1.angles == pytest.approx(arc2.angles)


@pytest.fixture(scope="module")
def arc_factory():
    # noinspection PyMethodMayBeStatic
    class _ArcFactory:
        def circle(self, center=0, radius=1, start_angle=0, ccw=True):
            return ArcSegment(
                center=center,
                radius=radius,
                angles=(
                    start_angle,
                    (start_angle + math.tau) if ccw else (start_angle - math.tau),
                ),
            )

        def random(
            self,
            center=None,
            radius=None,
            start_angle=None,
            sweep=None,
            center_range=100,
            radius_range=100,
            angle_range=(0, math.tau),
            sweep_range=(-math.tau, math.tau),
        ):
            if center is None:
                center = np.random.uniform(
                    -center_range, center_range
                ) + 1j * np.random.uniform(-center_range, center_range)
            if radius is None:
                radius = np.random.uniform(0, radius_range)
            if start_angle is None:
                start_angle = np.random.uniform(*angle_range)
            if sweep is None:
                sweep = np.random.uniform(*sweep_range)
            stop_angle = start_angle + sweep
            return ArcSegment(center=center, radius=radius, angles=(start_angle, stop_angle))

    return _ArcFactory()


@pytest.mark.parametrize(
    "angles",
    [
        (0, math.pi),
        (-math.pi, 0.1),
        (3 * math.tau, 3.1 * math.tau),
        (3 * math.tau, 2.9 * math.tau),
    ],
)
def test_arc_angle_normalisation(angles: tuple[float, float]):
    seg = ArcSegment(0, 1, angles)
    assert 0 <= seg.angles[0] < math.tau
    assert seg.sweep == pytest.approx(angles[1] - angles[0])


def test_arc_from_sweep():
    arc = ArcSegment.from_sweep(0, 1, 0, 2)
    assert arc.center == 0
    assert arc.radius == 1
    assert arc.angles == (0, 2)
    assert arc.sweep == 2

    arc = ArcSegment.from_sweep(0, 1, 0, -2)
    assert arc.center == 0
    assert arc.radius == 1
    assert arc.angles == (0, -2)
    assert arc.sweep == -2


# noinspection PyTypeChecker
def test_arc_bad_init():
    with pytest.raises(SegmentCreationError):
        ArcSegment(0, 1, (0, 1.5 * math.tau))
    with pytest.raises(SegmentCreationError):
        ArcSegment(0, 1, (0,))
    with pytest.raises(SegmentCreationError):
        ArcSegment(0, 1, (0, 1, 2))


def test_arc_point():
    arc = ArcSegment(0, 1, (0, math.tau))
    for a in np.linspace(0, math.tau, 10):
        c = arc.point(a)
        assert abs(c) == pytest.approx(1)
        exp_angle = math.atan2(c.imag, c.real)
        if exp_angle < 0:
            exp_angle += math.tau
        assert exp_angle == pytest.approx(a)


def test_arc_sweep():
    assert ArcSegment(0, 1, (0, 1)).sweep == pytest.approx(1)
    assert ArcSegment(0, 1, (0, -1)).sweep == pytest.approx(-1)
    assert ArcSegment(0, 2, (1, 2)).sweep == pytest.approx(1)
    assert ArcSegment(3 + 3j, 2, (1, 2)).sweep == pytest.approx(1)


def test_arc_ccw():
    a = ArcSegment(0, 1, (1, 2))
    assert not a.ccw
    assert a.reverse().ccw
    assert not a.translate(3 + 2j).ccw
    assert not a.scale(3 + 3j).ccw
    assert not a.scale(-2 - 2j).ccw
    assert a.scale(2 - 2j).ccw
    assert a.scale(-2 + 2j).ccw
    assert a.flip_axes().ccw


def test_arc_flip_axes():
    a = ArcSegment(0, 1, (0, 1))
    b = a.flip_axes()
    assert b == ArcSegment(0j, 1, (math.pi / 2, math.pi / 2 - 1))

    a = ArcSegment(5 + 3j, 1, (1, 2))
    b = a.flip_axes()
    assert b == ArcSegment(3 + 5j, 1, (math.pi / 2 - 1, math.pi / 2 - 2))


def test_arc_flip_axes_bis(arc_factory):
    for _ in range(30):
        arc = arc_factory.random()
        arc2 = arc.flip_axes().flip_axes()
        assert arc.center == arc2.center
        assert arc.radius == arc2.radius
        assert arc.angles == pytest.approx(arc2.angles)


def test_arc_translate(arc_factory):
    for _ in range(30):
        arc = arc_factory.random()
        arc2 = arc.translate(3 + 3j)
        assert arc2.center - arc.center == pytest.approx(3 + 3j)
        assert arc2.radius == pytest.approx(arc.radius)
        assert arc2.angles == pytest.approx(arc.angles)


def test_arc_rotate(arc_factory):
    for _, rot in itertools.product(range(30), np.linspace(-math.pi, math.pi, 11)):
        arc = arc_factory.random()
        arc2 = arc.rotate(rot)
        assert arc2.center == pytest.approx(arc.center * np.exp(1j * rot))
        assert arc2.radius == pytest.approx(arc.radius)
        assert arc2.sweep == pytest.approx(arc.sweep)
        assert arc2.ccw == arc.ccw


def test_arc_rotate_full(arc_factory):
    for _ in range(30):
        arc = arc_factory.random()
        arc2 = arc.rotate(math.tau)
        assert arc2.center == pytest.approx(arc.center)
        assert arc2.radius == arc.radius
        assert arc2.angles == pytest.approx(arc.angles)


def test_arc_scale(arc_factory):
    for _ in range(30):
        arc = arc_factory.random()

        # basic scaling
        arc2 = arc.scale(2 + 2j)
        assert arc2.center == pytest.approx(arc.center * 2)
        assert arc2.radius == pytest.approx(2 * arc.radius)
        assert arc2.angles == pytest.approx(arc.angles)
        _assert_arc_equal(arc, arc2.scale(0.5 + 0.5j))

        # negative scaling
        arc2 = arc.scale(-2 - 2j)
        assert arc2.center == pytest.approx(arc.center * -2)
        assert arc2.radius == pytest.approx(2 * arc.radius)
        assert arc2.begin == pytest.approx(arc.begin * -2)
        assert arc2.end == pytest.approx(arc.end * -2)
        assert arc2.sweep == pytest.approx(arc.sweep)
        _assert_arc_equal(arc, arc2.scale(-0.5 - 0.5j))

        # horizontal mirror
        arc2 = arc.scale(-1 + 1j)
        assert arc2.center == pytest.approx(-arc.center.conjugate())
        assert arc2.radius == pytest.approx(arc.radius)
        assert arc2.begin == pytest.approx(-arc.begin.conjugate())
        assert arc2.end == pytest.approx(-arc.end.conjugate())
        assert arc2.sweep == pytest.approx(-arc.sweep)
        _assert_arc_equal(arc, arc2.scale(-1 + 1j))

        # vertical mirror
        arc2 = arc.scale(1 - 1j)
        assert arc2.center == pytest.approx(arc.center.conjugate())
        assert arc2.radius == pytest.approx(arc.radius)
        assert arc2.begin == pytest.approx(arc.begin.conjugate())
        assert arc2.end == pytest.approx(arc.end.conjugate())
        assert arc2.sweep == pytest.approx(-arc.sweep)
        _assert_arc_equal(arc, arc2.scale(1 - 1j))


def test_arc_has_angle():
    assert ArcSegment(0, 1, (-0.1, 0.1))._angle_inside(0) == math.tau
    assert ArcSegment(0, 1, (0.1, -0.1))._angle_inside(0) == 0
    assert ArcSegment(0, 1, (math.tau - 0.1, math.tau + 0.1))._angle_inside(0) == math.tau
    assert ArcSegment(0, 1, (0.1, math.tau - 0.1))._angle_inside(0) is None

    assert ArcSegment(0, 1, (-0.1, 0.1))._angle_inside(math.pi) is None
    assert ArcSegment(0, 1, (0.1, -0.1))._angle_inside(math.pi) is None
    assert ArcSegment(0, 1, (math.tau - 0.1, math.tau + 0.1))._angle_inside(math.pi) is None
    assert ArcSegment(0, 1, (0.1, math.tau - 0.1))._angle_inside(math.pi) == math.pi


def test_arc_circle_has_all_angles():
    for angle in np.linspace(0, math.tau, 13):
        assert ArcSegment(0, 1, (0, math.tau))._angle_inside(angle) is not None


def _assert_intersect(a, b):
    a = tuple(a)
    b = tuple(b)
    assert pytest.approx(a) in [b, b[::-1]]


def test_arc_intersect_x_circle():
    arc = ArcSegment(0, 1, (0, math.tau))
    _assert_intersect(arc.intersect_x(0), [math.pi / 2, 3 * math.pi / 2])
    _assert_intersect(arc.intersect_x(-1), [math.pi])
    _assert_intersect(arc.intersect_x(1), [0])
    _assert_intersect(arc.intersect_x(2), [])
    _assert_intersect(arc.intersect_x(-2), [])


def test_arc_intersect_x():
    arc = ArcSegment(0, 1, (2, 0.1))
    _assert_intersect(arc.intersect_x(0), [math.pi / 2])
    _assert_intersect(arc.intersect_x(-1), [])
    _assert_intersect(arc.intersect_x(1), [])

    arc = ArcSegment(0, 1, (2, math.tau - 0.1))
    _assert_intersect(arc.intersect_x(0), [3 * math.pi / 2])
    _assert_intersect(arc.intersect_x(-1), [math.pi])
    _assert_intersect(arc.intersect_x(1), [])

    arc = ArcSegment(0, 1, (math.pi + 0.1, 3 * math.pi - 0.1))
    _assert_intersect(arc.intersect_x(0), [3 * math.pi / 2, 5 * math.pi / 2])
    _assert_intersect(arc.intersect_x(-1), [])
    _assert_intersect(arc.intersect_x(1), [math.tau])


def test_arc_divide():
    arc = ArcSegment(0, 1, (0.1, math.tau - 0.1))
    assert arc.divide(1) == (ArcSegment(0, 1, (0.1, 1)), ArcSegment(0, 1, (1, math.tau - 0.1)))
    assert arc.divide(math.pi) == arc.divide(math.pi * 3)

    with pytest.raises(ValueError):
        arc.divide(0)
    with pytest.raises(ValueError):
        arc.divide(math.tau)

    arc = ArcSegment(0, 1, (math.pi - 0.1, -math.pi + 0.1))
    assert arc.divide(0) == (
        ArcSegment(0, 1, (math.pi - 0.1, 0)),
        ArcSegment(0, 1, (0, -math.pi + 0.1)),
    )

    with pytest.raises(ValueError):
        arc.divide(math.pi)
    with pytest.raises(ValueError):
        arc.divide(math.pi * 3)


def _assert_crop_x(arc, x, keep_smaller):
    angles = np.linspace(*arc.angles, 20)
    pts = arc.point(angles)
    if keep_smaller:
        assert np.all((pts.real <= x) | np.isclose(pts.real, x))
    else:
        assert np.all((pts.real >= x) | np.isclose(pts.real, x))


@pytest.mark.parametrize(
    "arc x keep_smaller exp_count".split(),
    [
        (ArcSegment(0, 1, (0, math.tau)), 0, True, 1),
        (ArcSegment(0, 1, (0, math.tau)), 0, False, 2),
        (ArcSegment(0, 1, (0, math.tau)), -1, True, 0),
        (ArcSegment(0, 1, (0, math.tau)), -1, False, ...),
        (ArcSegment(0, 1, (0, math.tau)), 1, True, ...),
        (ArcSegment(0, 1, (0, math.tau)), 1, False, 0),
        (ArcSegment(0, 1, (3 / 2 * math.pi - 0.1, -math.pi / 2 + 0.1)), 0, True, 1),
        (ArcSegment(0, 1, (3 / 2 * math.pi - 0.1, -math.pi / 2 + 0.1)), 0, False, 1),
        (ArcSegment(0, 1, (3 / 2 * math.pi - 0.1, -math.pi / 2 + 0.1)), -1, True, 0),
        (ArcSegment(0, 1, (3 / 2 * math.pi - 0.1, -math.pi / 2 + 0.1)), -1, False, ...),
        (ArcSegment(0, 1, (3 / 2 * math.pi - 0.1, -math.pi / 2 + 0.1)), 1, True, ...),
        (ArcSegment(0, 1, (3 / 2 * math.pi - 0.1, -math.pi / 2 + 0.1)), 1, False, 0),
        (ArcSegment(0, 1, (0.1, math.tau - 0.1)), 0, False, 2),
        (ArcSegment(0, 1, (0.1, math.tau - 0.1)), 0, True, 1),
        (ArcSegment(0, 1, (0.1, math.tau - 0.1)), -1, True, 0),
        (ArcSegment(0, 1, (0.1, math.tau - 0.1)), -1, False, ...),
        (ArcSegment(0, 1, (0.1, math.tau - 0.1)), 1, True, ...),
        (ArcSegment(0, 1, (0.1, math.tau - 0.1)), 1, False, 0),
        (ArcSegment(0, 1, (math.pi / 2 - 0.1, -3 / 2 * math.pi + 0.1)), 1, False, 0),
        (ArcSegment(0, 1, (math.pi / 2 - 0.1, -3 / 2 * math.pi + 0.1)), 1, True, ...),
        (ArcSegment(0, 1, (math.pi / 2 - 0.1, -3 / 2 * math.pi + 0.1)), -1, False, ...),
        (ArcSegment(0, 1, (math.pi / 2 - 0.1, -3 / 2 * math.pi + 0.1)), -1, True, 0),
        (ArcSegment(0, 1, (math.pi / 2 - 0.1, -3 / 2 * math.pi + 0.1)), 0, True, 1),
        (ArcSegment(0, 1, (math.pi / 2 - 0.1, -3 / 2 * math.pi + 0.1)), 0, False, 1),
        (ArcSegment(0, 1, (math.pi - 0.1, -math.pi + 0.1)), 0, False, 1),
        (ArcSegment(0, 1, (math.pi - 0.1, -math.pi + 0.1)), 0, True, 2),
        (ArcSegment(0, 1, (math.pi - 0.1, -math.pi + 0.1)), -1, True, 0),
        (ArcSegment(0, 1, (math.pi - 0.1, -math.pi + 0.1)), -1, False, ...),
        (ArcSegment(0, 1, (math.pi - 0.1, -math.pi + 0.1)), 1, False, 0),
        (ArcSegment(0, 1, (math.pi - 0.1, -math.pi + 0.1)), 1, True, 1),
    ],
)
def test_arc_crop_x(arc, x, keep_smaller, exp_count):
    lst = list(arc.crop_x(x, keep_smaller))

    if exp_count is ...:
        assert len(lst) == 1
    else:
        assert len(lst) == exp_count

    for sub in lst:
        _assert_crop_x(sub, x, keep_smaller)
    if exp_count is ...:
        _assert_arc_equal(arc, lst[0])

    # reverse should work the same
    lst2 = list(arc.reverse().crop_x(x, keep_smaller))

    if exp_count is ...:
        assert len(lst2) == 1
    else:
        assert len(lst2) == exp_count
    for sub in lst2:
        _assert_crop_x(sub, x, keep_smaller)

    # both results should be identical
    for sub1, sub2 in zip(lst, lst2[::-1]):
        _assert_arc_equal(sub1, sub2.reverse())


def test_arc_to_polyline():
    tolerance = 0.1
    arc = ArcSegment(0, 2, (3, 4.5))
    pts = arc.to_polyline(tolerance)

    assert pts[0] == arc.begin
    assert pts[-1] == arc.end

    interp = vpype.interpolate(pts, tolerance / 100)

    dist_to_center = interp - arc.center
    radius = np.hypot(dist_to_center.real, dist_to_center.imag)

    assert np.all((radius >= arc.radius - tolerance) & (radius <= arc.radius + tolerance))
    # make sure we're not too precise
    # FIXME
    assert np.any(radius <= arc.radius - tolerance / 2)
