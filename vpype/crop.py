import click
from shapely.geometry import MultiLineString, Polygon

from .vpype import cli, processor
from .utils import Length


@cli.command(group="Editing")
@click.argument("x", type=Length(), required=True)
@click.argument("y", type=Length(), required=True)
@click.argument("width", type=Length(), required=True)
@click.argument("height", type=Length(), required=True)
@processor
def crop(mls: MultiLineString, x: float, y: float, width: float, height: float):
    """
    Crop the geometries.

    The crop area is defined by the (X, Y) top-left corner and the WIDTH and HEIGHT arguments.
    All arguments understand supported units.
    """
    if mls.is_empty:
        return mls

    p = Polygon([(x, y), (x + width, y), (x + width, y + height), (x, y + height)])

    # Because of this bug, we cannot use the simpler `mls.intersection(p)` function
    # https://github.com/Toblerity/Shapely/issues/779
    ls_arr = []
    for ls in mls:
        res = ls.intersection(p)
        if res.geom_type == "MultiLineString":
            ls_arr.extend(res)
        elif not res.is_empty:
            ls_arr.append(res)

    return MultiLineString(ls_arr)
