import pytest

import vpype as vp
from vpype_cli.show import _has_show

if _has_show:
    from vpype_viewer import ImageRenderer, UnitType

# noinspection SpellCheckingInspection
LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
    "Semper quis lectus nulla at volutpat. Nibh tortor id aliquet lectus.\n"
    "\n"
    "Ultrices sagittis orci a scelerisque purus semper eget duis at. Ultrices vitae auctor eu "
    "augue ut lectus.\n"
    "Interdum velit euismod in pellentesque massa placerat duis ultricies lacus. Morbi quis "
    "commodo odio aenean sed adipiscing diam. Risus nec feugiat in fermentum posuere urna nec "
    "tincidunt."
)
show_available = pytest.mark.skipif(not _has_show, reason="show not imported")


def test_text_unknown_font():
    with pytest.raises(ValueError):
        vp.text_line("Hello", "unknown font")

    with pytest.raises(ValueError):
        vp.text_block("Hello world", 500, font_name="unknown font")


def test_text_unknown_align():
    with pytest.raises(ValueError):
        vp.text_line("Hello", align="wild")

    with pytest.raises(ValueError):
        vp.text_block("Hello", 500, align="wild")


def test_text_unicode_ok():
    vp.text_line("hello 😂 world")


@show_available
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
    doc[1].append(vp.line(500, -20, 500, 500))
    renderer = ImageRenderer((1024, 1024))
    renderer.engine.document = doc
    renderer.engine.show_rulers = True
    renderer.engine.unit_type = UnitType.PIXELS
    renderer.engine.origin = (-20, -20)
    renderer.engine.scale = 1.8
    assert_image_similarity(renderer.render())
