import math
import random

import matplotlib.pyplot as plt
from shapely import affinity, ops
from shapely.geometry import MultiLineString

__ALL__ = ["generate"]

N = 5
M = 6


def append_maybe(item, lst):
    if random.random() < 0.5:
        lst.append(item)


def generate():
    segs = []

    # horizontal segments
    for i in range(math.floor(N / 2)):
        for j in range(M):
            append_maybe([(i, j), (i + 1, j)], segs)

    # add half horizontal segments
    if N % 2 == 0:
        for j in range(M):
            append_maybe([((N / 2) - 1, j), (N / 2, j)], segs)

    # add vertical segments
    for i in range(math.ceil(N / 2)):
        for j in range(M - 1):
            append_maybe([(i, j), (i, j + 1)], segs)

    half_mls = MultiLineString(segs)
    other_mls = affinity.translate(affinity.scale(half_mls, -1, 1, origin=(0, 0)), N - 1, 0)

    return ops.linemerge(ops.unary_union([half_mls, other_mls]))


if __name__ == "__main__":
    mls = generate()

    for ls in mls:
        plt.plot(*ls.xy, "-")

    plt.axis("equal")
    plt.show()
