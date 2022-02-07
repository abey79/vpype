import logging
from typing import ClassVar, List, Optional, Tuple, Union

import click

import vpype as vp

from .state import State, _DeferredEvaluator


class _DeferredEvaluatorType(click.ParamType):
    """Base class for types which rely on a deferred evaluator.

    Sub-classes must set the value of ``_evaluator_class``.
    """

    _evaluator_class: ClassVar = _DeferredEvaluator

    def convert(self, value, param, ctx):
        if isinstance(value, str):
            return self.__class__._evaluator_class(value)
        else:
            return super().convert(value, param, ctx)


class TextType(_DeferredEvaluatorType):
    """:class:`click.ParamType` sub-class to automatically perform
    :ref:`property substitution <fundamentals_property_substitution>` on user input.

    Example::

        >>> import click
        >>> import vpype_cli
        >>> import vpype
        >>> @vpype_cli.cli.command(group="my commands")
        ... @click.argument("text", type=vpype_cli.TextType())
        ... @vpype_cli.generator
        ... def my_command(text: str):
        ...     pass
    """

    class _TextDeferredEvaluator(_DeferredEvaluator):
        def evaluate(self, state: "State") -> str:
            return state.substitute(self._text)

    name = "text"
    _evaluator_class = _TextDeferredEvaluator


class IntegerType(_DeferredEvaluatorType):
    """:class:`click.ParamType` sub-class to automatically perform
    :ref:`property substitution <fundamentals_property_substitution>` on user input.

    Example::

        >>> import click
        >>> import vpype_cli
        >>> import vpype
        >>> @vpype_cli.cli.command(group="my commands")
        ... @click.argument("number", type=vpype_cli.IntegerType())
        ... @vpype_cli.generator
        ... def my_command(number: int):
        ...     pass
    """

    class _IntegerDeferredEvaluator(_DeferredEvaluator):
        def evaluate(self, state: "State") -> int:
            return int(state.substitute(self._text))

    name = "number"
    _evaluator_class = _IntegerDeferredEvaluator


class LengthType(_DeferredEvaluatorType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided lengths
    into CSS pixel units.


    User-provided length strings may contains units which are converted using
    :func:`convert_length`. :ref:`Property substitution <fundamentals_property_substitution>`
    is perfomred as well.

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

    class _LengthDeferredEvaluator(_DeferredEvaluator):
        def evaluate(self, state: "State") -> float:
            return vp.convert_length(state.substitute(self._text))

    name = "length"
    _evaluator_class = _LengthDeferredEvaluator


class AngleType(_DeferredEvaluatorType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided angle.

    User-provided angle strings may contain units and are converted into a value in degrees.
    This class uses :func:`convert_angle` internally.
    :ref:`Property substitution <fundamentals_property_substitution>` is perfomred as well.

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

    class _AngleDeferredEvaluator(_DeferredEvaluator):
        def evaluate(self, state: "State") -> float:
            return vp.convert_angle(state.substitute(self._text))

    name = "angle"
    _evaluator_class = _AngleDeferredEvaluator


class PageSizeType(_DeferredEvaluatorType):
    """:class:`click.ParamType` sub-class to automatically converts a user-provided page size.

    User-provided page size strings are converted into a tuple of float in CSS pixel units.
    See :func:`convert_page_size` for information on the page size descriptor syntax.
    :ref:`Property substitution <fundamentals_property_substitution>` is perfomred as well.

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

    class _PageSizeDeferredEvaluator(_DeferredEvaluator):
        def evaluate(self, state: "State") -> Tuple[float, float]:
            return vp.convert_page_size(state.substitute(self._text))

    name = "pagesize"
    _evaluator_class = _PageSizeDeferredEvaluator


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
        must_exists: if True, the function raises a :class:`click.BadParameter` exception

    Returns:
        Target layer ID
    """
    current_target_layer = State.get_current().target_layer_id

    if layer is LayerType.NEW or (layer is None and current_target_layer is None):
        lid = document.free_id()
    elif layer is None:
        lid = State.get_current().target_layer_id
    else:
        lid = layer

    if must_exist and lid not in document.layers:
        raise click.BadParameter(f"layer {layer} does not exist")

    return lid


class LayerType(click.ParamType):
    """Interpret values of --layer options.

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
