import os
from typing import Optional, Tuple

import cachetools
import cachetools.keys
import moderngl as mgl
from PySide2.QtGui import QIcon

ColorType = Tuple[float, float, float, float]


@cachetools.cached(cache={}, key=lambda name, ctx: cachetools.keys.hashkey((name, id(ctx))))
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


def load_icon(path: str) -> QIcon:
    path = os.path.abspath(
        os.path.dirname(__file__) + os.path.sep + "resources" + os.path.sep + path
    )

    return QIcon(path)
