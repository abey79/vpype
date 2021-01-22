from typing import Optional, Tuple

import moderngl
from PIL import Image

import vpype as vp
from vpype_viewer.engine import DEFAULT_PEN_OPACITY, DEFAULT_PEN_WIDTH, Engine, ViewMode


def render_image(
    document: vp.Document,
    size: Tuple[int, int] = (512, 512),
    view_mode: ViewMode = ViewMode.PREVIEW,
    show_pen_up: bool = False,
    show_points: bool = False,
    pen_width: float = DEFAULT_PEN_WIDTH,
    pen_opacity: float = DEFAULT_PEN_OPACITY,
    scale: Optional[float] = None,
    origin: Optional[Tuple[float, float]] = None,
) -> Image:
    """Render a :class:`Document` instance as a Pillow :class:`Image`.

    By default, the document is scaled and offset to entirely fit in the image. This behaviour
    can be overridden using the ``scale`` and ``offset`` arguments.

    Args:
        document: document to render
        size: output image size
        view_mode: :class:`ViewMode` to use
        show_pen_up: render pen-up trajectories
        show_points: render points
        pen_width: pen width (``ViewMode.PREVIEW`` only)
        pen_opacity: pen opacity (``ViewMode.PREVIEW`` only)
        scale: manually set scale
        origin: manually set origin
    Returns:
        an :class:`Image` instance
    """

    ctx = moderngl.create_standalone_context()
    fbo = ctx.simple_framebuffer(size)
    fbo.use()

    engine = Engine(
        view_mode=view_mode,
        show_pen_up=show_pen_up,
        show_points=show_points,
        pen_width=pen_width,
        pen_opacity=pen_opacity,
    )
    engine.post_init(ctx, size[0], size[1])
    engine.document = document
    engine.fit_to_viewport()
    if scale is not None:
        engine.scale = scale
    if origin is not None:
        engine.origin = origin

    engine.render()
    return Image.frombytes("RGB", fbo.size, fbo.read(), "raw", "RGB", 0, -1)
