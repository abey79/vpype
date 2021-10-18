import os
import signal
import socket
from contextlib import contextmanager
from typing import Callable

from PySide2 import QtNetwork
from PySide2.QtCore import QCoreApplication
from PySide2.QtGui import QIcon, QPalette
from PySide2.QtWidgets import QAction, QActionGroup


def load_icon(path: str) -> QIcon:
    path = os.path.abspath(
        os.path.dirname(__file__) + os.path.sep + "resources" + os.path.sep + path
    )

    # check if dark mode is enabled
    base_color = QCoreApplication.instance().palette().color(QPalette.Base)
    if base_color.lightnessF() < 0.5:
        file, ext = os.path.splitext(path)
        path = file + "-dark" + ext

    icon = QIcon(path)
    return icon


class PenWidthActionGroup(QActionGroup):
    widths = [
        0.05,
        0.1,
        0.15,
        0.2,
        0.25,
        0.3,
        0.35,
        0.4,
        0.45,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.2,
    ]

    def __init__(self, current: float = 0.3, parent=None):
        super().__init__(parent)

        if current not in self.widths:
            self.widths.append(current)
        for w in sorted(self.widths):
            act = self.addAction(QAction(f"{w} mm"))
            act.setCheckable(True)
            act.setChecked(w == current)
            act.setData(w)


class PenOpacityActionGroup(QActionGroup):
    opacities = [
        0.3,
        0.5,
        0.7,
        0.8,
        0.9,
        0.95,
        1,
    ]

    def __init__(self, current: float = 0.8, parent=None):
        super().__init__(parent)

        if current not in self.opacities:
            self.opacities.append(current)
        for w in sorted(self.opacities):
            act = self.addAction(QAction(f"{int(w*100)}%"))
            act.setCheckable(True)
            act.setChecked(w == current)
            act.setData(w)


class SignalWatchdog(QtNetwork.QAbstractSocket):
    """This object notify PySide2's event loop of an incoming signal and makes it process it.

    The python interpreter flags incoming signals and triggers the handler only upon the next
    bytecode is processed. Since PySide2's C++ event loop function never/rarely returns when
    the UX is in the background, the Python interpreter doesn't have a chance to run and call
    the handler.

    From: https://stackoverflow.com/a/65802260/229511 and
    https://stackoverflow.com/a/37229299/229511
    """

    def __init__(self):
        # noinspection PyTypeChecker
        super().__init__(QtNetwork.QAbstractSocket.SctpSocket, None)  # type: ignore
        self.writer, self.reader = socket.socketpair()
        self.writer.setblocking(False)
        signal.set_wakeup_fd(self.writer.fileno())
        self.setSocketDescriptor(self.reader.fileno())
        self.readyRead.connect(lambda: None)


@contextmanager
def set_sigint_handler(handler: Callable):
    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handler)
    # noinspection PyUnusedLocal
    watchdog = SignalWatchdog()
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, original_handler)
        del watchdog
