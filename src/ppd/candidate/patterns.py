from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ppd.schema import constants


def _require_threshold(name: str, value) -> None:
    """Raise if a required threshold is not set."""
    if value is None:
        raise RuntimeError(
            f"Threshold '{name}' is not set (currently None). "
            "Set it in ppd.schema.constants.THRESHOLDS before running patterns."
        )


def is_balanced(std_pop: float) -> bool:
    """Return True if dispersion is within the balance threshold."""
    _require_threshold("tau_balance", constants.THRESHOLDS.tau_balance)
    return std_pop <= constants.THRESHOLDS.tau_balance


def is_bottlenecked(min_value: float) -> bool:
    """Return True if the minimum dimension breaches the bottleneck threshold."""
    _require_threshold("tau_bottleneck", constants.THRESHOLDS.tau_bottleneck)
    return min_value <= constants.THRESHOLDS.tau_bottleneck


def is_noisy(std_pop: float) -> bool:
    """Return True if dispersion exceeds the noisy threshold."""
    _require_threshold("tau_noisy", constants.THRESHOLDS.tau_noisy)
    return std_pop >= constants.THRESHOLDS.tau_noisy


def is_uniform_low(mean: float, std_pop: float) -> bool:
    """Return True if group is balanced and the mean is low."""
    _require_threshold("tau_uniform_low_mean", constants.THRESHOLDS.tau_uniform_low_mean)
    return is_balanced(std_pop) and mean <= constants.THRESHOLDS.tau_uniform_low_mean


def is_uniform_high(mean: float, std_pop: float) -> bool:
    """Return True if group is balanced and the mean is high."""
    _require_threshold("tau_uniform_high_mean", constants.THRESHOLDS.tau_uniform_high_mean)
    return is_balanced(std_pop) and mean >= constants.THRESHOLDS.tau_uniform_high_mean


def is_polarised(min_value: float, max_value: float, range_value: float) -> bool:
    """Return True if the group is polarised: low min, high max, and large spread."""
    _require_threshold("tau_polarised_range", constants.THRESHOLDS.tau_polarised_range)
    _require_threshold("tau_low", constants.THRESHOLDS.tau_low)
    _require_threshold("tau_high", constants.THRESHOLDS.tau_high)

    return (
        range_value >= constants.THRESHOLDS.tau_polarised_range
        and min_value <= constants.THRESHOLDS.tau_low
        and max_value >= constants.THRESHOLDS.tau_high
    )


def _extract_dimension_scores(candidate_metrics: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Best-effort extraction of per-dimension scores from candidate_metrics.

    Supports:
    - candidate_metrics["scores"] = {dim: score}
    - candidate_metrics["dimension_scores"] = {dim: score}
    - candidate_metrics["dimensions"] = {dim: {"raw": score}} or {dim: score}
    """
    for key in ("scores", "dimension_scores"):
        if key in candidate_metrics and isinstance(candidate_metrics[key], dict):
            out: Dict[str, float] = {}
            for d, v in candidate_metrics[key].items():
                try:
                    out[str(d)] = float(v)
                except (TypeError, ValueError):
                    continue
            return out if out else None

    if "dimensions" in candidate_metrics and isinstance(candidate_metrics["dimensions"], dict):
        out2: Dict[str, float] = {}
        for d, v in candidate_metrics["dimensions"].items():
            if isinstance(v, dict) and "raw" in v:
                try:
                    out2[str(d)] = float(v["raw"])
                except (TypeError, ValueError):
                    continue
            else:
                try:
                    out2[str(d)] = float(v)
                except (TypeError, ValueError):
                    continue
        return out2 if out2 else None

    return None


def _polarised_dimension_lists(
    *,
    mean: float,
    std_pop: float,
    dim_scores: Dict[str, float],
    z_threshold: float,
) -> Tuple[List[Dict[str, float]], List[Dict[str, float]]]:
    """
    Return (high, low) polarised dimension lists using within-candidate z-scores:
      z = (x - mean) / std_pop

    If std_pop == 0, returns empty lists.
    """
    if std_pop == 0.0:
        return [], []

    high: List[Dict[str, float]] = []
    low: List[Dict[str, float]] = []

    for dim, x in dim_scores.items():
        z = (float(x) - float(mean)) / float(std_pop)
        if z >= z_threshold:
            high.append({"dimension": dim, "z": float(z)})
        elif z <= -z_threshold:
            low.append({"dimension": dim, "z": float(z)})

    high.sort(key=lambda d: abs(d["z"]), reverse=True)
    low.sort(key=lambda d: abs(d["z"]), reverse=True)

    return high, low

# Fixed in version 1.1.2 to adjust for min_dimensions error
def classify_candidate_patterns(candidate_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret within-candidate metrics into diagnostic pattern flags.

    Required keys in candidate_metrics:
    - mean
    - std_pop
    - min
    - min_dimensions
    - max
    - range

    Optional (for polarised dimension lists):
    - scores | dimension_scores | dimensions
    - polarised_z_threshold (float)  # default 1.0

    Output contract:
    - If polarised == False -> polarised_dimensions_high/low are null (None)
    - If polarised == True and per-dimension scores exist -> lists are populated
    - If polarised == True but scores absent -> null (None)
    """
    required = ("mean", "std_pop", "min", "min_dimensions", "max", "range")
    for k in required:
        if k not in candidate_metrics:
            raise KeyError(f"candidate_metrics missing required key: '{k}'")

    mean = float(candidate_metrics["mean"])
    std_pop = float(candidate_metrics["std_pop"])
    min_val = float(candidate_metrics["min"])
    max_val = float(candidate_metrics["max"])
    range_val = float(candidate_metrics["range"])
    min_dims = candidate_metrics["min_dimensions"]

    balanced = is_balanced(std_pop)
    bottlenecked = is_bottlenecked(min_val)

    polarised = is_polarised(min_val, max_val, range_val)
    noisy = is_noisy(std_pop)
    uniform_low = is_uniform_low(mean, std_pop)
    uniform_high = is_uniform_high(mean, std_pop)

    bottleneck_dim = min_dims[0] if bottlenecked else None
    bottleneck_dims = min_dims if bottlenecked else None
    bottleneck_value = min_val if bottlenecked else None

    # --------------------------------------------------------------
    # NEW: polarised dimension lists (only if polarised == True)
    # Polarised dimension lists (explicit nulls when not applicable)
    # --------------------------------------------------------------
    polarised_high: Optional[List[Dict[str, float]]] = None
    polarised_low: Optional[List[Dict[str, float]]] = None

    if polarised:
        dim_scores = _extract_dimension_scores(candidate_metrics)
        if dim_scores is not None:
            z_threshold = float(candidate_metrics.get("polarised_z_threshold", 1.0))
            polarised_high, polarised_low = _polarised_dimension_lists(
                mean=mean,
                std_pop=std_pop,
                dim_scores=dim_scores,
                z_threshold=z_threshold,
            )
        # else: remain None (null)

    return {
        "balanced": balanced,
        "bottlenecked": bottlenecked,
        "polarised": polarised,
        "noisy": noisy,
        "uniform_low": uniform_low,
        "uniform_high": uniform_high,
        "bottleneck_dimension": bottleneck_dim,
        "bottleneck_dimensions": bottleneck_dims,
        "bottleneck_value": bottleneck_value,
        # NEW in 1.1.0 (only populated when polarised=True and scores are available)
        "polarised_dimensions_high": polarised_high,
        "polarised_dimensions_low": polarised_low,
    }
