import click

import vpype as vp

from .cli import cli


@cli.command(group="Filters")
@click.option(
    "-a",
    "--amplitude",
    type=vp.LengthType(),
    default="0.5mm",
    help="Amplitude of the noise-based displacement (default: 0.5mm).",
)
@click.option(
    "-p",
    "--period",
    type=vp.LengthType(),
    default="3mm",
    help="Period of the noise-based displacement (default: 3mm).",
)
@click.option(
    "-q",
    "--quantization",
    type=vp.LengthType(),
    default="0.05mm",
    help="Maximum segment size used for the resampling (default: 0.05mm).",
)
@vp.layer_processor
def squiggles(lines: vp.LineCollection, amplitude: float, period: float, quantization: float):
    """Apply a squiggle filter to the geometries.

    This filter works by first resampling the input lines, and then applying a random
    displacement to all points. This displacement is based on a 2D Perlin noise field with
    adjustable amplitude and period.

    The default values of amplitude and period give a "shaky-hand" style to the geometries.
    Larger values of amplitude (~15mm) and period (~10cm) result in a a smoother, liquid-like
    effect.
    """

    return vp.squiggles(lines, amplitude, period, quantization)
