from typing import Any


def batch_list(l: list[Any], batch_size: int) -> list[list[Any]]:

    batches = []
    num_items = len(l)

    for idx_start in range(0, num_items, batch_size):
        idx_end = min([num_items, idx_start + batch_size])
        batches.append(l[idx_start:idx_end])

    return batches
