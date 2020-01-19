import click

from vpype.model import LineCollection
from vpype.decorators import generator


@click.command()
@generator
def star():
    """
    Demo plug-in

    This demo plug-in generates a star.
    """

    lc = LineCollection()
    lc.append(
        [
            150 + 25j,
            179 + 111j,
            269 + 111j,
            197 + 165j,
            223 + 251j,
            150 + 200j,
            77 + 251j,
            103 + 165j,
            31 + 111j,
            121 + 111j,
            150 + 25j,
        ]
    )
    return lc


star.help_group = "Plugins"
