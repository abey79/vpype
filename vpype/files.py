import logging

import click
import svgwrite
from shapely import affinity
from shapely.geometry import MultiLineString

from .vpype import cli, processor


@cli.command()
@click.argument("output", type=click.File("w"))
@click.option("-s", "--single-path", is_flag=True, help="generate a single compound path")
@processor
def svg(mls: MultiLineString, output, single_path):
    """
    Generate random lines in [0, 1] x [0, 1] space
    """
    logging.info(f"saving to {output.name}")

    # align geometries to (0, 0
    bounds = mls.bounds
    corrected_mls = affinity.translate(mls, -bounds[0], -bounds[1])

    dwg = svgwrite.Drawing(
        size=(bounds[2] - bounds[0], bounds[3] - bounds[1]), profile="tiny", debug=False
    )

    if single_path:
        dwg.add(
            dwg.path(
                " ".join(
                    ("M" + " L".join(f"{x},{y}" for x, y in ls.coords)) for ls in corrected_mls
                ),
                fill="none",
                stroke="black",
            )
        )
    else:
        for ls in corrected_mls:
            dwg.add(
                dwg.path(
                    "M" + " L".join(f"{x},{y}" for x, y in ls.coords),
                    fill="none",
                    stroke="black",
                )
            )

    dwg.write(output)
    return mls
