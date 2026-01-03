import copy

import pytest

from ppd.report.candidate_report import build_candidate_report


# ------------------------------------------------------------------
# build_candidate_report
# ------------------------------------------------------------------

# Builds report with metadata + analysis (always)
def test_build_candidate_report_includes_metadata_and_analysis():
    analysis = {
        "scores_raw": {"A": 1.0},
        "scores_norm": {"A": 0.2},
        "metrics": {"mean": 0.2},
        "patterns": None,
    }

    report = build_candidate_report(
        analysis=analysis,
        candidate_identity=None,
        include_identity=False,
        version="0.1.0",
    )

    assert "metadata" in report
    assert "analysis" in report
    assert report["analysis"] == analysis

    assert report["metadata"]["tool"] == "Profile Pattern Diagnostics (PPD)"
    assert report["metadata"]["axis"] == "within-candidate"
    assert report["metadata"]["version"] == "0.1.0"
    assert "generated_at_utc" in report["metadata"]
    assert "scope_note" in report["metadata"]


# Identity is omitted when include_identity=False
def test_build_candidate_report_omits_identity_when_disabled():
    analysis = {"scores_raw": {"A": 1.0}, "scores_norm": {"A": 0.2}, "metrics": {"mean": 0.2}}

    report = build_candidate_report(
        analysis=analysis,
        candidate_identity={"id": 123, "email": "x@y.com", "phone_number": "123", "linkedin_tag": "tag"},
        include_identity=False,
    )

    assert "candidate" not in report


# Identity key exists and is None when include_identity=True but candidate_identity=None
def test_build_candidate_report_identity_is_none_when_missing():
    analysis = {"scores_raw": {"A": 1.0}, "scores_norm": {"A": 0.2}, "metrics": {"mean": 0.2}}

    report = build_candidate_report(
        analysis=analysis,
        candidate_identity=None,
        include_identity=True,
    )

    assert "candidate" in report
    assert report["candidate"] is None


# Identity is included when include_identity=True and candidate_identity is provided
def test_build_candidate_report_includes_identity_when_enabled():
    analysis = {"scores_raw": {"A": 1.0}, "scores_norm": {"A": 0.2}, "metrics": {"mean": 0.2}}
    identity = {"id": 123, "email": "x@y.com", "phone_number": "123", "linkedin_tag": "tag"}

    report = build_candidate_report(
        analysis=analysis,
        candidate_identity=identity,
        include_identity=True,
    )

    assert "candidate" in report
    assert report["candidate"]["id"] == 123
    assert report["candidate"]["email"] == "x@y.com"
    assert report["candidate"]["phone_number"] == "123"
    assert report["candidate"]["linkedin_tag"] == "tag"


# Report does not mutate the provided analysis dict
def test_build_candidate_report_does_not_mutate_analysis():
    analysis = {
        "scores_raw": {"A": 1.0},
        "scores_norm": {"A": 0.2},
        "metrics": {"mean": 0.2},
        "patterns": None,
    }
    analysis_before = copy.deepcopy(analysis)

    report = build_candidate_report(
        analysis=analysis,
        candidate_identity=None,
        include_identity=False,
    )

    assert analysis == analysis_before
    assert report["analysis"] == analysis_before


# Report does not mutate the provided identity dict
def test_build_candidate_report_does_not_mutate_identity():
    analysis = {"scores_raw": {"A": 1.0}, "scores_norm": {"A": 0.2}, "metrics": {"mean": 0.2}}
    identity = {"id": 123, "email": "x@y.com", "phone_number": "123", "linkedin_tag": "tag"}
    identity_before = copy.deepcopy(identity)

    report = build_candidate_report(
        analysis=analysis,
        candidate_identity=identity,
        include_identity=True,
    )

    assert identity == identity_before
    assert report["candidate"] == identity_before
