"""
.. module:: vpype
"""

from typing import Union

import click

UNITS = [
    ("px", 1.0),
    ("in", 96.0),
    ("mm", 96.0 / 25.4),
    ("cm", 96.0 / 2.54),
    ("pc", 16.0),
    ("pt", 96.0 / 72.0),
]


def convert(value: Union[str, float]):
    """Convert a string with unit to px value. May raise exception for bad input.
    """
    if isinstance(value, str):
        value = value.strip().lower()
        for unit, factor in UNITS:
            if value.endswith(unit):
                num = value.strip(unit)
                return (float(num) if len(num) > 0 else 1.) * factor

    return float(value)


class Length(click.ParamType):
    name = "length"

    def convert(self, value, param, ctx):
        try:
            return convert(value)
        except ValueError:
            self.fail(f"parameter {value} is an incorrect length")
