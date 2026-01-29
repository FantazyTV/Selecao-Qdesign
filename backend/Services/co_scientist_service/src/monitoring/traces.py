from contextlib import contextmanager
from time import perf_counter


@contextmanager
def trace_span(name: str):
    start = perf_counter()
    yield
    _ = perf_counter() - start
