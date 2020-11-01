import math

import numpy as np

__ALL__ = ["line", "rect", "arc", "circle", "ellipse"]


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


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    tl: float = 0,
    tr: float = 0,
    br: float = 0,
    bl: float = 0,
    quantization: float = 0.1,
) -> np.ndarray:
    """Build a rectangular path, with optional rounded angles.

    Args:
        x: top-left corner X coordinate
        y: top-left corner Y coordinate
        width: rectangle width
        height: rectangle height
        tl: top-left corner radius (0 if not provided)
        tr: top-right corner radius (0 if not provided)
        br: bottom-right corner radius (0 if not provided)
        bl: bottom-left corner radius (0 if not provided)
        quantization: maximum size of segments approximating round corners

    Returns:
        rectangular path
    """
    if (tr + tl) > width:
        scale = width / (tr + tl)
        tr *= scale
        tl *= scale
    if (br + bl) > width:
        scale = width / (br + bl)
        tr *= scale
        tl *= scale
    if (tl + bl) > height:
        scale = height / (tl + bl)
        tl *= scale
        bl *= scale
    if (tr + br) > height:
        scale = height / (tr + br)
        tr *= scale
        br *= scale

    if tl != 0:
        p1 = arc(x + tl, y + tl, tl, tl, 90, 180, quantization)
    else:
        p1 = np.array([complex(x, y)])

    if bl != 0:
        p2 = arc(x + bl, y + height - bl, bl, bl, 180, 270, quantization)
    else:
        p2 = np.array([complex(x, y + height)])

    if br != 0:
        p3 = arc(x + width - br, y + height - br, br, br, 270, 360, quantization)
    else:
        p3 = np.array([complex(x + width, y + height)])

    if tr != 0:
        p4 = arc(x + width - tr, y + tr, tr, tr, 0, 90, quantization)
    else:
        p4 = np.array([complex(x + width, y)])

    return np.concatenate((p1, p2, p3, p4, np.array([p1[0]])))


def arc(
    x: float,
    y: float,
    rw: float,
    rh: float,
    start: float,
    stop: float,
    quantization: float = 0.1,
) -> np.ndarray:
    """Build an elliptical arc path. Zero angles refer to east of unit circle and positive
    values extend counter-clockwise.

    Args:
        x: center X coordinate
        y: center Y coordinate
        rw: ellipse half-width
        rh: ellipse half-height (use the same value as ``rw`` for a circular arc)
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

    n = max(3, math.ceil((stop - start) / 180 * math.pi * max(rw, rh) / quantization))
    angle = np.linspace(start, stop, n + 1)
    angle[angle == 360] = 0
    angle *= math.pi / 180
    return rw * np.cos(-angle) + 1j * rh * np.sin(-angle) + complex(x, y)


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
    return arc(x, y, radius, radius, 0, 360, quantization)


def ellipse(x: float, y: float, w: float, h: float, quantization: float = 0.1) -> np.ndarray:
    """Build an elliptical path.

    Args:
        x: center X coordinate
        y: center Y coordinate
        w: half width of the ellipse
        h: half height of the ellipse
        quantization: maximum length of linear segment

    Returns:
        elliptical path
    """
    return arc(x, y, w, h, 0, 360, quantization)
