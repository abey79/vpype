import os
from typing import Optional, Tuple

import cachetools
import cachetools.keys
import moderngl as mgl
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QActionGroup

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


class PenWidthActionGroup(QActionGroup):
    widths = [
        0.05,
        0.1,
        0.15,
        0.2,
        0.25,
        0.3,
        0.35,
        0.4,
        0.45,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.2,
    ]

    def __init__(self, current: float = 0.3, parent=None):
        super().__init__(parent)

        if current not in self.widths:
            self.widths.append(current)
        for w in sorted(self.widths):
            act = self.addAction(QAction(f"{w} mm", checkable=True, checked=(w == current)))
            act.setData(w)


class PenOpacityActionGroup(QActionGroup):
    opacities = [
        0.3,
        0.5,
        0.7,
        0.8,
        0.9,
        0.95,
        1,
    ]

    def __init__(self, current: float = 0.8, parent=None):
        super().__init__(parent)

        if current not in self.opacities:
            self.opacities.append(current)
        for w in sorted(self.opacities):
            act = self.addAction(
                QAction(f"{int(w*100)}%", checkable=True, checked=(w == current))
            )
            act.setData(w)
