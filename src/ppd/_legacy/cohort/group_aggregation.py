# src/ppd/cohort/group_aggregation.py

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


def aggregate_by_group(
    df: pd.DataFrame,
    *,
    group_col: str,
    id_col: Optional[str] = "candidate_id",
    method: str = "mean",
) -> Dict[str, Any]:
    """
    Aggregate dimension columns by group.

    - method: "mean" or "median"
    - group_col must exist
    - id_col is ignored if present
    - all non-group, non-id columns are treated as dimensions and must be numeric
    """
    df = _require_dataframe(df)

    if group_col not in df.columns:
        raise ValueError(f"group_col '{group_col}' not found in DataFrame.")

    if method not in {"mean", "median"}:
        raise ValueError(f"Unsupported method: {method}. Use 'mean' or 'median'.")

    dim_cols = []
    for c in df.columns:
        if c == group_col:
            continue
        if id_col is not None and c == id_col:
            continue
        dim_cols.append(c)

    if len(dim_cols) == 0:
        raise ValueError("No dimension columns found to aggregate.")

    out: Dict[str, Any] = {"group_col": group_col, "method": method, "groups": {}}

    grouped = df.groupby(group_col, dropna=False)

    for group_value, subdf in grouped:
        group_key = str(group_value)

        group_summary: Dict[str, Any] = {}
        group_summary["n_candidates"] = int(subdf.shape[0])
        group_summary["dimensions"] = {}

        for dim in dim_cols:
            values = _coerce_numeric(subdf[dim], name=str(dim))

            if method == "mean":
                agg = float(np.mean(values))
            else:
                agg = float(np.median(values))

            group_summary["dimensions"][str(dim)] = {method: agg}

        out["groups"][group_key] = group_summary

    return out
