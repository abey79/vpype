import importlib.util

import click
from shapely.geometry import MultiLineString

from .vpype import cli, generator


@cli.command(group="Input")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@generator
def script(file) -> MultiLineString:
    """
    Call an external python script to generate geometries.

    The script must contain a `generate()` which will be called without arguments. It must
    return a Shapely MultiLineString object containing the generated geometries. The
    coordinates used are expected to be in SVG pixel units (1/96th of an inch).
    """

    try:
        spec = importlib.util.spec_from_file_location("<external>", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        mls = module.generate()
    except Exception as exc:
        raise click.ClickException(
            (
                f"the file path must point to a Python script containing a `generate()`"
                f"function ({str(exc)})"
            )
        )

    return mls
