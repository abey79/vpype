from .vpype import cli, processor, generator

# register all commands
from .blocks import *
from .generators import *
from .hatch import *
from .transforms import *
from .files import *
from .frames import *
from .show import *

__all__ = ["cli"]
