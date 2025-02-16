from __future__ import annotations

import glob
import os
import pathlib
import sys
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Callable

import asteval

import vpype as vp

if TYPE_CHECKING:  # pragma no cover
    from .state import State


class PropertySubstitutionError(Exception):
    """Error while performing property substitution."""


class ExpressionSubstitutionError(Exception):
    """Error while performing expression substitution."""


class _PropertyProxy:
    """Helper proxy class to provide access to global and current layer properties.

    Used for :ref:`property substitution <fundamentals_property_substitution>`
    using :meth:`str.format_map` and for expression evaluation.

    Either or both global and current layer properties may be configured. If both are enabled,
    current layer's properties take precedence over global properties.

    Args:
        state: :class:`State` instance
        global_prop: access global properties
        layer_prop: access current layer properties
    """

    def __init__(self, state: State, global_prop: bool = True, layer_prop: bool = True):
        self._state = state
        self._global_prop = global_prop
        self._layer_prop = layer_prop

    def _get_prop(self, name) -> Any | None:
        if self._state.document is None:
            return None

        if (
            self._layer_prop
            and self._state.current_layer_id is not None
            and self._state.document.exists(self._state.current_layer_id)
            and self._state.document.layers[self._state.current_layer_id].property_exists(name)
        ):
            return self._state.document.layers[self._state.current_layer_id].property(name)
        elif self._global_prop and self._state.document.property_exists(name):
            return self._state.document.property(name)
        else:
            return None

    def _set_prop(self, name, value) -> None:
        if self._state.document is None or self._layer_prop == self._global_prop:
            raise TypeError("cannot set property value (read-only)")

        if self._layer_prop:
            if self._state.current_layer_id is None or not self._state.document.exists(
                self._state.current_layer_id
            ):
                raise TypeError("cannot set property value (unknown current layer)")
            else:
                self._state.document.layers[self._state.current_layer_id].set_property(
                    name, value
                )
        elif self._global_prop:
            self._state.document.set_property(name, value)

    def keys(self):
        k = set()
        if self._global_prop and self._state.document is not None:
            k |= self._state.document.metadata.keys()
        if (
            self._layer_prop
            and self._state.current_layer_id is not None
            and self._state.document.exists(self._state.current_layer_id)
        ):
            k |= self._state.document.layers[self._state.current_layer_id].metadata.keys()
        return k

    def __getitem__(self, name):
        prop = self._get_prop(name)
        if prop is not None:
            return prop
        else:
            raise KeyError(f"property '{name}' not found")

    def __setitem__(self, name, value):
        self._set_prop(name, value)

    def __getattr__(self, name):
        prop = self._get_prop(name)
        if prop is not None:
            return prop
        else:
            # Note: this cannot be `AttributeError` because they are silenced by asteval
            raise KeyError(f"property '{name}' not found")

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._set_prop(name, value)


def _split_text(
    text: str, prop_interpreter: Callable[[str], str], expr_interpreter: Callable[[str], Any]
) -> Iterable[str]:
    """Split input in chunks, applying either the property or expression interpreter based
    on markers.

    Args:
        text: input to process
        prop_interpreter: interpreter for chunks enclosed in curly braces (the braces will be
            included in the input provided)
        expr_interpreter: interpreter for the chunks enclosed in ``%`` markers (the marker will
            *not* be included in the input provided)

    Returns:
        generator of processed text chunks
    """

    in_prop = False
    in_expr = False
    cur_token = ""

    while True:
        if len(text) == 0:
            if in_expr:
                raise ExpressionSubstitutionError(
                    "unterminated expression substitution pattern"
                )
            if in_prop:
                raise PropertySubstitutionError("unterminated property substitution pattern")
            break

        assert not (in_prop and in_expr)

        s, text = text[0], text[1:]
        peek = text[0] if len(text) > 0 else ""

        if s == "{":
            if in_prop:
                raise PropertySubstitutionError(
                    "'{' not allowed inside property substitution patterns"
                )
            elif in_expr:
                cur_token += s
            elif peek == "{":
                cur_token += s
                text = text[1:]
            else:
                yield cur_token
                cur_token = s
                in_prop = True
        elif s == "}":
            if in_prop:
                try:
                    yield str(prop_interpreter(cur_token + s))
                except Exception as exc:
                    raise PropertySubstitutionError() from exc
                cur_token = ""
                in_prop = False
            elif in_expr:
                cur_token += s
            elif peek == "}":
                cur_token += s
                text = text[1:]
            else:
                raise PropertySubstitutionError("closing '}' without matching '{'")
        elif s == "%":
            if in_prop:
                cur_token += s
            elif peek == "%":
                cur_token += s
                text = text[1:]
            elif in_expr:
                try:
                    yield str(expr_interpreter(cur_token))
                except Exception as exc:
                    raise ExpressionSubstitutionError() from exc
                cur_token = ""
                in_expr = False
            else:
                yield cur_token
                cur_token = ""
                in_expr = True
        else:
            cur_token += s

    yield cur_token


def _substitute_expressions(
    text: str, prop_interpreter: Callable[[str], str], expr_interpreter: Callable[[str], Any]
) -> str:
    """Apply substitution with custom interpreter functions for property substitution and for
    expression substitution.

    Used for testing :func:`_split_text`.
    """
    return "".join(_split_text(text, prop_interpreter, expr_interpreter))


def _glob(files: str) -> list[pathlib.Path]:
    return [
        pathlib.Path(file) for file in glob.glob(os.path.expandvars(os.path.expanduser(files)))
    ]


_OS_PATH_SYMBOLS = (
    "abspath",
    "basename",
    "dirname",
    "exists",
    "expanduser",
    "isfile",
    "isdir",
    "splitext",
)


class SubstitutionHelper:
    """Helper class to perform :ref:`property <fundamentals_property_substitution>` and
    :ref:`expression <fundamentals_expression_substitution>` substitution.

    Args:
        state: :class:`State` instance
    """

    def __init__(self, state: State):
        self._property_proxy = _PropertyProxy(state, True, True)
        symtable = {
            **vp.UNITS,
            **{f: getattr(os.path, f) for f in _OS_PATH_SYMBOLS},
            "input": input,
            "glob": _glob,
            "convert_length": vp.convert_length,
            "convert_angle": vp.convert_angle,
            "convert_page_size": vp.convert_page_size,
            "stdin": sys.stdin,
            "Color": vp.Color,
            "prop": self._property_proxy,
            "lprop": _PropertyProxy(state, False, True),
            "gprop": _PropertyProxy(state, True, False),
        }
        # disabling numpy as its math functions such as `ceil` do not convert to int.
        self._interpreter = asteval.Interpreter(
            user_symbols=symtable,
            readonly_symbols=symtable.keys() - vp.UNITS.keys(),
            use_numpy=False,
        )

    @property
    def symtable(self) -> dict[str, Any]:
        return self._interpreter.symtable

    def substitute(self, text: str) -> str:
        """Apply :ref:`property <fundamentals_property_substitution>` and
        :ref:`expression <fundamentals_expression_substitution>` substitution.

        Args:
            text: user input

        Returns:
            fully substituted text
        """
        return _substitute_expressions(
            text,
            lambda s: s.format_map(self._property_proxy),
            lambda s: self._interpreter(s, raise_errors=True, show_errors=False),
        )
