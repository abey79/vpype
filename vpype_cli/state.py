from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple, Union

import asteval
import click

import vpype as vp

__all__ = ("State", "_DeferredEvaluator")


class _SubstitutionHelper:
    """Dict-like class for :ref:`property substitution <fundamentals_property_substitution>`
    using :meth:`str.format_map`."""

    def __init__(
        self, document: Optional[vp.Document] = None, layer: Optional[vp.LineCollection] = None
    ):
        self.document = document
        self.layer = layer

    def __getitem__(self, item):
        if self.layer is not None and self.layer.property_exists(item):
            return self.layer.property(item)
        elif self.document is not None and self.document.property_exists(item):
            return self.document.property(item)
        else:
            raise click.BadParameter(f"Cannot substitute {{{item}}}: property not found")


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

    def __init__(self, text: str):
        self._text = text

    @abstractmethod
    def evaluate(self, state: "State") -> Any:
        """Sub-class must override this function and return the converted value of
        ``self._text``"""


class State:
    """Encapsulates the current state of the *vpype* pipeline processing.

    This class encapsulates the current state of the pipeline and provides services to
    commands. To access the current state instance, a command must use the :func:`pass_state`
    decorator.
    """

    _current_state: Union["State", None] = None

    def __init__(self, document: Optional[vp.Document] = None):
        #: Content of the current pipeline.
        self.document: vp.Document = document or vp.Document()

        #: Default layer ID used by :func:`generator` and :func:`layer_processor` commands
        #: when ``--layer`` is not provided.
        self.target_layer_id: Optional[int] = 1

        #: Layer ID being populated by a :func:`generator` or processed by a
        #: :func:`layer_processor` command.
        self.current_layer_id: Optional[int] = None

        self._symtable = {}
        self._interpreter = asteval.Interpreter(usersyms=self._symtable)

    def _evaluate_arg(self, arg: Any) -> Any:
        if isinstance(arg, tuple):
            return tuple(self._evaluate_arg(item) for item in arg)
        else:
            return arg.evaluate(self) if isinstance(arg, _DeferredEvaluator) else arg

    def evaluate_parameters(
        self, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
        """Replace any instance of :class:`_DeferredEvaluator` and replace them with the
        converted value.
        """
        return (
            tuple(self._evaluate_arg(arg) for arg in args),
            {k: self._evaluate_arg(v) for k, v in kwargs.items()},
        )

    def substitute_input(self, txt: str) -> str:
        """Apply :ref:`property substitution <fundamentals_property_substitution>` on input
        from user.

        Command implementation should favour using one (or more) of the types which have
        built-in substitution, such as :class:`TextType`, :class:`LengthType`, etc. This method
        may be used in cases where using types is not appropriate.

        Args:
            txt: input text on which to apply substitution

        Returns:
            fully-substituted text
        """
        helper = _SubstitutionHelper(
            self.document,
            self.document.layers[self.current_layer_id]
            if self.current_layer_id in self.document.layers
            else None,
        )

        try:
            return txt.format_map(helper)
        except ValueError as exc:
            raise click.BadParameter("Could not perform substitution: " + exc.args[0])

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
    def clear_document(self):
        """Context manager to temporarily clear and extend the state's document.

        This context manager is typically used by block processor to clear the document of
        line data while retaining its structure when executing nested processors, and then
        add the generated geometries to the original document. See :func:`block` for an
        example.
        """

        original_doc = self.document
        self.document = original_doc.clone(keep_layers=True)
        yield
        original_doc.extend(self.document)
        self.document = original_doc
