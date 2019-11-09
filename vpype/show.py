import logging

import click
from shapely.geometry import MultiLineString
import matplotlib.pyplot as plt

from .vpype import cli, processor


@cli.command(group="Output")
@click.option("-a", "--show-axes", is_flag=True, help="display matplotlib axes")
@click.option("-g", "--show-grid", is_flag=True, help="display matplotlib grid (implies -a)")
@processor
def show(mls: MultiLineString, show_axes: bool, show_grid: bool):
    """
    Display the geometry using matplotlib.
    """
    logging.info(f"running matplotlib display")

    for ls in mls:
        plt.plot(*ls.xy, "-k", lw=0.5)
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
