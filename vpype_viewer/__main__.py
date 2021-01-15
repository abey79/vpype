import sys

from PySide2 import QtWidgets

import vpype as vp

from .qt_viewer import QtViewer

app = QtWidgets.QApplication(sys.argv)

# doc = vp.read_multilayer_svg("/Users/hhip/Downloads/meow3.svg", 0.1)
# doc = vp.read_multilayer_svg("/Users/hhip/Downloads/spirograph-grids/spirograph-grid.svg", 0.1)
doc = vp.read_multilayer_svg("/Users/hhip/src/vsketch/mywork/bezier_column_saved.svg", 0.1)
widget = QtViewer(doc)
widget.resize(1024, 768)
widget.show()
sys.exit(app.exec_())
