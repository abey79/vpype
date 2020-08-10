from typing import Sequence

import numpy as np
import vpype as vp


def line_collection_contains(lc: vp.LineCollection, line: Sequence[complex]) -> bool:
    """Test existence of line in collection"""

    line_arr = np.array(line, dtype=complex)
    for line_ in lc:
        if np.all(line_ == line_arr):
            return True

    return False
