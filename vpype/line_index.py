import logging
from typing import Iterable, Optional, Tuple

import numpy as np
from scipy.spatial import cKDTree as KDTree

# REMINDER: anything added here must be added to docs/api.rst
__all__ = ["LineIndex"]


class LineIndex:
    """Wrapper to scipy.spatial.cKDTree to facilitate systematic processing of a line
    collection.

    Implementation note: we use the `available` bool array because deleting stuff from the
    index is costly.
    """

    def __init__(self, lines: Iterable[np.ndarray], reverse: bool = False):
        self.lines = [line for line in lines if len(line) > 0]
        self.reverse = reverse
        self._make_index()

    def _make_index(self) -> None:
        logging.info(f"LineIndex: creating index for {len(self.lines)} lines")
        self.available = np.ones(shape=len(self.lines), dtype=bool)

        # create rtree index
        self.index = KDTree(
            np.array([(line[0].real, line[0].imag) for line in self.lines]).reshape(-1, 2)
        )

        # create reverse index
        if self.reverse:
            self.rindex = KDTree(
                np.array([(line[-1].real, line[-1].imag) for line in self.lines]).reshape(
                    -1, 2
                )
            )

    def _reindex(self) -> None:
        self.lines = [line for idx, line in enumerate(self.lines) if self.available[idx]]
        self._make_index()

    def __len__(self) -> int:
        return np.count_nonzero(self.available)

    def __getitem__(self, item):
        return self.lines[item]

    def pop_front(self) -> np.ndarray:
        if len(self) == 0:
            raise RuntimeError
        idx = int(np.argmax(self.available))
        self.available[idx] = False
        return self.lines[idx]

    def pop(self, idx: int) -> Optional[np.ndarray]:
        if not self.available[idx]:
            return None
        self.available[idx] = False
        return self.lines[idx]

    def find_nearest_within(self, p: complex, max_dist: float) -> Tuple[Optional[int], bool]:
        """Find the closest line, assuming a maximum admissible distance.
        Returns a tuple of (idx, reverse), where `idx` may be None if nothing is found.
        `reverse` indicates whether or not a line ending has been matched instead of a start.
        False is always returned if index was created with `reverse=False`.s
        """

        ridx = None
        rdist: Optional[float] = 0.0

        while True:
            reindex, idx, dist = self._find_nearest_within_in_index(p, max_dist, self.index)
            if reindex:
                self._reindex()
                continue

            if self.reverse:
                reindex, ridx, rdist = self._find_nearest_within_in_index(
                    p, max_dist, self.rindex
                )
                if reindex:
                    self._reindex()
                    continue
            break

        if self.reverse:
            if idx is None and ridx is None:
                return None, False
            elif idx is not None and ridx is None:
                return idx, False
            elif idx is None and ridx is not None:
                return ridx, True
            elif rdist < dist:  # type: ignore
                return ridx, True
            else:
                return idx, False
        else:
            return idx, False

    def _find_nearest_within_in_index(
        self, p: complex, max_dist: float, index: KDTree
    ) -> Tuple[bool, Optional[int], Optional[float]]:
        """Find nearest in specific index. Return (reindex, idx, dist) tuple, where
        reindex indicates if a reindex is needed.
        """

        # For performance reason, we query only a max of k candidates. In the special case
        # where all distances are not inf and none are available, we might have more than k
        # suitable candidate, so we reindex and loop. Otherwise, we check the query results
        # for availability and not inf and return anything found
        dists, idxs = index.query((p.real, p.imag), k=50, distance_upper_bound=max_dist)
        dists = np.array(dists)

        not_inf = ~np.isinf(dists)
        if np.all(not_inf) and np.all(~self.available[idxs[not_inf]]):
            return True, None, 0

        candidates = self.available[idxs[not_inf]]

        if np.any(candidates):
            idx = np.argmax(candidates)
            return False, idxs[not_inf][idx], dists[not_inf][idx]
        else:
            return False, None, 0

    # noinspection PyUnboundLocalVariable
    def find_nearest(self, p: complex) -> Tuple[int, bool]:
        while True:
            idx, dist = self._find_nearest_in_index(p, self.index)
            if self.reverse:
                ridx, rdist = self._find_nearest_in_index(p, self.rindex)

                if ridx is not None and idx is not None:
                    break
            elif idx is not None:
                break
            self._reindex()

        if self.reverse:
            if rdist < dist:
                return ridx, True  # type: ignore
            else:
                return idx, False
        else:
            return idx, False

    def _find_nearest_in_index(self, p: complex, index: KDTree) -> Tuple[Optional[int], float]:
        """Check the N nearest lines, hopefully find one that is active."""

        dists, idxs = index.query((p.real, p.imag), k=100)
        for dist, idx in zip(dists, idxs):
            if ~np.isinf(dist) and self.available[idx]:
                return idx, dist

        return None, 0.0
