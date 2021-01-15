"""
Qt Viewer
"""
import functools
from typing import Optional

import moderngl as mgl
from PySide2.QtCore import QEvent, QSize, Qt
from PySide2.QtOpenGL import QGLFormat, QGLWidget
from PySide2.QtWidgets import QAction, QActionGroup, QToolBar, QVBoxLayout, QWidget

import vpype as vp

from .engine import Engine, ViewMode


class QtViewerWidget(QGLWidget):
    def __init__(self, document: Optional[vp.Document] = None, parent=None):
        fmt = QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)
        super().__init__(fmt, parent=parent)

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
        if self._mouse_drag:
            factor = self.window().devicePixelRatio()
            self.engine.pan(
                factor * (evt.x() - self._last_mouse_x),
                factor * (evt.y() - self._last_mouse_y),
            )
            self.update()
            self._last_mouse_x = evt.x()
            self._last_mouse_y = evt.y()

    def mouseReleaseEvent(self, evt):
        self._mouse_drag = False

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

        self._viewer_widget = QtViewerWidget(document=document, parent=self)

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

        # setup layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._viewer_widget)
        self.setLayout(layout)

    def set_view_mode(self, mode: ViewMode) -> None:
        self._viewer_widget.engine.view_mode = mode
        self._viewer_widget.update()

    def set_show_pen_up(self, show_pen_up: bool) -> None:
        self._viewer_widget.engine.show_pen_up = show_pen_up
        self._viewer_widget.update()

    def set_show_points(self, show_points: bool) -> None:
        self._viewer_widget.engine.show_points = show_points
        self._viewer_widget.update()
