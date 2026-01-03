from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class CandidateReportMeta:
    tool: str
    version: str
    axis: str
    generated_at_utc: str
    scope_note: str


@dataclass(frozen=True)
class CohortReportMeta:
    tool: str
    version: str
    axis: str
    generated_at_utc: str
    scope_note: str


_FORBIDDEN_PII_KEYS = {"email", "phone_number", "linkedin_tag"}
_FORBIDDEN_ID_KEYS = {"candidate_id", "candidate_email", "candidate_phone_no", "candidate_phone_number"}


def _require_dict(obj: Any, name: str) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError(f"{name} must be a dict.")
    return obj


def _require_str(obj: Any, name: str) -> str:
    if not isinstance(obj, str) or obj.strip() == "":
        raise ValueError(f"{name} must be a non-empty string.")
    return obj


def _require_metadata(meta: Dict[str, Any], *, axis_expected: str) -> Dict[str, str]:
    _require_dict(meta, "metadata")

    tool = _require_str(meta.get("tool"), "metadata.tool")
    version = _require_str(meta.get("version"), "metadata.version")
    axis = _require_str(meta.get("axis"), "metadata.axis")
    generated_at_utc = _require_str(meta.get("generated_at_utc"), "metadata.generated_at_utc")
    scope_note = _require_str(meta.get("scope_note"), "metadata.scope_note")

    if axis != axis_expected:
        raise ValueError(f"metadata.axis must be '{axis_expected}', got '{axis}'.")

    return {
        "tool": tool,
        "version": version,
        "axis": axis,
        "generated_at_utc": generated_at_utc,
        "scope_note": scope_note,
    }


def _walk_keys(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                yield k
            for kk in _walk_keys(v):
                yield kk
    elif isinstance(obj, list):
        for item in obj:
            for kk in _walk_keys(item):
                yield kk


def _contains_forbidden_keys(obj: Any, forbidden: set) -> bool:
    for k in _walk_keys(obj):
        if k in forbidden:
            return True
    return False


def validate_candidate_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the shape of a candidate report.

    Rules:
    - metadata required, axis must be within-candidate
    - analysis required
    - candidate key optional:
        - may be missing (when include_identity=False)
        - or present as dict
        - or present as None
    """
    report = _require_dict(report, "candidate_report")

    meta = report.get("metadata")
    _require_metadata(_require_dict(meta, "metadata"), axis_expected="within-candidate")

    analysis = report.get("analysis")
    _require_dict(analysis, "analysis")

    if "candidate" in report:
        candidate = report["candidate"]
        if candidate is not None:
            _require_dict(candidate, "candidate")

    return report


def validate_cohort_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the shape of a cohort report.

    Rules:
    - metadata required, axis must be across-candidate
    - cohort_summary required
    - group_summary optional
    - NO candidate identity / PII allowed anywhere in cohort/group summaries
    """
    report = _require_dict(report, "cohort_report")

    meta = report.get("metadata")
    _require_metadata(_require_dict(meta, "metadata"), axis_expected="across-candidate")

    cohort_summary = report.get("cohort_summary")
    _require_dict(cohort_summary, "cohort_summary")

    if "group_summary" in report:
        group_summary = report["group_summary"]
        if group_summary is not None:
            _require_dict(group_summary, "group_summary")

    # PII / identity leakage guard (cohort outputs must not contain this)
    forbidden = set(_FORBIDDEN_PII_KEYS) | set(_FORBIDDEN_ID_KEYS) | {"candidate"}
    if _contains_forbidden_keys(cohort_summary, forbidden):
        raise ValueError("Cohort report contains forbidden identity/PII keys in cohort_summary.")

    if "group_summary" in report and report["group_summary"] is not None:
        if _contains_forbidden_keys(report["group_summary"], forbidden):
            raise ValueError("Cohort report contains forbidden identity/PII keys in group_summary.")

    return report
