"""This module contains vpype core and its API."""

from ._deprecated import *
from .config import *
from .filters import *
from .geometry import *
from .io import *
from .line_index import *
from .metadata import *
from .model import *
from .primitives import *
from .text import *
from .utils import *


def _get_version() -> str:
    from importlib.metadata import version

    return version(__name__)


__version__ = _get_version()
