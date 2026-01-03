from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from ppd._legacy.cohort.dimension_metrics import summarize_dimensions
from ppd._legacy.cohort.group_aggregation import aggregate_by_group
from ppd.report.cohort_report import build_cohort_report


def summarize_cohort(
    df: pd.DataFrame,
    *,
    id_col: str = "candidate_id",
    group_col: Optional[str] = None,
    threshold: Optional[float] = None,
    include_percentiles: bool = False,
    include_group_summary: bool = True,
    group_method: str = "mean",
    version: str = "0.1.0",
    validate_report: bool = True,
) -> Dict[str, Any]:
    """
    Orchestrate cohort-level summaries (Axis B).

    - Dimension metrics are computed over numeric dimension columns only.
    - If group_col is provided, it is excluded from dimension metrics (it is not a dimension).
    """
    df_for_dims = df
    if group_col is not None and group_col in df.columns:
        df_for_dims = df.drop(columns=[group_col])

    cohort_summary = summarize_dimensions(
        df_for_dims,
        id_col=id_col,
        threshold=threshold,
        include_percentiles=include_percentiles,
    )

    group_summary = None
    if include_group_summary and group_col is not None:
        group_summary = aggregate_by_group(
            df,
            group_col=group_col,
            id_col=id_col,
            method=group_method,
        )

    report = build_cohort_report(
        cohort_summary=cohort_summary,
        group_summary=group_summary,
        include_group_summary=include_group_summary,
        version=version,
        validate=validate_report,
    )

    return report
