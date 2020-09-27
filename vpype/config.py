"""
.. module:: vpype

Config file support for vpype.

Configuration data is accessed via the ``CONFIG_MANAGER`` global variable::

    >>> from vpype import CONFIG_MANAGER
    >>> CONFIG_MANAGER.config  # dictionary of all configuration

HPGL plotter have specific config support::

    >>> plotter_config = CONFIG_MANAGER.get_plotter_config("hp7475a")
    >>> plotter_config
    PlotterConfig(name='hp7475a', ...)
    >>> plotter_config.paper_config("a4")
    PaperConfig(name='a4', paper_size=(1122.5196850393702, 793.7007874015749), ...)
"""

import logging
import os
import pathlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import attr
import toml

from .utils import convert_length

__all__ = [
    "PaperConfig",
    "PlotterConfig",
    "ConfigManager",
    "CONFIG_MANAGER",
]


def _convert_length_pair(data: Sequence[Union[float, str]]) -> Tuple[float, float]:
    return convert_length(data[0]), convert_length(data[1])


@attr.s(auto_attribs=True, frozen=True)
class PaperConfig:
    name: str
    paper_size: Tuple[float, float]  #: X/Y axis convention of the plotter
    x_range: Tuple[int, int]
    y_range: Tuple[int, int]
    y_axis_up: bool
    origin_location: Tuple[float, float]  #: same coordinates as ``format``

    set_ps: Optional[int] = None  # if set, call PS with corresponding value
    aka_names: List[str] = []

    @classmethod
    def from_config(cls, data: Dict[str, Any]) -> "PaperConfig":
        return cls(
            name=data["name"],
            paper_size=_convert_length_pair(data["paper_size"]),
            x_range=(data["x_range"][0], data["x_range"][1]),
            y_range=(data["y_range"][0], data["y_range"][1]),
            y_axis_up=data["y_axis_up"],
            origin_location=_convert_length_pair(data["origin_location"]),
            set_ps=data.get("set_ps", None),
            aka_names=data.get("aka_names", []),
        )


@attr.s(auto_attribs=True, frozen=True)
class PlotterConfig:
    name: str
    paper_configs: List[PaperConfig]
    plotter_unit_length: float
    pen_count: int

    @classmethod
    def from_config(cls, data: Dict[str, Any]) -> "PlotterConfig":
        return cls(
            name=data["name"],
            paper_configs=[PaperConfig.from_config(d) for d in data["paper"]],
            plotter_unit_length=convert_length(data["plotter_unit_length"]),
            pen_count=data["pen_count"],
        )

    def paper_config(self, paper: str) -> Optional[PaperConfig]:
        """Return the paper configuration for `paper` or none if not found.

        Args:
            paper: desired paper format

        Returns:
            the :class:`PaperConfig` instance corresponding to `paper` or None if not found
        """
        for pc in self.paper_configs:
            if paper == pc.name or paper in pc.aka_names:
                return pc
        return None


class ConfigManager:
    def __init__(self):
        self._config: Dict = {}

    def load_config_file(self, path: str) -> None:
        """Load a config file and add its content to the configuration database. The
        configuration file must be in TOML format.

        Args:
            path: path of the config file
        """

        def _update(d: Dict, u: Mapping) -> Dict:
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
        self._config = _update(self._config, toml.load(path))

    def get_plotter_config(self, name: str) -> Optional[PlotterConfig]:
        """Returns a :class:`PlotterConfig` instance for plotter ``name`.

        Args:
            name: name of desired plotter

        Returns:
            :class:`PlotterConfig` instance or None if not found
        """
        devices = self.config.get("device", {})
        if name in devices:
            return PlotterConfig.from_config(devices[name])
        else:
            return None

    def get_command_config(self, name: str) -> Dict[str, Any]:
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
    def config(self) -> Dict[str, Any]:
        return self._config


CONFIG_MANAGER = ConfigManager()


def _init():
    CONFIG_MANAGER.load_config_file(str(pathlib.Path(__file__).parent / "hpgl_devices.toml"))
    path = os.path.expanduser("~/.vpype.toml")
    if os.path.exists(path):
        CONFIG_MANAGER.load_config_file(str(path))


_init()
