from typing import Tuple

import moderngl as mgl
import numpy as np

import vpype as vp

from .utils import ColorType, load_program


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
        self._bounds_vao = ctx.simple_vertex_array(
            self._prog, vbo, "in_vert", index_buffer=ctx.buffer(line_idx.tobytes())
        )
        self._shading_vao = ctx.simple_vertex_array(
            self._prog, vbo, "in_vert", index_buffer=ctx.buffer(triangle_idx.tobytes())
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

        self._prog = load_program("fast_line", ctx)

        vertices, indices = self._build_buffers(lc, color=color)
        vbo = ctx.buffer(vertices.astype("f4").tobytes())
        ibo = ctx.buffer(indices.astype("i4").tobytes())
        self._vao = ctx.simple_vertex_array(
            self._prog, vbo, "in_vert", "in_color", index_buffer=ibo
        )

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["projection"].write(projection)
        self._vao.render(mgl.LINE_STRIP)

    @staticmethod
    def _build_buffers(
        lc: vp.LineCollection, color: ColorType = (0.0, 0.0, 0.0, 1.0)
    ) -> Tuple[np.ndarray, np.ndarray]:
        # build index array
        ranges = []
        block = []
        cur_index = 0
        restart_mark = [-1]
        for line in lc:
            ranges.append(range(cur_index, cur_index + len(line)))
            ranges.append(restart_mark)
            cur_index += len(line)

            block.append([vp.as_vector(line), np.tile(color, (len(line), 1))])

        return np.block(block), np.concatenate(ranges)


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

        vertices, indices = self._build_buffers(lc)
        vbo = ctx.buffer(vertices.astype("f4").tobytes())
        ibo = ctx.buffer(indices.astype("i4").tobytes())
        self._vao = ctx.simple_vertex_array(
            self._prog, vbo, "in_vert", "in_color", index_buffer=ibo
        )

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["projection"].write(projection)
        self._vao.render(mgl.LINE_STRIP)
        if self._show_points:
            self._vao.render(mgl.POINTS)

    @classmethod
    def _build_buffers(cls, lc: vp.LineCollection) -> Tuple[np.ndarray, np.ndarray]:
        # build index array
        ranges = []
        block = []
        cur_index = 0
        restart_mark = [-1]
        for i, line in enumerate(lc):
            n = len(line)
            ranges.append(range(cur_index, cur_index + n))
            ranges.append(restart_mark)
            cur_index += n

            color = cls.COLORS[i % len(cls.COLORS)]
            colors = np.tile(color, (n, 1))
            colors[::2, 0:3] *= 0.6

            block.append([vp.as_vector(line), colors])

        return np.block(block), np.concatenate(ranges)


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

        vertices, indices = self._build_buffers(lc)
        vbo = ctx.buffer(vertices.astype("f4").tobytes())
        ibo = ctx.buffer(indices.astype("i4").tobytes())
        self._vao = ctx.simple_vertex_array(self._prog, vbo, "position", index_buffer=ibo)

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["projection"].write(projection)
        self._prog["color"].value = self._color
        self._vao.render(mgl.POINTS)

    @staticmethod
    def _build_buffers(lc: vp.LineCollection) -> Tuple[np.ndarray, np.ndarray]:
        # build index array
        ranges = []
        block = []
        cur_index = 0
        restart_mark = [-1]
        for line in lc:
            ranges.append(range(cur_index, cur_index + len(line)))
            ranges.append(restart_mark)
            cur_index += len(line)

            block.append(vp.as_vector(line))

        return np.vstack(block), np.concatenate(ranges)


class LineCollectionPenUpPainter(Painter):
    def __init__(
        self, ctx: mgl.Context, lc: vp.LineCollection, color: ColorType = (0, 0, 0, 0.5)
    ):
        super().__init__(ctx)

        self._color = color
        self._prog = load_program("fast_line_mono", ctx)

        # build vertices
        vertices = []
        for i in range(len(lc) - 1):
            vertices.extend(
                ((lc[i][-1].real, lc[i][-1].imag), (lc[i + 1][0].real, lc[i + 1][0].imag))
            )

        vbo = ctx.buffer(np.array(vertices, dtype="f4").tobytes())
        self._vao = ctx.simple_vertex_array(self._prog, vbo, "in_vert")

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["color"].value = self._color
        self._prog["projection"].write(projection)
        self._vao.render(mgl.LINES)


class LineCollectionPreviewPainter(Painter):
    def __init__(
        self, ctx: mgl.Context, lc: vp.LineCollection, line_width: float, color: ColorType
    ):
        super().__init__(ctx)

        self._color = color
        self._line_width = line_width
        self._prog = load_program("preview_line", ctx)

        vertices, indices = self._build_buffers(lc)
        vbo = ctx.buffer(vertices.tobytes())
        ibo = ctx.buffer(indices.tobytes())
        self._vao = ctx.simple_vertex_array(self._prog, vbo, "position", index_buffer=ibo)

    def render(self, projection: np.ndarray, scale: float, debug: bool = False) -> None:
        self._prog["miter_limit"].value = -1
        self._prog["color"].value = self._color
        self._prog["linewidth"].value = self._line_width
        self._prog["antialias"].value = 1.5 / scale
        self._prog["projection"].write(projection)

        if debug:
            self._prog["kill_frag_shader"].value = False
            self._prog["debug_v_caps"].value = True
            self._prog["color"].value = self._color[0:3] + (0.3,)

            # self._ctx.cull_face = "back"
            # self._ctx.wireframe = True
            self._vao.render(mgl.LINE_STRIP_ADJACENCY)

            self._prog["kill_frag_shader"].value = True
            self._prog["debug_v_caps"].value = False
            self._ctx.wireframe = True
            self._vao.render(mgl.LINE_STRIP_ADJACENCY)
            self._ctx.wireframe = False
        else:
            self._prog["kill_frag_shader"].value = False
            self._prog["debug_v_caps"].value = False
            self._vao.render(mgl.LINE_STRIP_ADJACENCY)

    # self._ctx.wireframe = False

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
