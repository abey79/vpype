from contextlib import contextmanager
from typing import List, Optional, Union

import click

from .model import Document

# REMINDER: anything added here must be added to docs/api.rst
__all__ = ["VpypeState", "multiple_to_layer_ids", "single_to_layer_id", "LayerType"]


class VpypeState:
    current_state: Union["VpypeState", None] = None

    def __init__(self, doc: Union[Document, None] = None):
        if doc is not None:
            self.document = doc
        else:
            self.document = Document()

        self.target_layer: Optional[int] = None

    @classmethod
    def get_current(cls):
        return cls.current_state

    @contextmanager
    def current(self):
        self.__class__.current_state = self
        yield
        self.__class__.current_state = None


def multiple_to_layer_ids(
    layers: Optional[Union[int, List[int]]], document: Document
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
        return sorted(vid for vid in layers if document.exists(vid))
    else:
        return []


def single_to_layer_id(
    layer: Optional[int], document: Document, must_exist: bool = False
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
    current_target_layer = VpypeState.get_current().target_layer

    if layer is LayerType.NEW or (layer is None and current_target_layer is None):
        lid = document.free_id()
    elif layer is None:
        lid = VpypeState.get_current().target_layer
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
