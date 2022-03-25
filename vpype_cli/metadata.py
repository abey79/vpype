from __future__ import annotations

import logging
from typing import Any, Callable

import click

import vpype as vp

from .cli import cli
from .decorators import global_processor, layer_processor
from .types import LayerType, LengthType, TextType, multiple_to_layer_ids

__all__ = (
    "propset",
    "proplist",
    "propget",
    "propdel",
    "propclear",
    "penwidth",
    "color",
    "name",
    "pens",
)


_STR_TO_TYPE: dict[str, Callable] = {
    "str": str,
    "int": lambda x: int(vp.convert_length(x)),
    "float": vp.convert_length,
    "color": vp.Color,
}


def _check_scope(
    global_flag: bool, layer: int | list[int] | None
) -> tuple[bool, int | list[int] | None]:
    if global_flag and layer is not None:
        logging.warning(
            "incompatible `--global` and `--layer` options were provided, assuming `--global`"
        )
        layer = None
    elif not global_flag and layer is None:
        logging.warning(
            "neither `--global` nor `--layer` options were provide, assuming `--layer all`"
        )
        layer = LayerType.ALL

    return global_flag, layer


@cli.command(group="Metadata")
@click.argument("prop", type=TextType())
@click.argument("value", type=TextType())
@click.option("--global", "-g", "global_flag", is_flag=True, help="Global mode.")
@click.option("-l", "--layer", type=LayerType(accept_multiple=True), help="Target layer(s).")
@click.option(
    "--type",
    "-t",
    "prop_type",
    type=click.Choice(list(_STR_TO_TYPE.keys())),
    default="str",
    help="Property type.",
)
@global_processor
def propset(
    document: vp.Document,
    global_flag: bool,
    layer: int | list[int] | None,
    prop: str,
    value: str,
    prop_type: str,
):
    """Set the value of a global or layer property.

    Either the `--global` or `--layer` option must be used to specify whether a global or
    layer property should be set. When using `--layer`, either a single layer ID, a
    coma-separated list of layer ID, or `all` may be used.

    By default, the value is stored as a string. Alternative types may be specified with the
    `--type` option. The following types are available:

        \b
        str: text string
        int: integer number
        float: floating-point number
        color: color

    When using the `int` and `float` types, units may be used and the value will be converted
    to pixels.

    When using the `color` type, any SVG-compatible string may be used for VALUE, including
    16-bit RGB (#ff0000), 16-bit RGBA (#ff0000ff), 8-bit variants (#f00 or #f00f), or color
    names (red).

    Examples:

        Set a global property of type `int`:

            vpype [...] propset --global --type int my_prop 10 [...]

        Set the layer property of type `float` (this is equivalent to using the `penwidth`
        command:

            vpype [...] propset --layer 1 --type float vp_pen_width 0.5mm [...]

        Set a layer property of type `color`:

            vpype [...] propset --layer 1 --type color my_prop red [...]
    """

    global_flag, layer = _check_scope(global_flag, layer)

    if global_flag:
        document.set_property(prop, _STR_TO_TYPE[prop_type](value))
    else:
        for lid in multiple_to_layer_ids(layer, document):
            document.layers[lid].set_property(prop, _STR_TO_TYPE[prop_type](value))

    return document


def _value_to_str(value: Any) -> str:
    if value is None:
        return "n/a"
    elif isinstance(value, vp.Color):
        value_str = value.as_hex()
        value_type = "color"
    else:
        value_str = str(value)
        value_type = type(value).__name__
    return f"({value_type}) {value_str}"


@cli.command(group="Metadata")
@click.option("--global", "-g", "global_flag", is_flag=True, help="Global mode.")
@click.option("-l", "--layer", type=LayerType(accept_multiple=True), help="Target layer(s).")
@global_processor
def proplist(document: vp.Document, global_flag: bool, layer: int | list[int] | None):
    """Print a list the existing global or layer properties and their values.

    Either the `--global` or `--layer` option must be used to specify whether global or
    layer properties should be listed. When using `--layer`, either a single layer ID, a
    coma-separated list of layer ID, or `all` may be used.

    Examples:

        Print a list of global properties:

            vpype pagesize a4 proplist -g
    """
    global_flag, layer = _check_scope(global_flag, layer)

    if global_flag:
        print(f"listing {len(document.metadata)} global properties")
        for prop in sorted(document.metadata.keys()):
            print(f"  {prop}: {_value_to_str(document.property(prop))}")
    else:
        for lid in multiple_to_layer_ids(layer, document):
            lc = document.layers[lid]
            print(f"listing {len(lc.metadata)} properties for layer {lid}")
            for prop in sorted(lc.metadata.keys()):
                print(f"  {prop}: {_value_to_str(lc.property(prop))}")

    return document


@cli.command(group="Metadata")
@click.argument("prop", type=TextType())
@click.option("--global", "-g", "global_flag", is_flag=True, help="Global mode.")
@click.option("-l", "--layer", type=LayerType(accept_multiple=True), help="Target layer(s).")
@global_processor
def propget(
    document: vp.Document, global_flag: bool, layer: int | list[int] | None, prop: str
):
    """Print the value of a global or layer property.

    Either the `--global` or `--layer` option must be used to specify whether a global or
    layer property should be displayed. When using `--layer`, either a single layer ID, a
    coma-separated list of layer ID, or `all` may be used.

    Examples:

        Print the value of property `vp_color` for all layers:

            vpype [...] pens cmyk propget --layer all vp_color [...]
    """
    global_flag, layer = _check_scope(global_flag, layer)

    if global_flag:
        print(f"global property {prop}: {_value_to_str(document.property(prop))}")
    else:
        for lid in multiple_to_layer_ids(layer, document):
            print(
                f"layer {lid} property {prop}: "
                f"{_value_to_str(document.layers[lid].property(prop))}"
            )

    return document


@cli.command(group="Metadata")
@click.argument("prop", type=TextType())
@click.option("--global", "-g", "global_flag", is_flag=True, help="Global mode.")
@click.option("-l", "--layer", type=LayerType(accept_multiple=True), help="Target layer(s).")
@global_processor
def propdel(
    document: vp.Document, global_flag: bool, layer: int | list[int] | None, prop: str
):
    """Remove a global or layer property.

    Either the `--global` or `--layer` option must be used to specify whether a global or
    layer property should be removed. When using `--layer`, either a single layer ID, a
    coma-separated list of layer ID, or `all` may be used.

    Examples:

        Remove a property from a layer:

            vpype [...] pens cmyk propdel --layer 1 vp_name [...]
    """
    global_flag, layer = _check_scope(global_flag, layer)

    if global_flag:
        document.set_property(prop, None)
    else:
        for lid in multiple_to_layer_ids(layer, document):
            document.layers[lid].set_property(prop, None)

    return document


@cli.command(group="Metadata")
@click.option("--global", "-g", "global_flag", is_flag=True, help="Global mode.")
@click.option("-l", "--layer", type=LayerType(accept_multiple=True), help="Target layer(s).")
@global_processor
def propclear(document: vp.Document, global_flag: bool, layer: int | list[int] | None):
    """Remove all global or layer properties.

    Either the `--global` or `--layer` option must be used to specify whether global or
    layer properties should be cleared. When using `--layer`, either a single layer ID, a
    coma-separated list of layer ID, or `all` may be used.

    Examples:

        Remove all global properties:

            vpype [...] propclear --global [...]

        Remove all properties from layer 1 and 2:

            vpype [...] propclear --layer 1,2 [...]
    """
    global_flag, layer = _check_scope(global_flag, layer)

    if global_flag:
        document.clear_metadata()
    else:
        for lid in multiple_to_layer_ids(layer, document):
            document.layers[lid].clear_metadata()

    return document


@cli.command(group="Metadata")
@click.argument("pen_width", type=LengthType(), metavar="WIDTH")
@layer_processor
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
    layer.set_property(vp.METADATA_FIELD_PEN_WIDTH, pen_width)
    return layer


# noinspection PyShadowingNames
@cli.command(group="Metadata")
@click.argument("color", type=TextType())
@layer_processor
def color(layer: vp.LineCollection, color: str) -> vp.LineCollection:
    """Set the color for one or more layers.

    Any SVG-compatible string may be used for VALUE, including 16-bit RGB (#ff0000),
    16-bit RGBA (#ff0000ff), 8-bit variants (#f00 or #f00f), or color names (red).

    By default, this commands sets the color for all layers. Use the `--layer` option to set
    the color of one (or more) specific layer(s).

    Examples:

        Set the color for all layers:

            $ vpype [...] color red [...]

        Set the color for a specific layer:

            $ vpype [...] color --layer 2 #0f0 [...]
    """

    layer.set_property(vp.METADATA_FIELD_COLOR, vp.Color(color))
    return layer


# noinspection PyShadowingNames
@cli.command(group="Metadata")
@click.argument("name", type=TextType())
@layer_processor
def name(layer: vp.LineCollection, name: str) -> vp.LineCollection:
    """Set the name for one or more layers.

    By default, this commands sets the name for all layers. Use the `--layer` option to set
    the name of one (or more) specific layer(s).

    Examples:

        Set the name for a specific layer:

            $ vpype [...] name --layer 4 black [...]
    """

    layer.set_property(vp.METADATA_FIELD_NAME, name)
    return layer


PENS_HELP_STRING = f"""Apply a pen configuration.

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


@cli.command(group="Metadata", help=PENS_HELP_STRING)
@click.argument("pen_config", metavar="CONF", type=TextType())
@global_processor
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
            document.layers[lid].set_property(vp.METADATA_FIELD_NAME, layer_data["name"])
        if "color" in layer_data:
            document.layers[lid].set_property(vp.METADATA_FIELD_COLOR, layer_data["color"])
        if "pen_width" in layer_data:
            document.layers[lid].set_property(
                vp.METADATA_FIELD_PEN_WIDTH, vp.convert_length(layer_data["pen_width"])
            )

    return document
