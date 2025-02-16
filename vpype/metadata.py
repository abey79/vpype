from __future__ import annotations

import dataclasses
import pathlib

import svgelements


@dataclasses.dataclass(frozen=True)
class Color:
    """Simple, immutable, hashable color class with flexible construction.

    Examples:
        >>> Color()
        Color(red=0, green=0, blue=0, alpha=255)
        >>> Color(255, 0, 255)
        Color(red=255, green=0, blue=255, alpha=255)
        >>> Color(255, 0, 255, 128)
        Color(red=255, green=0, blue=255, alpha=128)
        >>> red = Color("red")
        >>> red
        Color(red=255, green=0, blue=0, alpha=255)
        >>> Color(red)
        Color(red=255, green=0, blue=0, alpha=255)
        >>> Color(svgelements.Color("#0f0"))
        Color(red=0, green=255, blue=0, alpha=255)
    """

    red: int
    green: int
    blue: int
    alpha: int

    def __init__(
        self,
        red: int | str | Color | svgelements.Color | None = None,
        green: int | None = None,
        blue: int | None = None,
        alpha: int | None = None,
    ):
        svgc = None
        if isinstance(red, svgelements.Color | Color):
            svgc = red
        elif isinstance(red, str):
            svgc = svgelements.Color(red)
        if svgc is not None:
            red, green, blue, alpha = svgc.red, svgc.green, svgc.blue, svgc.alpha

        object.__setattr__(self, "red", int(red or 0))  # type: ignore
        object.__setattr__(self, "green", int(green or 0))
        object.__setattr__(self, "blue", int(blue or 0))
        object.__setattr__(self, "alpha", int(alpha if alpha is not None else 255))

    def as_floats(self) -> tuple[float, float, float, float]:
        """Returns a float representation of the instance."""
        return self.red / 255, self.green / 255, self.blue / 255, self.alpha / 255

    def as_hex(self) -> str:
        """Return a standard, hexadecimal representation of the instance."""
        return svgelements.Color(self.red, self.green, self.blue, self.alpha).hex

    def as_rgb_hex(self) -> str:
        """Return a standard, hexadecimal representation of the instance, ignoring alpha."""
        return svgelements.Color(self.red, self.green, self.blue).hexrgb

    def __str__(self) -> str:
        return self.as_hex()


# layer metadata field names
METADATA_FIELD_NAME = "vp_name"
METADATA_FIELD_COLOR = "vp_color"
METADATA_FIELD_PEN_WIDTH = "vp_pen_width"
METADATA_FIELD_SOURCE = "vp_source"
METADATA_FIELD_SOURCE_LIST = "vp_sources"

# global metadata field names
METADATA_FIELD_SVG_NAMESPACES = "vp_svg_ns"
METADATA_FIELD_PAGE_SIZE = "vp_page_size"

METADATA_SYSTEM_FIELD_TYPES = {
    METADATA_FIELD_NAME: str,
    METADATA_FIELD_COLOR: Color,
    METADATA_FIELD_PEN_WIDTH: float,
    METADATA_FIELD_PAGE_SIZE: tuple,
    METADATA_FIELD_SOURCE: pathlib.Path,
    METADATA_FIELD_SOURCE_LIST: set,
}

# noinspection HttpUrlsUsage
METADATA_SVG_NAMESPACES = {
    "http://www.inkscape.org/namespaces/inkscape": "inkscape",
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd": "sodipodi",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://creativecommons.org/ns": "cc",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns": "rdf",
}

METADATA_SVG_ATTRIBUTES_WHITELIST = {
    # list based on https://css-tricks.com/svg-properties-and-css/
    # font properties
    "font",
    "font-family",
    "font-size",
    "font-size-adjust",
    "font-stretch",
    "font-style",
    "font-variant",
    "font-weight",
    # text properties
    "direction",
    "letter-spacing",
    "text-decoration",
    "unicode-bidi",
    "word-spacing",
    "writing-mode",
    "alignment-baseline",
    "baseline-shift",
    "dominant-baseline",
    "glyph-orientation-horizontal",
    "glyph-orientation-vertical",
    "kerning",
    "text-anchor",
    # masking properties
    "overflow",
    "mask",
    "opacity",
    # filter effect
    "enable-background",
    "filter",
    # interactivity properties
    "cursor",
    "pointer-events",
    # visibility properties
    "display",
    "visibility",
    # painting properties
    "color-interpolation",
    "color-interpolation-filters",
    "color-rendering",
    "fill",
    "fill-rule",
    "fill-opacity",
    "image-rendering",
    "marker",
    "marker-start",
    "marker-mid",
    "marker-end",
    "shape-rendering",
    "stroke",
    "stroke-dasharray",
    "stroke-dashoffset",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "stroke-opacity",
    "stroke-width",
    "text-rendering",
}


METADATA_DEFAULT_COLOR_SCHEME = [
    Color("#00f"),
    Color("#080"),
    Color("#f00"),
    Color("#0cc"),
    Color("#0f0"),
    Color("#c0c"),
    Color("#cc0"),
    Color("black"),
]
