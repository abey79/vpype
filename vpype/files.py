import logging

import click
import svgwrite
from shapely.geometry import MultiLineString

from .vpype import cli, processor


@cli.command()
@click.argument("output", type=click.File("w"))
@processor
def svg(mls: MultiLineString, output):
    """
    Generate random lines in [0, 1] x [0, 1] space
    """
    logging.info(f"saving to {output.name}")

    dwg = svgwrite.Drawing()  # size=(w, h), profile="tiny", debug=False)

    dwg.add(
        dwg.path(
            " ".join(("M" + " L".join(f"{x},{y}" for x, y in ls.coords)) for ls in mls),
            fill="none",
            stroke="black",
        )
    )

    dwg.write(output)
    return mls
