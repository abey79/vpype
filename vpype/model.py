"""
Implementation of vpype's data model
"""
import math
from typing import Union, Iterable, List, Dict, Tuple

import numpy as np
from shapely.geometry import MultiLineString, LineString

LineLike = Union[LineString, Iterable[complex]]
LineCollectionLike = Union[Iterable[LineLike], MultiLineString, "LineCollection"]


def as_vector(a: np.ndarray):
    """Return a view of a complex line array that behaves as an Nx2 real array"""
    return a.view(dtype=float).reshape(len(a), 2)


class LineCollection:
    def __init__(self, lines: LineCollectionLike = ()):
        """
        Create a line collection.
        :param lines: iterable of line-like things
        """
        self._lines: List[np.ndarray] = []
        for line in lines:
            self.append(line)

    @property
    def lines(self) -> List[np.ndarray]:
        return self._lines

    def append(self, line: LineLike) -> None:
        if isinstance(line, LineString):
            # noinspection PyTypeChecker
            self._lines.append(np.array(line).view(dtype=complex).reshape(-1))
        else:
            self._lines.append(np.array(line, dtype=complex).reshape(-1))

    def extend(self, lines: LineCollectionLike) -> None:
        for line in lines:
            self.append(line)

    def is_empty(self) -> bool:
        return len(self) == 0

    def __iter__(self):
        return self._lines.__iter__()

    def __len__(self) -> int:
        return len(self._lines)

    def __getitem__(self, item: int):
        return self._lines[item]

    def as_mls(self) -> MultiLineString:
        return MultiLineString([as_vector(line) for line in self.lines])

    def translate(self, dx: float, dy: float) -> None:
        c = complex(dx, dy)
        for line in self._lines:
            line += c

    def scale(self, sx: float, sy: float) -> None:
        for line in self._lines:
            line.real *= sx
            line.imag *= sy

    def rotate(self, angle: float) -> None:
        c = complex(math.cos(angle), math.sin(angle))
        for line in self._lines:
            line *= c

    def skew(self, ax: float, ay: float) -> None:
        tx, ty = math.tan(ax), math.tan(ay)
        for line in self._lines:
            line += tx * line.imag + 1j * ty * line.real

    def bounds(self) -> Tuple[float, float, float, float]:
        return (
            min((l.real.min() for l in self._lines)),
            min((l.imag.min() for l in self._lines)),
            max((l.real.max() for l in self._lines)),
            max((l.imag.max() for l in self._lines)),
        )

    def length(self) -> float:
        return sum(np.sum(np.abs(np.diff(line))) for line in self._lines)


class VectorData:
    """This class implements the core of vpype's data model. An empty VectorData is created at
    launch and passed from commands to commands until termination. It models an arbitrary
    number of layers whose label are a positive integer, each consisting of a LineCollection"""

    def __init__(self):
        self._layers: Dict[int, LineCollection] = {}
        # self._current: Union[int, None] = None

    @property
    def layers(self) -> Dict[int, LineCollection]:
        return self._layers

    def ids(self) -> Iterable[int]:
        return self._layers.keys()

    def layers_from_ids(self, layer_ids: Iterable[int]):
        """Returns an generator that yield layers corresponding to the provided IDs, provided
        they exist.
        """
        return (self._layers[lid] for lid in layer_ids if lid in self._layers)

    def exists(self, layer_id: int) -> bool:
        return layer_id in self._layers

    def __getitem__(self, layer_id: int):
        return self._layers.__getitem__(layer_id)

    def __setitem__(self, layer_id: int, value: LineCollectionLike):
        if layer_id < 1:
            raise ValueError(f"expected non-null, positive layer id, got {layer_id} instead")

        if isinstance(value, LineCollection):
            self._layers[layer_id] = value
        else:
            self._layers[layer_id] = LineCollection(value)

    def __contains__(self, layer_id) -> bool:
        return self._layers.__contains__(layer_id)

    def free_id(self) -> int:
        """Returns the lowest free layer id"""
        vid = 1
        while vid in self._layers:
            vid += 1
        return vid

    def add(self, lc: LineCollection, layer_id: Union[None, int] = None) -> None:
        """if layer_id is None, a new layer with lowest possible id is created"""
        if layer_id is None:
            layer_id = 1
            while layer_id in self._layers:
                layer_id += 1

        if layer_id in self._layers:
            self._layers[layer_id].extend(lc)
        else:
            self._layers[layer_id] = lc

    def extend(self, vd: "VectorData"):
        for layer_id, layer in vd.layers.items():
            self.add(layer, layer_id)

    def is_empty(self) -> bool:
        for layer in self.layers.values():
            if not layer.is_empty():
                return False
        return True

    def count(self) -> int:
        return len(self._layers.keys())

    def translate(self, dx: float, dy: float) -> None:
        for layer in self._layers.values():
            layer.translate(dx, dy)

    def bounds(
        self, layer_ids: Union[None, Iterable[int]] = None
    ) -> Tuple[float, float, float, float]:
        """
        Compute bounds of the vector data. If `layer_ids` is provided, bounds are computed only
        the corresponding ids.

        :param layer_ids: layers to consider
        :return: boundaries of the geometries
        """
        if layer_ids is None:
            layer_ids = self.ids()
        a = np.array([self._layers[vid].bounds() for vid in layer_ids if self.exists(vid)])
        return a[:, 0].min(), a[:, 1].min(), a[:, 2].max(), a[:, 3].max()

    def length(self) -> float:
        return sum(layer.length() for layer in self._layers.values())
