import sys
import timeit


def timeit_smart(stmt="pass", setup="pass", globals=None, number=None):
    timer = timeit.Timer(stmt, setup, globals=globals)
    if number is None:
        number, _ = timer.autorange()
    return timer.timeit(number=number), number


def benchmark(stmt="pass", setup="pass", globals=None, number=None):
    s, number = timeit_smart(stmt, setup, globals, number)
    s /= number

    unit = "s"
    units = ["ms", "us", "ns"]

    while s < 0.1 and units:
        s *= 1000
        unit = units.pop(0)

    print(f"{stmt} took {s:.3f}{unit} ({number} iterations)")


def memory(obj):
    print(f"{obj} takes {sys.getsizeof(obj)} bytes")
