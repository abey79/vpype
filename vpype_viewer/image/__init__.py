from typing import Optional, Tuple

import moderngl
from PIL import Image

import vpype as vp

from .._scales import UnitType
from ..engine import DEFAULT_PEN_OPACITY, DEFAULT_PEN_WIDTH, Engine, ViewMode


class ImageRenderer:
    """Viewer engine wrapper class to render to a :class:`PIL.Image.Image` instance.

    Example:

        >>> doc = vp.Document()
        # populate doc
        >>> renderer = ImageRenderer((640, 480))
        >>> renderer.engine.document = doc
        >>> renderer.engine.fit_to_viewport()
        >>> img = renderer.render()
    """

    def __init__(self, size: Tuple[int, int]):
        """Constructor.

        Args:
            size: image size
        """
        ctx = moderngl.create_standalone_context()
        self._fbo = ctx.simple_framebuffer(size)
        self.engine = Engine()
        self.engine.post_init(ctx, *size)

    def render(self) -> Image:
        """Render to a :class:`PIL.Image.Image` instance.

        Returns:
            :class:`PIL.Image.Image`: the rendered mage
        """
        self._fbo.use()
        self.engine.render()
        return Image.frombytes("RGB", self._fbo.size, self._fbo.read(), "raw", "RGB", 0, -1)


def render_image(
    document: vp.Document,
    size: Tuple[int, int] = (512, 512),
    view_mode: ViewMode = ViewMode.PREVIEW,
    show_pen_up: bool = False,
    show_points: bool = False,
    pen_width: float = DEFAULT_PEN_WIDTH,
    pen_opacity: float = DEFAULT_PEN_OPACITY,
    show_ruler: bool = False,
    pixel_factor: float = 1.0,
    unit_type: UnitType = UnitType.METRIC,
    scale: Optional[float] = None,
    origin: Optional[Tuple[float, float]] = None,
) -> Image:
    """Render a :class:`vpype.Document` instance as a Pillow :class:`PIL.Image.Image`.

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
        show_ruler: display the rulers
        pixel_factor: pixel factor (HiDPI screen support)
        unit_type: type of unit to use for the ruler
        scale: manually set scale
        origin: manually set origin

    Returns:
        :class:`PIL.Image.Image`: the rendered image
    """

    renderer = ImageRenderer(size)

    renderer.engine.document = document
    renderer.engine.view_mode = view_mode
    renderer.engine.show_pen_up = show_pen_up
    renderer.engine.show_points = show_points
    renderer.engine.pen_width = pen_width
    renderer.engine.pen_opacity = pen_opacity
    renderer.engine.show_rulers = show_ruler
    renderer.engine.pixel_factor = pixel_factor
    renderer.engine.unit_type = unit_type

    renderer.engine.fit_to_viewport()
    if scale is not None:
        renderer.engine.scale = scale
    if origin is not None:
        renderer.engine.origin = origin

    return renderer.render()
