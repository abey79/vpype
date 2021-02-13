import os

import pytest

import vpype as vp
from vpype_viewer import (
    DEFAULT_SCALE_SPEC,
    Engine,
    ImageRenderer,
    UnitType,
    ViewMode,
    render_image,
)

from .utils import TEST_FILE_DIRECTORY


# assert_image_similarity fixture added for automated exclusion on unsupported runner
def test_viewer_engine_properties(assert_image_similarity):
    renderer = ImageRenderer((640, 480))

    doc = vp.Document()
    renderer.engine.document = doc
    assert renderer.engine.document is doc

    renderer.engine.scale = 3.0
    assert renderer.engine.scale == 3.0

    renderer.engine.origin = (10.0, 20.0)
    assert renderer.engine.origin == (10.0, 20.0)

    renderer.engine.view_mode = ViewMode.OUTLINE_COLORFUL
    assert renderer.engine.view_mode == ViewMode.OUTLINE_COLORFUL

    renderer.engine.show_pen_up = True
    assert renderer.engine.show_pen_up

    renderer.engine.show_points = True
    assert renderer.engine.show_points

    renderer.engine.pen_width = 0.5
    assert renderer.engine.pen_width == 0.5

    renderer.engine.pen_opacity = 0.5
    assert renderer.engine.pen_opacity == 0.5

    renderer.engine.debug = True
    assert renderer.engine.debug

    renderer.engine.unit_type = UnitType.IMPERIAL
    assert renderer.engine.unit_type == UnitType.IMPERIAL

    renderer.engine.ruler_thickness = 50.0
    assert renderer.engine.ruler_thickness == 50.0

    renderer.engine.show_rulers = False
    assert not renderer.engine.show_rulers

    assert renderer.engine.current_scale_spec == DEFAULT_SCALE_SPEC

    renderer.engine.toggle_layer_visibility(10)
    assert not renderer.engine.layer_visible(10)


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
        pytest.param(
            {"view_mode": ViewMode.OUTLINE, "show_ruler": True, "unit_type": UnitType.PIXELS},
            id="outline_pixels",
        ),
        pytest.param(
            {"view_mode": ViewMode.OUTLINE, "show_ruler": True, "unit_type": UnitType.METRIC},
            id="outline_metric",
        ),
        pytest.param(
            {
                "view_mode": ViewMode.OUTLINE,
                "show_ruler": True,
                "unit_type": UnitType.IMPERIAL,
            },
            id="outline_imperial",
        ),
    ],
)
def test_viewer(assert_image_similarity, file, render_kwargs):
    doc = vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / file), 0.4)

    # noinspection PyArgumentList
    assert_image_similarity(render_image(doc, (1024, 1024), **render_kwargs))


def test_viewer_zoom_scale(assert_image_similarity):
    doc = vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / "issue_124/plotter.svg"), 0.4)
    renderer = ImageRenderer((1024, 1024))
    renderer.engine.document = doc
    renderer.engine.fit_to_viewport()
    renderer.engine.show_rulers = False
    renderer.engine.zoom(2, 500, 500)
    renderer.engine.pan(160, 250)
    assert_image_similarity(renderer.render())


def test_viewer_scale_origin(assert_image_similarity):
    doc = vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / "issue_124/plotter.svg"), 0.4)
    assert_image_similarity(
        render_image(doc, view_mode=ViewMode.OUTLINE, origin=(600, 400), scale=4)
    )


def test_viewer_debug(assert_image_similarity):
    doc = vp.read_multilayer_svg(str(TEST_FILE_DIRECTORY / "issue_124/plotter.svg"), 0.4)
    renderer = ImageRenderer((1024, 1024))
    renderer.engine.document = doc
    renderer.engine.origin = (600, 400)
    renderer.engine.scale = 8
    renderer.engine.view_mode = ViewMode.PREVIEW
    renderer.engine.debug = True
    renderer.engine.show_rulers = False
    assert_image_similarity(renderer.render())


# assert_image_similarity fixture added for automated exclusion on unsupported runner
def test_viewer_uninitialized(assert_image_similarity):
    """An uninitialized engine should not crash"""
    engine = Engine()

    engine.scale = 3.0
    engine.origin = (10.0, 20.0)
    engine.view_mode = ViewMode.OUTLINE_COLORFUL
    engine.show_pen_up = True
    engine.show_points = True
    engine.pen_width = 0.5
    engine.pen_opacity = 0.5
    engine.debug = True
    engine.show_rulers = True
    engine.ruler_thickness = 50.0
    engine.unit_type = UnitType.IMPERIAL

    engine.zoom(2, 10, 10)
    engine.pan(50, 40)
    engine.render()
    engine.viewport_to_model(30, 30)
    engine.toggle_layer_visibility(10)
    engine.fit_to_viewport()

    # ensure 100% coverage
    doc = vp.Document()
    engine.document = doc
    engine.fit_to_viewport()
