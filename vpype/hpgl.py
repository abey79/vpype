from typing import List, Tuple, Optional

import attr

from .utils import convert_length

__all__ = ["PaperConfig", "PlotterConfig", "get_plotter_config"]


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


@attr.s(auto_attribs=True, frozen=True)
class PlotterConfig:
    name: str
    paper_configs: List[PaperConfig]
    plotter_unit_length: float
    pen_count: int

    def paper_config(self, paper: str) -> PaperConfig:
        for pc in self.paper_configs:
            if paper == pc.name or paper in pc.aka_names:
                return pc

        raise NotImplementedError(
            f"no configuration available for paper size '{paper}' with plotter '{self.name}'"
        )


PLOTTER_DEFS = {
    "hp7475a": PlotterConfig(
        name="hp7475a",
        plotter_unit_length=convert_length("0.02488mm"),
        pen_count=6,
        paper_configs=[
            PaperConfig(
                name="a4",
                paper_size=(convert_length("297mm"), convert_length("210mm")),
                x_range=(0, 11040),
                y_range=(0, 7721),
                y_axis_up=True,
                origin_location=(convert_length("10mm"), convert_length("206mm")),
                set_ps=4,
            ),
            PaperConfig(
                name="a3",
                paper_size=(convert_length("420mm"), convert_length("297mm")),
                x_range=(0, 16158),
                y_range=(0, 11040),
                y_axis_up=True,
                origin_location=(convert_length("15mm"), convert_length("287mm")),
                set_ps=0,
            ),
            PaperConfig(
                name="a",
                aka_names=["ansi_a", "letter"],
                paper_size=(convert_length("11in"), convert_length("8.5in")),
                x_range=(0, 10365),
                y_range=(0, 7962),
                y_axis_up=True,
                origin_location=(convert_length("10mm"), convert_length("206mm")),
                set_ps=4,
            ),
            PaperConfig(
                name="b",
                aka_names=["ansi_b", "tabloid"],
                paper_size=(convert_length("17in"), convert_length("11in")),
                x_range=(0, 16640),
                y_range=(0, 10365),
                y_axis_up=True,
                origin_location=(convert_length("15mm"), convert_length("287mm")),
                set_ps=0,
            ),
        ],
    )
}


def get_plotter_config(name: str) -> PlotterConfig:
    if name in PLOTTER_DEFS:
        return PLOTTER_DEFS[name]
    else:
        raise NotImplementedError(f"no configuration available for plotter '{name}'")
