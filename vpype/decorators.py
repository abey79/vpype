import logging
from functools import update_wrapper
from typing import Union, List

import click

from .model import VectorData
from .vpype import VpypeState


class LayerType(click.ParamType):
    """
    Interpret value of --layer options.

    If `accept_multiple == True`, comma-separated array of int is accepted or 'all'. Returns either a list of IDs or
    `LayerType.ALL`.

    If `accept_new == True`, 'new' is also accepted, in which case returns `LayerType.NEW`.

    None is passed through, which typically means to use the default behaviour.
    """

    name = "layers"

    NEW = -1
    ALL = -2

    def __init__(self, accept_multiple: bool = False, accept_new: bool = False):
        self.accept_multiple = accept_multiple
        self.accept_new = accept_new

    def convert(self, value, param, ctx):
        # comply with ParamType requirements
        if value is None:
            return None

        if value.lower() == "all":
            if self.accept_multiple:
                return LayerType.ALL
            else:
                self.fail("'all' was not expected", param, ctx)
        elif value.lower() == "new":
            if self.accept_new:
                return LayerType.NEW
            else:
                self.fail("'new' was not expected", param, ctx)

        try:
            if self.accept_multiple:
                id_arr = list(map(int, value.split(",")))
                for i in id_arr:
                    if i < 1:
                        raise TypeError
                return id_arr
            else:
                return int(value)
        except TypeError:
            self.fail(f"unexpected {value!r} of type {type(value).__name__}", param, ctx)
        except ValueError:
            self.fail(f"{value!r} is not a valid value", param, ctx)

    @staticmethod
    def multiple_to_layer_ids(
        layers: Union[None, int, List[int]], vector_data: VectorData,
    ) -> Union[None, List[int]]:
        """

        :param layers:
        :param vector_data:
        :return:
        """
        if layers is None or layers is LayerType.ALL:
            return sorted(vector_data.ids())
        else:
            return sorted(vid for vid in layers if vector_data.exists(vid))


def layer_processor(f):
    """Helper decorator to define layer processor commands.

    These type of command implements intra-layer processing, which is applied to one or more layers, as controlled
    by the --layer option. The layer processor receives a LineCollection as input and must return one.
    """

    @click.option(
        "-l",
        "--layer",
        type=LayerType(accept_multiple=True),
        default="all",
        help="Target layers.",
    )
    def new_func(*args, **kwargs):
        layers = kwargs.pop("layer", -1)

        # noinspection PyShadowingNames
        def layer_processor(state: VpypeState) -> VpypeState:
            for lid in LayerType.multiple_to_layer_ids(layers, state.vector_data):
                logging.info(
                    f"executing layer processor `{f.__name__}` on layer {lid} (kwargs: {kwargs})"
                )
                with state.current():
                    state.vector_data[lid] = f(state.vector_data[lid], *args, **kwargs)

            return state

        return layer_processor

    return update_wrapper(new_func, f)


def global_processor(f):
    """Helper decorator to define "global" processor commands.

    These type of command implements global, multi-layer processing, for which no layer facility is provided (no --layer
    option or processing structure). A global processor receives a VectorData as input and must return one.
    """

    def new_func(*args, **kwargs):
        # noinspection PyShadowingNames
        def global_processor(state: VpypeState) -> VpypeState:

            logging.info(f"executing global processor `{f.__name__}` (kwargs: {kwargs})")
            with state.current():
                state.vector_data = f(state.vector_data, *args, **kwargs)

            return state

        return global_processor

    return update_wrapper(new_func, f)


def generator(f):
    """Helper decorator to define generator-type commands.

    Generator do not have input, have automatically a "-l, --layer" option added to them, and must return a
    LineCollection structure, which will be added to a new layer or an existing one depending the option.
    """

    @click.option(
        "-l", "--layer", type=LayerType(accept_new=True), default=None, help="Target layer."
    )
    def new_func(*args, **kwargs):
        layer = kwargs.pop("layer", -1)

        # noinspection PyShadowingNames
        def generator(state: VpypeState) -> VpypeState:
            if layer is LayerType.NEW or (layer is None and state.target_layer is None):
                target_layer = state.vector_data.free_id()
            elif layer is None:
                target_layer = state.target_layer
            else:
                target_layer = layer

            logging.info(
                f"executing generator `{f.__name__}` to layer {target_layer} (kwargs: {kwargs})"
            )

            with state.current():
                state.vector_data.add(f(*args, **kwargs), target_layer)
            state.target_layer = target_layer
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
