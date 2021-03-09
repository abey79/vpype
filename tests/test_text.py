import pytest

import vpype as vp

# noinspection SpellCheckingInspection
from vpype_viewer import ImageRenderer

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
)


def test_text_unknown_font():
    with pytest.raises(ValueError):
        vp.text_line("Hello", "unknown font")

    with pytest.raises(ValueError):
        vp.text_block("Hello world", 500, font_name="unkown font")


def test_text_unknown_align():
    with pytest.raises(ValueError):
        vp.text_line("Hello", align="wild")

    with pytest.raises(ValueError):
        vp.text_block("Hello", 500, align="wild")


def test_text_unicode_ok():
    vp.text_line("hello 😂 world")


@pytest.mark.parametrize("font_name", ["timesg", "futural", "gothiceng"])
@pytest.mark.parametrize(
    ["align", "line_spacing", "justify"],
    [
        ("left", 1, False),
        ("left", 1, True),
        ("center", 1, False),
        ("right", 1, False),
        ("left", 2, False),
    ],
)
def test_text_block_render(assert_image_similarity, font_name, align, line_spacing, justify):
    doc = vp.Document()
    doc.add(
        vp.text_block(
            LOREM,
            500,
            font_name,
            size=18,
            align=align,
            line_spacing=line_spacing,
            justify=justify,
        )
    )
    renderer = ImageRenderer((1024, 1024))
    renderer.engine.document = doc
    renderer.engine.show_rulers = False
    renderer.engine.origin = (-20, -20)
    renderer.engine.scale = 1.8
    assert_image_similarity(renderer.render())
