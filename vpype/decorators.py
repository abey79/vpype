import datetime
import logging
import math
from functools import update_wrapper

import click

from .layers import LayerType, VpypeState, single_to_layer_id, multiple_to_layer_ids


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
    """Helper decorator to define layer processor commands.

    These type of command implements intra-layer processing, which is applied to one or more
    layers, as controlled by the --layer option. The layer processor receives a LineCollection
    as input and must return one.
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
            for lid in multiple_to_layer_ids(layers, state.vector_data):
                logging.info(
                    f"executing layer processor `{f.__name__}` on layer {lid} "
                    f"(kwargs: {kwargs})"
                )

                start = datetime.datetime.now()
                with state.current():
                    state.vector_data[lid] = f(state.vector_data[lid], *args, **kwargs)
                stop = datetime.datetime.now()

                logging.info(
                    f"layer processor `{f.__name__}` execution complete "
                    f"({_format_timedelta(stop - start)})"
                )

            return state

        return layer_processor

    return update_wrapper(new_func, f)


def global_processor(f):
    """Helper decorator to define "global" processor commands.

    These type of command implements global, multi-layer processing, for which no layer
    facility is provided (no --layer option or processing structure). A global processor
    receives a VectorData as input and must return one.
    """

    def new_func(*args, **kwargs):
        # noinspection PyShadowingNames
        def global_processor(state: VpypeState) -> VpypeState:
            logging.info(f"executing global processor `{f.__name__}` (kwargs: {kwargs})")

            start = datetime.datetime.now()
            with state.current():
                state.vector_data = f(state.vector_data, *args, **kwargs)
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
                target_layer = single_to_layer_id(layer, state.vector_data)

                logging.info(
                    f"executing generator `{f.__name__}` to layer {target_layer} "
                    f"(kwargs: {kwargs})"
                )

                start = datetime.datetime.now()
                state.vector_data.add(f(*args, **kwargs), target_layer)
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
    """
    Create an instance of the block layer_processor class
    """

    def new_func(*args, **kwargs):
        return c(*args, **kwargs)

    return update_wrapper(new_func, c)


def pass_state(f):
    """Marks a command as wanting to receive the current state.
    """

    def new_func(*args, **kwargs):
        return f(VpypeState.get_current(), *args, **kwargs)

    return update_wrapper(new_func, f)
