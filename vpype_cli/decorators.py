from __future__ import annotations

import datetime
import logging
import math
from functools import update_wrapper
from typing import TYPE_CHECKING, Iterable

import click

from .state import State
from .types import LayerType, multiple_to_layer_ids, single_to_layer_id

if TYPE_CHECKING:  # pragma: no cover
    from .cli import ProcessorType

__all__ = [
    "layer_processor",
    "global_processor",
    "generator",
    "block_processor",
    "pass_state",
]


def _format_timedelta(dt: datetime.timedelta) -> str:
    s = dt.total_seconds()

    out = ""
    if s >= 60.0:
        minutes = math.floor(s / 60)
        s -= 60 * minutes

        out += str(minutes) + "min "

    out += f"{s:.3f}s"
    return out


def layer_processor(f):
    """Decorator to define a :ref:`layer processor <fundamentals_layer_processors>`
    command.

    Layer processors implements "intra-layer" processing, i.e. they are independently called
    for every layer in the pipeline. A ``--layer`` option is automatically appended to the
    option to let the user control on which layer(s) the processor should be applied (by
    default, ``all`` is used).

    Layer processors receive a :py:class:`LineCollection` as input and must return one.

    Example:

    .. code-block:: python3

        @click.command()
        @layer_processor
        def my_processor(lines: vpype.LineCollection) -> vpype.LineCollection:
            '''Example layer processor'''

            new_lines = vpype.LineCollection()

            for line in lines:
                # [do something with line]
                new_lines.append(line)

            return lines

        my_processor.help_group = "My Plugins"
    """

    @click.option(
        "-l",
        "--layer",
        type=LayerType(accept_multiple=True),
        default="all",
        help="Target layer(s) or 'all'.",
    )
    def new_func(*args, **kwargs):
        layers = kwargs.pop("layer", [])

        # noinspection PyShadowingNames
        def layer_processor(state: State) -> None:
            layers_eval = state.preprocess_argument(layers)

            for lid in multiple_to_layer_ids(layers_eval, state.document):
                start = datetime.datetime.now()
                with state.current():
                    state.current_layer_id = lid
                    new_args, new_kwargs = state.preprocess_arguments(args, kwargs)
                    logging.info(
                        f"executing layer processor `{f.__name__}` on layer {lid} "
                        f"(kwargs: {new_kwargs})"
                    )
                    state.document[lid] = f(state.document[lid], *new_args, **new_kwargs)
                    state.current_layer_id = None
                stop = datetime.datetime.now()

                logging.info(
                    f"layer processor `{f.__name__}` execution complete "
                    f"({_format_timedelta(stop - start)})"
                )

        return layer_processor

    return update_wrapper(new_func, f)


def global_processor(f):
    """Decorator to define a :ref:`global processor <fundamentals_global_processors>`
    command.

    This type of command implement a global, multi-layer processing and should be used for
    processors which cannot be applied layer-by-layer independently (in which case, using
    a :func:`layer_processor` is advised.

    No option is automatically added to global processors. In cases where the user should be
    able to control on which layer(s) the processing must be applied, it is advised to
    add a ``--layer`` option (with type :py:class:`LayerType`) and use the
    :func:`multiple_to_layer_ids` companion function (see example below)

    A global processor receives a :py:class:`Document` as input and must return one.

    Example::

        @click.command()
        @click.option(
            "-l",
            "--layer",
            type=vpype.LayerType(accept_multiple=True),
            default="all",
            help="Target layer(s).",
        )
        @global_processor
        def my_global_processor(
            document: vpype.Document, layer: Union[int, List[int]]
        ) -> vpype.Document:
            '''Example global processor'''

            layer_ids = multiple_to_layer_ids(layer, document)
            for lines in document.layers_from_ids(layer_ids):
                # [apply some modification to lines]

            return document


        my_global_processor.help_group = "My Plugins"
    """

    def new_func(*args, **kwargs):
        # noinspection PyShadowingNames
        def global_processor(state: State) -> None:
            start = datetime.datetime.now()
            with state.current():
                new_args, new_kwargs = state.preprocess_arguments(args, kwargs)
                logging.info(
                    f"executing global processor `{f.__name__}` (kwargs: {new_kwargs})"
                )
                state.document = f(state.document, *new_args, **new_kwargs)
            stop = datetime.datetime.now()

            logging.info(
                f"global processor `{f.__name__}` execution complete "
                f"({_format_timedelta(stop - start)})"
            )

        return global_processor

    return update_wrapper(new_func, f)


def generator(f):
    """Decorator to define a :ref:`generator <fundamentals_generators>` command.

    Generator do not have input, have automatically a "-l, --layer" option added to them, and
    must return a LineCollection structure, which will be added to a new layer or an existing
    one depending the option.
    """

    @click.option(
        "-l",
        "--layer",
        type=LayerType(accept_new=True),
        default=None,
        help="Target layer or 'new'.",
    )
    def new_func(*args, **kwargs):
        layer = kwargs.pop("layer", None)

        # noinspection PyShadowingNames
        def generator(state: State) -> None:
            with state.current():
                layer_eval = state.preprocess_argument(layer)
                target_layer = single_to_layer_id(layer_eval, state.document)

                start = datetime.datetime.now()
                state.current_layer_id = target_layer
                new_args, new_kwargs = state.preprocess_arguments(args, kwargs)
                logging.info(
                    f"executing generator `{f.__name__}` to layer {target_layer} "
                    f"(kwargs: {new_kwargs})"
                )
                state.document.add(f(*new_args, **new_kwargs), target_layer)
                state.current_layer_id = None
                stop = datetime.datetime.now()

            state.target_layer_id = target_layer

            logging.info(
                f"generator `{f.__name__}` execution complete "
                f"({_format_timedelta(stop - start)})"
            )

        return generator

    return update_wrapper(new_func, f)


def block_processor(f):
    """Decorator to define a `block <fundamentals_blocks>`_ processor command.

    Block processor function take a :class:`State` instance and a processor list as their
    first two argument. The processor list consists of the commands enclosed within the block.
    The block processor implementation should call the :func:`execute_processors` function
    to run the processor list, possibly temporarily changing the content of the :class:`State`
    instance content.

    Example::

        @click.command()
        @vpype_cli.block_processor
        def my_block_processor(state: vpype_cli.State, processors) -> vpype_cli.State:
            '''Example block processor'''

            # block implementation
            # should include call(s) to vpype_cli.execute_processors(processors, state)

            return state

        my_block_processor.help_group = "My Plugins"
    """

    def new_func(*args, **kwargs):
        # noinspection PyShadowingNames
        def block_processor(state: State, processors: Iterable[ProcessorType]) -> None:
            start = datetime.datetime.now()
            new_args, new_kwargs = state.preprocess_arguments(args, kwargs)
            logging.info(f"executing block processor `{f.__name__}` (kwargs: {new_kwargs})")
            f(state, processors, *new_args, **new_kwargs)
            stop = datetime.datetime.now()

            logging.info(
                f"block processor `{f.__name__}` execution complete "
                f"({_format_timedelta(stop - start)})"
            )

        # mark processor as being a block processor, needed by execute_processors()
        block_processor.__vpype_block_processor__ = True
        return block_processor

    return update_wrapper(new_func, f)


def pass_state(f):
    """Marks a command as wanting to receive the current state.

    Note: :func:`pass_state` must always be placed *after* the command type decorator (e.g.
    :func:`generator` and friends).

    Example::

        @click.command()
        @generator
        @pass_state
        def my_generator(state: State) -> vpype.Document:
            lc = vpype.LineCollection()
            current_layer_id = state.current_layer_id
            # ...

            return lc
    """

    def new_func(*args, **kwargs):
        return f(State.get_current(), *args, **kwargs)

    return update_wrapper(new_func, f)
