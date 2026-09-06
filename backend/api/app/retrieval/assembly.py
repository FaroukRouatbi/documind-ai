from collections.abc import Callable


def reorder_lost_in_middle[T](chunks: list[T]) -> list[T]:
    left: list[T] = []
    right: list[T] = []
    for i, chunk in enumerate(chunks):
        if i % 2 == 0:
            left.append(chunk)
        else:
            right.append(chunk)
    return left + right[::-1]


def dedup_chunks[T](chunks: list[T], key: Callable[[T], str]) -> list[T]:
    seen: set[str] = set()
    result: list[T] = []
    for chunk in chunks:
        k = key(chunk)
        if k not in seen:
            seen.add(k)
            result.append(chunk)
    return result
