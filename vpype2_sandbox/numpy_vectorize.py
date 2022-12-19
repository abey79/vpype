"""Mini-benchmark of numpy.vectorize vs. list comprehension."""

from __future__ import annotations

import timeit
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Line:
    start: complex
    end: complex

    def move(self, offset: complex) -> Line:
        return self.__class__(self.start + offset, self.end + offset)


@dataclass(frozen=True)
class Arc:
    start: complex
    end: complex
    control: complex

    def move(self, offset: complex) -> Arc:
        return self.__class__(self.start + offset, self.end + offset, self.control + offset)


arr = np.array([Line(3, 5), Line(6, 7), Arc(1, 2, 3), Arc(4, 5, 6)])
vmove = np.vectorize(lambda seg, off: seg.move(off))
print(vmove(arr, 1j))

# How does this compare to [s.move(off) for s in arr] and regular lists?


# build random list of lines
data = np.zeros((10000, 2), dtype=complex)
data.real = np.random.rand(10000, 2)
data.imag = np.random.rand(10000, 2)

lst = [Line(*d) for d in data]
arr = np.array(lst)


print("Python list:", timeit.timeit(lambda: [l.move(1j) for l in lst], number=100))
print("Numpy vectorized function:", timeit.timeit(lambda: vmove(arr, 1j), number=100))
print("Raw numpy array:", timeit.timeit(lambda: data + 1j, number=100))
