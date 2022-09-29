from __future__ import annotations

import contextlib
import enum
import time
from threading import Event, RLock, Thread
from typing import Any, Iterator

import click
from rich.columns import Columns
from rich.console import RenderableType
from rich.emoji import Emoji
from rich.spinner import Spinner
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

_dim_style = Style(italic=True, color="grey50")
_command_name_style = Style(underline=True, bold=True)
_options_style = Style(italic=True, color="grey50")
_arguments_style = Style()
_time_style = Style(italic=True, color="blue")
_warning_style = Style(color="red")


_TIME_UNITS = ["s", "ms", "ns"]

#######################################
# Monkey patch value formatting
#######################################


# noinspection PyUnusedLocal
def format_value(self: click.Parameter, value: Any) -> str:
    return f"{value}"


click.ParamType.format_value = format_value

#######################################


class Level(enum.Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2


def _format_duration(duration: float) -> str:
    for unit in _TIME_UNITS:
        if duration > 0.1:
            return f"{duration:0.2f}{unit}"
        else:
            duration *= 1000


def format_number(num: float, precision: int = 3) -> str:
    s = f"{num:.{precision}f}"
    if float(s) == num:
        s = s.rstrip("0").rstrip(".")
    else:
        s += "…"
    return s


def format_length(length: float) -> str:
    return format_number(length) + "px"


def test_format_number():
    assert format_number(1) == "1"
    assert format_number(1.234) == "1.234"
    assert format_number(1.2345) == "1.234…"
    assert format_number(1000.123456) == "1000.123…"
    assert format_number(1000.123456, 4) == "1000.1235…"


def test_format_length():
    assert format_length(1) == "1px"
    assert format_length(1.234) == "1.234px"
    assert format_length(1.2345) == "1.234…px"
    assert format_length(1000.123456) == "1000.123…px"


class HierarchicalTable:
    def __init__(self):
        self.table = Table(show_header=False, border_style=None, box=None, padding=0)
        self._current_level = 0
        self._current_root: Table | Tree = self.table
        self._last_item = None

    def add(self, *renderables: RenderableType):
        self._last_item = Tree(Columns(renderables))
        if isinstance(self._current_root, Table):
            self._current_root.add_row(self._last_item)
        else:
            self._current_root.add(self._last_item)

    @contextlib.contextmanager
    def nest(self):
        previous_root = self._current_root
        self._current_root = self._last_item
        try:
            yield
        finally:
            self._current_root = previous_root


htable = HierarchicalTable()

nest = htable.nest


# class MessageType(enum.Enum):
#     NOTE = ("Note", Style(color="cyan", bold=True), Style(color="cyan"))
#     WARNING = ("Warning", Style(color="orange1", bold=True), Style(color="orange1"))
#     ERROR = ("Error", Style(color="red", bold=True), Style(color="red"))
#
#     def __init__(self, title: str, title_style: Style, message_style: Style):
#         self.title = title
#         self.title_style = title_style
#         self.message_style = message_style


class _DurationUpdateThread(Thread):
    def __init__(self, command: CommandBlock, refresh_per_second: float) -> None:
        self.command = command
        self.refresh_per_second = refresh_per_second
        self.done = Event()
        super().__init__(daemon=True)

    def stop(self) -> None:
        self.done.set()

    def run(self) -> None:
        while not self.done.wait(1 / self.refresh_per_second):
            self.command.update_duration()


def _format_kwargs(kwargs: dict[str, Any]) -> RenderableType:
    return Text(", ".join(f"{k}: {v}" for k, v in kwargs.items()), style=_options_style)


class _Block(Table):
    _current_block: _Block | None = None

    def __init__(self):
        super().__init__(show_header=False, border_style=None, box=None, padding=0)

    def add_line(self, *renderables: RenderableType) -> None:
        self.add_row(Columns(renderables))

    @contextlib.contextmanager
    def as_current(self) -> Iterator[None]:
        prev_block = _Block._current_block
        _Block._current_block = self
        yield
        _Block._current_block = prev_block

    @classmethod
    def current(cls) -> _Block | None:
        return cls._current_block


class ContextBlock(_Block):
    def __init__(self, label: str):
        super().__init__()
        self.add_column()
        self.add_row(Text(label, style=_dim_style))


class CommandBlock(_Block):
    def __init__(self, command: click.Command, name_style: Style = _command_name_style):
        super().__init__()
        self.add_column(width=3)
        self.add_column()
        self._command = command
        self._execution_time_label = Text("(running...)", style=_time_style)
        self._arguments_label = Text("", style=_arguments_style)
        self._options_label = Text("", style=_options_style)
        self._status_columns = Columns([Spinner("dots")])
        self._lock = RLock()
        self._duration_update_thread = _DurationUpdateThread(self, 10)
        self._duration_update_thread.start()

        self.add_row(
            self._status_columns,
            Columns(
                [
                    Text(command.name, style=name_style),
                    # self._options_label,
                    # self._arguments_label,
                    self._execution_time_label,
                ]
            ),
        )
        self._start_time = time.perf_counter()

    def add_line(self, *renderables: RenderableType) -> None:
        self.add_row("", Columns(renderables))

    def update_duration(self) -> None:
        with self._lock:
            self._execution_time_label.plain = (
                f"(in {_format_duration(time.perf_counter() - self._start_time)})"
            )

    def set_kwargs(self, kwargs: dict[str, Any]):
        if kwargs:
            self.add_line(_format_kwargs(kwargs))

    def add_subcontext(self, label: str, kwargs: dict[str, Any]):
        # TODO: this probably need to be reimplemented based on print()
        renderables = [Text(label + ":" if kwargs else "")]
        if kwargs:
            renderables.append(_format_kwargs(kwargs))
        self.add_line(*renderables)

    def completed(self, success: bool = True) -> None:
        self._duration_update_thread.stop()
        with self._lock:
            self.update_duration()
            # noinspection PyUnresolvedReferences
            self._status_columns.renderables[0] = Emoji(
                "white_check_mark" if success else "cross_mark"
            )

    def message(self, *renderables: RenderableType):
        self.add_line(*renderables)


_handled_exceptions = set()
_current_block: _Block | None = None


@contextlib.contextmanager
def _set_current_block(block: _Block) -> Iterator[None]:
    global _current_block

    prev_block = _current_block
    _current_block = block
    yield
    _current_block = prev_block


@contextlib.contextmanager
def context(label: str) -> Iterator[ContextBlock]:
    ctx = ContextBlock(label)
    with _set_current_block(ctx):
        htable.add(ctx)
        yield ctx


@contextlib.contextmanager
def command(click_command: click.Command) -> Iterator[CommandBlock]:
    global _current_block

    cmd = CommandBlock(click_command)
    with _set_current_block(cmd):
        htable.add(cmd)
        success = True
        try:
            yield cmd
        except click.ClickException as exc:
            if exc not in _handled_exceptions:
                cmd.message(Text(exc.format_message(), style=_warning_style))
                _handled_exceptions.add(exc)
            success = False
            raise
        except:
            # TODO: add message
            success = False
            raise
        finally:
            cmd.completed(success=success)


# noinspection PyShadowingBuiltins
def print(*args, level: Level | None = None) -> None:
    # TODO: handle level
    # TODO: this needs renaming
    # TODO: this is proper plug-in API, so must be exposed
    assert _current_block is not None
    _current_block.add_line(*args)
