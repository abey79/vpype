import re
from typing import Union, Tuple

import click

__all__ = ["UNITS", "PAGE_FORMATS", "Length", "LengthType", "PageSizeType"]


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
}


def convert(value: Union[str, float]):
    """Convert a string with unit to px value. May raise exception for bad input.
    """
    if isinstance(value, str):
        value = value.strip().lower()
        for unit, factor in UNITS.items():
            if value.endswith(unit):
                num = value.strip(unit)
                return (float(num) if len(num) > 0 else 1.0) * factor

    return float(value)


class LengthType(click.ParamType):
    name = "length"

    def convert(self, value, param, ctx):
        try:
            return convert(value)
        except ValueError:
            self.fail(f"parameter {value} is an incorrect length")


Length = LengthType  # TODO: to be deprecated


class PageSizeType(click.ParamType):
    name = "PAGESIZE"

    def convert(self, value, param, ctx) -> Tuple[float, float]:
        if value in PAGE_FORMATS:
            return PAGE_FORMATS[value]

        try:
            match = re.match(
                r"^(\d+\.?\d*)({0})?x(\d+\.?\d*)({0})?$".format("|".join(UNITS.keys())), value
            )

            if not match:
                raise ValueError()

            x, x_unit, y, y_unit = match.groups()

            if not x_unit:
                x_unit = y_unit if y_unit else "px"
            if not y_unit:
                y_unit = x_unit

            return float(x) * convert(x_unit), float(y) * convert(y_unit)

        except ValueError:
            self.fail(f"parameter {value} is not a valid page format")
