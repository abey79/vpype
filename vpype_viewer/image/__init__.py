from typing import Tuple

import moderngl
from PIL import Image

import vpype as vp
from vpype_viewer.engine import Engine, ViewMode


def render_image(document: vp.Document, size: Tuple[int, int] = (512, 512)) -> Image:
    ctx = moderngl.create_standalone_context()
    fbo = ctx.simple_framebuffer(size)
    fbo.use()

    engine = Engine(view_mode=ViewMode.PREVIEW)
    engine.post_init(ctx, size[0], size[1])
    engine.document = document
    engine.fit_to_viewport()
    engine.render()

    return Image.frombytes("RGB", fbo.size, fbo.read(), "raw", "RGB", 0, -1)
