import datetime
import logging
import math
from functools import update_wrapper

import click

from .layers import LayerType, VpypeState, multiple_to_layer_ids, single_to_layer_id

# REMINDER: anything added here must be added to docs/api.rst
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
    """Helper decorator to define a :ref:`layer processor <fundamentals_layer_processors>`
    command.

    Layer processors implements "intra-layer" processing, i.e. they are independently called
    for every layer in the pipeline. A ``--layer`` option is automatically appended to the
    option to let the user control on which layer(s) the processor should be applied (by
    default, ``all`` is used).

    Layer processors receive a :py:class:`LineCollection` as input and must return one.

    Example:

    .. code-block:: python3

        @click.command()
        @vpype.layer_processor
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
        layers = kwargs.pop("layer", -1)

        # noinspection PyShadowingNames
        def layer_processor(state: VpypeState) -> VpypeState:
            for lid in multiple_to_layer_ids(layers, state.document):
                logging.info(
                    f"executing layer processor `{f.__name__}` on layer {lid} "
                    f"(kwargs: {kwargs})"
                )

                start = datetime.datetime.now()
                with state.current():
                    state.document[lid] = f(state.document[lid], *args, **kwargs)
                stop = datetime.datetime.now()

                logging.info(
                    f"layer processor `{f.__name__}` execution complete "
                    f"({_format_timedelta(stop - start)})"
                )

            return state

        return layer_processor

    return update_wrapper(new_func, f)


def global_processor(f):
    """Helper decorator to define a :ref:`global processor <fundamentals_global_processors>`
    command.

    This type of command implement a global, multi-layer processing and should be used for
    processors which cannot be applied layer-by-layer independently (in which case, using
    a :func:`layer_processor` is advised.

    No option is automatically added to global processors. In cases where the user should be
    able to control on which layer(s) the processing must be applied, it is advised to
    add a ``--layer`` option (with type :py:class:`LayerType`) and use the
    :func:`multiple_to_layer_ids` companion function (see example below)

    A global processor receives a :py:class:`Document` as input and must return one.

    Example:

    .. code-block:: python3

        @click.command()
        @click.option(
            "-l",
            "--layer",
            type=vpype.LayerType(accept_multiple=True),
            default="all",
            help="Target layer(s).",
        )
        @vpype.global_processor
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
        def global_processor(state: VpypeState) -> VpypeState:
            logging.info(f"executing global processor `{f.__name__}` (kwargs: {kwargs})")

            start = datetime.datetime.now()
            with state.current():
                state.document = f(state.document, *args, **kwargs)
            stop = datetime.datetime.now()

            logging.info(
                f"global processor `{f.__name__}` execution complete "
                f"({_format_timedelta(stop - start)})"
            )

            return state

        return global_processor

    return update_wrapper(new_func, f)


def generator(f):
    """Helper decorator to define generator-type commands.

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
        layer = kwargs.pop("layer", -1)

        # noinspection PyShadowingNames
        def generator(state: VpypeState) -> VpypeState:
            with state.current():
                target_layer = single_to_layer_id(layer, state.document)

                logging.info(
                    f"executing generator `{f.__name__}` to layer {target_layer} "
                    f"(kwargs: {kwargs})"
                )

                start = datetime.datetime.now()
                state.document.add(f(*args, **kwargs), target_layer)
                stop = datetime.datetime.now()

            state.target_layer = target_layer

            logging.info(
                f"generator `{f.__name__}` execution complete "
                f"({_format_timedelta(stop - start)})"
            )

            return state

        return generator

    return update_wrapper(new_func, f)


def block_processor(c):
    """Create an instance of the block processor class."""

    def new_func(*args, **kwargs):
        return c(*args, **kwargs)

    return update_wrapper(new_func, c)


def pass_state(f):
    """Marks a command as wanting to receive the current state."""

    def new_func(*args, **kwargs):
        return f(VpypeState.get_current(), *args, **kwargs)

    return update_wrapper(new_func, f)
