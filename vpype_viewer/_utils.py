import os
import pathlib
from typing import Optional, Tuple

import cachetools
import cachetools.keys
import moderngl as mgl
import numpy as np
from PIL import Image

ColorType = Tuple[float, float, float, float]


@cachetools.cached(
    cache={},  # type: ignore
    key=lambda name, ctx: cachetools.keys.hashkey((name, id(ctx))),
)
def load_program(name: str, ctx: mgl.Context) -> mgl.Program:
    """Create a program based on a shader name prefix.

    This function automatically load all shader type based on file existence, looking for
    _vertex, _fragment and _geometry suffices in the ``shaders`` directory.

    The same program instance is returned for identical combination of ``name``/``_ctx``.

    Args:
         name: shader file name prefix
         ctx: context

    Returns:
        the loaded program
    """

    def _load_shader(path: str) -> Optional[str]:
        try:
            with open(path) as fp:
                return fp.read()
        except IOError:
            return None

    full_path = os.path.dirname(__file__) + os.path.sep + "shaders" + os.path.sep + name

    return ctx.program(
        vertex_shader=_load_shader(full_path + "_vertex.glsl"),
        fragment_shader=_load_shader(full_path + "_fragment.glsl"),
        geometry_shader=_load_shader(full_path + "_geometry.glsl"),
    )


@cachetools.cached(
    cache={},  # type: ignore
    key=lambda name, ctx, size, components: cachetools.keys.hashkey(
        (name, id(ctx), size, components)
    ),
)
def load_texture_array(
    name: str, ctx: mgl.Context, size: Tuple[int, int, int], components: int = 4
) -> mgl.TextureArray:
    texture_path = pathlib.Path(__file__).parent / "resources" / name
    img = Image.open(str(texture_path))
    texture = ctx.texture_array(size, components, data=img.convert("RGBA").tobytes())
    texture.build_mipmaps()
    return texture


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
