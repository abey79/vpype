import logging

import click
from shapely.geometry import MultiLineString
import matplotlib.pyplot as plt

from .vpype import cli, processor


@cli.command(group="Output")
@click.option("-a", "--show-axes", is_flag=True, help="Display axes.")
@click.option("-g", "--show-grid", is_flag=True, help="Display grid (implies -a).")
@click.option(
    "-c", "--colorful", is_flag=True, help="Display each segment in a different color."
)
@processor
def show(mls: MultiLineString, show_axes: bool, show_grid: bool, colorful: bool):
    """
    Display the geometry using matplotlib.

    By default, only the geometries are displayed without the axis. All geometries are
    displayed with black. When using the `--colorful` flag, each segment will have a different
    color (default matplotlib behaviour). This can be useful for debugging purposes.

    Note: matplotlib can be rather slow when displaying a large number of lines, which
    typically happens with lots of curved elements. For complex geometries, using `write`
    and inspecting the resulting SVG may be preferable.
    """
    logging.info(f"running matplotlib display")

    if colorful:
        spec = "-"
    else:
        spec = "-k"

    for ls in mls:
        plt.plot(*ls.xy, spec, lw=0.5)
    plt.gca().invert_yaxis()
    plt.axis("equal")
    if show_axes or show_grid:
        plt.axis("on")
    else:
        plt.axis("off")
    if show_grid:
        plt.grid("on")
    plt.show()

    return mls
