import logging
from functools import update_wrapper

import click
from shapely.geometry import MultiLineString


@click.group(chain=True)
@click.option("-v", "--verbose", "verbose", count=True)
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
    mls = MultiLineString([])
    for processor in processors:
        mls = processor(mls)


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
        ls_arr += [ls for ls in f(*args, **kwargs) ]
        return MultiLineString(ls_arr)

    return update_wrapper(new_func, f)
