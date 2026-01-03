from __future__ import annotations

from typing import Any, Dict, Optional

from ppd.report.metadata import build_metadata
from ppd.schema.output_schema import validate_cohort_report

def _round_floats(obj, ndigits=6):
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, ndigits) for v in obj]
    return obj

def build_cohort_report(
    *,
    cohort_summary: Dict[str, Any],
    group_summary: Optional[Dict[str, Any]] = None,
    include_group_summary: bool = True,
    version: str = "1.1.2",
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Wrap cohort-level outputs into a stable report contract.

    cohort_summary and group_summary must contain no candidate identity fields.
    """
    report: Dict[str, Any] = {
        "metadata": build_metadata(axis="across-candidate", version=version),
        "cohort_summary": cohort_summary,
    }

    if include_group_summary:
        report["group_summary"] = group_summary

    report = _round_floats(report, ndigits=6)

    if validate:
        validate_cohort_report(report)

    return report
