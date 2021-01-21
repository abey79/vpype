import os

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QActionGroup


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
            act = self.addAction(QAction(f"{w} mm"))
            act.setCheckable(True)
            act.setChecked(w == current)
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
            act = self.addAction(QAction(f"{int(w*100)}%"))
            act.setCheckable(True)
            act.setChecked(w == current)
            act.setData(w)
