"""
Debug command to help testing.
TODO: move this to tests directory, use as plug-in
"""
import json
from typing import Union, Any, Dict

from shapely.geometry import MultiLineString

from .vpype import cli, processor

debug_data = []


@cli.command(hidden=True)
@processor
def dbsample(mls: MultiLineString):
    """
    Show statistics on the current geometries in JSON format.
    """
    global debug_data

    data = {}
    if mls.is_empty:
        data["count"] = 0
    else:
        data["count"] = len(mls)
        data["length"] = mls.length
        data["centroid"] = [mls.centroid.x, mls.centroid.y]
        data["bounds"] = list(mls.bounds)
        data["geom_type"] = mls.geom_type
        data["valid"] = mls.is_valid

    debug_data.append(data)
    return mls


@cli.command(hidden=True)
@processor
def dbdump(mls: MultiLineString):
    global debug_data
    print(json.dumps(debug_data))
    debug_data = []
    return mls


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
        self.centroid = data.get("centroid", [0, 0])
        self.bounds = data.get("bounds", [0, 0, 0, 0])
        self.geom_type = data.get("geom_type", "EmptyGeometry")
        self.valid = data.get("valid", False)

    def bounds_within(
        self, x: float, y: float, width: Union[float, None], height: Union[float, None],
    ) -> bool:
        """
        Test if coordinates are inside. If `x` and `y` are provided only, consider input as
        a point. If `width` and `height` are passed as well, consider input as rect.
        """
        if self.count == 0:
            return False

        if (
            self.bounds[0] < x
            or self.bounds[1] < y
            or self.bounds[2] > x + width
            or self.bounds[3] > y + height
        ):
            return False

        return True

    def __eq__(self, other: "DebugData"):
        if self.count == 0:
            return other.count == 0

        return (
            self.bounds == other.bounds
            and self.length == other.length
            and self.centroid == other.centroid
            and self.geom_type == other.geom_type
            and self.valid == other.valid
        )
