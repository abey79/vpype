import os

import numpy as np
import pytest

import vpype as vp
from vpype_viewer import ViewMode, render_image

from .utils import TEST_FILE_DIRECTORY


@pytest.mark.parametrize(
    "file",
    ["misc/empty.svg", "misc/multilayer.svg", "issue_124/plotter.svg"],
    ids=lambda s: os.path.splitext(s)[0],
)
@pytest.mark.parametrize(
    "render_kwargs",
    [
        pytest.param({"view_mode": ViewMode.OUTLINE}, id="outline"),
        pytest.param({"view_mode": ViewMode.OUTLINE_COLORFUL}, id="outline_colorful"),
        pytest.param({"view_mode": ViewMode.PREVIEW}, id="preview"),
        pytest.param({"view_mode": ViewMode.OUTLINE, "show_points": True}, id="points"),
        pytest.param(
            {"view_mode": ViewMode.OUTLINE_COLORFUL, "show_points": True}, id="colorful_points"
        ),
        pytest.param(
            {"view_mode": ViewMode.OUTLINE, "show_pen_up": True}, id="outline_pen_up"
        ),
        pytest.param(
            {"view_mode": ViewMode.PREVIEW, "show_pen_up": True}, id="preview_pen_up"
        ),
        pytest.param(
            {"view_mode": ViewMode.PREVIEW, "pen_opacity": 0.3}, id="preview_transparent"
        ),
        pytest.param({"view_mode": ViewMode.PREVIEW, "pen_width": 4.0}, id="preview_thick"),
    ],
)
def test_viewer(assert_image_similarity, file, render_kwargs):
    doc = vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / file), 0.4)

    # noinspection PyArgumentList
    assert_image_similarity(render_image(doc, (1024, 1024), **render_kwargs))
