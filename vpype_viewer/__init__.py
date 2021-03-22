"""This module implements a flexible, GPU-accelerated viewer for interactive and offscreen
rendering of :class:`vpype.Document` instances. It includes a Qt-based interactive backend as
well as a Pillow-based offscreen rendering backend.
"""
from ._scales import DEFAULT_SCALE_SPEC, UnitType
from .engine import *
from .image import ImageRenderer, render_image

# currently Qt is the only GUI backend so we unconditionally import from qt
from .qtviewer import QtViewer, show
