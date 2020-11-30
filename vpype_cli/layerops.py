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
@global_processor
def lcopy(document, sources, dest):
    """Copy the content of one or more layer(s) to another layer.

    SOURCES can be a single layer ID, the string 'all' (to copy all non-empty layers,
    or a coma-separated, whitespace-free list of layer IDs.

    DEST can be a layer ID or the string 'new', in which case a new layer with the
    lowest available ID will be created.

    If a layer is both in the source and destination, its content is not duplicated.

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
        lc.extend(document[lid])
    document.add(lc, dest_lid)

    return document


@cli.command(group="Layers")
@click.argument("sources", type=LayerType(accept_multiple=True))
@click.argument("dest", type=LayerType(accept_new=True))
@global_processor
def lmove(document, sources, dest):
    """Move the content of one or more layer(s) to another layer.

    SOURCES can be a single layer ID, the string 'all' (to copy all non-empty layers,
    or a coma-separated, whitespace-free list of layer IDs.

    DEST can be a layer ID or the string 'new', in which case a new layer with the
    lowest available ID will be created.

    Layer(s) left empty after the move are then discarded and may thus be reused by subsequent
    commands using 'new' as destination layer.

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
        document.add(document.pop(lid), dest_lid)

    return document


@cli.command(group="Layers")
@click.argument("layers", type=LayerType(accept_multiple=True))
@global_processor
def ldelete(document: Document, layers) -> Document:
    """Delete one or more layers.

    LAYERS can be a single layer ID, the string 'all' (to delete all layers), or a
    coma-separated, whitespace-free list of layer IDs.
    """

    lids = set(multiple_to_layer_ids(layers, document))

    new_doc = document.empty_copy()
    for lid in document.ids():
        if lid not in lids:
            new_doc[lid] = document[lid]

    return new_doc
