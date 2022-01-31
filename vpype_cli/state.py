from contextlib import contextmanager
from typing import Optional, Union

import vpype as vp

__all__ = ("State",)


class State:
    current_state: Union["State", None] = None

    def __init__(self, doc: Union[vp.Document, None] = None):
        if doc is not None:
            self.document = doc
        else:
            self.document = vp.Document()

        self.target_layer: Optional[int] = None

    @classmethod
    def get_current(cls):
        return cls.current_state

    @contextmanager
    def current(self):
        self.__class__.current_state = self
        yield
        self.__class__.current_state = None
