import logging
from types import ModuleType
from typing import Optional

import click
import numpy as np

import vpype as vp

from .cli import cli

try:
    # noinspection PyUnresolvedReferences
    import vpype_viewer

    _vpype_viewer_ok = True
except ImportError:  # pragma: no cover
    _vpype_viewer_ok = False


__all__ = ("show",)

COLORS = [
    (0, 0, 1),
    (0, 0.5, 0),
    (1, 0, 0),
    (0, 0.75, 0.75),
    (0, 1, 0),
    (0.75, 0, 0.75),
    (0.75, 0.75, 0),
    (0, 0, 0),
]


@cli.command(group="Output")
@click.option("--classic", is_flag=True, help="Use the classic viewer.")
@click.option("--force", is_flag=True, hidden=True, help="Force modern viewer")
@click.option("-p", "--show-pen-up", is_flag=True, help="Display pen-up trajectories.")
@click.option("-d", "--show-points", is_flag=True, help="Display paths points with dots.")
@click.option("-o", "--outline", is_flag=True, help="Display in outline mode (modern only).")
@click.option(
    "-c",
    "--colorful",
    is_flag=True,
    help="Display in outline colorful mode (takes precedence over --outline).",
)
@click.option("-a", "--show-axes", is_flag=True, help="Display axes (classic only).")
@click.option(
    "-g", "--show-grid", is_flag=True, help="Display grid (implies -a, classic only)."
)
@click.option(
    "-h", "--hide-legend", is_flag=True, help="Do not display the legend (classic only)."
)
@click.option(
    "-u",
    "--unit",
    type=str,
    default="px",
    help="Units of the plot (when --show-grid is active, classic only).",
)
@vp.global_processor
def show(
    document: vp.Document,
    classic: bool,
    force: bool,
    show_pen_up: bool,
    show_points: bool,
    outline: bool,
    colorful: bool,
    show_axes: bool,
    show_grid: bool,
    hide_legend: bool,
    unit: str,
):
    """Display the geometry in an graphical user interface.

    By default, this command use a modern, hardware-accelerated viewer (currently in beta) with
    a preview mode (adjustable pen width and opacity) and interactive controls to adjust
    display options. This viewer requires OpenGL 3.3 support.

    The original, Matplotlib-based viewer is still available with the `--classic` option. The
    classic viewer does not have interactive controls for display options. Use the command-line
    options to customize the display.
    """

    if not classic:
        # test for vpype_viewer
        if not _vpype_viewer_ok:
            logging.warning(
                "!!! show: vpype viewer not available, reverting to classic mode. Note: use "
                "`pip install vpype[all]` to install the vpype viewer."
            )
            classic = True
        else:
            mgl_ok = _test_mgl()
            if not mgl_ok and not force:
                classic = True
                logging.warning("!!! show: ModernGL not available, reverting to classic mode.")
            elif not mgl_ok and force:
                logging.warning("!!! show: ModernGL not available but forced to vpype viewer.")

    if classic:
        _show_mpl(
            document,
            show_axes,
            show_grid,
            show_pen_up,
            show_points,
            hide_legend,
            colorful,
            unit,
        )
    else:
        view_mode = vpype_viewer.ViewMode.PREVIEW
        if outline or show_points:
            view_mode = vpype_viewer.ViewMode.OUTLINE
        if colorful:
            view_mode = vpype_viewer.ViewMode.OUTLINE_COLORFUL

        vpype_viewer.show(
            document, view_mode=view_mode, show_pen_up=show_pen_up, show_points=show_points
        )

    return document


def _test_mgl() -> bool:
    """Tests availability of ModernGL."""
    # noinspection PyBroadException
    try:
        import glcontext

        backend = glcontext.default_backend()
        ctx = backend(mode="standalone", glversion=330)
        if ctx.load("glProgramUniform1iv") == 0:
            logging.info("ModernGL detection: glProgramUniform1iv not found")
            return False
    except Exception as exc:
        logging.info(f"ModernGL detection failed with error {exc}")
        return False

    return True


def _show_mpl(
    document: vp.Document,
    show_axes: bool,
    show_grid: bool,
    show_pen_up: bool,
    show_points: bool,
    hide_legend: bool,
    colorful: bool,
    unit: str,
):
    """Display the geometry using matplotlib.

    By default, only the geometries are displayed without the axis. All geometries are
    displayed with black. When using the `--colorful` flag, each segment will have a different
    color (default matplotlib behaviour). This can be useful for debugging purposes.
    """

    # deferred import to optimise startup time
    try:
        import matplotlib.collections
        import matplotlib.pyplot as plt
    except ImportError:
        logging.warning(
            "!!! show: classic viewer not available, ignore command. Note: use `pip install "
            "matplotlib` to enable the classic viewer."
        )
        return

    scale = 1 / vp.convert_length(unit)

    fig = plt.figure()
    color_idx = 0
    collections = {}

    # draw page boundaries
    if document.page_size:
        w = document.page_size[0] * scale
        h = document.page_size[1] * scale
        dw = 10 * scale
        plt.plot(
            np.array([0, 1, 1, 0, 0]) * w,
            np.array([0, 0, 1, 1, 0]) * h,
            "-k",
            lw=0.25,
            label=None,
        )
        plt.fill(
            np.array([w, w + dw, w + dw, dw, dw, w]),
            np.array([dw, dw, h + dw, h + dw, h, h]),
            "k",
            alpha=0.3,
            label=None,
        )

    for layer_id, lc in document.layers.items():
        if colorful:
            color = COLORS[color_idx:] + COLORS[:color_idx]
            marker_color = "k"
            color_idx += len(lc)
        else:
            color = COLORS[color_idx]  # type: ignore
            marker_color = [color]  # type: ignore
            color_idx += 1
        if color_idx >= len(COLORS):
            color_idx = color_idx % len(COLORS)

        layer_lines = matplotlib.collections.LineCollection(
            (vp.as_vector(line) * scale for line in lc),
            color=color,
            lw=1,
            alpha=0.5,
            label=str(layer_id),
        )
        collections[layer_id] = [layer_lines]
        plt.gca().add_collection(layer_lines)

        if show_points:
            points = np.hstack([line for line in lc]) * scale
            layer_points = plt.gca().scatter(
                points.real, points.imag, marker=".", c=marker_color, s=16
            )
            collections[layer_id].append(layer_points)

        if show_pen_up:
            pen_up_lines = matplotlib.collections.LineCollection(
                (
                    (vp.as_vector(lc[i])[-1] * scale, vp.as_vector(lc[i + 1])[0] * scale)
                    for i in range(len(lc) - 1)
                ),
                color=(0, 0, 0),
                lw=0.5,
                alpha=0.5,
            )
            collections[layer_id].append(pen_up_lines)
            plt.gca().add_collection(pen_up_lines)

    plt.gca().invert_yaxis()
    plt.axis("equal")
    plt.margins(0, 0)

    if not hide_legend:
        lgd = plt.legend(loc="upper right")
        # we will set up a dict mapping legend line to orig line, and enable
        # picking on the legend line
        line_dict = {}
        for lgd_line, lgd_text in zip(lgd.get_lines(), lgd.get_texts()):
            lgd_line.set_picker(True)  # 5 pts tolerance
            lgd_line.set_pickradius(5)
            layer_id = int(lgd_text.get_text())
            if layer_id in collections:
                line_dict[lgd_line] = collections[layer_id]

        def on_pick(event):
            line = event.artist
            vis = not line_dict[line][0].get_visible()
            for ln in line_dict[line]:
                ln.set_visible(vis)

            if vis:
                line.set_alpha(1.0)
            else:
                line.set_alpha(0.2)
            fig.canvas.draw()

        fig.canvas.mpl_connect("pick_event", on_pick)

    if show_axes or show_grid:
        plt.axis("on")
        plt.xlabel(f"[{unit}]")
        plt.ylabel(f"[{unit}]")
    else:
        plt.axis("off")
    if show_grid:
        plt.grid("on")
    plt.show()
