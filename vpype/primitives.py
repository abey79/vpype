import math

import numpy as np

__ALL__ = ["line", "rect", "circle"]


def line(x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    """Build a line from two points

    Args:
        x0: line start X coordinate
        y0: line start Y coordinate
        x1: line end X coordinate
        y1: line end Y coordinate

    Returns:
        line path
    """
    return np.array([complex(x0, y0), complex(x1, y1)])


def rect(x: float, y: float, width: float, height: float) -> np.ndarray:
    """Build a rectangular path

    Args:
        x: top-left corner X coordinate
        y: top-left corner Y coordinate
        width: rectangle width
        height: rectangle height

    Returns:
        rectangular path
    """
    return np.array(
        [
            complex(x, y),
            complex(x + width, y),
            complex(x + width, y + height),
            complex(x, y + height),
            complex(x, y),
        ]
    )


def arc(
    x: float,
    y: float,
    radius: float,
    start: float,
    stop: float,
    quantization: float = 0.1,
) -> np.ndarray:
    """Build a circular arc path. Zero angles refer to east of unit circle and positive values
    extend counter-clockwise.

    Args:
        x: center X coordinate
        y: center Y coordinate
        radius: circle radius
        start: start angle (degree)
        stop: stop angle (degree)
        quantization: maximum length of linear segment

    Returns:
        arc path
    """

    def normalize_angle(a):
        while a > 360:
            a -= 360
        while a < 0:
            a += 360
        return a

    start = normalize_angle(start)
    stop = normalize_angle(stop)
    if stop < start:
        stop += 360
    elif start == stop:
        raise ValueError("start and stop angles must have different values")

    n = math.ceil(stop - start / 180 * math.pi * radius / quantization)
    angle = np.linspace(start, stop, n)
    angle[angle == 360] = 0
    angle *= math.pi / 180
    return radius * (np.cos(-angle) + 1j * np.sin(-angle)) + complex(x, y)


def circle(x: float, y: float, radius: float, quantization: float = 0.1) -> np.ndarray:
    """Build a circular path.

    Args:
        x: center X coordinate
        y: center Y coordinate
        radius: circle radius
        quantization: maximum length of linear segment

    Returns:
        circular path
    """
    return arc(x, y, radius, 0, 360, quantization)
