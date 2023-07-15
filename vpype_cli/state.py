from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import click

import vpype as vp

from .substitution import (
    ExpressionSubstitutionError,
    PropertySubstitutionError,
    SubstitutionHelper,
)

__all__ = ("State", "_DeferredEvaluator")


class _DeferredEvaluator(ABC):
    """Abstract base-class for deferred evaluation of command parameters.

    Click parses all command arguments and options before running the corresponding command
    functions. In contrast, :ref:`property substitution <fundamentals_property_substitution>`
    must be performed just *just before* a command is executed, since it depends on the current
    context (e.g. currently defined properties and current layer ID).

    To address this issue, sub-classes of :class:`click.ParamType` may return some
    :class:`_DeferredEvaluator` instance instead of directly converting the user
    input. The command decorators (e.g. :func:`generator` and friends) will detect such
    instances, perform the conversion, and forward the converted value to the command function.
    """

    def __init__(self, text: str, param_name: str, *args, **kwargs):
        self._text = text
        self._param_name = param_name

    @abstractmethod
    def evaluate(self, state: State) -> Any:
        """Sub-class must override this function and return the converted value of
        ``self._text``
        """

    def __str__(self):
        return self._text

    def __repr__(self):
        return repr(self._text)


class State:
    """Encapsulates the current state of the *vpype* pipeline processing.

    This class encapsulates the current state of the pipeline and provides services to
    commands. To access the current state instance, a command must use the :func:`pass_state`
    decorator.

    Args:
        document: if provided, use this document
    """

    _current_state: State | None = None

    def __init__(self, document: vp.Document | None = None):
        #: Content of the current pipeline.
        self.document: vp.Document = document or vp.Document()

        #: Default layer ID used by :func:`generator` and :func:`layer_processor` commands
        #: when ``--layer`` is not provided.
        self.target_layer_id: int | None = 1

        #: Layer ID being populated by a :func:`generator` or processed by a
        #: :func:`layer_processor` command.
        self.current_layer_id: int | None = None

        self._interpreter = SubstitutionHelper(self)

    def preprocess_argument(self, arg: Any) -> Any:
        """Evaluate an argument.

        If ``arg`` is a :class:`_DeferredEvaluator` instance, evaluate it a return its value
        instead.

        Args:
            arg: argument to evaluate

        Returns:
            returns the fully evaluated ``arg``
        """
        if isinstance(arg, tuple):
            return tuple(self.preprocess_argument(item) for item in arg)
        else:
            try:
                return arg.evaluate(self) if isinstance(arg, _DeferredEvaluator) else arg
            except Exception as exc:
                raise click.BadParameter(str(exc)) from exc

    def preprocess_arguments(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Evaluate any instance of :class:`_DeferredEvaluator` and replace them with the
        converted value.
        """
        return (
            tuple(self.preprocess_argument(arg) for arg in args),
            {k: self.preprocess_argument(v) for k, v in kwargs.items()},
        )

    def substitute(self, text: str) -> str:
        """Apply :ref:`property <fundamentals_property_substitution>` and
        :ref:`expression <fundamentals_expression_substitution>` substitution on user input.

        Args:
            text: user input on which to perform the substitution

        Returns:
            fully substituted text
        """
        try:
            return self._interpreter.substitute(text)
        except (ExpressionSubstitutionError, PropertySubstitutionError) as exc:
            cause_err = "Error"
            cause = getattr(exc, "__cause__", None)
            if cause:
                cause_err = cause.__class__.__name__
            type_err = (
                "expression" if isinstance(exc, ExpressionSubstitutionError) else "property"
            )
            details = ""
            if cause and len(cause.args) > 0:
                details = ": " + cause.args[0]
            raise click.BadParameter(
                f"{cause_err} with {type_err} substitution{details}"
            ) from exc

    @classmethod
    def get_current(cls):
        """Returns the current :class:`State` instance.

        Commands should use the :func:`pass_state` decorator instead of using this function.
        """
        return cls._current_state

    @contextmanager
    def current(self):
        """Context manager to set the current state (used internally)."""
        self.__class__._current_state = self
        yield
        self.__class__._current_state = None

    @contextmanager
    def expression_variables(self, variables: dict[str, Any]) -> Generator[None, None, None]:
        """Context manager to temporarily set expression variables.

        This context manager is typically used by block processors to temporarily set relevant
        expression variables. These variables are deleted or, if pre-existing, restored upon
        exiting the context.

        Args:
            variables: variables to set

        Example::

            >>> import vpype_cli
            >>> @vpype_cli.cli.command()
            ... @vpype_cli.block_processor
            ... def run_twice(state, processors):
            ...     with state.expression_variables({"_first": True}):
            ...         vpype_cli.execute_processors(processors, state)
            ...     with state.expression_variables({"_first": False}):
            ...         vpype_cli.execute_processors(processors, state)
        """

        symtable = self._interpreter.symtable
        saved_items = {k: symtable[k] for k in variables if k in symtable}
        symtable.update(variables)
        yield
        for name in variables:
            symtable.pop(name)
        symtable.update(saved_items)
