# src/ppd/cohort/group_metrics.py

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def _require_dataframe(df: Any) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("df is empty.")
    return df


def _coerce_numeric(series: pd.Series, *, name: str) -> np.ndarray:
    s = pd.to_numeric(series, errors="raise")
    if s.isna().any():
        raise ValueError(f"Column '{name}' contains missing values (NaN).")
    return s.to_numpy(dtype=float)


def _compute_mean(values: np.ndarray) -> float:
    if values.size == 0:
        raise ValueError("values is empty.")
    return float(np.mean(values))


def _compute_std_sample(values: np.ndarray) -> Optional[float]:
    if values.size == 0:
        raise ValueError("values is empty.")
    if values.size < 2:
        return None
    return float(np.std(values, ddof=1))


def _compute_breach_rate(values: np.ndarray, *, threshold: float) -> float:
    if values.size == 0:
        raise ValueError("values is empty.")
    return float(np.mean(values < threshold))


def summarize_groups(
    df: pd.DataFrame,
    *,
    group_col: str,
    id_col: Optional[str] = "candidate_id",
    threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Group-level cohort summary.

    Returns:
        {
          "group_col": "<group_col>",
          "groups": {
             "<group_value>": {
                "n_candidates": int,
                "dimensions": {
                   "<dimension>": {
                      "mean": float,
                      "std_sample": float|None,
                      "breach_rate": float|None
                   },
                   ...
                }
             },
             ...
          }
        }
    """
    df = _require_dataframe(df)

    if group_col not in df.columns:
        raise ValueError(f"Missing group_col '{group_col}' in DataFrame.")

    dims = []
    for c in df.columns:
        if c == group_col:
            continue
        if id_col is not None and c == id_col:
            continue
        dims.append(c)

    if len(dims) == 0:
        raise ValueError("No dimension columns found (after excluding group_col/id_col).")

    out: Dict[str, Any] = {}
    out["group_col"] = group_col
    out["groups"] = {}

    grouped = df.groupby(group_col, dropna=False)

    for group_value, group_df in grouped:
        group_key = str(group_value)
        group_out: Dict[str, Any] = {}
        group_out["n_candidates"] = int(group_df.shape[0])
        group_out["dimensions"] = {}

        for dim in dims:
            values = _coerce_numeric(group_df[dim], name=str(dim))

            dim_summary: Dict[str, Any] = {}
            dim_summary["mean"] = _compute_mean(values)
            dim_summary["std_sample"] = _compute_std_sample(values)

            if threshold is None:
                dim_summary["breach_rate"] = None
            else:
                dim_summary["breach_rate"] = _compute_breach_rate(values, threshold=threshold)

            group_out["dimensions"][str(dim)] = dim_summary

        out["groups"][group_key] = group_out

    return out
