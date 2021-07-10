from typing import Optional, Tuple

import click

import vpype as vp

from .cli import cli

__all__ = ()


@cli.command(group="Text")
@click.argument("string", type=str)
@click.option(
    "-f", "--font", type=click.Choice(vp.FONT_NAMES), default="futural", help="Font to use."
)
@click.option(
    "-s", "--size", type=vp.LengthType(), default=18, help="Text size (default: 18)."
)
@click.option("-w", "--wrap", type=vp.LengthType(), help="Wrap to provided width.")
@click.option("-j", "--justify", is_flag=True, help="Justify text block (wrap-mode only).")
@click.option(
    "-p",
    "--position",
    nargs=2,
    type=vp.LengthType(),
    default=[0, 0],
    help="Position of the text (default: 0, 0).",
)
@click.option(
    "-a",
    "--align",
    type=click.Choice(["left", "right", "center"]),
    default="left",
    help="Text alignment with respect to position (default: left).",
)
@vp.generator
def text(
    string: str,
    font: str,
    size: float,
    wrap: Optional[float],
    justify: float,
    position: Tuple[float, float],
    align: str,
):
    """Generate text using Hershey fonts.

    By default, `text` generates a single line of text. Automatic text wrapping can be enabled
    using the the `--wrap` option.

    In normal mode, the text starts at coordinate (0, 0) and expends right. This can be
    controlled using the `--align` option. By passing "center", the text is centered around
    (0, 0). With "right", the text expends left of (0, 0).

    In wrap mode, the text start at (0, 0) and expends left until it reach the specified width.
    The `--align` option controls how the text is laid out within the column and behaves as
    typically expected.

    To start the text at the different location than (0, 0), use the `--position` option.
    """

    # skip if text is empty
    if string.strip() == "":
        return vp.LineCollection()

    if wrap:
        lc = vp.text_block(
            string, font_name=font, width=wrap, size=size, align=align, justify=justify
        )
    else:
        lc = vp.text_line(string, font_name=font, size=size, align=align)

    lc.translate(position[0], position[1])

    return lc
