import logging
from typing import Any, List, Optional, Tuple, Union

import click

import vpype as vp

from .state import State


class LengthType(click.ParamType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided length
    string (which may contain units) into a value in CSS pixel units. This class uses
    :func:`convert_length` internally.

    Example::

        >>> import click
        >>> import vpype_cli
        >>> import vpype
        >>> @vpype_cli.cli.command(group="my commands")
        ... @click.argument("x", type=vpype_cli.LengthType())
        ... @click.option("-o", "--option", type=vpype_cli.LengthType(), default="1mm")
        ... @vpype_cli.generator
        ... def my_command(x: float, option: float):
        ...     pass
    """

    name = "length"

    def convert(self, value, param, ctx):
        if isinstance(value, str):
            try:
                return vp.convert_length(value)
            except ValueError:
                self.fail(f"parameter {value} is an incorrect length")
        else:
            return super().convert(value, param, ctx)


class AngleType(click.ParamType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided angle
    string (which may contain units) into a value in degrees. This class uses
    :func:`convert_angle` internally.

    Example::

        >>> import click
        >>> import vpype_cli
        >>> import vpype
        >>> @vpype_cli.cli.command(group="my commands")
        ... @click.argument("angle", type=vpype_cli.AngleType())
        ... @vpype_cli.generator
        ... def my_command(angle: float):
        ...     pass
    """

    name = "angle"

    def convert(self, value, param, ctx):
        try:
            if isinstance(value, str):
                return vp.convert_angle(value)
            else:
                return super().convert(value, param, ctx)
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
        ... @click.argument("fmt", type=vpype_cli.PageSizeType())
        ... @vpype_cli.generator
        ... def my_command(fmt: Tuple[float, float]):
        ...     pass
    """

    name = "pagesize"

    def convert(self, value: Any, param, ctx) -> Optional[Tuple[float, float]]:
        try:
            if isinstance(value, str):
                return vp.convert_page_size(value)
            else:
                return super().convert(value, param, ctx)

        except ValueError:
            self.fail(f"parameter {value} is not a valid page size")


def multiple_to_layer_ids(
    layers: Optional[Union[int, List[int]]], document: vp.Document
) -> List[int]:
    """Convert multiple-layer CLI argument to list of layer IDs.

    Args:
        layers: value from a :class:`LayerType` argument with accept_multiple=True
        document: target :class:`Document` instance

    Returns:
        List of layer IDs
    """
    if layers is None or layers is LayerType.ALL:
        return sorted(document.ids())
    elif isinstance(layers, list):
        lids = []
        for lid in sorted(layers):
            if document.exists(lid):
                lids.append(lid)
            else:
                logging.info(f"layer {lid} does not exist")
        return lids
    else:
        return []


def single_to_layer_id(
    layer: Optional[int], document: vp.Document, must_exist: bool = False
) -> int:
    """Convert single-layer CLI argument to layer ID, accounting for the existence of a current
    a current target layer and dealing with default behavior.

    Arg:
        layer: value from a :class:`LayerType` argument
        document: target :class:`Document` instance (for new layer ID)
        must_exists: if True, the function

    Returns:
        Target layer ID
    """
    current_target_layer = State.get_current().target_layer

    if layer is LayerType.NEW or (layer is None and current_target_layer is None):
        lid = document.free_id()
    elif layer is None:
        lid = State.get_current().target_layer
    else:
        lid = layer

    if must_exist and lid not in document.layers:
        raise click.BadParameter(f"layer {layer} does not exist")

    return lid


class LayerType(click.ParamType):
    """
    Interpret value of --layer options.

    If `accept_multiple == True`, comma-separated array of int is accepted or 'all'. Returns
    either a list of IDs or `LayerType.ALL`.

    If `accept_new == True`, 'new' is also accepted, in which case returns `LayerType.NEW`.

    None is passed through, which typically means to use the default behaviour.
    """

    name = "layer ID"

    NEW = -1
    ALL = -2

    def __init__(self, accept_multiple: bool = False, accept_new: bool = False):
        self.accept_multiple = accept_multiple
        self.accept_new = accept_new

        if accept_multiple:
            self.name = "layers"
        else:
            self.name = "layer"

    def convert(self, value, param, ctx):
        # accept value when already converted to final type
        if isinstance(value, int):
            if value > 0 or value in [self.ALL, self.NEW]:
                return value
            else:
                self.fail(f"inconsistent converted value {value}")

        value = str(value)
        if value.lower() == "all":
            if self.accept_multiple:
                return LayerType.ALL
            else:
                self.fail(
                    f"parameter {param.human_readable_name} must be a single layer and does "
                    "not accept `all`",
                    param,
                    ctx,
                )
        elif value.lower() == "new":
            if self.accept_new:
                return LayerType.NEW
            else:
                self.fail(
                    f"parameter {param.human_readable_name} must be an existing layer and "
                    "does not accept `new`",
                    param,
                    ctx,
                )

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
            self.fail(
                f"{value!r} is not a valid value for parameter {param.human_readable_name}",
                param,
                ctx,
            )
