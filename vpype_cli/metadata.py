from typing import Optional

import click
import svgelements

import vpype as vp

from .cli import cli

__all__ = ()


_STR_TO_TYPE = {
    "str": str,
    "int": int,
    "float": float,
}


@cli.command(group="Metadata")
@click.argument("prop")
@click.argument("value")
@click.option(
    "-type",
    "--t",
    "prop_type",
    type=click.Choice(list(_STR_TO_TYPE.keys())),
    help="specify type for property",
)
@vp.layer_processor
def metadata(
    layer: vp.LineCollection, prop: str, value: str, prop_type: Optional[str]
) -> vp.LineCollection:
    """Set the value of a metadata property."""

    converted_value = _STR_TO_TYPE[prop_type](value) if prop_type is not None else value
    layer.set_property(prop, converted_value)
    return layer


@cli.command(group="Metadata")
@click.argument("pen_width", type=vp.LengthType(), metavar="WIDTH")
@vp.layer_processor
def penwidth(layer: vp.LineCollection, pen_width: float) -> vp.LineCollection:
    """Set the pen width for one or more layers.

    By default, this commands sets the pen width for all layers. Use the `--layer` option to set
    the pen width of one (or more) specific layer(s).

    Examples:

        Set the pen width for all layers:

            $ vpype [...] penwidth 0.15mm [...]

        Set the pen width for a specific layer:

            $ vpype [...] penwidth --layer 2 0.15mm [...]
    """
    layer.set_property("vp:pen_width", pen_width)
    return layer


# noinspection PyShadowingNames
@cli.command(group="Metadata")
@click.argument("color", type=str)
@vp.layer_processor
def color(layer: vp.LineCollection, color: str) -> vp.LineCollection:
    """Set the color for one or more layers.

    All CSS ways of specifying color are valid for COLOR.

    By default, this commands sets the color for all layers. Use the `--layer` option to set
    the color of one (or more) specific layer(s).

    Examples:

        Set the color for all layers:

            $ vpype [...] color red [...]

        Set the color for a specific layer:

            $ vpype [...] color --layer 2 #0f0 [...]
    """

    layer.set_property("vp:color", svgelements.Color(color))
    return layer


# noinspection PyShadowingNames
@cli.command(group="Metadata")
@click.argument("name", type=str)
@vp.layer_processor
def name(layer: vp.LineCollection, name: str) -> vp.LineCollection:
    """Set the name for one or more layers.

    By default, this commands sets the name for all layers. Use the `--layer` option to set
    the name of one (or more) specific layer(s).

    Examples:

        Set the name for a specific layer:

            $ vpype [...] name --layer 4 black [...]
    """

    layer.set_property("vp:name", name)
    return layer


@cli.command(group="Metadata")
@vp.global_processor
def cmyk(document: vp.Document) -> vp.Document:
    """Sets the metadata for the first 4 layers for CMYK.

    This convenience command performs the following tasks:
    - create layers 1 to 4 if they don't exist
    - set the names of layers 1 to 4 to 'cyan', 'magenta', 'yellow', resp. 'black'
    - set layers 1 to 4 to the correct color

    Layers with ID of 5 or more are ignore by this command.
    """

    document.add([], 1)
    document.add([], 2)
    document.add([], 3)
    document.add([], 4)

    document.layers[1].set_property("vp:name", "cyan")
    document.layers[2].set_property("vp:name", "magenta")
    document.layers[3].set_property("vp:name", "yellow")
    document.layers[4].set_property("vp:name", "black")

    document.layers[1].set_property("vp:color", "cyan")
    document.layers[2].set_property("vp:color", "magenta")
    document.layers[3].set_property("vp:color", "yellow")
    document.layers[4].set_property("vp:color", "black")

    return document
