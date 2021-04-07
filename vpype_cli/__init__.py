"""This module implements vpype's CLI interface and the :func:`execute() <vpype_cli.execute>`
function.
"""
# register all commands
from .blocks import *
from .cli import *
from .debug import *
from .filters import *
from .frames import *
from .generators import *
from .layerops import *
from .operations import *
from .primitives import *
from .read import *
from .script import *

try:
    from .show import *

    show_imported = True
except ImportError:
    pass

from .text import *
from .transforms import *
from .write import *
