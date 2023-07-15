from __future__ import annotations

import click

import vpype as vp

from .cli import cli
from .decorators import generator, pass_state
from .state import State
from .types import LengthType

__all__ = ("frame",)


@cli.command(group="Generators")
@click.option(
    "-o",
    "--offset",
    default=0.0,
    type=LengthType(),
    help="Offset from the geometries' bounding box. This option understands supported units.",
)
@generator
@pass_state
def frame(state: State, offset: float):
    """Add a single-line frame around the geometry.

    By default, the frame shape is the current geometries' bounding box. An optional offset can
    be provided.
    """
    if state.document.is_empty():
        return vp.LineCollection()

    bounds = state.document.bounds() or (0, 0, 0, 0)
    return vp.LineCollection(
        [
            (
                bounds[0] - offset + 1j * (bounds[1] - offset),
                bounds[0] - offset + 1j * (bounds[3] + offset),
                bounds[2] + offset + 1j * (bounds[3] + offset),
                bounds[2] + offset + 1j * (bounds[1] - offset),
                bounds[0] - offset + 1j * (bounds[1] - offset),
            )
        ]
    )
