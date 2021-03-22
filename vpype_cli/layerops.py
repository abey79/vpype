import random
from typing import Optional

import click

from vpype import (
    Document,
    LayerType,
    LineCollection,
    global_processor,
    multiple_to_layer_ids,
    single_to_layer_id,
)

from .cli import cli

__all__ = ("lcopy", "lmove", "ldelete")


@cli.command(group="Layers")
@click.argument("sources", type=LayerType(accept_multiple=True))
@click.argument("dest", type=LayerType(accept_new=True))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path copy probability (default: 1.0).",
)
@global_processor
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

    src_lids = multiple_to_layer_ids(sources, document)
    dest_lid = single_to_layer_id(dest, document)

    if dest_lid in src_lids:
        src_lids.remove(dest_lid)

    lc = LineCollection()
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
@click.argument("sources", type=LayerType(accept_multiple=True))
@click.argument("dest", type=LayerType(accept_new=True))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path move probability (default: 1.0).",
)
@global_processor
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

    src_lids = multiple_to_layer_ids(sources, document)
    dest_lid = single_to_layer_id(dest, document)

    if dest_lid in src_lids:
        src_lids.remove(dest_lid)

    for lid in src_lids:
        if prob is not None:
            # split lines with provided probability
            remaining_lines = LineCollection()
            moving_lines = LineCollection()
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
@click.argument("layers", type=LayerType(accept_multiple=True))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path deletion probability (default: 1.0).",
)
@global_processor
def ldelete(document: Document, layers, prob: Optional[float]) -> Document:
    """Delete one or more layers.

    LAYERS can be a single layer ID, the string 'all' (to delete all layers), or a
    coma-separated, whitespace-free list of layer IDs.

    The `--prob` option controls the probability with which each path is deleted. With a value
    lower than 1.0, some paths will not be deleted.
    """

    lids = set(multiple_to_layer_ids(layers, document))

    for lid in lids:
        if prob is not None:
            lc = LineCollection()
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
