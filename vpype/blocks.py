from typing import Tuple

import click
from shapely import affinity

from .vpype import cli, block_processor, BlockProcessor, execute_processors, merge_mls


@cli.command("matrix", group="Block processors")
@click.option("-n", "--number", nargs=2, default=(2, 2), type=int)
@click.option("-d", "--delta", nargs=2, default=(100, 100), type=float)
@block_processor
class MatrixBlockProcessor(BlockProcessor):
    """
    Arrange generated geometries on a cartesian matrix.
    """

    def __init__(self, number: Tuple[int, int], delta: Tuple[float, float]):
        self.number = number
        self.delta = delta

    def process(self, processors):
        mls_arr = []
        for i in range(self.number[0]):
            for j in range(self.number[1]):
                mls = execute_processors(processors)
                mls_arr.append(affinity.translate(mls, self.delta[0] * i, self.delta[1] * j))

        return merge_mls(mls_arr)


@cli.command("repeat", group="Block processors"
                             "")
@click.option("-n", "--number", default=1, type=int)
@block_processor
class RepeatBlockProcessor(BlockProcessor):
    """
    Overlap generated geometries on top of each other.
    """

    def __init__(self, number: int):
        self.number = number

    def process(self, processors):
        return merge_mls([execute_processors(processors) for _ in range(self.number)])
