from contextlib import contextmanager
from typing import Union, List

import click

from .model import VectorData


class VpypeState:
    current_state: Union["VpypeState", None] = None

    def __init__(self, vd: Union[VectorData, None] = None):
        if vd is not None:
            self.vector_data = vd
        else:
            self.vector_data = VectorData()

        self.target_layer = None

    @classmethod
    def get_current(cls):
        return cls.current_state

    @contextmanager
    def current(self):
        self.__class__.current_state = self
        yield
        self.__class__.current_state = None


class LayerType(click.ParamType):
    """
    Interpret value of --layer options.

    If `accept_multiple == True`, comma-separated array of int is accepted or 'all'. Returns
    either a list of IDs or `LayerType.ALL`.

    If `accept_new == True`, 'new' is also accepted, in which case returns `LayerType.NEW`.

    None is passed through, which typically means to use the default behaviour.
    """

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