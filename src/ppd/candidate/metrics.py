from __future__ import annotations

from typing import Dict, List, Tuple, Any

import numpy as np


def compute_mean(values: List[float]) -> float:
    """
    Compute the mean of a list of values.
    """
    if len(values) == 0:
        raise ValueError("Cannot compute mean of empty list.")

    return float(np.mean(values))


def compute_population_std(values: List[float]) -> float:
    """
    Compute the population standard deviation (ddof=0).
    """
    if len(values) == 0:
        raise ValueError("Cannot compute standard deviation of empty list.")

    return float(np.std(values, ddof=0))  # population standard deviation


def compute_min(values: List[float]) -> float:
    """
    Compute the minimum value.
    """
    if len(values) == 0:
        raise ValueError("Cannot compute min of empty list.")

    return float(np.min(values))


def compute_max(values: List[float]) -> float:             # This is now redundant however, deleting it
    """
    Compute the maximum value (contextual only).
    """
    if len(values) == 0:
        raise ValueError("Cannot compute max of empty list.")

    return float(np.max(values))


def compute_range(values: List[float]) -> float:
    """
    Compute the range (max - min).
    """
    if len(values) == 0:
        raise ValueError("Cannot compute range of empty list.")

    return float(np.max(values) - np.min(values))


def compute_argmin_dimensions(
    scores: Dict[str, float], tol: float = 1e-12
) -> Tuple[List[str], float]:
    """
    Return all bottleneck (min) dimension names (tie-aware) and the min value.

    Notes
    -----
    - Uses a tolerance to handle floating-point noise.
    - Returns a list because ties are valid and meaningful diagnostics.
    """
    if len(scores) == 0:
        raise ValueError("Cannot compute argmin for empty scores dict.")

    min_val = min(scores.values())
    min_dims = [dim for dim, val in scores.items() if abs(val - min_val) <= tol]

    return min_dims, float(min_val)

def compute_argmax_dimensions(scores: Dict[str, float], tol: float = 1e-12) -> Tuple[List[str], float]:
    """
    Return all top (max) dimension names (tie-aware) and the max value.
    """
    if len(scores) == 0:
        raise ValueError("Cannot compute argmax for empty scores dict.")

    max_val = max(scores.values())
    max_dims = [dim for dim, val in scores.items() if abs(val - max_val) <= tol]

    return max_dims, float(max_val)

def compute_candidate_metrics(scores: Dict[str, float]) -> Dict[str, object]:
    """
    Compute order-invariant, within-candidate summary descriptors.

    Parameters
    ----------
    scores:
        Mapping of dimension -> score (typically normalized).

    Returns
    -------
    dict
        Keys include:
        - mean
        - std_pop
        - min
        - min_dimensions
        - max
        - range
        - n_dimensions
    """
    if len(scores) == 0:
        raise ValueError("Scores dict is empty.")

    values = list(scores.values())

    mean = compute_mean(values)
    std_pop = compute_population_std(values)

    min_dims, min_val = compute_argmin_dimensions(scores)

    max_dims, max_val = compute_argmax_dimensions(scores)
    range_val = max_val - min_val

    return {
        "mean": mean,
        "std_pop": std_pop,
        "min": min_val,
        "min_dimensions": min_dims,   # tie-aware (as of 0.7.6)
        "max": max_val, 
        "max_dimensions": max_dims,   # tie-aware (as of 0.7.6)
        "range": range_val,
        "n_dimensions": len(values),
    }

# Added in 1.1.2 (moved from candidate/analyze.py to reduce confusion)
def compute_candidate_metrics_by_group(
    scores: Dict[str, float],
    *,
    delimiter: str = "::",
) -> Dict[str, Any]:
    """
    Compute within-candidate metrics per group (category), without cross-group aggregation.

    Parameters
    ----------
    scores:
        Mapping of dimension_key -> score, where dimension_key is "group::metric".
    delimiter:
        Separator between group and metric in the dimension key.

    Returns
    -------
    dict
        Mapping of group -> metrics dict (output of compute_candidate_metrics).
    """
    if len(scores) == 0:
        raise ValueError("Scores dict is empty.")

    grouped: Dict[str, Dict[str, float]] = {}
    for dim, val in scores.items():
        if delimiter in dim:
            group, _metric = dim.split(delimiter, 1)
        else:
            group = "ungrouped"
        grouped.setdefault(group, {})[dim] = val

    out: Dict[str, Any] = {}
    for group, group_scores in grouped.items():
        out[group] = compute_candidate_metrics(group_scores)

    return out