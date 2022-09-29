"""
Hidden debug commands to help testing.
"""
from __future__ import annotations

import functools
import json
import math
from typing import Any, Iterable, Sequence

import click
import numpy as np
from rich.console import RenderableType
from rich.pretty import Pretty
from rich.table import Table

import vpype as vp

from . import _print as pp
from .cli import cli
from .decorators import global_processor
from .types import ChoiceType

debug_data: list[dict[str, Any]] = []

__all__ = ("dbsample", "dbdump", "stat", "DebugData")


@cli.command(hidden=True)
@global_processor
def dbsample(document: vp.Document):
    """
    Show statistics on the current geometries in JSON format.
    """
    global debug_data

    data: dict[str, Any] = {}
    if document.is_empty():
        data["count"] = 0
    else:
        data["count"] = sum(len(lc) for lc in document.layers.values())
        data["layer_count"] = len(document.layers)
        data["length"] = document.length()
        data["pen_up_length"] = document.pen_up_length()
        data["bounds"] = document.bounds()
        data["layers"] = {
            layer_id: [vp.as_vector(line).tolist() for line in layer]
            for layer_id, layer in document.layers.items()
        }

    debug_data.append(data)
    return document


@cli.command(hidden=True)
@global_processor
def dbdump(document: vp.Document):
    global debug_data
    print(json.dumps(debug_data))
    debug_data = []
    return document


class DebugData:
    """
    Helper class to load
    """

    @staticmethod
    def load(debug_output: str):
        """
        Create DebugData instance array from debug output
        :param debug_output:
        :return:
        """
        return [DebugData(data) for data in json.loads(debug_output)]

    def __init__(self, data: dict[str, Any]):
        self.count = data["count"]
        self.length = data.get("length", 0)
        self.pen_up_length = data.get("pen_up_length", 0)
        self.bounds = data.get("bounds", [0, 0, 0, 0])
        self.layers = data.get("layers", {})

        self.document = vp.Document()
        for vid, lines in self.layers.items():
            self.document[int(vid)] = vp.LineCollection(
                [np.array([x + 1j * y for x, y in line]) for line in lines]
            )

    def bounds_within(self, x: float, y: float, width: float, height: float) -> bool:
        """
        Test if coordinates are inside. If `x` and `y` are provided only, consider input as
        a point. If `width` and `height` are passed as well, consider input as rect.
        """
        if self.count == 0:
            return False

        def approx_check(a, b, lt):
            if lt:
                return a < b and not np.isclose(a, b)
            else:
                return a > b and not np.isclose(a, b)

        if (
            approx_check(self.bounds[0], x, True)
            or approx_check(self.bounds[1], y, True)
            or approx_check(self.bounds[2], x + width, False)
            or approx_check(self.bounds[3], y + height, False)
        ):
            return False

        return True

    def __eq__(self, other: object):
        if not isinstance(other, DebugData):
            return NotImplemented

        if self.count == 0:
            return other.count == 0

        return (
            np.all(np.isclose(np.array(self.bounds), np.array(other.bounds)))
            and self.length == other.length
        )

    def has_layer(self, lid: int) -> bool:
        return self.has_layers([lid])

    def has_layers(self, lids: Iterable[int]) -> bool:
        return all(str(lid) in self.layers for lid in lids)

    def has_layer_only(self, lid: int) -> bool:
        return self.has_layers_only([lid])

    def has_layers_only(self, lids: Sequence[int]) -> bool:
        return self.has_layers(lids) and len(self.layers.keys()) == len(lids)


def _build_table(data: dict[str, RenderableType], title: str | None = None) -> Table:
    table = Table(
        title=title,
        show_header=False,
        min_width=len(title) if title else None,
        title_justify="left",
    )
    table.add_column()

    if data:
        table.add_column()
        for k, v in data.items():
            table.add_row(k, v)
    else:
        table.add_row("[italic]n/a")

    return table


@cli.command(group="Output")
@click.option(
    "-u",
    "--unit",
    type=ChoiceType(tuple(vp.UNIT_SYSTEMS.keys()) + tuple(vp.UNITS.keys())),
    default="metric",
)
@global_processor
def stat(document: vp.Document, unit: str):
    """Print human-readable statistics on the current geometries."""

    length_tot = 0.0
    pen_up_length_tot = 0.0

    fmt = functools.partial(vp.format_length, unit=unit, full_precision=False)

    for layer_id in sorted(document.layers.keys()):
        layer = document.layers[layer_id]
        length = layer.length()
        pen_up_length, pen_up_mean, pen_up_median = layer.pen_up_length()
        length_tot += length
        pen_up_length_tot += pen_up_length

        layer_data = {
            "Length": fmt(length),
            "Pen-up length": fmt(pen_up_length),
            "Total length": fmt(length + pen_up_length),
            "Mean pen-up length": fmt(pen_up_mean),
            "Median pen-up length": fmt(pen_up_median),
            "Path count": str(len(layer)),
            "Segment count": str(layer.segment_count()),
            "Mean segment length": (
                fmt(length / layer.segment_count()) if layer.segment_count() else "n/a"
            ),
            "Bounds": str(layer.bounds()),
        }
        pp.print(_build_table(layer_data, title=f"Layer {layer_id} statistics"))
        pp.print(
            _build_table(
                {k: Pretty(v) for k, v in layer.metadata.items()},
                title=f"Layer {layer_id} properties",
            )
        )

    global_data = {
        "Layer count": str(len(document.layers)),
        "Length": fmt(length_tot),
        "Pen-up length": fmt(pen_up_length_tot),
        "Total length": fmt(length_tot + pen_up_length_tot),
        "Path count": str(sum(len(layer) for layer in document.layers.values())),
        "Segment count": str(document.segment_count()),
        "Mean segment length": (
            fmt(length_tot / document.segment_count()) if document.segment_count() else "n/a"
        ),
        "Bounds": str(document.bounds()),
    }

    pp.print(_build_table(global_data, title="Global statistics"))
    pp.print(
        _build_table(
            {k: Pretty(v) for k, v in document.metadata.items()}, title="Global properties"
        )
    )

    return document
