import logging
import os
import random
import shlex
from typing import Any, List, Optional, TextIO, Union

import click
import numpy as np
from click import get_os_args
from click_plugins import with_plugins
from pkg_resources import iter_entry_points
from shapely.geometry import MultiLineString

import vpype as vp

__all__ = ("cli", "execute", "begin", "end")


class GroupedGroup(click.Group):
    """Custom group class which implements command grouping in --help display.

    Based on Stephen Rauch's excellent answer: https://stackoverflow.com/a/58770064/229511
    """

    def command(self, *args, **kwargs):
        """Gather the command help groups"""
        help_group = kwargs.pop("group", None)
        decorator = super(GroupedGroup, self).command(*args, **kwargs)

        def wrapper(f):
            cmd = decorator(f)
            cmd.help_group = help_group
            return cmd

        return wrapper

    def format_commands(self, ctx, formatter):
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            commands.append((subcommand, cmd))

        # allow for 3 times the default spacing
        if len(commands):
            longest = max(len(cmd[0]) for cmd in commands)
            limit = formatter.width - 6 - longest

            groups = {}
            for subcommand, cmd in commands:
                help_text = cmd.get_short_help_str(limit)
                subcommand += " " * (longest - len(subcommand))
                groups.setdefault(getattr(cmd, "help_group", "Unknown"), []).append(
                    (subcommand, help_text)
                )

            with formatter.section("Commands"):
                for group_name, rows in groups.items():
                    with formatter.section(group_name):
                        formatter.write_dl(rows)

    def main(self, args=None, **extra):
        """Let's get a chance to pre-process the argument list for include options."""
        if args is None:
            args = get_os_args()
        return super().main(args=preprocess_argument_list(args), **extra)


# noinspection PyUnusedLocal,PyUnresolvedReferences
@with_plugins(iter_entry_points("vpype.plugins"))
@click.group(cls=GroupedGroup, chain=True)
@click.version_option(version=vp.__version__, message="%(prog)s %(version)s")
@click.option("-v", "--verbose", count=True)
@click.option("-I", "--include", type=click.Path(), help="Load commands from a command file.")
@click.option(
    "-H",
    "--history",
    is_flag=True,
    help="Record this command in a `vpype_history.txt` in the current directory.",
)
@click.option("-s", "--seed", type=int, help="Specify the RNG seed.")
@click.option(
    "-c", "--config", type=click.Path(exists=True), help="Load an additional config file."
)
@click.pass_context
def cli(ctx, verbose, include, history, seed, config):
    """Execute the vector processing pipeline passed as argument."""

    logging.basicConfig()
    if verbose == 0:
        logging.getLogger().setLevel(logging.WARNING)
    elif verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif verbose > 1:
        logging.getLogger().setLevel(logging.DEBUG)

    # We use the command string as context object, mainly for the purpose of the `write`
    # command. This is a bit of a hack, and will need to be updated if we ever need more state
    # to be passed around (probably VpypeState should go in there!)
    cmd_string = "vpype " + " ".join(shlex.quote(arg) for arg in get_os_args()) + "\n"
    ctx.obj = cmd_string

    if history:
        with open("vpype_history.txt", "a") as fp:
            fp.write(cmd_string)

    if seed is None:
        seed = np.random.randint(2 ** 31)
        logging.info(f"vpype: no seed provided, using {seed}")
    np.random.seed(seed)
    random.seed(seed)

    if config is not None:
        vp.config_manager.load_config_file(config)


# noinspection PyShadowingNames,PyUnusedLocal
@cli.resultcallback()
def process_pipeline(processors, verbose, include, history, seed, config):
    execute_processors(processors)


def execute_processors(processors) -> vp.VpypeState:
    """
    Execute a sequence of processors to generate a Document structure. For block handling, we
    use a recursive approach. Only top-level blocks are extracted and processed by block
    processors, which, in turn, recursively call this function.
    :param processors: iterable of processors
    :return: generated geometries
    """

    outer_processors: List[Any] = []  # gather commands outside of top-level blocks
    top_level_processors: List[Any] = []  # gather commands inside of top-level blocks
    block = None  # save the current top-level block's block layer_processor
    nested_count = 0  # block depth counter
    expect_block = False  # set to True by `begin` command

    for proc in processors:
        if isinstance(proc, BlockProcessor):
            if expect_block:
                expect_block = False
                # if we in a top level block, we save the block layer_processor
                # (nested block are ignored for the time being)
                if nested_count == 1:
                    block = proc
                else:
                    top_level_processors.append(proc)
            else:
                raise click.ClickException("A block command must always follow 'begin'")
        elif expect_block:
            raise click.ClickException("A block command must always follow 'begin'")
        elif isinstance(proc, BeginBlock):
            # entering a block
            nested_count += 1
            expect_block = True

            if nested_count > 1:
                top_level_processors.append(proc)
        elif isinstance(proc, EndBlock):
            if nested_count < 1:
                raise click.ClickException(
                    "A 'end' command has no corresponding 'begin' command"
                )

            nested_count -= 1

            if nested_count == 0:
                # we're closing a top level block, let's process it
                block_document = block.process(top_level_processors)  # type: ignore

                # Create a placeholder layer_processor that will add the block's result to the
                # current frame. The placeholder_processor is a closure, so we need to make
                # a closure-building function. Failing that, the closure would refer directly
                # to the block_vd variable above, which might be overwritten by a subsequent
                # top-level block
                # noinspection PyShadowingNames
                def build_placeholder_processor(block_document):
                    def placeholder_processor(input_state):
                        input_state.document.extend(block_document)
                        return input_state

                    return placeholder_processor

                outer_processors.append(build_placeholder_processor(block_document))

                # reset the top level layer_processor list
                top_level_processors = list()
            else:
                top_level_processors.append(proc)
        else:
            # this is a 'normal' layer_processor, we can just add it to the top of the stack
            if nested_count == 0:
                outer_processors.append(proc)
            else:
                top_level_processors.append(proc)

    # at this stage, the stack must have a single frame, otherwise we're missing end commands
    if nested_count > 0:
        raise click.ClickException("An 'end' command is missing")

    # the (only) frame's processors should now be flat and can be chain-called
    state = vp.VpypeState()
    for proc in outer_processors:
        state = proc(state)
    return state


class BeginBlock:
    pass


@cli.command(group="Block control")
def begin():
    """Marks the start of a block.

    A `begin` command must be followed by a block processor command (eg. `grid` or `repeat`),
    which indicates how the block is processed. Blocks must be ended by a `end` command.

    Blocks can be nested.
    """
    return BeginBlock()


class EndBlock:
    pass


@cli.command(group="Block control")
def end():
    """Marks the end of a block."""
    return EndBlock()


class BlockProcessor:
    """
    Base class for all block processors. Although it does nothing, block processors must
    sub-class :class:`BlockProcessor` to be recognized as such.
    """

    def process(self, processors) -> MultiLineString:
        """
        Generate the compound geometries based on the provided processors. Sub-class must
        override this function in their implementation.
        :param processors: list of processors
        :return: compound geometries
        """


def extract_arguments(f: TextIO) -> List[str]:
    """Read the content of a file-like object and extract the corresponding argument list.

    Everything following a '#' is ignored until end of line. Any whitespace is considered
    to separate arguments. Single and double quote are honored, i.e. content becomes an
    argument (but quote are removed).

    :param f: file-like object
    :return: list of argument extracted from input
    """
    args = []
    for line in f.readlines():
        args.extend(shlex.split(line, comments=True))
    return args


def preprocess_argument_list(args: List[str], cwd: Union[str, None] = None) -> List[str]:
    """Preprocess an argument list, replacing 'include' options by the corresponding file's
    content.

    Include options are either '-I' or '--include', and must be followed by a file path. This
    behaviour is recursive, e.g. a file could contain an include statement as well.

    :param args:
    :param cwd: current working directory, used as reference for relative file paths (use
        actual current working directory if None)
    :return: preprocessed list or argument
    """

    if cwd is None:
        cwd = os.getcwd()

    result = []

    while len(args) > 0:
        arg = args.pop(0)

        if arg == "-I" or arg == "--include":
            if len(args) == 0:
                raise click.ClickException("include option must be followed by a file path")
            else:
                # include statement in files are relative to that file, so we need to
                # provide the file's path to ourselves
                file_path = args.pop(0)
                if not os.path.isabs(file_path):
                    file_path = os.path.join(cwd, file_path)
                dir_path = os.path.dirname(file_path)

                with open(file_path, "r") as f:
                    result.extend(preprocess_argument_list(extract_arguments(f), dir_path))
        else:
            result.append(arg)

    return result


def execute(pipeline: str, document: Optional[vp.Document] = None) -> vp.Document:
    """Execute a vpype pipeline.

    This function serves as a Python API to vpype's pipeline. It can be used from a regular
    Python script (as opposed to the ``vpype`` CLI which must be used from a console or via
    :func:`os.system`.

    If a :class:`vpype.Document` instance is provided, it will be preloaded in the pipeline
    before the first command executes. The pipeline's content after the last command is
    returned as a :class:`vpype.Document` instance.

    Examples:

        Read a SVG file, optimize it and return the result as a :class:`vpype.Document`
        instance::

            >>> doc = execute("read input.svg linemerge linesimplify linesort")

        Optimize and save a :class:`vpype.Document` instance::

            >>> doc = vp.Document()
            >>> # populate `doc` with some graphics
            >>> execute("linemerge linesimplify linesort write output.svg", doc)

    Args:
        pipeline: vpype pipeline as would be used with ``vpype`` CLI
        document: if provided, is perloaded in the pipeline before the first command executes

    Returns:
        pipeline's content after the last command executes
    """

    if document:

        @cli.command()
        @vp.global_processor
        def vsketchinput(doc):
            doc.extend(document)
            return doc

    out_doc = vp.Document()

    @cli.command()
    @vp.global_processor
    def vsketchoutput(doc):
        out_doc.extend(doc)
        return doc

    args = ("vsketchinput " if document else "") + pipeline + " vsketchoutput"
    cli.main(prog_name="vpype", args=shlex.split(args), standalone_mode=False)
    return out_doc
