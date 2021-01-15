import numpy as np


def orthogonal_projection_matrix(
    left: float, right: float, bottom: float, top: float, near: float, far: float, dtype=None
) -> np.ndarray:
    """Creates an orthogonal projection matrix."""

    rml = right - left
    tmb = top - bottom
    fmn = far - near

    A = 2.0 / rml
    B = 2.0 / tmb
    C = -2.0 / fmn
    Tx = -(right + left) / rml
    Ty = -(top + bottom) / tmb
    Tz = -(far + near) / fmn

    return np.array(
        (
            (A, 0.0, 0.0, 0.0),
            (0.0, B, 0.0, 0.0),
            (0.0, 0.0, C, 0.0),
            (Tx, Ty, Tz, 1.0),
        ),
        dtype=dtype,
    )


# TODO: unused
def translation_matrix(dx: float, dy: float, dtype=None) -> np.ndarray:
    return np.array(
        (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (dx, dy, 0.0, 1.0),
        ),
        dtype=dtype,
    )
