"""
Hidden debug commands to help testing.
"""
import json
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

from vpype import Document, LineCollection, as_vector, global_processor

from .cli import cli

debug_data: List[Dict[str, Any]] = []

__all__ = ("dbsample", "dbdump", "stat", "DebugData")


@cli.command(hidden=True)
@global_processor
def dbsample(document: Document):
    """
    Show statistics on the current geometries in JSON format.
    """
    global debug_data

    data: Dict[str, Any] = {}
    if document.is_empty():
        data["count"] = 0
    else:
        data["count"] = sum(len(lc) for lc in document.layers.values())
        data["layer_count"] = len(document.layers)
        data["length"] = document.length()
        data["pen_up_length"] = document.pen_up_length()
        data["bounds"] = document.bounds()
        data["layers"] = {
            layer_id: [as_vector(line).tolist() for line in layer]
            for layer_id, layer in document.layers.items()
        }

    debug_data.append(data)
    return document


@cli.command(hidden=True)
@global_processor
def dbdump(document: Document):
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

    def __init__(self, data: Dict[str, Any]):
        self.count = data["count"]
        self.length = data.get("length", 0)
        self.pen_up_length = data.get("pen_up_length", 0)
        self.bounds = data.get("bounds", [0, 0, 0, 0])
        self.layers = data.get("layers", {})

        self.document = Document()
        for vid, lines in self.layers.items():
            self.document[int(vid)] = LineCollection(
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


@cli.command(group="Output")
@global_processor
def stat(document: Document):
    """Print human-readable statistics on the current geometries."""

    print("========= Stats ========= ")
    print(f"Current page size: {document.page_size}")
    length_tot = 0.0
    pen_up_length_tot = 0.0
    for layer_id in sorted(document.layers.keys()):
        layer = document.layers[layer_id]
        length = layer.length()
        pen_up_length, pen_up_mean, pen_up_median = layer.pen_up_length()
        length_tot += length
        pen_up_length_tot += pen_up_length
        print(f"Layer {layer_id}")
        print(f"  Length: {length}")
        print(f"  Pen-up length: {pen_up_length}")
        print(f"  Total length: {length + pen_up_length}")
        print(f"  Mean pen-up length: {pen_up_mean}")
        print(f"  Median pen-up length: {pen_up_median}")
        print(f"  Path count: {len(layer)}")
        print(f"  Segment count: {layer.segment_count()}")
        print(
            f"  Mean segment length:",
            str(length / layer.segment_count() if layer.segment_count() else "n/a"),
        )
        print(f"  Bounds: {layer.bounds()}")
        print("  Metadata:")
        if layer.metadata:
            for key, value in layer.metadata.items():
                print(f"    {key}: {value!r}")
        else:
            print(f"    n/a")
    print(f"Totals")
    print(f"  Layer count: {len(document.layers)}")
    print(f"  Length: {length_tot}")
    print(f"  Pen-up length: {pen_up_length_tot}")
    print(f"  Total length: {length_tot + pen_up_length_tot}")
    print(f"  Path count: {sum(len(layer) for layer in document.layers.values())}")
    print(f"  Segment count: {document.segment_count()}")

    print(
        f"  Mean segment length:",
        str(length_tot / document.segment_count() if document.segment_count() else "n/a"),
    )
    print(f"  Bounds: {document.bounds()}")
    print("========================= ")

    return document
