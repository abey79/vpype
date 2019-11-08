import cv2
import hatched


import logging

import click

from .vpype import cli, generator


@cli.command("hatched")
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "-l",
    "--levels",
    nargs=3,
    type=int,
    default=(64, 128, 192),
    help="Pixel value of the 3 threshold between black, dark, light and white (0-255)",
)
@click.option("-s", "--scale", default=1.0, help="Scale factor to apply to the image")
@click.option(
    "-i",
    "--interpolation",
    default="linear",
    type=click.Choice(["linear", "nearest"], case_sensitive=False),
    help="Interpolation used for scaling",
)
@click.option("-b", "--blur", default=0, type=int, help="Blur radius to apply to the image")
@click.option("-p", "--pitch", default=5, type=int, help="Densest hatching pitch (pixels)")
@click.option(
    "-x", "--invert", is_flag=True, help="Invert the image (and levels) before processing"
)
@click.option("-c", "--circular", is_flag=True, help="Use circular instead of diagonal hatches")
@click.option(
    "-d", "--show-plot", is_flag=True, help="Display the contours and resulting pattern"
)
@generator
def hatched_gen(
    filename: str,
    levels,
    scale: float,
    interpolation: str,
    blur: int,
    pitch: int,
    invert: bool,
    circular: bool,
    show_plot: bool,
):
    """
    Generate hatched pattern from an image (see `hatched` library)
    """
    logging.info(f"generating hatches from {filename}")

    interp = cv2.INTER_LINEAR
    if interpolation == 'nearest':
        interp = cv2.INTER_NEAREST

    return hatched.hatch(
        file_path=filename,
        levels=levels,
        image_scale=scale,
        interpolation=interp,
        blur_radius=blur,
        hatch_pitch=pitch,
        invert=invert,
        circular=circular,
        show_plot=show_plot,
        h_mirror=False,  # this is best handled by vpype
        save_svg=False,  # this is best handled by vpype
    )
