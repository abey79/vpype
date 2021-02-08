from typing import List, Tuple

import moderngl as mgl
import numpy as np

import vpype as vp

from ._utils import ColorType, load_program


class Painter:
    def __init__(self, ctx: mgl.Context):
        self._ctx = ctx

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        raise NotImplementedError


class PaperBoundsPainter(Painter):
    def __init__(
        self,
        ctx: mgl.Context,
        paper_size: Tuple[float, float],
        color: ColorType = (0, 0, 0, 0.45),
        shadow_size: float = 7.0,
    ):
        super().__init__(ctx)

        data = np.array(
            [
                (0, 0),
                (paper_size[0], 0),
                (paper_size[0], paper_size[1]),
                (0, paper_size[1]),
                (paper_size[0], shadow_size),
                (paper_size[0] + shadow_size, shadow_size),
                (paper_size[0] + shadow_size, paper_size[1] + shadow_size),
                (shadow_size, paper_size[1] + shadow_size),
                (shadow_size, paper_size[1]),
            ],
            dtype="f4",
        )
        line_idx = np.array([0, 1, 2, 3], dtype="i4")
        triangle_idx = np.array(
            [
                (0, 3, 1),  # page background
                (1, 3, 2),
                (4, 2, 5),  # shadow
                (2, 6, 5),
                (7, 6, 2),
                (8, 7, 2),
            ],
            dtype="i4",
        ).reshape(-1)

        self._color = color
        self._prog = load_program("fast_line_mono", ctx)

        vbo = ctx.buffer(data.tobytes())
        self._bounds_vao = ctx.vertex_array(
            self._prog, [(vbo, "2f", "in_vert")], ctx.buffer(line_idx.tobytes())
        )
        self._shading_vao = ctx.vertex_array(
            self._prog, [(vbo, "2f", "in_vert")], ctx.buffer(triangle_idx.tobytes())
        )

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["projection"].write(projection)

        self._prog["color"].value = (0, 0, 0, 0.25)
        self._shading_vao.render(mgl.TRIANGLES, first=6, vertices=12)

        self._prog["color"].value = (1, 1, 1, 1)
        self._shading_vao.render(mgl.TRIANGLES, first=0, vertices=6)

        self._prog["color"].value = self._color
        self._bounds_vao.render(mgl.LINE_LOOP)


class LineCollectionFastPainter(Painter):
    def __init__(self, ctx: mgl.Context, lc: vp.LineCollection, color: ColorType):
        super().__init__(ctx)

        self._prog = load_program("fast_line_mono", ctx)
        self._color = color

        vertices, indices = self._build_buffers(lc)
        vbo = ctx.buffer(vertices.tobytes())
        ibo = ctx.buffer(indices.tobytes())
        self._vao = ctx.vertex_array(self._prog, [(vbo, "2f4", "in_vert")], index_buffer=ibo)

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["projection"].write(projection)
        self._prog["color"].value = self._color
        self._vao.render(mgl.LINE_STRIP)

    @staticmethod
    def _build_buffers(lc: vp.LineCollection) -> Tuple[np.ndarray, np.ndarray]:
        total_length = sum(len(line) for line in lc)
        buffer = np.empty((total_length, 2), dtype="f4")
        indices = np.empty(total_length + len(lc), dtype="i4")
        indices.fill(-1)

        # build index array
        cur_index = 0
        for i, line in enumerate(lc):
            next_idx = cur_index + len(line)
            indices[i + cur_index : i + next_idx] = np.arange(cur_index, next_idx)
            buffer[cur_index:next_idx] = vp.as_vector(line)
            cur_index = next_idx

        return buffer, indices


class LineCollectionFastColorfulPainter(Painter):
    COLORS = [
        np.array((0.0, 0.0, 1.0, 1.0)),
        np.array((0.0, 0.5, 0.0, 1.0)),
        np.array((1.0, 0.0, 0.0, 1.0)),
        np.array((0.0, 0.75, 0.75, 1.0)),
        np.array((0.0, 1.0, 0.0, 1.0)),
        np.array((0.75, 0, 0.75, 1.0)),
        np.array((0.75, 0.75, 0.0, 1.0)),
    ]

    def __init__(self, ctx: mgl.Context, lc: vp.LineCollection, show_points: bool = False):
        super().__init__(ctx)

        self._show_points = show_points
        self._prog = load_program("fast_line", ctx)

        # TODO: hacked color table size is not ideal, this will need to be changed when
        # implementing color themes
        self._prog["colors"].write(np.concatenate(self.COLORS).astype("f4").tobytes())

        vertices, indices = self._build_buffers(lc)
        vbo = ctx.buffer(vertices.tobytes())
        ibo = ctx.buffer(indices.tobytes())

        self._vao = ctx.vertex_array(
            self._prog,
            [(vbo, "2f4 i1", "in_vert", "color_idx")],
            ibo,
        )

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["projection"].write(projection)
        self._vao.render(mgl.LINE_STRIP)
        if self._show_points:
            self._vao.render(mgl.POINTS)

    @classmethod
    def _build_buffers(cls, lc: vp.LineCollection) -> Tuple[np.ndarray, np.ndarray]:
        total_length = sum(len(line) for line in lc)
        buffer = np.empty(total_length, dtype=[("vertex", "2f4"), ("color", "i1")])
        indices = np.empty(total_length + len(lc), dtype="i4")
        indices.fill(-1)

        # build index array
        cur_index = 0
        for i, line in enumerate(lc):
            next_idx = cur_index + len(line)
            indices[i + cur_index : i + next_idx] = np.arange(cur_index, next_idx)

            buffer["vertex"][cur_index:next_idx] = vp.as_vector(line)
            buffer["color"][cur_index:next_idx] = i % len(cls.COLORS)

            cur_index = next_idx

        return buffer, indices


class LineCollectionPointsPainter(Painter):
    def __init__(
        self, ctx: mgl.Context, lc: vp.LineCollection, color: ColorType = (0, 0, 0, 0.25)
    ):
        super().__init__(ctx)

        vertex = """
            #version 330
            
            uniform mat4 projection;
            
            in vec2 position;
            
            void main() {
              gl_PointSize = 5.0;
              gl_Position = projection * vec4(position, 0.0, 1.0);
            }
        """

        fragment = """
            #version 330
            
            uniform vec4 color;
            
            out vec4 out_color;
            
            void main() {
               out_color = color;
            }
        """

        self._prog = ctx.program(vertex_shader=vertex, fragment_shader=fragment)
        self._color = color

        vertices = self._build_buffers(lc)
        vbo = ctx.buffer(vertices.tobytes())
        self._vao = ctx.vertex_array(self._prog, [(vbo, "2f4", "position")])

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["projection"].write(projection)
        self._prog["color"].value = self._color
        self._vao.render(mgl.POINTS)

    @staticmethod
    def _build_buffers(lc: vp.LineCollection) -> np.ndarray:
        buffer = np.empty((sum(len(line) for line in lc), 2), dtype="f4")

        # build index array
        cur_index = 0
        for i, line in enumerate(lc):
            next_idx = cur_index + len(line)
            buffer[cur_index:next_idx] = vp.as_vector(line)
            cur_index = next_idx

        return buffer


class LineCollectionPenUpPainter(Painter):
    def __init__(
        self, ctx: mgl.Context, lc: vp.LineCollection, color: ColorType = (0, 0, 0, 0.5)
    ):
        super().__init__(ctx)

        self._color = color
        self._prog = load_program("fast_line_mono", ctx)

        # build vertices
        vertices: List[Tuple[float, float]] = []
        for i in range(len(lc) - 1):
            vertices.extend(
                ((lc[i][-1].real, lc[i][-1].imag), (lc[i + 1][0].real, lc[i + 1][0].imag))
            )

        if len(vertices) > 0:
            vbo = ctx.buffer(np.array(vertices, dtype="f4").tobytes())
            self._vao = ctx.vertex_array(self._prog, [(vbo, "2f4", "in_vert")])
        else:
            self._vao = None

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        if self._vao is not None:
            self._prog["color"].value = self._color
            self._prog["projection"].write(projection)
            self._vao.render(mgl.LINES)


class LineCollectionPreviewPainter(Painter):
    def __init__(
        self, ctx: mgl.Context, lc: vp.LineCollection, pen_width: float, color: ColorType
    ):
        super().__init__(ctx)

        self._color = color
        self._pen_width = pen_width
        self._prog = load_program("preview_line", ctx)

        vertices, indices = self._build_buffers(lc)
        vbo = ctx.buffer(vertices.tobytes())
        ibo = ctx.buffer(indices.tobytes())
        self._vao = ctx.vertex_array(self._prog, [(vbo, "2f4", "position")], ibo)

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["color"].value = self._color
        self._prog["pen_width"].value = self._pen_width
        self._prog["antialias"].value = 1.5 / scale
        self._prog["projection"].write(projection)

        if debug:
            self._prog["kill_frag_shader"].value = False
            self._prog["debug_view"].value = True
            self._prog["color"].value = self._color[0:3] + (0.3,)
            self._vao.render(mgl.LINE_STRIP_ADJACENCY)

            self._prog["kill_frag_shader"].value = True
            self._prog["debug_view"].value = False
            self._prog["color"].value = (0, 1, 0, 1)
            self._ctx.wireframe = True
            self._vao.render(mgl.LINE_STRIP_ADJACENCY)
            self._ctx.wireframe = False
        else:
            self._prog["kill_frag_shader"].value = False
            self._prog["debug_view"].value = False
            self._vao.render(mgl.LINE_STRIP_ADJACENCY)

    @staticmethod
    def _build_buffers(lc: vp.LineCollection):
        """Prepare the buffers for multi-polyline rendering. Closed polyline must have their
        last point identical to their first point."""

        indices = []
        reset_index = [-1]
        start_index = 0
        for i, line in enumerate(lc):
            if line[0] == line[-1]:  # closed path
                idx = np.arange(len(line) + 3) - 1
                idx[0], idx[-2], idx[-1] = len(line) - 1, 0, 1
            else:
                idx = np.arange(len(line) + 2) - 1
                idx[0], idx[-1] = 0, len(line) - 1

            indices.append(idx + start_index)
            start_index += len(line)
            indices.append(reset_index)

        return (
            np.vstack([vp.as_vector(line).astype("f4") for line in lc]),
            np.concatenate(indices).astype("i4"),
        )
