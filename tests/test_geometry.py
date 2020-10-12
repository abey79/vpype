import numpy as np
import pytest

from vpype import interpolate

# noinspection PyProtectedMember
from vpype.geometry import _interpolate_crop, crop, crop_half_plane, reloop


def test_reloop_small():
    line = np.array([3, 3], dtype=complex)
    assert np.all(reloop(line, 0) == line)
    assert np.all(reloop(line, 1) == line)


def test_reloop():
    line = np.array([0, 1, 2, 3, 0.2], dtype=complex)
    assert np.all(reloop(line, 2) == np.array([2, 3, 0.1, 1, 2], dtype=complex))
    assert np.all(reloop(line, 0) == np.array([0.1, 1, 2, 3, 0.1], dtype=complex))
    assert np.all(reloop(line, 4) == np.array([0.1, 1, 2, 3, 0.1], dtype=complex))


@pytest.mark.parametrize(
    ["line", "step", "expected"],
    [
        ([0, 10], 1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        ([0, 1, 3, 10], 1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        ([0, 1j, 3j, 10j], 1, [0, 1j, 2j, 3j, 4j, 5j, 6j, 7j, 8j, 9j, 10j]),
        ([0, 10], 10, [0, 10]),
        ([0, 10], 1.01, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        ([0, 1, 1 + 1j, 1j, 0], 0.5, [0, 0.5, 1, 1 + 0.5j, 1 + 1j, 0.5 + 1j, 1j, 0.5j, 0]),
    ],
)
def test_interpolate(line, step, expected):
    result = interpolate(np.array(line, dtype=complex), step)
    assert len(result) == len(expected)
    assert np.all(np.isclose(result, np.array(expected, dtype=complex),))


def test_interpolate_crop():
    assert _interpolate_crop(5, 10, 7, axis=0) == 7
    assert _interpolate_crop(0, 10 + 10j, 5, axis=0) == 5 + 5j
    assert _interpolate_crop(0, 10 + 20j, 8, axis=1) == 4 + 8j


@pytest.mark.parametrize(
    ["line", "expected"],
    [
        ([-1, -2, -3], []),
        ([1, 2, 3], [[1, 2, 3]]),
        ([1j, 2j, 3j], [[1j, 2j, 3j]]),
        ([1 + 1j, 2 + 2j, 3 + 3j], [[1 + 1j, 2 + 2j, 3 + 3j]]),
        ([1, 2, 3, -1, -1, 4, 3], [[1, 2, 3, 0], [0, 4, 3]]),
        ([1, 2, 3, -1, -1, 4, 3, -1], [[1, 2, 3, 0], [0, 4, 3, 0]]),
        ([-1, 1, 2, 3, -1, -1, 4, 3, -1], [[0, 1, 2, 3, 0], [0, 4, 3, 0]]),
        ([-1, 1, 2, 3, 4, 3, -1], [[0, 1, 2, 3, 4, 3, 0]]),
        (
            [-1 + 5j, 1 + 5j, 2 + 5j, 3 + 5j, -1 + 5j, -1 + 5j, 4 + 5j, 3 + 5j, -1 + 5j],
            [[+5j, 1 + 5j, 2 + 5j, 3 + 5j, +5j], [+5j, 4 + 5j, 3 + 5j, +5j]],
        ),
        ([-1, 1], [[0, 1]]),
        ([1, -1], [[1, 0]]),
        ([-1, 0], []),
        ([-1, 0, 1], [[0, 1]]),
        ([0, 1j], [[0, 1j]]),
    ],
)
def test_crop_half_plane_x_gt_0(line, expected):
    result = crop_half_plane(np.array(line, dtype=complex), loc=0, axis=0, keep_smaller=False)

    assert len(result) == len(expected)
    for res, exp in zip(result, expected):
        assert np.all(res == np.array(exp, dtype=complex))


@pytest.mark.parametrize(
    ["line", "expected"],
    [
        ([0, 1 + 1j], [[0, 1 + 1j]]),
        ([0, 1, 1 + 1j, 1j, 0], [[0, 1, 1 + 1j, 1j, 0]]),
        ([-1 - 1j, 2 + 2j], [[0, 1 + 1j]]),
        ([-1 - 1j, 0.5 + 0.5j, 2 - 1j], [[0, 0.5 + 0.5j, 1]]),
        (
            [-1 - 1j, 0.5 + 0.5j, 2 - 1j, 2 + 2j, 0.5 + 0.5j, -1 + 2j],
            [[0, 0.5 + 0.5j, 1], [1 + 1j, 0.5 + 0.5j, 1j]],
        ),
    ],
)
def test_crop_unit_square(line, expected):
    result = crop(np.array(line, dtype=complex), 0, 0, 1, 1)

    assert len(result) == len(expected)
    for res, exp in zip(result, expected):
        assert np.all(res == np.array(exp, dtype=complex))
