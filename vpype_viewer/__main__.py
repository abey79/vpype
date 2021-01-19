import sys

import numpy as np
from PySide2 import QtWidgets
from PySide2.QtCore import Qt

import vpype as vp

from .qt_viewer import QtViewer

app = QtWidgets.QApplication(sys.argv)
app.setAttribute(Qt.AA_UseHighDpiPixmaps)

# TODO this should probably be moved somewhere else
app.setStyleSheet(
    """
QToolButton:pressed {
    background-color: rgba(0, 0, 0, 0.2);
}
"""
)


doc = vp.Document()
doc.page_size = 600, 400

tt = np.linspace(0, np.pi, 20)
doc.add(
    vp.LineCollection(
        [
            i * 15j
            + np.array([50 + 50j, 100 + 50j, 100 + 50j + 10 * complex(np.cos(t), np.sin(t))])
            for i, t in enumerate(tt)
        ]
    )
)


# unit_line = np.array([0, 10 + 1j, 2j])
# unit_line = np.array([0, 10, 5])
# doc.add(
#     vp.LineCollection(
#         [
#             complex(50, 50 + 3 * i) + sz * unit_line.real + unit_line.imag * 1j
#             for i, sz in enumerate(np.arange(50))
#         ]
#     )
# )

#
# doc.add(
#     vp.LineCollection(
#         [
#             np.array([-4, -2, 0, 10], dtype=complex) + complex(50, 50),
#             np.array([-4, -2, 0, 1], dtype=complex) + complex(50, 55),
#             np.array([-4, -2, 0, 0.9], dtype=complex) + complex(50, 60),
#             # ...
#             np.array([-4, -2, 0, 2, 10], dtype=complex) + complex(50, 100),
#             np.array([-4, -2, 0, 1, 10], dtype=complex) + complex(50, 105),
#             np.array([-4, -2, 0, 0.9, 10], dtype=complex) + complex(50, 110),
#         ]
#     )
# )
#
# unit_line = np.array([-3, -1.5, 0, 0.5 + 0.1j, 1, 2.5, 4], dtype=complex)
# doc.add(
#     vp.LineCollection(
#         [
#             complex(50, 50 + 3 * i) + sz * unit_line.real + unit_line.imag * 1j
#             for i, sz in enumerate(np.logspace(2, -1, 100))
#         ]
#     )
# )

# doc = vp.read_multilayer_svg("/Users/hhip/Downloads/meow3.svg", 0.1)
# doc = vp.read_multilayer_svg("/Users/hhip/Downloads/spirograph-grids/spirograph-grid.svg", 0.1)
# doc = vp.read_multilayer_svg("/Users/hhip/src/vsketch/mywork/bezier_column_saved.svg", 0.1)

widget = QtViewer(doc)
widget.resize(1024, 768)
widget.show()
sys.exit(app.exec_())
