from __future__ import annotations


def _check_wayland():
    """Fix QT env variable on Wayland-based systems.

    See https://github.com/abey79/vpype/issues/596
    """
    import os
    import sys

    if sys.platform.startswith("linux"):
        if os.environ.get("XDG_SESSION_TYPE", "") == "wayland":
            if "QT_QPA_PLATFORM" not in os.environ:
                os.environ["QT_QPA_PLATFORM"] = "xcb"


_check_wayland()


from .viewer import *  # noqa: E402
