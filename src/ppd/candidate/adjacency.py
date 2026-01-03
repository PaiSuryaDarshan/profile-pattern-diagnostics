from __future__ import annotations

from typing import Dict, List

import numpy as np


def compute_adjacency_energy(ordered_dimensions: List[str], scores: Dict[str, float]) -> float:
    """
    Compute the cyclic adjacent-difference energy D over an explicitly ordered axis.

    D = (1/n) * sum_{i=1..n} |r_i - r_{i+1}|, with r_{n+1} = r_1
    """
    if len(ordered_dimensions) == 0:
        raise ValueError("ordered_dimensions is empty.")

    for dim in ordered_dimensions:
        if dim not in scores:
            raise KeyError(f"Missing score for dimension: {dim}")

    values = []

    for dim in ordered_dimensions:
        values.append(scores[dim])

    n = len(values)

    if n == 1:
        return 0.0

    diffs = []

    i = 0
    while i < n:
        current_val = values[i]

        if i == n - 1:
            next_val = values[0]
        else:
            next_val = values[i + 1]

        diffs.append(abs(current_val - next_val))
        i += 1

    return float(np.mean(diffs))
