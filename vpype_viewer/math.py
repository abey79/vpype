import numpy as np


def orthogonal_projection_matrix(
    left: float, right: float, bottom: float, top: float, near: float, far: float, dtype=None
) -> np.ndarray:
    """Creates an orthogonal projection matrix."""

    rml = right - left
    tmb = top - bottom
    fmn = far - near

    a = 2.0 / rml
    b = 2.0 / tmb
    c = -2.0 / fmn
    tx = -(right + left) / rml
    ty = -(top + bottom) / tmb
    tz = -(far + near) / fmn

    # GLSL is column major, thus the transpose
    return np.array(
        (
            (a, 0.0, 0.0, 0.0),
            (0.0, b, 0.0, 0.0),
            (0.0, 0.0, c, 0.0),
            (tx, ty, tz, 1.0),
        ),
        dtype=dtype,
    )
