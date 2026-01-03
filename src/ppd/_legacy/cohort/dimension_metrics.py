from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple, List

import numpy as np
import pandas as pd


# ------------------------------------------------------------------
# Validation / selection helpers
# ------------------------------------------------------------------

def _require_dataframe(df: Any) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("df is empty.")
    return df


def _get_dimension_columns(
    df: pd.DataFrame,
    *,
    id_col: Optional[str],
    allow_numeric_only: bool = True,
) -> List[str]:
    """
    Return the columns that should be treated as score dimensions.

    Rules:
    - Always exclude id_col (if provided and present).
    - If allow_numeric_only=True (default), include ONLY columns that are
      coercible to numeric WITHOUT error (non-numeric columns are skipped).
    - If no dimension columns remain, raise a helpful error.
    """
    cols: List[str] = []

    for c in df.columns:
        if id_col is not None and c == id_col:
            continue

        if not allow_numeric_only:
            cols.append(c)
            continue

        # Keep only columns that are numeric or fully numeric-coercible
        s = df[c]
        if pd.api.types.is_numeric_dtype(s):
            cols.append(c)
            continue

        coerced = pd.to_numeric(s, errors="coerce")
        if coerced.notna().all():
            cols.append(c)
        # else: silently skip non-numeric columns (e.g., email, name)

    if len(cols) == 0:
        msg = (
            "No dimension columns found after excluding id_col and filtering for numeric columns.\n"
            f"- id_col={id_col!r}\n"
            f"- columns={list(df.columns)!r}\n"
            "Expected: one row per candidate, with numeric score columns (and optionally an id column)."
        )
        raise ValueError(msg)

    return cols


def _coerce_numeric(series: pd.Series, *, name: str, allow_missing: bool = False) -> np.ndarray:
    """
    Convert a series to a strict numeric numpy array.

    - allow_missing=False (default): fails if any NaN after coercion
    - allow_missing=True: drops missing values (useful if upstream data is sparse)
    """
    s = pd.to_numeric(series, errors="raise")
    if not allow_missing and s.isna().any():
        raise ValueError(f"Column '{name}' contains missing values (NaN).")
    if allow_missing:
        s = s.dropna()
    return s.to_numpy(dtype=float)


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------

def compute_mean(values: np.ndarray) -> float:
    """Mean across candidates for a dimension."""
    if values.size == 0:
        raise ValueError("values is empty.")
    return float(np.mean(values))


def compute_std_sample(values: np.ndarray) -> Optional[float]:
    """Sample std across candidates (ddof=1). Returns None if n < 2."""
    if values.size == 0:
        raise ValueError("values is empty.")
    if values.size < 2:
        return None
    return float(np.std(values, ddof=1))


def compute_breach_rate(values: np.ndarray, *, threshold: float) -> float:
    """Proportion of candidates strictly below threshold."""
    if values.size == 0:
        raise ValueError("values is empty.")
    return float(np.mean(values < threshold))


def compute_percentiles(
    values: np.ndarray,
    *,
    probs: Tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90),
) -> Dict[str, float]:
    """Percentiles (quantiles) for a dimension."""
    if values.size == 0:
        raise ValueError("values is empty.")

    out: Dict[str, float] = {}
    for p in probs:
        if p < 0.0 or p > 1.0:
            raise ValueError(f"Percentile probability out of range: {p}")
        q = float(np.quantile(values, p))
        key = f"p{int(round(p * 100)):02d}"
        out[key] = q

    return out


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def summarize_dimensions(
    df: pd.DataFrame,
    *,
    id_col: Optional[str] = "candidate_id",
    threshold: Optional[float] = None,
    include_percentiles: bool = False,
    percentile_probs: Tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90),
    allow_missing: bool = False,
    allow_numeric_only: bool = True,
) -> Dict[str, Any]:
    """
    Dimension-level cohort summary.

    Key behavior fixes:
    - Excludes id_col reliably (so strings like "C001" never get coerced).
    - Ignores non-numeric columns by default (e.g., email/name) instead of crashing.
    - Provides optional allow_missing behavior if your upstream data becomes sparse.

    Returns:
        {
          "n_candidates": int,
          "dimensions": {
             "<dimension>": {
                "mean": float,
                "std_sample": float|None,
                "breach_rate": float|None,
                "percentiles": {...}|None
             },
             ...
          }
        }
    """
    df = _require_dataframe(df)

    # n_candidates is simply the row count; id presence shouldn't change it
    n_candidates = int(df.shape[0])

    dims = _get_dimension_columns(df, id_col=id_col, allow_numeric_only=allow_numeric_only)

    out: Dict[str, Any] = {
        "n_candidates": n_candidates,
        "dimensions": {},
    }

    for dim in dims:
        values = _coerce_numeric(df[dim], name=str(dim), allow_missing=allow_missing)

        dim_summary: Dict[str, Any] = {
            "mean": compute_mean(values) if values.size else (None if allow_missing else compute_mean(values)),
            "std_sample": compute_std_sample(values) if values.size else None,
            "breach_rate": None if threshold is None or values.size == 0 else compute_breach_rate(values, threshold=threshold),
            "percentiles": compute_percentiles(values, probs=percentile_probs) if include_percentiles and values.size else ({} if include_percentiles else None),
        }

        if not include_percentiles:
            dim_summary["percentiles"] = None

        out["dimensions"][str(dim)] = dim_summary

    return out
