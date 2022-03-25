"""Config file support for vpype.

Configuration data is accessed via the ``config_manager`` global variable::

    >>> from vpype import config_manager
    >>> config_manager.config  # dictionary of all configuration

HPGL plotter have specific config support::

    >>> plotter_config = config_manager.get_plotter_config("hp7475a")
    >>> plotter_config
    PlotterConfig(name='hp7475a', ...)
    >>> plotter_config.paper_config("a4")
    PaperConfig(name='a4', paper_size=(1122.5196850393702, 793.7007874015749), ...)
"""

from __future__ import annotations

import dataclasses
import logging
import math
import os
import pathlib
from typing import Any, Mapping, Sequence

import tomli

from .utils import convert_length

__all__ = [
    "PaperConfig",
    "PlotterConfig",
    "ConfigManager",
    "config_manager",
]


def _convert_length_pair(data: Sequence[float | str]) -> tuple[float, float]:
    return convert_length(data[0]), convert_length(data[1])


@dataclasses.dataclass(frozen=True)
class PaperConfig:
    """Data class containing configuration for a give plotter type/paper size combinations."""

    name: str  #: name of the paper format
    y_axis_up: bool  #: if True, the Y axis point upwards instead of downwards
    origin_location: tuple[
        float, float
    ]  #: location on paper of the (0, 0) plotter unit coordinates

    paper_size: tuple[float, float] | None = None  #: X/Y axis convention of the plotter
    paper_orientation: None | (
        str
    ) = None  #: orientation of the plotter coordinate system on paper
    x_range: tuple[int, int] | None = None  #: admissible range of X coordinates
    y_range: tuple[int, int] | None = None  #: admissible range of Y coordinates
    origin_location_reference: str | None = "topleft"  #: reference for ``origin_location``

    info: str = ""  #: information printed to the user when paper is used
    rotate_180: bool = False  #: if True, the geometries are rotated by 180 degrees on the page
    set_ps: int | None = None  #: if not None, call PS with corresponding value
    final_pu_params: None | (
        str
    ) = None  #: if not None, these params are added to the final PU command
    aka_names: list[str] = dataclasses.field(
        default_factory=list
    )  #: alternative paper names (will be found by :func:`paper_config`

    @classmethod
    def from_config(cls, data: dict[str, Any]) -> PaperConfig:
        return cls(
            name=data["name"],
            y_axis_up=data["y_axis_up"],
            origin_location=_convert_length_pair(data["origin_location"]),
            paper_size=_convert_length_pair(data["paper_size"])
            if "paper_size" in data
            else None,
            paper_orientation=data.get("paper_orientation", None),
            x_range=(data["x_range"][0], data["x_range"][1]) if "x_range" in data else None,
            y_range=(data["y_range"][0], data["y_range"][1]) if "y_range" in data else None,
            origin_location_reference=data.get("origin_location_reference", "topleft"),
            info=data.get("info", ""),
            rotate_180=data.get("rotate_180", False),
            set_ps=data.get("set_ps", None),
            final_pu_params=data.get("final_pu_params", None),
            aka_names=data.get("aka_names", []),
        )


@dataclasses.dataclass(frozen=True)
class PlotterConfig:
    """Data class containing configuration for a given plotter type."""

    name: str  #: name of the plotter
    paper_configs: list[PaperConfig]  #: list of :class:`PaperConfig` instance
    plotter_unit_length: float  #: physical size of plotter units (in pixel)
    pen_count: int  #: number of pen supported by the plotter

    info: str = ""  #: information printed to the user when plotter is used

    @classmethod
    def from_config(cls, data: dict[str, Any]) -> PlotterConfig:
        return cls(
            name=data["name"],
            paper_configs=[PaperConfig.from_config(d) for d in data["paper"]],
            plotter_unit_length=convert_length(data["plotter_unit_length"]),
            pen_count=data["pen_count"],
            info=data.get("info", ""),
        )

    def paper_config(self, paper: str) -> PaperConfig | None:
        """Return the paper configuration for ``paper`` or none if not found.

        Args:
            paper: desired paper format designator

        Returns:
            the :class:`PaperConfig` instance corresponding to ``paper`` or None if not found
        """
        for pc in self.paper_configs:
            if paper == pc.name or paper in pc.aka_names:
                return pc
        return None

    def paper_config_from_size(
        self, page_size: tuple[float, float] | None
    ) -> PaperConfig | None:
        """Look for a paper configuration matching ``paper_format`` and return it if found.

        Args:
            page_size: tuple of desired page size (may be ``None``, in which case ``None`` is
                returned

        Returns:
            the :class:`PaperConfig` instance corresponding to ``paper_format`` or None if not
            found
        """

        if page_size is None:
            return None

        def _isclose_tuple(a, b):
            return all(math.isclose(aa, bb) for aa, bb in zip(a, b))

        for pc in self.paper_configs:
            if _isclose_tuple(pc.paper_size, page_size) or _isclose_tuple(
                pc.paper_size, tuple(reversed(page_size))
            ):
                return pc
        return None


class ConfigManager:
    """Helper class to handle vpype's TOML configuration files.

    This class is typically used via its singleton instance ``config_manager``::

        >>> from vpype import config_manager
        >>> my_config = config_manager.config.get("my_config", None)

    Helper methods are provided for specific aspects of configuration, such as command-specific
    configs or HPGL-related configs.

    By default, built-in configuration packaged with vpype are loaded at startup. If a file
    exists at path ``~/.vpype.toml``, it will be loaded as well. Additionaly files may be
    loaded using the :func:`load_config_file` method.
    """

    def __init__(self):
        self._config: dict = {}

    def load_config_file(self, path: str) -> None:
        """Load a config file and add its content to the configuration database. The
        configuration file must be in TOML format.

        Args:
            path: path of the config file
        """

        def _update(d: dict, u: Mapping) -> dict:
            """This function must overwrite list member, UNLESS they are list of table, in
            which case they must extend the list."""
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = _update(d.get(k, {}), v)
                elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    if k in d:
                        d[k].extend(v)
                    else:
                        d[k] = v
                else:
                    d[k] = v
            return d

        logging.info(f"loading config file at {path}")
        with open(path, "rb") as fp:
            self._config = _update(self._config, tomli.load(fp))

    def get_plotter_list(self) -> list[str]:
        """Returns a list of plotter names whose configuration is available.

        Returns:
            list of plotter name
        """
        return list(self.config.get("device", {}).keys())

    def get_plotter_config(self, device: str | None) -> PlotterConfig | None:
        """Returns a :class:`PlotterConfig` instance for plotter ``device``.

        If ``None`` is passed, this function attempts to use the default device if one is
        configured, or the function returns None.

        Args:
            device: name of desired plotter (or ``None`` to use the default device if
                configured)

        Returns:
            :class:`PlotterConfig` instance or None if not found
        """
        devices = self.config.get("device", {})
        if device is None:
            device = self.get_command_config("write").get("default_hpgl_device", None)
        if device in devices:
            return PlotterConfig.from_config(devices[device])
        else:
            return None

    def get_command_config(self, name: str) -> dict[str, Any]:
        """Returns the configuration for command ``name``.

        Args:
            name: name of the command

        Returns:
            dictionary containing the config values (empty if none defined)
        """
        commands = self.config.get("command", {})
        if name in commands:
            return commands[name]
        else:
            return {}

    @property
    def config(self) -> dict[str, Any]:
        return self._config


config_manager = ConfigManager()


def _init():
    config_manager.load_config_file(str(pathlib.Path(__file__).parent / "vpype_config.toml"))
    path = os.path.expanduser("~/.vpype.toml")
    if os.path.exists(path):
        config_manager.load_config_file(str(path))


_init()
