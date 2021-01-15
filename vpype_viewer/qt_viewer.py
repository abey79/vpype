"""
Qt Viewer
"""
import functools
from typing import Optional

import moderngl as mgl
from PySide2.QtCore import QEvent, QSize, Qt, Signal
from PySide2.QtOpenGL import QGLFormat, QGLWidget
from PySide2.QtWidgets import (
    QAction,
    QActionGroup,
    QLabel,
    QMenu,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import vpype as vp

from .engine import Engine, ViewMode


# noinspection PyUnresolvedReferences
class QtViewerWidget(QGLWidget):
    mouse_coords = Signal(str)

    def __init__(self, document: Optional[vp.Document] = None, parent=None):
        fmt = QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)
        super().__init__(fmt, parent=parent)

        self.setMouseTracking(True)

        self._document = document

        self._last_mouse_x = 0.0
        self._last_mouse_y = 0.0
        self._mouse_drag = False

        # deferred initialization in initializeGL()
        self._ctx: Optional[mgl.Context] = None
        self._screen = None
        self.engine = Engine(view_mode=ViewMode.FAST, show_pen_up=False, render_cb=self.update)

        # adjust default scale based on hidpi
        self.engine.scale = self.window().devicePixelRatio()

    def document(self) -> Optional[vp.Document]:
        return self._document

    def set_document(self, document: vp.Document) -> None:
        self._document = document
        self.engine.document = document

    def initializeGL(self):
        self._ctx = mgl.create_context()
        factor = self.window().devicePixelRatio()
        self._ctx.viewport = (0, 0, factor * self.width(), factor * self.height())
        self._screen = self._ctx.detect_framebuffer()

        self.engine.post_init(self._ctx, factor * self.width(), factor * self.height())
        self.engine.document = self._document
        self.engine.fit_to_viewport()

    def paintGL(self):
        self._screen.use()
        self.engine.render()

    def resizeGL(self, w: int, h: int) -> None:
        self.engine.resize(w, h)
        if self._ctx:
            self._ctx.viewport = (0, 0, w, h)

    def mousePressEvent(self, evt):
        self._last_mouse_x = evt.x()
        self._last_mouse_y = evt.y()
        self._mouse_drag = True

    def mouseMoveEvent(self, evt):
        factor = self.window().devicePixelRatio()

        if self._mouse_drag:
            self.engine.pan(
                factor * (evt.x() - self._last_mouse_x),
                factor * (evt.y() - self._last_mouse_y),
            )
            self.update()
            self._last_mouse_x = evt.x()
            self._last_mouse_y = evt.y()

        x, y = self.engine.viewport_to_model(factor * evt.x(), factor * evt.y())
        self.mouse_coords.emit(f"{x:.5f}, {y:.5f}")

    def mouseReleaseEvent(self, evt):
        self._mouse_drag = False

    def leaveEvent(self, event: QEvent) -> None:
        self.mouse_coords.emit("")

    def event(self, event: QEvent) -> bool:
        # handle pinch zoom on mac
        if event.type() == QEvent.Type.NativeGesture:
            if event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                factor = self.window().devicePixelRatio()
                self.engine.zoom(
                    event.value(), event.localPos().x() * factor, event.localPos().y() * factor
                )
                self.update()
                return True

        return super().event(event)


class QtViewer(QWidget):
    def __init__(self, document: Optional[vp.Document] = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("vpype viewer")

        self._viewer_widget = QtViewerWidget(parent=self)

        # setup toolbar
        self._toolbar = QToolBar()
        self._toolbar.setIconSize(QSize(32, 32))

        view_mode_grp = QActionGroup(self._toolbar)
        view_mode_grp.addAction(
            QAction(
                "None",
                checkable=True,
                triggered=functools.partial(self.set_view_mode, ViewMode.NONE),
            )
        )
        view_mode_grp.addAction(
            QAction(
                "Fast",
                checkable=True,
                checked=True,
                triggered=functools.partial(self.set_view_mode, ViewMode.FAST),
            )
        )
        view_mode_grp.addAction(
            QAction(
                "FastC",
                checkable=True,
                triggered=functools.partial(self.set_view_mode, ViewMode.FAST_COLORFUL),
            )
        )
        view_mode_grp.addAction(
            QAction(
                "Prev",
                checkable=True,
                triggered=functools.partial(self.set_view_mode, ViewMode.PREVIEW),
            )
        )

        self._toolbar.addActions(view_mode_grp.actions())
        self._toolbar.addSeparator()
        show_pen_up_act = self._toolbar.addAction("PenUp")
        show_pen_up_act.setCheckable(True)
        show_pen_up_act.triggered.connect(self.set_show_pen_up)
        show_points_act = self._toolbar.addAction("Pts")
        show_points_act.setCheckable(True)
        show_points_act.triggered.connect(self.set_show_points)
        fit_act = self._toolbar.addAction("Fit")
        fit_act.triggered.connect(self._viewer_widget.engine.fit_to_viewport)

        self._toolbar.addSeparator()

        self._layer_visibility_btn = QToolButton()
        self._layer_visibility_btn.setText("Layer")
        self._layer_visibility_btn.setMenu(QMenu(self._layer_visibility_btn))
        self._layer_visibility_btn.setPopupMode(QToolButton.MenuButtonPopup)
        self._layer_visibility_btn.pressed.connect(self._layer_visibility_btn.showMenu)
        self._toolbar.addWidget(self._layer_visibility_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._toolbar.addWidget(spacer)

        mouse_coord_lbl = QLabel("")
        font = mouse_coord_lbl.font()
        font.setPointSize(11)
        mouse_coord_lbl.setFont(font)
        self._toolbar.addWidget(mouse_coord_lbl)
        # noinspection PyUnresolvedReferences
        self._viewer_widget.mouse_coords.connect(mouse_coord_lbl.setText)

        # setup layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._viewer_widget)
        self.setLayout(layout)

        if document is not None:
            self.set_document(document)

    def set_document(self, document: vp.Document) -> None:
        self._viewer_widget.set_document(document)
        self._update_layer_menu()

    def _update_layer_menu(self):
        layer_menu = QMenu(self._layer_visibility_btn)
        for layer_id in sorted(self._viewer_widget.document().layers):
            action = layer_menu.addAction(f"Layer {layer_id}")
            action.setCheckable(True)
            action.setChecked(True)
            # TODO: set color icon
            action.triggered.connect(
                functools.partial(self._viewer_widget.engine.toggle_layer_visibility, layer_id)
            )
        self._layer_visibility_btn.setMenu(layer_menu)

    def set_view_mode(self, mode: ViewMode) -> None:
        self._viewer_widget.engine.view_mode = mode
        self._viewer_widget.update()

    def set_show_pen_up(self, show_pen_up: bool) -> None:
        self._viewer_widget.engine.show_pen_up = show_pen_up
        self._viewer_widget.update()

    def set_show_points(self, show_points: bool) -> None:
        self._viewer_widget.engine.show_points = show_points
        self._viewer_widget.update()
