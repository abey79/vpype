from __future__ import annotations

import random

import click

import vpype as vp

from .cli import cli
from .decorators import global_processor
from .types import LayerType, multiple_to_layer_ids, single_to_layer_id

__all__ = ("lcopy", "lmove", "ldelete", "lreverse", "lswap")


@cli.command(group="Layers")
@click.argument("sources", type=LayerType(accept_multiple=True))
@click.argument("dest", type=LayerType(accept_new=True))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path copy probability (default: 1.0).",
)
@click.option("-m", "--no-prop", is_flag=True, help="Do not copy metadata.")
@global_processor
def lcopy(document, sources, dest, prob: float | None, no_prop: bool):
    """Copy the content of one or more layer(s) to another layer.

    SOURCES can be a single layer ID, the string 'all' (to copy all non-empty layers,
    or a coma-separated, whitespace-free list of layer IDs.

    DEST can be a layer ID or the string 'new', in which case a new layer with the
    lowest available ID will be created.

    If a layer is both in the source and destination, its content is not duplicated.

    The `--prob` option controls the probability with which each path is copied. With a value
    lower than 1.0, some paths will not be copied to DEST, which may be used to achieve random
    coloring effects.

    If a single source layer is specified and the `--prob` option is not used, the properties
    of the source layer are copied to the destination layer, overwriting any existing
    properties with the same name. This behaviour can be disabled with the `--no-prop` option.

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

    if len(src_lids) == 1 and prob is None and not no_prop:
        document.layers[dest_lid].metadata.update(document.layers[src_lids[0]].metadata)

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
@click.option("-m", "--no-prop", is_flag=True, help="Do not move metadata.")
@global_processor
def lmove(document, sources, dest, prob: float | None, no_prop: bool):
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

    If a single source layer is specified and the `--prob` option is not used, the properties
    of the source layer are moved to the destination layer, overwriting any existing
    properties with the same name. This behaviour can be disabled with the `--no-prop` option.

    Example:

        Merge layer 1 and 2 to layer 1 (the content of layer 1 is not duplicated):

            vpype [...] lmove 1,2 1 [...]  # merge layer 1 and 2 to layer 1
    """

    src_lids = multiple_to_layer_ids(sources, document)
    dest_lid = single_to_layer_id(dest, document)

    if dest_lid in document.layers:
        dest_lc = document.layers[dest_lid].clone()
    else:
        dest_lc = vp.LineCollection()

    move_metadata = len(src_lids) == 1 and prob is None and not no_prop
    source_metadata = document.layers[src_lids[0]].metadata if move_metadata else {}

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
                document.replace(remaining_lines, lid)
            else:
                document.pop(lid)

            if len(moving_lines) > 0:
                dest_lc.extend(moving_lines)
        else:
            dest_lc.extend(document.pop(lid))
            if move_metadata:
                dest_lc.metadata.update(source_metadata)

    if len(dest_lc) > 0:
        document.add(dest_lc, dest_lid, with_metadata=True)
    return document


@cli.command(group="Layers")
@click.argument("layers", type=LayerType(accept_multiple=True))
@click.option(
    "-k", "--keep", is_flag=True, help="Specified layers must be kept instead of deleted."
)
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path deletion probability (default: 1.0).",
)
@global_processor
def ldelete(document: vp.Document, layers, keep: bool, prob: float | None) -> vp.Document:
    """Delete one or more layers.

    LAYERS can be a single layer ID, the string 'all' (to delete all layers), or a
    coma-separated, whitespace-free list of layer IDs.

    If the `--keep` option is used, the specified layers are kept and, instead, all other
    layers deleted.

    The `--prob` option controls the probability with which each path is deleted. With a value
    lower than 1.0, some paths will not be deleted.
    """

    lids = set(multiple_to_layer_ids(layers, document))

    if keep:
        lids = document.layers.keys() - lids

    for lid in lids:
        if prob is not None:
            lc = document.layers[lid].clone()
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
@click.argument("first", type=LayerType(accept_multiple=False, accept_new=False))
@click.argument("second", type=LayerType(accept_multiple=False, accept_new=False))
@click.option(
    "-p",
    "--prob",
    type=click.FloatRange(0.0, 1.0),
    help="Path deletion probability (default: 1.0).",
)
@click.option("-m", "--no-prop", is_flag=True, help="Do not move metadata.")
@global_processor
def lswap(
    document: vp.Document, first: int, second: int, prob: float | None, no_prop: bool
) -> vp.Document:
    """Swap the content between two layers

    This command swaps the content of layers FIRST and SECOND. Both FIRST and SECOND must be
    existing layer ids.

    The `--prob` option controls the probability with which each path are swapped. With a value
    lower than 1.0, some paths will remain in their original layer.

    If  the `--prob` option is not used, the layer properties are swapped between layers as
    well. This behaviour can be disabled with the `--no-prop` option.
    """

    first_lid = single_to_layer_id(first, document, must_exist=True)
    second_lid = single_to_layer_id(second, document, must_exist=True)

    if prob is None:
        document.swap_content(first_lid, second_lid)
        if not no_prop:
            document.layers[first_lid].metadata, document.layers[second_lid].metadata = (
                document.layers[second_lid].metadata,
                document.layers[first_lid].metadata,
            )
    else:
        new_first = vp.LineCollection()
        new_second = vp.LineCollection()

        for line in document.layers[first_lid]:
            (new_second if random.random() < prob else new_first).append(line)
        for line in document.layers[second_lid]:
            (new_first if random.random() < prob else new_second).append(line)

        document.replace(new_first, first_lid)
        document.replace(new_second, second_lid)

    return document


@cli.command(group="Layers")
@click.argument("layers", type=LayerType(accept_multiple=True, accept_new=False))
@global_processor
def lreverse(document: vp.Document, layers) -> vp.Document:
    """Reverse the path order within one or more layers.

    This command reverses the order in which paths are ordered within layer(s) LAYERS. LAYERS
    may be a single layer ID, multiple layer IDs (coma-separated without whitespace) or `all`
    (to refer to every exising layers).

    Example:

        Reverse path order in layer 1:

            $ vpype [...] lreverse 1 [...]
    """

    lids = set(multiple_to_layer_ids(layers, document))

    for layer_id in lids:
        document.layers[layer_id].reverse()

    return document
