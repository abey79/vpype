import random
from typing import Optional

import click

import vpype as vp

from .cli import cli

__all__ = ("lcopy", "lmove", "ldelete", "lswap")


@cli.command(group="Layers")
@click.argument("sources", type=vp.LayerType(accept_multiple=True))
@click.argument("dest", type=vp.LayerType(accept_new=True))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path copy probability (default: 1.0).",
)
@vp.global_processor
def lcopy(document, sources, dest, prob: Optional[float]):
    """Copy the content of one or more layer(s) to another layer.

    SOURCES can be a single layer ID, the string 'all' (to copy all non-empty layers,
    or a coma-separated, whitespace-free list of layer IDs.

    DEST can be a layer ID or the string 'new', in which case a new layer with the
    lowest available ID will be created.

    If a layer is both in the source and destination, its content is not duplicated.

    The `--prob` option controls the probability with which each path is copied. With a value
    lower than 1.0, some paths will not be copied to DEST, which may be used to achieve random
    coloring effects.

    Examples:

        Copy layer 1 to a new layer:

            vpype [...] lcopy 1 new [...]  # duplicate layer 1

        Make a new layer with a merged copy of layer 1 and 2:

            vpype [...] lcopy 1,2 new [...]  # make new layer with merged copy of layer 1 and 2

        Add a merged copy of all layers to layer 1. If layer 1 previously had content, this \
content is not duplicated:

            vpype [...] lcopy all 1 [...]
    """

    src_lids = vp.multiple_to_layer_ids(sources, document)
    dest_lid = vp.single_to_layer_id(dest, document)

    if dest_lid in src_lids:
        src_lids.remove(dest_lid)

    lc = vp.LineCollection()
    for lid in src_lids:
        if prob is not None:
            for line in document[lid]:
                if random.random() < prob:
                    lc.append(line)
        else:
            lc.extend(document[lid])

    if len(lc) > 0:
        document.add(lc, dest_lid)

    return document


@cli.command(group="Layers")
@click.argument("sources", type=vp.LayerType(accept_multiple=True))
@click.argument("dest", type=vp.LayerType(accept_new=True))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path move probability (default: 1.0).",
)
@vp.global_processor
def lmove(document, sources, dest, prob: Optional[float]):
    """Move the content of one or more layer(s) to another layer.

    SOURCES can be a single layer ID, the string 'all' (to copy all non-empty layers,
    or a coma-separated, whitespace-free list of layer IDs.

    DEST can be a layer ID or the string 'new', in which case a new layer with the
    lowest available ID will be created.

    Layer(s) left empty after the move are then discarded and may thus be reused by subsequent
    commands using 'new' as destination layer.

    The `--prob` option controls the probability with which each path is moved. With a value
    lower than 1.0, some paths will not be moved to DEST, which may be used to achieve random
    coloring effects.

    If a layer is both in the source and destination, its content is not duplicated.

    Examples:

        Merge layer 1 and 2 to layer 1 (the content of layer 1 is not duplicated):

            vpype [...] lmove 1,2 1 [...]  # merge layer 1 and 2 to layer 1
    """

    src_lids = vp.multiple_to_layer_ids(sources, document)
    dest_lid = vp.single_to_layer_id(dest, document)

    if dest_lid in src_lids:
        src_lids.remove(dest_lid)

    for lid in src_lids:
        if prob is not None:
            # split lines with provided probability
            remaining_lines = vp.LineCollection()
            moving_lines = vp.LineCollection()
            for line in document.layers[lid]:
                if random.random() < prob:
                    moving_lines.append(line)
                else:
                    remaining_lines.append(line)

            if len(remaining_lines) > 0:
                document.layers[lid] = remaining_lines
            else:
                document.pop(lid)

            if len(moving_lines) > 0:
                document.add(moving_lines, dest_lid)
        else:
            document.add(document.pop(lid), dest_lid)

    return document


@cli.command(group="Layers")
@click.argument("layers", type=vp.LayerType(accept_multiple=True))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path deletion probability (default: 1.0).",
)
@vp.global_processor
def ldelete(document: vp.Document, layers, prob: Optional[float]) -> vp.Document:
    """Delete one or more layers.

    LAYERS can be a single layer ID, the string 'all' (to delete all layers), or a
    coma-separated, whitespace-free list of layer IDs.

    The `--prob` option controls the probability with which each path is deleted. With a value
    lower than 1.0, some paths will not be deleted.
    """

    lids = set(vp.multiple_to_layer_ids(layers, document))

    for lid in lids:
        if prob is not None:
            lc = vp.LineCollection()
            for line in document[lid]:
                if not random.random() < prob:
                    lc.append(line)

            if len(lc) == 0:
                document.pop(lid)
            else:
                document[lid] = lc
        else:
            document.pop(lid)

    return document


@cli.command(group="Layers")
@click.argument("first", type=vp.LayerType(accept_multiple=False, accept_new=False))
@click.argument("second", type=vp.LayerType(accept_multiple=False, accept_new=False))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path deletion probability (default: 1.0).",
)
@vp.global_processor
def lswap(
    document: vp.Document, first: int, second: int, prob: Optional[float]
) -> vp.Document:
    """Swap the content between two layers

    This command swaps the content of layers FIRST and SECOND. Both FIRST and SECOND must be
    existing layer ids.

    The `--prob` option controls the probability with which each path are swapped. With a value
    lower than 1.0, some paths will remain in their original layer.
    """

    first_lid = vp.single_to_layer_id(first, document, must_exist=True)
    second_lid = vp.single_to_layer_id(second, document, must_exist=True)

    if prob is None:
        document.layers[first_lid], document.layers[second_lid] = (
            document.layers[second_lid],
            document.layers[first_lid],
        )
    else:
        new_first = vp.LineCollection()
        new_second = vp.LineCollection()

        for line in document.layers[first_lid]:
            (new_second if random.random() < prob else new_first).append(line)
        for line in document.layers[second_lid]:
            (new_first if random.random() < prob else new_second).append(line)

        document.layers[first_lid] = new_first
        document.layers[second_lid] = new_second

    return document


@cli.command(group="Layers")
@click.argument("layers", type=vp.LayerType(accept_multiple=True, accept_new=False))
@vp.global_processor
def lreverse(document: vp.Document, layers) -> vp.Document:
    """Reverse the path order within one or more layers.

    This command reverses the order in which paths are ordered within layer(s) LAYERS. LAYERS
    may be a single layer ID, multiple layer IDs (coma-separated without whitespace) or `all`
    (to refer to every exising layers).

    Examples:

        Delete layer one:

            $ vpype [...] ldelete 1 [...]

        Delete layers 1 and 2:

            $ vpype [...] ldelete 1,2 [...]

        Delete all layers:

            $ vpype [...] ldelete all [...]
    """

    lids = set(vp.multiple_to_layer_ids(layers, document))

    for layer_id in lids:
        document.layers[layer_id].reverse()

    return document
