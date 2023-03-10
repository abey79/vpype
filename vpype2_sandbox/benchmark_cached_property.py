import timeit
from functools import cached_property

import numpy as np
import numpy.typing as npt
from attr import field, frozen
from benchmark_tools import benchmark, memory


def line_length(line: np.ndarray) -> float:
    """Compute the length of a line."""
    return np.sum(np.abs(np.diff(line)))


@frozen
class Slotted:
    coords: npt.NDArray[np.complex64] = field(
        converter=lambda x: np.array(x, dtype=np.complex64), repr=False
    )

    @property
    def length(self) -> float:
        return line_length(self.coords)


@frozen(slots=False)
class CachedProperty:
    coords: npt.NDArray[np.complex64] = field(
        converter=lambda x: np.array(x, dtype=np.complex64), repr=False
    )

    @cached_property
    def length(self) -> float:
        return line_length(self.coords)


arr = np.linspace(0, 1, 1000) + 1j * np.linspace(4, 1, 1000)
slotted = Slotted(arr)
try:
    slotted.__dict__
    assert False
except:
    pass
cached_prop = CachedProperty(arr)


memory(slotted)
memory(cached_prop)

benchmark("slotted.length", globals=globals())
benchmark("cached_prop.length", globals=globals())
benchmark("slotted.length", globals=globals(), number=10)
benchmark("cached_prop.length", globals=globals(), number=10)
benchmark("slotted.length", globals=globals(), number=1)
benchmark("cached_prop.length", globals=globals(), number=1)
