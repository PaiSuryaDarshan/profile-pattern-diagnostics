from __future__ import annotations

from typing import Any, Dict, Optional

from ppd.report.metadata import build_metadata
from ppd.schema.output_schema import validate_candidate_report

# NOTE: QOL update in (0.2.0): round all floats to 6dp in final report
def _round_floats(obj, ndigits=6):
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, ndigits) for v in obj]
    return obj

def build_candidate_report(
    *,
    analysis: Dict[str, Any],
    candidate_identity: Optional[Dict[str, Any]] = None,
    include_identity: bool = True,
    version: str = "1.1.2",
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Wrap candidate analysis into a stable report contract.

    analysis comes from ppd.candidate.analyze.analyze_candidate.
    candidate_identity is metadata only (id/email/phone/linkedin etc).
    """
    report: Dict[str, Any] = {
        "metadata": build_metadata(axis="within-candidate", version=version),
        "analysis": analysis,
    }

    if include_identity:
        if candidate_identity is None:
            report["candidate"] = None
        else:
            report["candidate"] = dict(candidate_identity)

    report = _round_floats(report, ndigits=6)

    if validate:
        validate_candidate_report(report)

    return report
