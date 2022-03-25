from __future__ import annotations

import glob
import os
import pathlib
from typing import Any, Iterable

import click

import vpype as vp

from .cli import ProcessorType, cli, execute_processors
from .decorators import block_processor
from .state import State
from .types import IntegerType, LengthType, TextType

__all__ = ("grid", "repeat", "forfile", "forlayer")


@cli.command(group="Block processors")
@click.argument("number", nargs=2, default=(2, 2), type=IntegerType(), metavar="NX NY")
@click.option(
    "-o",
    "--offset",
    nargs=2,
    default=("10mm", "10mm"),
    type=LengthType(),
    metavar="DX DY",
    help="Offset between columns and rows.",
)
@block_processor
def grid(
    state: State,
    processors: Iterable[ProcessorType],
    number: tuple[int, int],
    offset: tuple[float, float],
) -> None:
    """Creates a NX by NY grid of geometry

    The number of column and row must always be specified. By default, 10mm offsets are used
    in both directions. Use the `--offset` option to override these values.

    The nested commands are exposed to a pipeline which does not contain any geometry but
    retains the layer structure and metadata. The properties created and modified by the
    nested commands are applied on the pipeline. However, the properties deleted by the nested
    commands are not deleted from the outer pipeline.

    The following variables are set by `grid` and available for expressions:

    \b
        _nx: number of columns (NX)
        _ny: number of rows (NY)
        _n: total number of cells (NX*NY)
        _x: current column (0 to NX-1)
        _y: current row (0 to NY-1)
        _i: current cell (0 to _n-1)

    Examples:

        Create a grid of random line patches:

            $ vpype begin grid 3 4 random end show

        Create a grid of circles, each on a different layer:

            $ vpype begin grid -o 3cm 3cm 2 3 circle --layer new 0 0 1cm end show
    """

    nx, ny = number

    for j in range(ny):
        for i in range(nx):
            variables = {
                "_nx": nx,
                "_ny": ny,
                "_n": nx * ny,
                "_x": i,
                "_y": j,
                "_i": i + j * nx,
            }
            with state.temp_document() as doc, state.expression_variables(variables):
                execute_processors(processors, state)
            doc.translate(offset[0] * i, offset[1] * j)
            state.document.extend(doc)
    if nx > 0 and ny > 0:
        state.document.page_size = (nx * offset[0], ny * offset[1])


@cli.command(group="Block processors")
@click.argument("number", type=IntegerType(), metavar="N")
@block_processor
def repeat(state: State, processors: Iterable[ProcessorType], number: int) -> None:
    """Repeat geometries N times.

    Repeats the enclosed command N times, stacking their output on top of each other.

    The nested commands are exposed to a pipeline which does not contain any geometry but
    retains the layer structure and metadata. The properties created and modified by the
    nested commands are applied on the pipeline. However, the properties deleted by the nested
    commands are not deleted from the outer pipeline.

    The following variables are set by `repeat` and available for expressions:

    \b
        _n: number of repetitions (N)
        _i: counter (0 to N-1)

    Examples:

        Create a patch of random lines of 3 different colors:

            $ vpype begin repeat 3 random --layer %_i+1% end show
    """

    for i in range(number):
        variables = {"_n": number, "_i": i}
        with state.temp_document() as doc, state.expression_variables(variables):
            execute_processors(processors, state)
        state.document.extend(doc)


@cli.command(group="Block processors")
@click.argument("files", type=TextType(), metavar="FILES")
@block_processor
def forfile(state: State, processors: Iterable[ProcessorType], files: str) -> None:
    """Iterate over a file list.

    The `forfile` block processor expends the FILES pattern into a file list like a shell
    would. In particular, wildcards (`*` and `**`) are expended, environmental variables are
    substituted (`$ENVVAR`), and the `~` expended to the user directory. It then executes the
    nested commands once for each file.

    The following variables are set by `forfile` and available for expressions:

    \b
        _path (pathlib.Path): file path
        _name (str): file name, same as _path.name (e.g. 'input.svg')
        _parent (pathlib.Path): parent directory, same as _path.parent
        _ext (str): file extension, same as _path.suffix (e.g. '.svg')
        _stem (str): file name without extension, same as _path.stem (e.g. 'input')
        _n (int): total number of files
        _i (int): counter (0 to _n-1)

    Example:

        Process all SVGs in the current directory:

    \b
            $ vpype begin forfile \\*.svg read %_path% linemerge linesort \\
                write "optimized/%basename(_path)%" end
    """

    file_list = glob.glob(os.path.expandvars(os.path.expanduser(files)))

    for i, file in enumerate(file_list):
        path = pathlib.Path(file)
        variables = {
            "_path": path,
            "_name": path.name,
            "_parent": path.parent,
            "_ext": path.suffix,
            "_stem": path.stem,
            "_i": i,
            "_n": len(files),
        }
        with state.temp_document() as doc, state.expression_variables(variables):
            execute_processors(processors, state)
        state.document.extend(doc)


class _MetadataProxy:
    def __init__(self, metadata: dict[str, Any]):
        self._metadata = metadata

    def __getattr__(self, name):
        if name in self._metadata:
            return self._metadata[name]
        else:
            raise AttributeError(f"property '{name}' not found")

    def __setattr__(self, name, value):
        if name == "_metadata":
            super().__setattr__(name, value)
        else:
            self._metadata[name] = value

    def __getitem__(self, name):
        return self._metadata[name]

    def __setitem__(self, name, value):
        self._metadata[name] = value


@cli.command(group="Block processors")
@block_processor
def forlayer(state: State, processors: Iterable[ProcessorType]) -> None:
    """Iterate over each layer.

    This block processor execute the nested pipeline once per layer. The nested pipeline is
    exclusively exposed to the current layer. In addition, if the nested commands create any
    other layer, they are merged as well into the outer pipeline.

    The following variables are set by `forlayer` and available for expressions:

    \b
        _lid (int): the current layer ID
        _name (str): the name of the current layer
        _color (Color): the color of the current layer
        _pen_width (float): the pen width of the current layer
        _prop: properties of the current layer (accessible by item and/or attribute)
        _i (int): counter (0 to _n-1)
        _n (int): number of layers

    Example:

        Export one file per layer:

            vpype read input.svg forlayer write output_%_name%.svg end
    """

    orig_doc = state.document
    new_doc: vp.Document = orig_doc.clone()

    for i, lid in enumerate(list(orig_doc.layers)):
        with state.temp_document(keep_layer=False) as doc:
            doc.add(orig_doc.pop(lid), lid, with_metadata=True)
            variables = {
                "_lid": lid,
                "_i": i,
                "_n": len(doc.layers),
                "_name": doc.layers[lid].property(vp.METADATA_FIELD_NAME) or "",
                "_color": doc.layers[lid].property(vp.METADATA_FIELD_COLOR),
                "_pen_width": doc.layers[lid].property(vp.METADATA_FIELD_PEN_WIDTH),
                "_prop": _MetadataProxy(doc.layers[lid].metadata),
            }
            with state.expression_variables(variables):
                execute_processors(processors, state)
        new_doc.extend(doc)

    # The original document's content has been entirely popped and can be restored.
    # Note: we *cannot* replace state.document by new_doc, as this interferes with
    # state.temp_document() and ultimately breaks nested blocks
    state.document.extend(new_doc)
