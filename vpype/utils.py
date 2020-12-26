import logging
import math
import re
from typing import Callable, Dict, List, Tuple, Union

import click
import numpy as np

# REMINDER: anything added here must be added to docs/api.rst
__all__ = [
    "UNITS",
    "ANGLE_UNITS",
    "PAGE_SIZES",
    "LengthType",
    "AngleType",
    "PageSizeType",
    "convert_length",
    "convert_angle",
    "convert_page_size",
    "union",
    # deprecated:
    "PAGE_FORMATS",
    "convert",
    "convert_page_format",
    "Length",
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

ANGLE_UNITS = {
    "deg": 1.0,
    "grad": 9.0 / 10.0,  # note: must be before "rad"!
    "rad": 180.0 / math.pi,
    "turn": 360.0,
}

# page sizes in pixel
PAGE_SIZES = {
    "tight": _mm_to_px(0, 0),
    "a6": _mm_to_px(105.0, 148.0),
    "a5": _mm_to_px(148.0, 210.0),
    "a4": _mm_to_px(210.0, 297.0),
    "a3": _mm_to_px(297.0, 420.0),
    "a2": _mm_to_px(420.0, 594.0),
    "a1": _mm_to_px(594.0, 841.0),
    "a0": _mm_to_px(841.0, 1189.0),
    "letter": _mm_to_px(215.9, 279.4),
    "legal": _mm_to_px(215.9, 355.6),
    "executive": _mm_to_px(185.15, 266.7),
    "tabloid": _mm_to_px(279.4, 431.8),
}

# deprecated
PAGE_FORMATS = PAGE_SIZES


def _convert_unit(value: Union[str, float], units: Dict[str, float]) -> float:
    """Converts a string with unit to a value"""
    if isinstance(value, str):
        value = value.strip().lower()
        for unit, factor in units.items():
            if value.endswith(unit):
                num = value.strip(unit)
                return (float(num) if len(num) > 0 else 1.0) * factor

    return float(value)


def convert_length(value: Union[str, float]) -> float:
    """Convert a length optionally expressed as a string with unit to px value.

    Args:
        value: value to convert

    Returns:
        converted value

    Raises:
        :class:`ValueError`
    """
    return _convert_unit(value, UNITS)


def convert(value: Union[str, float]) -> float:  # pragma: no cover
    """Deprecated, use convert_length."""
    logging.warning(
        "!!! `vpype.convert()` is deprecated, use `vpype.convert_length()` instead."
    )
    return convert_length(value)


def convert_angle(value: Union[str, float]) -> float:
    """Convert an angle optionally expressed as a string with unit to degrees.

    Args:
        value: angle to convert

    Returns:
        converted angle in degree

    Raises:
        :class:`ValueError`
    """
    return _convert_unit(value, ANGLE_UNITS)


def convert_page_size(value: str) -> Tuple[float, float]:
    """Converts a string with page size to dimension in pixels.

    The input can be either a known page size (see ``vpype write --help`` for a list) or
    a page size descriptor in the form of "WxH" where both W and H can have units.

    Examples:

        Using a know page size::

            >>> import vpype
            >>> vpype.convert_page_size("a3")
            (1122.5196850393702, 1587.4015748031497)

        Using page size descriptor (no units, pixels are assumed)::

            >>> vpype.convert_page_size("100x200")
            (100.0, 200.0)

        Using page size descriptor (explicit units)::

            >>> vpype.convert_page_size("1inx2in")
            (96.0, 192.0)

    Args:
        value: page size descriptor

    Returns:
        the page size in CSS pixels
    """
    if value in PAGE_SIZES:
        return PAGE_SIZES[value]

    match = re.match(
        r"^(\d+\.?\d*)({0})?x(\d+\.?\d*)({0})?$".format("|".join(UNITS.keys())), value
    )

    if not match:
        raise ValueError(f"page size '{value}' unknown")

    x, x_unit, y, y_unit = match.groups()

    if not x_unit:
        x_unit = y_unit if y_unit else "px"
    if not y_unit:
        y_unit = x_unit

    return float(x) * convert_length(x_unit), float(y) * convert_length(y_unit)


def convert_page_format(value: str) -> Tuple[float, float]:  # pragma: no cover
    """Deprecated, use convert_page_size."""
    logging.warning(
        "!!! `vpype.convert_page_format()` is deprecated, use `vpype.convert_page_size()` "
        "instead."
    )
    return convert_page_size(value)


class LengthType(click.ParamType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided length
    string (which may contain units) into a value in CSS pixel units. This class uses
    :func:`convert_length` internally.

    Example::

        >>> import click
        >>> import vpype_cli
        >>> import vpype
        >>> @vpype_cli.cli.command(group="my commands")
        ... @click.argument("x", type=vpype.LengthType())
        ... @click.option("-o", "--option", type=vpype.LengthType(), default="1mm")
        ... @vpype.generator
        ... def my_command(x: float, option: float):
        ...     pass
    """

    name = "length"

    def convert(self, value, param, ctx):
        try:
            return convert_length(value)
        except ValueError:
            self.fail(f"parameter {value} is an incorrect length")


class Length(LengthType):  # pragma: no cover
    """Deprecated, use LengthType."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.warning("!!! `vpype.Length` is deprecated, use `vpype.LengthType` instead.")


class AngleType(click.ParamType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided angle
    string (which may contain units) into a value in degrees. This class uses
    :func:`convert_angle` internally.

    Example::

        >>> import click
        >>> import vpype_cli
        >>> import vpype
        >>> @vpype_cli.cli.command(group="my commands")
        ... @click.argument("angle", type=vpype.AngleType())
        ... @vpype.generator
        ... def my_command(angle: float):
        ...     pass
    """

    name = "angle"

    def convert(self, value, param, ctx):
        try:
            return convert_angle(value)
        except ValueError:
            self.fail(f"parameter {value} is an incorrect angle")


class PageSizeType(click.ParamType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided page size
    string into a tuple of float in CSS pixel units. See :func:`convert_page_size` for
    information on the page size descriptor syntax.

    Example::

        >>> import click
        >>> import vpype_cli
        >>> import vpype
        >>> @vpype_cli.cli.command(group="my commands")
        ... @click.argument("fmt", type=vpype.PageSizeType())
        ... @vpype.generator
        ... def my_command(fmt: Tuple[float, float]):
        ...     pass
    """

    name = "PAGESIZE"

    def convert(self, value, param, ctx) -> Tuple[float, float]:
        try:
            return convert_page_size(value)
        except ValueError:
            self.fail(f"parameter {value} is not a valid page size")


def union(line: np.ndarray, keys: List[Callable[[np.ndarray], bool]]) -> bool:
    """Returns True if every callables in ``keys`` return True (similar to ``all()``. This
    function is typically used with :meth:`LineCollection.filter`.

    Args:
        line: line to test
        keys: list of callables

    Returns:
        True if every callables return True
    """
    for key in keys:
        if not key(line):
            return False
    return True
