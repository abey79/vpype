"""This module contains vpype core and its API."""

from .config import *
from .decorators import *
from .geometry import *
from .io import *
from .layers import *
from .line_index import *
from .model import *
from .primitives import *
from .utils import *


def _get_version() -> str:
    import pkg_resources

    return pkg_resources.get_distribution("vpype").version


__version__ = _get_version()
