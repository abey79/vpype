"""
Generic viewer
"""
import enum
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

import moderngl as mgl
import numpy as np

import vpype as vp

from ._painters import (
    LineCollectionFastColorfulPainter,
    LineCollectionFastPainter,
    LineCollectionPenUpPainter,
    LineCollectionPointsPainter,
    LineCollectionPreviewPainter,
    Painter,
    PaperBoundsPainter,
    RulersPainter,
)
from ._scales import DEFAULT_SCALE_SPEC, SCALES_MAP, ScaleSpec, UnitType
from ._utils import ColorType, orthogonal_projection_matrix

_COLORS: List[ColorType] = [
    (0, 0, 1, 1),
    (0, 0.5, 0, 1),
    (1, 0, 0, 1),
    (0, 0.75, 0.75, 1),
    (0, 1, 0, 1),
    (0.75, 0, 0.75, 1),
    (0.75, 0.75, 0, 1),
    (0, 0, 0, 1),
]

__all__ = ["DEFAULT_PEN_WIDTH", "DEFAULT_PEN_OPACITY", "ViewMode", "Engine"]

DEFAULT_PEN_WIDTH = 1.1  # about 0.3mm
DEFAULT_PEN_OPACITY = 0.8


class ViewMode(enum.Enum):
    """View mode enum."""

    NONE = enum.auto()  # for debug purposes
    OUTLINE = enum.auto()
    OUTLINE_COLORFUL = enum.auto()
    PREVIEW = enum.auto()


class Engine:
    """OpenGL-based rendering engine for :class:`vpype.Document`."""

    def __init__(
        self,
        view_mode: ViewMode = ViewMode.OUTLINE,
        show_pen_up: bool = False,
        show_points: bool = False,
        show_rulers: bool = True,
        pen_width: float = DEFAULT_PEN_WIDTH,
        pen_opacity: float = DEFAULT_PEN_OPACITY,
        render_cb: Callable[[], None] = lambda: None,
    ):
        """Constructor.

        Args:
            view_mode: the view mode to use
            show_pen_up: render pen-up trajectories if True
            show_points: render points if True
            show_rulers: display the rulers
            pen_width: pen width (preview only)
            pen_opacity: pen opacity (preview only)
            render_cb: callback that will be called when rendering is required
        """

        # params
        self._debug = False
        self._view_mode = view_mode
        self._show_pen_up = show_pen_up
        self._show_points = show_points
        self._show_rulers = show_rulers
        self._pen_width = pen_width
        self._pen_opacity = pen_opacity
        self._render_cb = render_cb
        self._unit_type = UnitType.METRIC
        self._scale_threshold = 100.0  # min size for a major tick in rulers

        # state
        self._pixel_factor = 1.0
        self._ctx: Optional[mgl.Context] = None
        self._viewport_width = 100
        self._viewport_height = 100
        self._scale = 1.0  # one pixel of page equal one pixel of view port
        self._origin = (0.0, 0.0)  # top-left of page aligned with top-left of view port
        self._document: Optional[vp.Document] = None
        self._rebuild_needed = True
        self._scale_spec = DEFAULT_SCALE_SPEC

        # painters
        self._layer_visibility: Dict[int, bool] = defaultdict(lambda: True)
        self._layer_painters: Dict[int, List[Painter]] = defaultdict(list)
        self._paper_bounds_painter: Optional[PaperBoundsPainter] = None
        self._rulers_painter: Optional[RulersPainter] = None

        self._fit_to_viewport_flag = True

    def post_init(self, ctx: mgl.Context, width: int = 100, height: int = 100):
        """Post-init configuration to provide a GL context."""

        self._ctx = ctx
        self._ctx.enable_only(mgl.BLEND | mgl.PROGRAM_POINT_SIZE)

        self._rulers_painter = RulersPainter(self._ctx)

        self.resize(width, height)

    # =========================================================================================
    # Properties

    @property
    def document(self) -> Optional[vp.Document]:
        """:class:`vpype.Document` being displayed."""
        return self._document

    @document.setter
    def document(self, document: Optional[vp.Document]) -> None:
        self._document = document
        self._layer_visibility.clear()
        self._update()

    @property
    def scale(self) -> float:
        """Current scale (ratio screen pixel per document pixel)"""
        return self._scale

    @scale.setter
    def scale(self, scale: float) -> None:
        self._scale = scale
        self._fit_to_viewport_flag = False
        self._update(False)

    @property
    def origin(self) -> Tuple[float, float]:
        """Current origin (document coordinates corresponding to the display window's top-left
        corner."""
        return self._origin

    @origin.setter
    def origin(self, origin: Tuple[float, float]):
        self._origin = origin
        self._fit_to_viewport_flag = False
        self._update(False)

    @property
    def width(self) -> float:
        return self._viewport_width

    @property
    def height(self) -> float:
        return self._viewport_height

    @property
    def view_mode(self) -> ViewMode:
        """Current view mode."""
        return self._view_mode

    @view_mode.setter
    def view_mode(self, view_mode: ViewMode) -> None:
        self._view_mode = view_mode
        self._update()

    @property
    def show_pen_up(self) -> bool:
        """True if pen-up trajectories are rendered."""
        return self._show_pen_up

    @show_pen_up.setter
    def show_pen_up(self, show_pen_up: bool):
        self._show_pen_up = show_pen_up
        self._update()

    @property
    def show_points(self) -> bool:
        """True if points are rendered."""
        return self._show_points

    @show_points.setter
    def show_points(self, show_points: bool):
        self._show_points = show_points
        self._update()

    @property
    def show_rulers(self) -> bool:
        return self._show_rulers

    @show_rulers.setter
    def show_rulers(self, show_rulers: bool) -> None:
        self._show_rulers = show_rulers
        if self._fit_to_viewport_flag:
            self.fit_to_viewport()
        self._update(False)

    @property
    def pixel_factor(self) -> float:
        return self._pixel_factor

    @pixel_factor.setter
    def pixel_factor(self, pixel_factor: float) -> None:
        self._pixel_factor = pixel_factor
        if self._fit_to_viewport_flag:
            self.fit_to_viewport()
        self._update(False)

    @property
    def scale_spec(self) -> ScaleSpec:
        return self._scale_spec

    @property
    def unit_type(self) -> UnitType:
        return self._unit_type

    @unit_type.setter
    def unit_type(self, unit_type: UnitType) -> None:
        self._unit_type = unit_type
        self._update(False)

    @property
    def pen_width(self) -> float:
        """Pen width used for rendering (preview only)."""
        return self._pen_width

    @pen_width.setter
    def pen_width(self, pen_width: float):
        self._pen_width = pen_width
        self._update()

    @property
    def pen_opacity(self) -> float:
        """Pen opacity used for rendering (preview only)."""
        return self._pen_opacity

    @pen_opacity.setter
    def pen_opacity(self, pen_opacity: float):
        self._pen_opacity = pen_opacity
        self._update()

    @property
    def debug(self) -> bool:
        """Debug mode for display."""
        return self._debug

    @debug.setter
    def debug(self, debug: bool):
        self._debug = debug
        self._update(False)

    def layer_visible(self, layer_id: int) -> bool:
        """True if the corresponding layer is currently visible.

        Args:
            layer_id: layer to check
        """
        return self._layer_visibility[layer_id]

    def toggle_layer_visibility(self, layer_id: int) -> None:
        """Toggles the visibility of the provided layer.

        Args:
            layer_id: layer to toggle
        """
        self._layer_visibility[layer_id] = not self._layer_visibility[layer_id]
        self._update(False)

    # =========================================================================================
    # Geometry

    def fit_to_viewport(self):
        """Fit the current document in the viewport, allowing for a 2.5% margin on either
        sides."""
        if self._document is None:
            return

        if self._document.page_size is not None:
            x1, y1 = 0.0, 0.0
            x2, y2 = self._document.page_size
        else:
            bounds = self._document.bounds()
            if bounds is None:
                return
            x1, y1, x2, y2 = bounds

        w = x2 - x1
        h = y2 - y1

        if self.show_rulers and self._rulers_painter is not None:
            ruler_thickness = self._rulers_painter.thickness * self.pixel_factor
        else:
            ruler_thickness = 0.0
        viewport_width = self._viewport_width - ruler_thickness
        viewport_height = self._viewport_height - ruler_thickness
        self._scale = 0.95 * min(viewport_width / w, viewport_height / h)
        self._origin = [
            x1 - (viewport_width / self._scale - w) / 2 - ruler_thickness / self.scale,
            y1 - (viewport_height / self._scale - h) / 2 - ruler_thickness / self.scale,
        ]

        self._fit_to_viewport_flag = True

        self._update(False)

    def viewport_to_model(self, x: float, y: float) -> Tuple[float, float]:
        """Converts viewport coordinates to model coordinates in pixels."""
        return x / self._scale + self._origin[0], y / self._scale + self._origin[1]

    def resize(self, width: int, height: int) -> None:
        """Resizes the viewport.
        Args:
            width: new viewport width
            height: new viewport height
        """
        self._viewport_width = max(width, 1)
        self._viewport_height = max(height, 1)

        if self._fit_to_viewport_flag:
            self.fit_to_viewport()

    def _get_projection(self) -> np.ndarray:
        proj = orthogonal_projection_matrix(
            self._origin[0],
            self._origin[0] + self._viewport_width / self._scale,
            self._origin[1] + self._viewport_height / self._scale,
            self._origin[1],
            -1,
            1,
            dtype="f4",
        )

        return proj

    def pan(self, dx: float, dy: float) -> None:
        """Pan the viewport.

        Args:
            dx: horizontal distance to pan
            dy: vertical distance to pan
        """

        if dx != 0 or dy != 0:
            self._fit_to_viewport_flag = False

        self._origin = (self._origin[0] - dx / self._scale, self._origin[1] - dy / self._scale)
        self._update(False)

    def zoom(self, delta_zoom: float, mouse_x: float, mouse_y: float) -> None:
        """Zoom the viewport.

        Coordinates must be provided to specify the point about which to zoom. This typically
        should be the mouse position when used in GUI.

        Args:
            delta_zoom: zoom adjustment value (the scale is multiplied by ``(1 + delta_zoom)``
            mouse_x: mouse X coordinate
            mouse_y: mouse Y coordinate
        """
        if delta_zoom != 0:
            self._fit_to_viewport_flag = False

        new_scale = self._scale * (1 + delta_zoom)
        new_scale = max(min(new_scale, 100000), 0.05)  # clamp to reasonable values

        dz = 1 / self._scale - 1 / new_scale
        self._origin = (self._origin[0] + mouse_x * dz, self._origin[1] + mouse_y * dz)
        self._scale = new_scale

        self._update(False)

    # =========================================================================================
    # Painters

    def render(self):
        """Execute a render."""
        if self._ctx is None:
            return

        if self._rebuild_needed:
            self._rebuild()

        # update scale spec
        scales = SCALES_MAP[self.unit_type]
        threshold = self._scale_threshold * self.pixel_factor
        for spec in scales:
            if spec.scale_px * self.scale < threshold:
                break
        else:
            spec = scales[-1]
        self._scale_spec = spec

        self._ctx.clear(0.95, 0.95, 0.95, 1)
        proj = self._get_projection()

        if self._paper_bounds_painter:
            self._paper_bounds_painter.render(self, proj)

        for layer_id in sorted(self._layer_painters):
            if self._layer_visibility[layer_id]:
                for painter in self._layer_painters[layer_id]:
                    painter.render(self, proj)

        if self._rulers_painter and self._show_rulers:
            self._rulers_painter.render(self, proj)

    def _update(self, rebuild=True):
        """"""
        if rebuild:
            self._rebuild_needed = True
        self._render_cb()

    def _rebuild(self):
        self._layer_painters.clear()
        self._paper_bounds_painter = None

        if self._ctx is None:
            return

        if self._document is not None:
            color_index = 0
            for layer_id in sorted(self._document.layers):
                layer_color: ColorType = _COLORS[color_index % len(_COLORS)]
                lc = self._document.layers[layer_id]

                if self.view_mode == ViewMode.OUTLINE:
                    self._layer_painters[layer_id].append(
                        LineCollectionFastPainter(self._ctx, lc=lc, color=layer_color)
                    )
                elif self.view_mode == ViewMode.OUTLINE_COLORFUL:
                    self._layer_painters[layer_id].append(
                        LineCollectionFastColorfulPainter(
                            self._ctx, lc=lc, show_points=self._show_points
                        )
                    )
                elif self.view_mode == ViewMode.PREVIEW:
                    self._layer_painters[layer_id].append(
                        LineCollectionPreviewPainter(
                            self._ctx,
                            lc=lc,
                            pen_width=self._pen_width,
                            color=(
                                layer_color[0],
                                layer_color[1],
                                layer_color[2],
                                self._pen_opacity,
                            ),
                        )
                    )

                if self.show_pen_up:
                    self._layer_painters[layer_id].append(
                        LineCollectionPenUpPainter(self._ctx, lc=lc)
                    )
                if self.show_points and self.view_mode != ViewMode.OUTLINE_COLORFUL:
                    self._layer_painters[layer_id].append(
                        LineCollectionPointsPainter(self._ctx, lc=lc, color=layer_color)
                    )

                color_index += 1

            page_size = self._document.page_size
            if page_size is not None:
                self._paper_bounds_painter = PaperBoundsPainter(
                    self._ctx, self._document.page_size
                )

        self._rebuild_needed = False
