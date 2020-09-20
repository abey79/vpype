import os
import pathlib
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import attr
import toml

from .utils import convert_length

__all__ = ["PaperConfig", "PlotterConfig", "get_plotter_config", "add_config"]


_PLOTTER_DEFS = {}


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

    def paper_config(self, paper: str) -> PaperConfig:
        for pc in self.paper_configs:
            if paper == pc.name or paper in pc.aka_names:
                return pc

        raise NotImplementedError(
            f"no configuration available for paper size '{paper}' with plotter '{self.name}'"
        )


def _read_config_file(path) -> Dict[str, PlotterConfig]:
    return {k: PlotterConfig.from_config(v) for k, v in toml.load(path).items()}


def add_config(path: str) -> None:
    _PLOTTER_DEFS.update({k: PlotterConfig.from_config(v) for k, v in toml.load(path).items()})


def get_plotter_config(name: str) -> PlotterConfig:
    if name in _PLOTTER_DEFS:
        return _PLOTTER_DEFS[name]
    else:
        raise NotImplementedError(f"no configuration available for plotter '{name}'")


def _init():
    add_config(str(pathlib.Path(__file__).parent / "hpgl.toml"))

    path = os.path.expanduser("~/.vpype_hpgl.toml")
    if os.path.exists(path):
        add_config(path)


_init()
