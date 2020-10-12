"""
.. module:: vpype
"""

import re
from typing import Tuple, Union

import click

# REMINDER: anything added here must be added to docs/api.rst
__all__ = [
    "UNITS",
    "PAGE_FORMATS",
    "Length",
    "LengthType",
    "PageSizeType",
    "convert",
    "convert_length",
    "convert_page_format",
]


def _mm_to_px(x: float, y: float) -> Tuple[float, float]:
    return x * 96.0 / 25.4, y * 96.0 / 25.4


UNITS = {
    "px": 1.0,
    "in": 96.0,
    "mm": 96.0 / 25.4,
    "cm": 96.0 / 2.54,
    "pc": 16.0,
    "pt": 96.0 / 72.0,
}

# page formats in pixel
PAGE_FORMATS = {
    "tight": _mm_to_px(0, 0),
    "a6": _mm_to_px(105.0, 148.0),
    "a5": _mm_to_px(148.0, 210.0),
    "a4": _mm_to_px(210.0, 297.0),
    "a3": _mm_to_px(297.0, 420.0),
    "letter": _mm_to_px(215.9, 279.4),
    "legal": _mm_to_px(215.9, 355.6),
    "executive": _mm_to_px(185.15, 266.7),
    "tabloid": _mm_to_px(279.4, 431.8),
}


def convert_length(value: Union[str, float]) -> float:
    """Convert a string with unit to px value. May raise exception for bad input.
    """
    if isinstance(value, str):
        value = value.strip().lower()
        for unit, factor in UNITS.items():
            if value.endswith(unit):
                num = value.strip(unit)
                return (float(num) if len(num) > 0 else 1.0) * factor

    return float(value)


convert = convert_length  # TODO: to be deprecated


def convert_page_format(value: str) -> Tuple[float, float]:
    """Converts a string with page format to dimension in pixels.

    The input can be either a known page format (see ``vpype write --help`` for a list) or
    a page format descriptor in the form of "WxH" where both W and H can have units.

    Examples:

        Using know page format::

            >>> import vpype
            >>> vpype.convert_page_format("a3")
            (1122.5196850393702, 1587.4015748031497)

        Using page format descriptor (no units, pixels are assumed)::

            >>> vpype.convert_page_format("100x200")
            (100.0, 200.0)

        Using page format descriptor (explicit units)::

            >>> vpype.convert_page_format("1inx2in")
            (96.0, 192.0)

    Args:
        value: page format descriptor

    Returns:
        the page format in CSS pixels
    """
    if value in PAGE_FORMATS:
        return PAGE_FORMATS[value]

    match = re.match(
        r"^(\d+\.?\d*)({0})?x(\d+\.?\d*)({0})?$".format("|".join(UNITS.keys())), value
    )

    if not match:
        raise ValueError(f"page format '{value}' unknown")

    x, x_unit, y, y_unit = match.groups()

    if not x_unit:
        x_unit = y_unit if y_unit else "px"
    if not y_unit:
        y_unit = x_unit

    return float(x) * convert(x_unit), float(y) * convert(y_unit)


class LengthType(click.ParamType):
    name = "length"

    def convert(self, value, param, ctx):
        try:
            return convert_length(value)
        except ValueError:
            self.fail(f"parameter {value} is an incorrect length")


Length = LengthType  # TODO: to be deprecated


class PageSizeType(click.ParamType):
    name = "PAGESIZE"

    def convert(self, value, param, ctx) -> Tuple[float, float]:
        try:
            return convert_page_format(value)
        except ValueError:
            self.fail(f"parameter {value} is not a valid page format")
