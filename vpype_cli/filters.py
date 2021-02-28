import click

import vpype as vp

from .cli import cli


@cli.command(group="Filters")
@click.option("-a", "--amplitude", type=vp.LengthType(), default="0.5mm", help="")
@click.option("-p", "--period", type=vp.LengthType(), default="3mm", help="")
@click.option("-q", "--quantization", type=vp.LengthType(), default="0.05mm", help="")
@vp.layer_processor
def squiggles(lines: vp.LineCollection, amplitude: float, period: float, quantization: float):
    """
    TODO
    """

    return vp.squiggles(lines, amplitude, period, quantization)
