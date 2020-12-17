import pathlib
from typing import Sequence

import numpy as np

import vpype as vp
from vpype_cli import execute

TESTS_DIRECTORY = pathlib.Path(__file__).parent


def line_collection_contains(lc: vp.LineCollection, line: Sequence[complex]) -> bool:
    """Test existence of line in collection"""

    line_arr = np.array(line, dtype=complex)
    for line_ in lc:
        if np.all(line_ == line_arr):
            return True

    return False


def execute_single_line(pipeline: str, line: vp.LineLike) -> vp.LineCollection:
    """Execute a pipeline on a single line. The pipeline is expected to remain single layer.

    Returns:
        the layer 1's LineCollection
    """
    doc = execute(pipeline, vp.Document(vp.LineCollection([line])))
    assert len(doc.layers) == 1
    return doc.layers[1]
