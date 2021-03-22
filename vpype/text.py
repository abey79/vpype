"""
This code is adapted from https://github.com/fogleman/axi, which comes with the following
notice:

Copyright (C) 2017 Michael Fogleman

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


import itertools
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

from .model import LineCollection

__all__ = ["FONT_NAMES", "text_line", "text_block"]


_FONT_DIR = Path(__file__).parent / "fonts"

FONT_NAMES = [p.stem for p in _FONT_DIR.glob("*.pickle")]


@dataclass
class _Glyph:
    """Glyph description class."""

    lt: float
    rt: float
    lines: LineCollection

    def append_with_offset(self, target: LineCollection, dx: float, dy: float = 0.0) -> None:
        """Append the glyph to a target LineCollection instance using the provided offset."""
        for line in self.lines:
            target.append(line + complex(dx, dy))


class _Font:
    """Font description class.

    Loads pickled version of the Ax i's Hershey font in:
    https://github.com/fogleman/axi/blob/master/axi/hershey_fonts.py

    The glyph data is converted to LineCollection.
    """

    _FONTS: Dict[str, "_Font"] = {}

    def __init__(self, name: str):
        with open(_FONT_DIR / (name + ".pickle"), "rb") as fp:
            font_data = pickle.load(fp)

        # convert all glyphs to LineCollections
        self.glyphs: List[_Glyph] = [
            _Glyph(
                lt, rt, LineCollection([[complex(i, j) for i, j in line] for line in lines])
            )
            for lt, rt, lines in font_data
        ]

        # compute base height for this font
        all_glyphs = LineCollection()
        for glyph in self.glyphs:
            all_glyphs.extend(glyph.lines)
        self.max_height = all_glyphs.height()

    @classmethod
    def get(cls, font_name: str) -> "_Font":
        """Get _Font instance for provided name, using caching."""
        try:
            if font_name not in cls._FONTS:
                cls._FONTS[font_name] = _Font(font_name)
            return cls._FONTS[font_name]
        except FileNotFoundError as exc:
            raise ValueError(f"font '{font_name}' could not be found", exc)


def _text_line(
    txt: str, font: _Font, spacing: float = 0.0, extra: float = 0.0
) -> LineCollection:
    """Generate a single line of text."""
    result = LineCollection()
    x = 0.0
    for ch in txt:
        index = ord(ch) - 32
        if index < 0 or index >= 96:
            x += spacing
            continue
        glyph = font.glyphs[index]
        glyph.append_with_offset(result, x - glyph.lt)
        x += glyph.rt - glyph.lt + spacing
        if index == 0:
            x += extra

    return result


def text_line(
    txt: str,
    font_name="futural",
    size: float = 18.0,
    align: str = "left",
    spacing: float = 0.0,
) -> LineCollection:
    """Create a line of text.

    The text block starts at (0, 0) and extends either right, left, or both, depending on the
    ``align`` argument.

    Args:
        txt: the text to layout
        font_name: the name of the font to use (see :const:`FONT_NAMES`)
        size: the font size
        align: text horizontal alignment (``"left"``, ``"right"``, or ``"center"``, default:
            left alignment)
        spacing: additional spacing added after each character
    """
    font = _Font.get(font_name)
    lc = _text_line(txt, font, spacing)
    lc.scale(size / font.max_height)

    if align == "right":
        lc.translate(-lc.width(), 0)
    elif align == "center":
        lc.translate(-lc.width() / 2, 0)
    elif align != "left":
        raise ValueError(f"unknown value for align ('{align}')")

    return lc


def _word_wrap(paragraph: str, width: float, measure_func: Callable[[str], float]):
    """Break text in multiple line."""
    result = []
    for line in paragraph.split("\n"):
        # handle empty lines
        if line == "":
            result.append("\n")
            continue

        fields = itertools.groupby(line, lambda c: c.isspace())
        fields = ["".join(g) for _, g in fields]
        if len(fields) % 2 == 1:
            fields.append("")
        x = ""
        for a, b in zip(fields[::2], fields[1::2]):
            w = measure_func(x + a)
            if w > width:
                if x == "":
                    result.append(a)
                    continue
                else:
                    result.append(x)
                    x = ""
            x += a + b
        if x != "":
            result.append(x + "\n")
    return result


def _justify_text(txt: str, font: _Font, width: float) -> LineCollection:
    """Draw text with justification."""
    txt = txt.strip()
    d = _text_line(txt, font)
    bounds = d.bounds()
    w = bounds[2] if bounds else 0.0
    spaces = txt.count(" ")
    if spaces == 0 or w >= width:
        return d
    e = (width - w) / spaces
    return _text_line(txt, font, extra=e)


def text_block(
    paragraph: str,
    width: float,
    font_name="futural",
    size: float = 18.0,
    align: str = "left",
    line_spacing: float = 1,
    justify=False,
) -> LineCollection:
    """Create a wrapped block of text using the provided width.

    The text block starts at (0, 0) and extends right and down. The parameters affects how the
    text is rendered.

    Args:
        paragraph: the text to layout
        font_name: the name of the font to use (see :const:`FONT_NAMES`)
        width: the width of the block
        size: the font size
        align: text horizontal alignment (``"left"``, ``"right"``, or ``"center"``, default:
            left alignment)
        line_spacing: line spacing (default: 1.0)
        justify: should the text be justified (default: False)
    """

    font = _Font.get(font_name)
    scale_factor = size / font.max_height
    width /= scale_factor

    def measure(txt):
        bounds = _text_line(txt, font).bounds()
        return bounds[2] if bounds else 0.0

    lines = _word_wrap(paragraph, width, measure)

    lc_arr = [
        _justify_text(line, font, width)
        if justify and not line.endswith("\n")
        else _text_line(line, font)
        for line in lines
    ]

    spacing = line_spacing * font.max_height
    result = LineCollection()
    y = 0.0
    for lc in lc_arr:
        bounds = lc.bounds()
        w = bounds[2] if bounds else 0.0
        if align == "left":
            x = 0.0
        elif align == "right":
            x = width - w
        elif align == "center":
            x = width / 2 - w / 2
        else:
            raise ValueError(f"unknown value for align ('{align}')")

        for line in lc:
            result.append(line + complex(x, y))
        y += spacing

    result.scale(scale_factor)
    return result
