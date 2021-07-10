import importlib.util

import click

from vpype import LineCollection, generator

from .cli import cli

__all__ = ()


@cli.command(group="Input")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@generator
def script(file) -> LineCollection:
    """
    Call an external python script to generate geometries.

    The script must contain a `generate()` function which will be called without arguments. It
    must return the generated geometries in one of the following format:

        - Shapely's MultiLineString
        - Iterable of Nx2 numpy float array
        - Iterable of Nx1 numpy complex array (where the real and imag part corresponds to
          the x, resp. y coordinates)

    All coordinates are expected to be in SVG pixel units (1/96th of an inch).
    """

    try:
        spec = importlib.util.spec_from_file_location("<external>", file)
        if spec is None:
            raise FileNotFoundError(f"file {file} not found")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return LineCollection(module.generate())  # type: ignore
    except Exception as exc:
        raise click.ClickException(
            (
                f"the file path must point to a Python script containing a `generate()`"
                f"function ({str(exc)})"
            )
        )
