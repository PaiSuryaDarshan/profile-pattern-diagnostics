# src/ppd/cohort/percentiles.py

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


def validate_probs(probs: Sequence[float]) -> Tuple[float, ...]:
    """Validate percentile probabilities in [0,1] and return as a tuple."""
    if probs is None:
        raise ValueError("probs must not be None.")

    out: List[float] = []
    for p in probs:
        if not isinstance(p, (int, float)):
            raise ValueError(f"Invalid percentile probability type: {p}")
        p_float = float(p)
        if p_float < 0.0 or p_float > 1.0:
            raise ValueError(f"Percentile probability out of range: {p_float}")
        out.append(p_float)

    if len(out) == 0:
        raise ValueError("probs must contain at least one value.")

    return tuple(out)


def probs_to_keys(probs: Sequence[float]) -> List[str]:
    """Convert probabilities into stable keys like p10, p25, p50."""
    probs_valid = validate_probs(probs)

    keys: List[str] = []
    for p in probs_valid:
        keys.append(f"p{int(round(p * 100)):02d}")
    return keys


def compute_percentiles(values: Iterable[float], probs: Sequence[float]) -> Dict[str, float]:
    """
    Compute percentiles for values at given probability levels.

    values:
        Iterable of numeric values (must be non-empty).
    probs:
        Probabilities in [0,1] e.g. (0.1, 0.5, 0.9).

    Returns:
        {"p10": ..., "p50": ..., "p90": ...}
    """
    probs_valid = validate_probs(probs)

    arr = np.array(list(values), dtype=float)
    if arr.size == 0:
        raise ValueError("values must be non-empty.")

    out: Dict[str, float] = {}
    for p in probs_valid:
        key = f"p{int(round(p * 100)):02d}"
        out[key] = float(np.quantile(arr, p))

    return out
