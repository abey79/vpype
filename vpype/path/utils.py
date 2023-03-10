from typing import Iterable, Sequence

import numpy as np
import shapely

from vpype.path.exceptions import ShapelyConversionError
from vpype.path.segment import CoordList


def _coordinates_to_numpy(coords: Sequence[Sequence[float]]) -> CoordList:
    """Convert a list of coordinates to a numpy array of complex coordinates."""
    return np.array(coords)[:2, :].view(dtype=np.complex64).reshape(-1)


def _shapely_to_numpy(shapely_obj: shapely.Geometry) -> Iterable[CoordList]:
    """Convert a Shapely object to a numpy array of complex coordinates."""
    match shapely_obj:
        case shapely.Point():
            yield np.array([shapely_obj.x + 1j * shapely_obj.y], dtype=np.complex64)

        case shapely.LineString() | shapely.LinearRing():
            yield _coordinates_to_numpy(shapely_obj.coords)

        case shapely.Polygon():
            yield _coordinates_to_numpy(shapely_obj.exterior.coords)
            for interior in shapely_obj.interiors:
                yield _coordinates_to_numpy(interior.coords)

        case (
            shapely.MultiPoint()
            | shapely.MultiLineString()
            | shapely.MultiPolygon()
            | shapely.GeometryCollection()
        ):
            for geom in shapely_obj.geoms:
                yield from _shapely_to_numpy(geom)

        case _:
            raise ShapelyConversionError(f"Cannot convert {shapely_obj} to numpy array")


def lerp(a, b, t):
    return a * (1 - t) + b * t


def cmin(*vals: complex) -> complex:
    """Element-wise complex min."""
    return complex(min(a.real for a in vals), min(a.imag for a in vals))


def cmax(*vals: complex) -> complex:
    """Element-wise complex max."""
    return complex(max(a.real for a in vals), max(a.imag for a in vals))


def cdiv(a: complex, b: complex) -> complex:
    """Element-wise complex division."""
    return complex(a.real / b.real, a.imag / b.imag)
