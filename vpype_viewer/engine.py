"""
Generic viewer
"""
import enum
from collections import defaultdict
from typing import Callable, Dict, List, Optional

import moderngl as mgl
import numpy as np

import vpype as vp

from .math import orthogonal_projection_matrix
from .painters import (
    LineCollectionFastPainter,
    LineCollectionPenUpPainter,
    LineCollectionPointsPainter,
    LineCollectionPreviewPainter,
    Painter,
    PaperBoundsPainter,
)

_COLORS = [
    (0, 0, 1, 1),
    (0, 0.5, 0, 1),
    (1, 0, 0, 1),
    (0, 0.75, 0.75, 1),
    (0, 1, 0, 1),
    (0.75, 0, 0.75, 1),
    (0.75, 0.75, 0, 1),
    (0, 0, 0, 1),
]


class ViewMode(enum.Enum):
    NONE = enum.auto()  # for debug purposes
    FAST = enum.auto()
    FAST_COLORFUL = enum.auto()
    PREVIEW = enum.auto()


class Engine:
    def __init__(
        self,
        view_mode: ViewMode = ViewMode.FAST,
        show_pen_up: bool = False,
        show_points: bool = False,
        render_cb: Optional[Callable[[], None]] = lambda: None,
    ):
        # params
        self._view_mode = view_mode
        self._show_pen_up = show_pen_up
        self._show_points = show_points
        self._render_cb = render_cb

        # state
        self._ctx: Optional[mgl.Context] = None
        self._viewport_width = 100
        self._viewport_height = 100
        self._scale = 1  # one pixel of page equal one pixel of view port
        self._origin = [0.0, 0.0]  # top-left of page aligned with top-left of view port
        self._document = None

        # painters
        self._layer_visibility: Dict[int, bool] = defaultdict(lambda: True)
        self._layer_painters: Dict[int, List[Painter]] = defaultdict(list)
        self._paper_bounds_painter: Optional[PaperBoundsPainter] = None

    def post_init(self, ctx: mgl.Context, width: int = 100, height: int = 100):
        self._ctx = ctx
        self._ctx.enable(mgl.BLEND | mgl.PROGRAM_POINT_SIZE)
        self.resize(width, height)

    # =========================================================================================
    # Properties

    @property
    def document(self) -> vp.Document:
        return self._document

    @document.setter
    def document(self, document: vp.Document) -> None:
        self._document = document
        self._rebuild()

    @property
    def scale(self) -> float:
        return self._scale

    @scale.setter
    def scale(self, scale: float) -> None:
        self._scale = scale
        self._render_cb()

    @property
    def view_mode(self) -> ViewMode:
        return self._view_mode

    @view_mode.setter
    def view_mode(self, view_mode: ViewMode) -> None:
        self._view_mode = view_mode
        self._rebuild()

    @property
    def show_pen_up(self) -> bool:
        return self._show_pen_up

    @show_pen_up.setter
    def show_pen_up(self, show_pen_up: bool):
        self._show_pen_up = show_pen_up
        self._rebuild()

    @property
    def show_points(self) -> bool:
        return self._show_points

    @show_points.setter
    def show_points(self, show_points: bool):
        self._show_points = show_points
        self._rebuild()

    # =========================================================================================
    # Geometry

    def fit_to_viewport(self):
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

        self._scale = 0.9 * min(self._viewport_width / w, self._viewport_height / h)
        self._origin = [
            x1 - (self._viewport_width / self._scale - w) / 2,
            y1 - (self._viewport_height / self._scale - h) / 2,
        ]

        self._render_cb()

    def resize(self, width: int, height: int) -> None:
        self._viewport_width = width
        self._viewport_height = height

    def get_projection(self) -> np.ndarray:
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
        self._origin[0] -= dx / self._scale
        self._origin[1] -= dy / self._scale

    def zoom(self, delta_zoom: float, mouse_x: float, mouse_y: float) -> None:
        new_scale = self._scale * (1 + 2 * delta_zoom)  # FIXME: magic number
        new_scale = max(min(new_scale, 100000), 0.05)  # clamp to reasonable values

        dz = 1 / self._scale - 1 / new_scale
        self._origin[0] += mouse_x * dz
        self._origin[1] += mouse_y * dz
        self._scale = new_scale

    # =========================================================================================
    # Painters

    def render(self):
        if self._ctx is None:
            return

        self._ctx.clear(0.95, 0.95, 0.95, 1)
        proj = self.get_projection()

        if self._paper_bounds_painter:
            self._paper_bounds_painter.render(proj, self._scale)

        for layer_id in sorted(self._layer_painters):
            if self._layer_visibility[layer_id]:
                for painter in self._layer_painters[layer_id]:
                    painter.render(proj, self._scale)

    def _rebuild(self):
        self._layer_painters.clear()
        self._layer_visibility.clear()
        self._paper_bounds_painter = None

        if self._ctx is None:
            return

        if self._document is not None:
            color_index = 0
            for layer_id in sorted(self._document.layers):
                layer_color = _COLORS[color_index % len(_COLORS)]
                lc = self._document.layers[layer_id]

                if self.view_mode == ViewMode.FAST:
                    self._layer_painters[layer_id].append(
                        LineCollectionFastPainter(self._ctx, lc=lc, color=layer_color)
                    )
                elif self.view_mode == ViewMode.PREVIEW:
                    self._layer_painters[layer_id].append(
                        LineCollectionPreviewPainter(
                            self._ctx, lc=lc, line_width=0.3, color=layer_color
                        )
                    )

                if self.show_pen_up:
                    self._layer_painters[layer_id].append(
                        LineCollectionPenUpPainter(self._ctx, lc=lc)
                    )
                if self.show_points:
                    self._layer_painters[layer_id].append(
                        LineCollectionPointsPainter(self._ctx, lc=lc, color=layer_color)
                    )
                    pass

                color_index += 1

            page_size = self._document.page_size
            if page_size is not None:
                self._paper_bounds_painter = PaperBoundsPainter(
                    self._ctx, self._document.page_size
                )
