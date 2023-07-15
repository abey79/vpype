from __future__ import annotations

import logging

import click

import vpype as vp

from .cli import cli
from .decorators import global_processor, pass_state
from .state import State


@cli.command("eval", group="Expressions")
@click.argument("expr", type=str)
@global_processor
@pass_state
def eval_cmd(state: State, document: vp.Document, expr: str):
    r"""Evaluate an expression.

    This command is a placeholder whose only purpose is to evaluate EXPR. It has no effect on
    the geometries, nor their properties. It is typically used at the beginning of a pipeline
    to initialise expression variables used later on.

    EXPR is interpreted as an expression in its entirety. As such, the enclosing `%` expression
    markers may be omitted.

    Example:
        Crop the geometry to a 1-cm margin.

    \b
            $ vpype read input.svg eval "m = 1*cm; w,h = prop.vp_page_size" \\
                crop %m% %m% %w-2*m% %h-2*m% write output.svg
    """

    if not expr.startswith("%"):
        expr = "%" + expr
    if not expr.endswith("%"):
        expr += "%"
    res = state.substitute(expr)
    logging.debug(f"eval: expression evaluated to {res}")

    return document
