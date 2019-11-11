import logging
from functools import update_wrapper
from typing import Iterable

import click
from shapely.geometry import MultiLineString


# noinspection PyShadowingBuiltins
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
                help = cmd.get_short_help_str(limit)
                subcommand += " " * (longest - len(subcommand))
                groups.setdefault(cmd.help_group, []).append((subcommand, help))

            with formatter.section("Commands"):
                for group_name, rows in groups.items():
                    with formatter.section(group_name):
                        formatter.write_dl(rows)


@click.group(cls=GroupedGroup, chain=True)
@click.option("-v", "--verbose", count=True)
def cli(verbose):
    logging.basicConfig()
    if verbose == 0:
        logging.getLogger().setLevel(logging.WARNING)
    elif verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif verbose > 1:
        logging.getLogger().setLevel(logging.DEBUG)


# noinspection PyShadowingNames,PyUnusedLocal
@cli.resultcallback()
def process_pipeline(processors, verbose):
    execute_processors(processors)


def execute_processors(processors) -> MultiLineString:
    """
    Execute a sequence of processors to generate a MultiLineString. For block handling, we use
    a recursive approach. Only top-level blocks are extracted and processed by block
    processors, which, in turn, recursively call this function.
    :param processors: iterable of processors
    :return: generated geometries
    """

    outer_processors = list()  # gather commands outside of top-level blocks
    top_level_processors = list()  # gather commands inside of top-level blocks
    block = None  # save the current top-level block's block processor
    nested_count = 0  # block depth counter
    expect_block = False  # set to True by `begin` command

    for proc in processors:
        if isinstance(proc, BlockProcessor):
            if expect_block:
                expect_block = False
                # if we in a top level block, we save the block processor
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
                block_mls = block.process(top_level_processors)

                # Create a placeholder processor that will add the block's result to the
                # current frame. The placeholder_processor is a closure, so we need to make
                # a closure-building function. Failing that, the closure would refer directly
                # to the block_mls variable above, which might be overwritten by a subsequent
                # top-level block
                # noinspection PyShadowingNames
                def build_placeholder_processor(block_mls):
                    def placeholder_processor(input_mls):
                        return merge_mls([input_mls, block_mls])

                    return placeholder_processor

                outer_processors.append(build_placeholder_processor(block_mls))

                # reset the top level processor list
                top_level_processors = list()
            else:
                top_level_processors.append(proc)
        else:
            # this is a 'normal' processor, we can just add it to the top of the stack
            if nested_count == 0:
                outer_processors.append(proc)
            else:
                top_level_processors.append(proc)

    # at this stage, the stack must have a single frame, otherwise we're missing end commands
    if nested_count > 0:
        raise click.ClickException("An 'end' command is missing")

    # the (only) frame's processors should now be flat and can be chain-called
    mls = MultiLineString([])
    for proc in outer_processors:
        mls = proc(mls)
    return mls


def merge_mls(mls_arr: Iterable[MultiLineString]) -> MultiLineString:
    """
    Merge multiple MultiLineString into one.
    :param mls_arr: iterable of MultiLineString
    :return: merged MultiLineString
    """

    return MultiLineString([ls for mls in mls_arr for ls in mls])


def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """

    def new_func(*args, **kwargs):
        # noinspection PyShadowingNames
        def processor(mls):
            return f(mls, *args, **kwargs)

        return processor

    return update_wrapper(new_func, f)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """

    @processor
    def new_func(mls: MultiLineString, *args, **kwargs):
        ls_arr = [ls for ls in mls]
        ls_arr += [ls for ls in f(*args, **kwargs)]
        return MultiLineString(ls_arr)

    return update_wrapper(new_func, f)


def block_processor(c):
    """
    Create an instance of the block processor class
    """

    def new_func(*args, **kwargs):
        return c(*args, **kwargs)

    return update_wrapper(new_func, c)


class BeginBlock:
    pass


@cli.command(group="Block control")
def begin():
    """
    Mark the start of a block. It must be followed by a block processor command (eg. `matrix`
    or `repeat`), which indicates how the block is processed. Blocks must be ended by a `end`
    command and can be nested.
    """
    return BeginBlock()


class EndBlock:
    pass


@cli.command(group="Block control")
def end():
    """
    Mark the end of a block.
    """
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
