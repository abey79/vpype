from typing import Iterable, Tuple

import click

from .cli import ProcessorType, cli, execute_processors
from .decorators import block_processor
from .state import State
from .types import LengthType

__all__ = ("grid", "repeat")


@cli.command(group="Block processors")
@click.argument("number", nargs=2, default=(2, 2), type=int, metavar="M N")
@click.option(
    "-o",
    "--offset",
    nargs=2,
    default=("10mm", "10mm"),
    type=LengthType(),
    metavar="DX DY",
    help="Offset between columns and rows.",
)
@block_processor
def grid(
    state: State,
    processors: Iterable[ProcessorType],
    number: Tuple[int, int],
    offset: Tuple[float, float],
) -> State:
    """Creates a MxN grid of geometry

    The number of column and row must always be specified. By default, 10mm offsets are used
    in both directions. Use the `--offset` option to override these values.

    Examples:

        Create a grid of random line patches:

            $ vpype begin grid 3 4 random end show

        Create a grid of circles, each on a different layer:

            $ vpype begin grid -o 3cm 3cm 2 3 circle --layer new 0 0 1cm end show
    """

    for j in range(number[1]):
        for i in range(number[0]):
            with state.clear_document():
                execute_processors(processors, state)
                state.document.translate(offset[0] * i, offset[1] * j)

    return state


@cli.command("repeat", group="Block processors")
@click.argument("number", type=int, metavar="N")
@block_processor
def repeat(state: State, processors: Iterable[ProcessorType], number: int) -> State:
    """Repeat geometries N times.

    Repeats the enclosed command N times, stacking their output on top of each other.

    Examples:

        Create a patch of random lines of 3 different colors:

            $ vpype begin repeat 3 random --layer new end show
    """

    for _ in range(number):
        with state.clear_document():
            execute_processors(processors, state)

    return state
