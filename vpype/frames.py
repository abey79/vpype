import click

from .decorators import generator, pass_state
from .model import LineCollection
from .utils import Length
from .vpype import cli, VpypeState


@cli.command(group="Generators")
@click.option(
    "-o",
    "--offset",
    default=0.0,
    type=Length(),
    help="Offset from the geometries' bounding box. This option understands supported units.",
)
@generator
@pass_state
def frame(state: VpypeState, offset: float):
    """
    Add a single-line frame around the geometry.

    By default, the frame shape is the current geometries' bounding box. An optional offset can
    be provided.
    """
    if state.vector_data.is_empty():
        return LineCollection()

    bounds = state.vector_data.bounds()
    return LineCollection(
        [
            (
                bounds[0] - offset + 1j * (bounds[1] - offset),
                bounds[0] - offset + 1j * (bounds[3] + offset),
                bounds[2] + offset + 1j * (bounds[3] + offset),
                bounds[2] + offset + 1j * (bounds[1] - offset),
                bounds[0] - offset + 1j * (bounds[1] - offset),
            )
        ]
    )
