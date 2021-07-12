from typing import Optional

import click
import svgelements

import vpype as vp

from .cli import cli

__all__ = ("metadata", "penwidth", "color", "name", "pens")


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

    By default, this commands sets the pen width for all layers. Use the `--layer` option to
    set the pen width of one (or more) specific layer(s).

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


COLORMAP_HELP_STRING = f"""Apply a pen configuration.

This command applies given names, pen colors and/or pen widths to one or more layers, as
defined by the pen configuration CONF. This pen configuration just be defined in either the
bundled or a user-provided config file (such as ~/.vpype.toml).

The following pen configurations are defined in the default config and the ~/.vpype.toml file:

    {", ".join(vp.config_manager.config.get("pen_config", {}).keys()) or "n/a"}

For example, the bundled pen configuration `cmyk` applies `cyan`,`magenta`, `yellow`, resp.
`black` to the name and color of layers 1 to 4 while leaving pen widths unchanged.

In details, for each of the layers defined in a pen configuration, this command performs the
following tasks:
- create the corresponding layer if it does not exist
- set the name of the layer as specified by the pen configuration (if specified)
- set the color of the layer as specified by the pen configuration (if specified)
- set the pen width of the layer as specified by the pen configuration (if specified)

Existing layers whose ID are not included in the pen configuration are not affected by this
command. Check the documentation for more information on creating custom pen configurations.
"""


@cli.command(group="Metadata", help=COLORMAP_HELP_STRING)
@click.argument("pen_config", metavar="CONF")
@vp.global_processor
def pens(document: vp.Document, pen_config: str) -> vp.Document:

    # the CONF parameter must be checked explicitly (instead of using click.Choice()) because
    # additional config file (potentially containing pen configs) may be added at runtime
    config = vp.config_manager.config.get("pen_config", {})

    if pen_config not in config:
        click.secho(
            f"pens: pen configuration '{pen_config}' not found, no pen configuration applied",
            fg="red",
        )
        return document

    for layer_data in config[pen_config]["layers"]:
        lid = layer_data["layer_id"]
        document.add([], lid)
        if "name" in layer_data:
            document.layers[lid].set_property("vp:name", layer_data["name"])
        if "color" in layer_data:
            document.layers[lid].set_property("vp:color", layer_data["color"])
        if "pen_width" in layer_data:
            document.layers[lid].set_property(
                "vp:pen_width", vp.convert_length(layer_data["pen_width"])
            )

    return document
