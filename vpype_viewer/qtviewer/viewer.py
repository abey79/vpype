"""
Qt Viewer
"""
import functools
import logging
import math
import os
import sys
from typing import Optional, Union

import moderngl as mgl
from PySide2.QtCore import QEvent, QSettings, QSize, Qt, Signal
from PySide2.QtGui import QScreen, QWheelEvent
from PySide2.QtOpenGL import QGLFormat, QGLWidget
from PySide2.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import vpype as vp

from .._scales import UnitType
from ..engine import Engine, ViewMode
from .utils import PenOpacityActionGroup, PenWidthActionGroup, load_icon

__all__ = ["QtViewerWidget", "QtViewer", "show"]


_DEBUG_ENABLED = "VPYPE_VIEWER_DEBUG" in os.environ


# handle UI scaling
def _configure_ui_scaling():
    viewer_config = vp.config_manager.config.get("viewer", {})
    if "QT_SCALE_FACTOR" not in os.environ and "ui_scale_factor" in viewer_config:
        os.environ["QT_SCALE_FACTOR"] = str(viewer_config["ui_scale_factor"])


_configure_ui_scaling()


class QtViewerWidget(QGLWidget):
    """QGLWidget wrapper around :class:`Engine` to display a :class:`vpype.Document` in
    Qt GUI."""

    mouse_coords = Signal(str)

    def __init__(self, document: Optional[vp.Document] = None, parent=None):
        """Constructor.
        Args:
            document: the document to display
            parent: QWidget parent
        """
        fmt = QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)
        super().__init__(fmt, parent=parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setMouseTracking(True)

        self._document = document

        self._last_mouse_x = 0.0
        self._last_mouse_y = 0.0
        self._mouse_drag = False
        self._factor = 1.0

        # deferred initialization in initializeGL()
        self._ctx: Optional[mgl.Context] = None
        self._screen = None
        self.engine = Engine(
            view_mode=ViewMode.OUTLINE, show_pen_up=False, render_cb=self.update
        )

        self.windowHandle().screenChanged.connect(self.on_screen_changed)

        # print diagnostic information
        screen = self.screen()
        logging.info(
            f"QScreen info: pixelRatio={screen.devicePixelRatio()}, "
            f"physicalSize={screen.physicalSize().toTuple()}, "
            f"physicalDotsPerInch={screen.physicalDotsPerInch()}, "
            f"virtualSize={screen.virtualSize().toTuple()}, "
            f"size={screen.size().toTuple()}, "
            f"logicalDotsPerInch={screen.logicalDotsPerInch()}, "
        )

    def document(self) -> Optional[vp.Document]:
        """Return the :class:`vpype.Document` currently assigned to the widget."""
        return self._document

    def set_document(self, document: Optional[vp.Document]) -> None:
        """Assign a new :class:`vpype.Document` to the widget."""
        self._document = document
        self.engine.document = document

    def on_screen_changed(self, screen: QScreen):
        self._factor = screen.devicePixelRatio()
        self.engine.pixel_factor = self._factor

        # force an update and reset of viewport's dimensions
        self.resizeGL(
            self.geometry().width() * self._factor, self.geometry().height() * self._factor
        )

    def initializeGL(self):
        self._ctx = mgl.create_context()
        logging.info(f"Context info: {self._ctx.info}")

        self._ctx.viewport = (0, 0, self._factor * self.width(), self._factor * self.height())
        self._screen = self._ctx.detect_framebuffer()

        self.engine.post_init(
            self._ctx, int(self._factor * self.width()), int(self._factor * self.height())
        )
        self.on_screen_changed(self.screen())
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
            self.engine.pan(
                self._factor * (evt.x() - self._last_mouse_x),
                self._factor * (evt.y() - self._last_mouse_y),
            )
            self._last_mouse_x = evt.x()
            self._last_mouse_y = evt.y()

        # update mouse coordinate display
        if evt.x() < 0 or evt.x() > self.width() or evt.y() < 0 or evt.y() > self.height():
            # noinspection PyUnresolvedReferences
            self.mouse_coords.emit("")
        else:
            x, y = self.engine.viewport_to_model(
                self._factor * evt.x(), self._factor * evt.y()
            )
            spec = self.engine.scale_spec
            decimals = max(0, math.ceil(-math.log10(1 / spec.to_px / self.engine.scale)))
            # noinspection PyUnresolvedReferences
            self.mouse_coords.emit(
                f"{x / spec.to_px:.{decimals}f}{spec.unit}, "
                f"{y / spec.to_px:.{decimals}f}{spec.unit}"
            )

    def mouseReleaseEvent(self, evt):
        self._mouse_drag = False

    def leaveEvent(self, event: QEvent) -> None:
        # noinspection PyUnresolvedReferences
        self.mouse_coords.emit("")  # type: ignore

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.source() == Qt.MouseEventSource.MouseEventSynthesizedBySystem:
            # track pad
            scroll_delta = event.pixelDelta()
            self.engine.pan(self._factor * scroll_delta.x(), self._factor * scroll_delta.y())
        else:
            # mouse wheel
            zoom_delta = event.angleDelta().y()
            self.engine.zoom(
                zoom_delta / 500.0, self._factor * event.x(), self._factor * event.y()
            )

    def event(self, event: QEvent) -> bool:
        # handle pinch zoom on mac
        if (
            event.type() == QEvent.Type.NativeGesture
            and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture
        ):
            self.engine.zoom(
                2.0 * event.value(),
                event.localPos().x() * self._factor,
                event.localPos().y() * self._factor,
            )
            return True

        return super().event(event)


class QtViewer(QWidget):
    """Full featured, stand-alone viewer suitable for displaying a :class:`vpype.Document` to
    a user."""

    def __init__(
        self,
        document: Optional[vp.Document] = None,
        view_mode: ViewMode = ViewMode.PREVIEW,
        show_pen_up: bool = False,
        show_points: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self._settings = QSettings()
        self._settings.beginGroup("viewer")

        self.setWindowTitle("vpype viewer")
        self.setStyleSheet(
            """
        QToolButton:pressed {
            background-color: rgba(0, 0, 0, 0.2);
        }
        """
        )

        self._viewer_widget = QtViewerWidget(parent=self)

        # setup toolbar
        self._toolbar = QToolBar()
        self._icon_size = QSize(32, 32)
        self._toolbar.setIconSize(self._icon_size)

        view_mode_grp = QActionGroup(self._toolbar)
        if _DEBUG_ENABLED:
            act = view_mode_grp.addAction("None")
            act.setCheckable(True)
            act.setChecked(view_mode == ViewMode.NONE)
            act.triggered.connect(functools.partial(self.set_view_mode, ViewMode.NONE))
        act = view_mode_grp.addAction("Outline Mode")
        act.setCheckable(True)
        act.setChecked(view_mode == ViewMode.OUTLINE)
        act.triggered.connect(functools.partial(self.set_view_mode, ViewMode.OUTLINE))
        act = view_mode_grp.addAction("Outline Mode (Colorful)")
        act.setCheckable(True)
        act.setChecked(view_mode == ViewMode.OUTLINE_COLORFUL)
        act.triggered.connect(functools.partial(self.set_view_mode, ViewMode.OUTLINE_COLORFUL))
        act = view_mode_grp.addAction("Preview Mode")
        act.setCheckable(True)
        act.setChecked(view_mode == ViewMode.PREVIEW)
        act.triggered.connect(functools.partial(self.set_view_mode, ViewMode.PREVIEW))
        self.set_view_mode(view_mode)

        # VIEW MODE
        # view modes
        view_mode_btn = QToolButton()
        view_mode_menu = QMenu(view_mode_btn)
        act = view_mode_menu.addAction("View Mode:")
        act.setEnabled(False)
        view_mode_menu.addActions(view_mode_grp.actions())
        view_mode_menu.addSeparator()
        # show pen up
        act = view_mode_menu.addAction("Show Pen-Up Trajectories")
        act.setCheckable(True)
        act.setChecked(show_pen_up)
        act.toggled.connect(self.set_show_pen_up)
        self._viewer_widget.engine.show_pen_up = show_pen_up
        # show points
        act = view_mode_menu.addAction("Show Points")
        act.setCheckable(True)
        act.setChecked(show_points)
        act.toggled.connect(self.set_show_points)
        self._viewer_widget.engine.show_points = show_points
        # preview mode options
        view_mode_menu.addSeparator()
        act = view_mode_menu.addAction("Preview Mode Options:")
        act.setEnabled(False)
        # pen width
        pen_width_menu = view_mode_menu.addMenu("Pen Width")
        act_grp = PenWidthActionGroup(0.3, parent=pen_width_menu)
        act_grp.triggered.connect(self.set_pen_width_mm)
        pen_width_menu.addActions(act_grp.actions())
        self.set_pen_width_mm(0.3)
        # pen opacity
        pen_opacity_menu = view_mode_menu.addMenu("Pen Opacity")
        act_grp = PenOpacityActionGroup(0.8, parent=pen_opacity_menu)
        act_grp.triggered.connect(self.set_pen_opacity)
        pen_opacity_menu.addActions(act_grp.actions())
        self.set_pen_opacity(0.8)
        # debug view
        if _DEBUG_ENABLED:
            act = view_mode_menu.addAction("Debug View")
            act.setCheckable(True)
            act.toggled.connect(self.set_debug)
        # rulers
        view_mode_menu.addSeparator()
        act = view_mode_menu.addAction("Show Rulers")
        act.setCheckable(True)
        val = bool(self._settings.value("show_rulers", True))
        act.setChecked(val)
        act.toggled.connect(self.set_show_rulers)
        self._viewer_widget.engine.show_rulers = val
        # units
        units_menu = view_mode_menu.addMenu("Units")
        unit_action_grp = QActionGroup(units_menu)
        unit_type = UnitType(self._settings.value("unit_type", UnitType.METRIC))
        act = unit_action_grp.addAction("Metric")
        act.setCheckable(True)
        act.setChecked(unit_type == UnitType.METRIC)
        act.setData(UnitType.METRIC)
        act = unit_action_grp.addAction("Imperial")
        act.setCheckable(True)
        act.setChecked(unit_type == UnitType.IMPERIAL)
        act.setData(UnitType.IMPERIAL)
        act = unit_action_grp.addAction("Pixel")
        act.setCheckable(True)
        act.setChecked(unit_type == UnitType.PIXELS)
        act.setData(UnitType.PIXELS)
        unit_action_grp.triggered.connect(self.set_unit_type)
        units_menu.addActions(unit_action_grp.actions())
        self._viewer_widget.engine.unit_type = unit_type

        view_mode_btn.setMenu(view_mode_menu)
        view_mode_btn.setIcon(load_icon("eye-outline.svg"))
        view_mode_btn.setText("View")
        view_mode_btn.setPopupMode(QToolButton.InstantPopup)
        view_mode_btn.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        self._toolbar.addWidget(view_mode_btn)

        # LAYER VISIBILITY
        self._layer_visibility_btn = QToolButton()
        self._layer_visibility_btn.setIcon(load_icon("layers-triple-outline.svg"))
        self._layer_visibility_btn.setText("Layer")
        self._layer_visibility_btn.setMenu(QMenu(self._layer_visibility_btn))
        self._layer_visibility_btn.setPopupMode(QToolButton.InstantPopup)
        self._layer_visibility_btn.setStyleSheet(
            "QToolButton::menu-indicator { image: none; }"
        )
        self._toolbar.addWidget(self._layer_visibility_btn)

        # FIT TO PAGE
        fit_act = self._toolbar.addAction(load_icon("fit-to-page-outline.svg"), "Fit")
        fit_act.triggered.connect(self._viewer_widget.engine.fit_to_viewport)

        # RULER
        # TODO: not implemented yet
        # self._toolbar.addAction(load_icon("ruler-square.svg"), "Units")

        # MOUSE COORDINATES>
        self._mouse_coord_lbl = QLabel("")
        self._mouse_coord_lbl.setMargin(6)
        self._mouse_coord_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self._mouse_coord_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._toolbar.addWidget(self._mouse_coord_lbl)
        # noinspection PyUnresolvedReferences
        self._viewer_widget.mouse_coords.connect(self.set_mouse_coords)  # type: ignore

        # setup horizontal layout for optional side widgets
        self._hlayout = QHBoxLayout()
        self._hlayout.setSpacing(0)
        self._hlayout.setMargin(0)
        self._hlayout.addWidget(self._viewer_widget)
        widget = QWidget()
        widget.setLayout(self._hlayout)

        # setup global vertical layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(widget)
        self.setLayout(layout)

        if document is not None:
            self.set_document(document)

    def add_side_widget(self, widget: QWidget) -> None:
        self._hlayout.addWidget(widget)

    def set_document(self, document: Optional[vp.Document]) -> None:
        self._viewer_widget.set_document(document)
        self._update_layer_menu()

    def _update_layer_menu(self):
        layer_menu = QMenu(self._layer_visibility_btn)
        doc = self._viewer_widget.document()
        if doc is not None:
            for layer_id in sorted(doc.layers):
                action = layer_menu.addAction(f"Layer {layer_id}")
                action.setCheckable(True)
                action.setChecked(True)
                # TODO: set color icon
                action.triggered.connect(
                    functools.partial(
                        self._viewer_widget.engine.toggle_layer_visibility, layer_id
                    )
                )
        self._layer_visibility_btn.setMenu(layer_menu)

    def set_mouse_coords(self, txt: str) -> None:
        self._mouse_coord_lbl.setText(txt)

    def set_view_mode(self, mode: ViewMode) -> None:
        self._viewer_widget.engine.view_mode = mode

    def set_show_pen_up(self, show_pen_up: bool) -> None:
        self._viewer_widget.engine.show_pen_up = show_pen_up

    def set_show_points(self, show_points: bool) -> None:
        self._viewer_widget.engine.show_points = show_points

    def set_pen_width_mm(self, value: Union[float, QAction]) -> None:
        if isinstance(value, QAction):
            value = value.data()
        self._viewer_widget.engine.pen_width = value / 25.4 * 96.0

    def set_pen_opacity(self, value: Union[float, QAction]) -> None:
        if isinstance(value, QAction):
            value = value.data()
        self._viewer_widget.engine.pen_opacity = value

    def set_debug(self, debug: bool) -> None:
        self._viewer_widget.engine.debug = debug

    def set_show_rulers(self, show_rulers: bool) -> None:
        self._viewer_widget.engine.show_rulers = show_rulers
        self._settings.setValue("show_rulers", show_rulers)

    def set_unit_type(self, sender: QAction) -> None:
        val = UnitType(sender.data())
        self._viewer_widget.engine.unit_type = val
        self._settings.setValue("unit_type", val)


def show(
    document: vp.Document,
    view_mode: ViewMode = ViewMode.PREVIEW,
    show_pen_up: bool = False,
    show_points: bool = False,
    argv=None,
) -> int:
    """Show a viewer for the provided :class:`vpype.Document` instance.

    This function returns when the user close the window.

    Args:
        document: the document to display
        view_mode: view mode
        show_pen_up: render pen-up trajectories
        show_points: render points
        argv: argument passed to Qt

    Returns:
        exit status returned by Qt
    """
    if argv is None and len(sys.argv) > 0:
        argv = [sys.argv[0]]

    if not QApplication.instance():
        app = QApplication(argv)
        app.setOrganizationName("abey79")
        app.setOrganizationDomain("abey79.github.io")
        app.setApplicationName("vpype")
    else:
        app = QApplication.instance()
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    widget = QtViewer(
        document, view_mode=view_mode, show_pen_up=show_pen_up, show_points=show_points
    )
    sz = app.primaryScreen().availableSize()
    widget.move(int(sz.width() * 0.05), int(sz.height() * 0.1))
    widget.resize(int(sz.width() * 0.9), int(sz.height() * 0.8))

    widget.show()

    return app.exec_()
