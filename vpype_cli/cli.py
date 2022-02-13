import logging
import os
import random
import shlex
import sys
import traceback
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Optional, TextIO, Union, cast

import click
import numpy as np
from pkg_resources import iter_entry_points

import vpype as vp

from .decorators import global_processor
from .state import State

__all__ = ("cli", "execute", "begin", "end", "execute_processors", "ProcessorType")


ProcessorType = Union[
    Callable,
    "BeginBlock",
    "EndBlock",
]


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
            args = sys.argv[1:]
        return super().main(args=preprocess_argument_list(args), **extra)


class _BrokenCommand(click.Command):  # pragma: no cover
    """Rather than completely crash the CLI when a broken plugin is loaded, this
    class provides a modified help message informing the user that the plugin is
    broken and they should contact the owner.  If the user executes the plugin
    or specifies `--help` a traceback is reported showing the exception the
    plugin loader encountered.
    """

    def __init__(self, name):
        """Define the special help messages after instantiating a `click.Command()`."""

        click.Command.__init__(self, name)
        util_name = os.path.basename(sys.argv and sys.argv[0] or __file__)
        self.help = (
            "\nWarning: entry point could not be loaded. Contact "
            "its author for help.\n\n\b\n" + traceback.format_exc()
        )
        self.short_help = "\u2020 Warning: could not load plugin. See `%s %s --help`." % (
            util_name,
            self.name,
        )

    def invoke(self, ctx):
        """Print the traceback instead of doing nothing."""
        click.echo(self.help, color=ctx.color)
        ctx.exit(1)

    def parse_args(self, ctx, args):
        return args


# noinspection PyUnusedLocal,PyUnresolvedReferences
@click.group(cls=GroupedGroup, chain=True)
@click.version_option(version=vp.__version__, message="%(prog)s %(version)s")
@click.option("-v", "--verbose", count=True)
@click.option("-I", "--include", type=click.Path(), help="Load commands from a command file.")
@click.option(
    "-H",
    "--history",
    is_flag=True,
    help="Record this command in a `vpype_history.txt` file in the current directory.",
)
@click.option("-s", "--seed", type=int, help="Specify the RNG seed.")
@click.option(
    "-c", "--config", type=click.Path(exists=True), help="Load an additional config file."
)
@click.pass_context
def cli(ctx, verbose, include, history, seed, config):
    """Execute the sequence of commands passed in argument.

    The available commands are listed below. Information on each command may be obtained using:

        vpype COMMAND --help

    Some of vpype's commands or plug-ins may rely on a random number generator (RNG). By
    default, vpype's RNG is seeded with the current time, such as to produce
    pseudo-random behaviour. The seed can instead be set to a specific value (using
    the `--seed` option) when reproducible behaviour is needed. For example, the following
    always yields the exact same result:

        vpype -s 0 random show

    Include files (commonly named with the `.vpy` extension) can be used instead passing
    commands in the command line, e.g.:

        vpype read input.svg -I my_post_processing.vpy write.output.svg

    Some commands and plug-in can be customized via a TOML configuration file. If a file named
    `.vpype.toml` exists at the root of the user directory, vpype will automatically load it.
    Alternatively, a custom configuration file may be loaded with the `--config` option, e.g.:

        vpype -c my_plotter_config.toml read input.svg write -d my_plotter output.hpgl

    When using the `--history` option, vpype will append its invocation (i.e. the full command
    line) in a `vpype_history.txt` file in the current directory (creating it if necessary).
    This may be useful to easily keep a trace of how project might have been created or
    post-processed with vpype.

    By default, vpype verbosity is low. It may be increased by using the `-v` option once or
    twice to increase verbosity to info, respectively debug level, e.g.:

        vpype -vv [...]

    Refer to the documentation at https://vpype.readthedocs.io/ for more information.
    """

    logging.basicConfig()
    if verbose == 0:
        logging.getLogger().setLevel(logging.WARNING)
    elif verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif verbose > 1:
        logging.getLogger().setLevel(logging.DEBUG)

    # Plug-in loading logic. This approach is preferred because:
    # 1) Deferred plug-in loading avoid circular import between vpype and vpype_cli when plug-
    #    in uses deprecated APIs.
    # 2) Avoids the PyCharm type error with CliRunner.invoke()
    for entry_point in iter_entry_points("vpype.plugins"):
        # noinspection PyBroadException
        try:
            ctx.command.add_command(entry_point.load())
        except Exception:
            # Catch this so a busted plugin doesn't take down the CLI.
            # Handled by registering a dummy command that does nothing
            # other than explain the error.
            ctx.command.add_command(_BrokenCommand(entry_point.name))

    # We use the command string as context object, mainly for the purpose of the `write`
    # command. This is a bit of a hack, and will need to be updated if we ever need more state
    # to be passed around (probably State should go in there!)
    cmd_string = "vpype " + " ".join(shlex.quote(arg) for arg in sys.argv[1:]) + "\n"
    ctx.obj = cmd_string

    if history:
        with open("vpype_history.txt", "a") as fp:
            fp.write(cmd_string)

    if seed is None:
        seed = np.random.randint(2**31)
        logging.info(f"vpype: no seed provided, using {seed}")
    np.random.seed(seed)
    random.seed(seed)

    if config is not None:
        vp.config_manager.load_config_file(config)


# this is somehow needed to make PyCharm happy with runner.invoke(cli, ...)
if TYPE_CHECKING:  # pragma: no cover
    cli = cast(GroupedGroup, cli)


# noinspection PyShadowingNames,PyUnusedLocal
@cli.result_callback()
def process_pipeline(processors, verbose, include, history, seed, config):
    execute_processors(processors, State())


def execute_processors(processors: Iterable[ProcessorType], state: State) -> None:
    """Execute a sequence of processors to generate a Document structure. For block handling,
    we use a recursive approach. Only top-level blocks are extracted and processed by block
    processors, which, in turn, recursively call this function.

    Args:
        processors: iterable of processors
        state: state structure

    Returns:
        generated geometries
    """

    outer_processors: List[Any] = []  # gather commands outside of top-level blocks
    top_level_processors: List[Any] = []  # gather commands inside of top-level blocks
    block = None  # save the current top-level block's block layer_processor
    nested_count = 0  # block depth counter
    expect_block = False  # set to True by `begin` command

    for proc in processors:
        if getattr(proc, "__vpype_block_processor__", False):
            if not expect_block:
                # `begin` was omitted
                nested_count += 1
            else:
                expect_block = False

            # if we in a top level block, we save the block layer_processor
            # (nested block are ignored for the time being)
            if nested_count == 1:
                block = proc
            else:
                top_level_processors.append(proc)
        elif expect_block:
            raise click.BadParameter("A block command must always follow 'begin'")
        elif isinstance(proc, BeginBlock):
            # entering a block
            nested_count += 1
            expect_block = True
        elif isinstance(proc, EndBlock):
            if nested_count < 1:
                raise click.BadParameter(
                    "A 'end' command has no corresponding 'begin' command"
                )

            nested_count -= 1

            if nested_count == 0:
                # We're closing a top level block. The top-level sequence [BeginBlock,
                # block_processor, *top_level_processors, EndBlock] is now replaced by a
                # placeholder closure that will execute the corresponding block processor on
                # the top_level_processors sequence.
                #
                # Note: we use the default argument trick to copy the *current* value of
                # block and top_level_processor "inside" the placeholder function.

                # noinspection PyShadowingNames
                def block_processor_placeholder(
                    state: State, block=block, processors=tuple(top_level_processors)
                ) -> State:
                    return cast(Callable, block)(state, processors)

                outer_processors.append(block_processor_placeholder)

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
    for proc in outer_processors:
        state = cast(Callable, proc)(state)


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


def extract_arguments(f: TextIO) -> List[str]:
    """Read the content of a file-like object and extract the corresponding argument list.

    Everything following a '#' is ignored until end of line. Any whitespace is considered
    to separate arguments. Single and double quote are honored, i.e. content becomes an
    argument (but quote are removed).

    Args:
        f: file-like object

    Returns:
        list of argument extracted from input
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

    Args:
        args: argument list
        cwd:  current working directory, used as reference for relative file paths (use
            actual current working directory if None)

    Returns:
        preprocessed list or argument
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


def execute(
    pipeline: str, document: Optional[vp.Document] = None, global_opt: str = ""
) -> vp.Document:
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
        global_opt: global CLI option (e.g. "--verbose")

    Returns:
        pipeline's content after the last command executes
    """

    if document:

        @cli.command()
        @global_processor
        def vsketchinput(doc):
            doc.extend(document)
            return doc

    out_doc = vp.Document()

    @cli.command()
    @global_processor
    def vsketchoutput(doc):
        out_doc.extend(doc)
        return doc

    args = " ".join(
        [global_opt, ("vsketchinput " if document else ""), pipeline, "vsketchoutput"]
    )
    cli.main(prog_name="vpype", args=shlex.split(args), standalone_mode=False)
    return out_doc
