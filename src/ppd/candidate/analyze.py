from __future__ import annotations

from typing import Any, Dict, List, Optional

from ppd.candidate.adjacency import compute_adjacency_energy
from ppd.candidate.metrics import compute_candidate_metrics_by_group
from ppd.candidate.normalize import normalize_score
from ppd.candidate.patterns import classify_candidate_patterns
from ppd.schema import constants

# NOTE : This has been adapted to prevent pytest fail by checking 
# for all newly added Kendall Threshold factors (added on 2021-10-10)
def _has_pattern_thresholds() -> bool:
    """Return True if all required pattern thresholds are set."""
    t = constants.THRESHOLDS
    return (
        t.tau_balance is not None
        and t.tau_bottleneck is not None
        and t.tau_noisy is not None                     # New 
        and t.tau_uniform_low_mean is not None          # New
        and t.tau_uniform_high_mean is not None         # New
        and t.tau_polarised_range is not None           # New     
        and t.tau_low is not None                       # New       
        and t.tau_high is not None                      # New            
    )

def analyze_candidate(
    raw_scores: Dict[str, float],
    *,
    ordered_dimensions: Optional[List[str]] = None,
    include_adjacency: bool = True,
    include_patterns: bool = True,
) -> Dict[str, Any]:
    """
    Candidate-level orchestration:
    - normalize raw scores
    - compute within-candidate metrics
    - optionally compute adjacency D (order-aware)
    - optionally compute pattern flags (requires thresholds)
    """
    if len(raw_scores) == 0:
        raise ValueError("raw_scores is empty.")

    normalized_scores: Dict[str, float] = {}

    for dim, raw in raw_scores.items():
        normalized_scores[dim] = normalize_score(raw)

    metrics_by_group = compute_candidate_metrics_by_group(normalized_scores)

    # Backwards-compat: tests expect 'metrics' for ungrouped inputs ("A","B","C")
    metrics = metrics_by_group.get("ungrouped")

    out: Dict[str, Any] = {
        "scores_raw": dict(raw_scores),
        "scores_norm": dict(normalized_scores),
        "metrics": dict(metrics) if metrics is not None else None,
        "metrics_by_group": dict(metrics_by_group),
    }

    # --- adjacency D (order-aware, explicit) ---
    if include_adjacency:
        order = ordered_dimensions

        if order is None or len(order) == 0:
            if getattr(constants, "DIMENSION_ORDER", None):
                if len(constants.DIMENSION_ORDER) > 0:
                    order = list(constants.DIMENSION_ORDER)

        if order is not None and len(order) > 0:
            d = compute_adjacency_energy(order, normalized_scores)
            out["adjacency_D"] = d
            out["adjacency_order"] = list(order)
        else:
            out["adjacency_D"] = None
            out["adjacency_order"] = None

    # --- patterns (interpretation, requires thresholds) ---
    if include_patterns:
        if _has_pattern_thresholds():
            patterns_by_group: Dict[str, Any] = {}

            for group, group_metrics in metrics_by_group.items():
                # Build per-group dimension score map (normalized, scale-consistent)
                group_scores = {
                    dim: float(val)
                    for dim, val in normalized_scores.items()
                    if dim.startswith(f"{group}::")
                }

                # Merge metrics + scores
                candidate_metrics = dict(group_metrics)
                candidate_metrics["scores"] = group_scores
                candidate_metrics["polarised_z_threshold"] = 1.0  # optional, explicit

                patterns_by_group[group] = classify_candidate_patterns(candidate_metrics)

            out["patterns_by_group"] = patterns_by_group

        else:
            out["patterns_by_group"] = None

        out["patterns"] = None

    return out
