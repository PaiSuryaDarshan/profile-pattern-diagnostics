import pytest

from ppd.schema.output_schema import (
    validate_candidate_report,
    validate_cohort_report,
)


# ------------------------------------------------------------------
# validate_candidate_report
# ------------------------------------------------------------------

# Valid candidate report passes (no identity included)
def test_validate_candidate_report_valid_without_identity():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "within-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "analysis": {"metrics": {"mean": 0.5}},
    }

    out = validate_candidate_report(report)
    assert out["analysis"]["metrics"]["mean"] == pytest.approx(0.5)


# Valid candidate report passes (identity included)
def test_validate_candidate_report_valid_with_identity():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "within-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "candidate": {
            "id": 123,
            "email": "x@y.com",
            "phone_number": "+44-7000",
            "linkedin_tag": "linkedin.com/in/x",
        },
        "analysis": {"metrics": {"mean": 0.5}},
    }

    out = validate_candidate_report(report)
    assert out["candidate"]["id"] == 123


# Wrong axis should fail
def test_validate_candidate_report_wrong_axis_raises():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "across-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "analysis": {"metrics": {"mean": 0.5}},
    }

    with pytest.raises(ValueError):
        validate_candidate_report(report)


# ------------------------------------------------------------------
# validate_cohort_report
# ------------------------------------------------------------------

# Valid cohort report passes (no group summary)
def test_validate_cohort_report_valid_without_group_summary():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "across-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "cohort_summary": {
            "dimensions": {
                "Communication Skills::Grammar": {"mean": 0.7, "std_sample": 0.1, "breach_rate": 0.0}
            }
        },
    }

    out = validate_cohort_report(report)
    assert "cohort_summary" in out


# Valid cohort report passes (with group summary)
def test_validate_cohort_report_valid_with_group_summary():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "across-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "cohort_summary": {
            "dimensions": {
                "Communication Skills::Grammar": {"mean": 0.7, "std_sample": 0.1, "breach_rate": 0.0}
            }
        },
        "group_summary": {
            "groups": {
                "TeamA": {
                    "dimensions": {
                        "Communication Skills::Grammar": {"mean": 0.8, "std_sample": 0.05, "breach_rate": 0.0}
                    }
                }
            }
        },
    }

    out = validate_cohort_report(report)
    assert "group_summary" in out


# Wrong axis should fail
def test_validate_cohort_report_wrong_axis_raises():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "within-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "cohort_summary": {"dimensions": {}},
    }

    with pytest.raises(ValueError):
        validate_cohort_report(report)


# Cohort report must reject identity/PII leakage in cohort_summary
def test_validate_cohort_report_rejects_pii_in_cohort_summary():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "across-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "cohort_summary": {
            "dimensions": {"Communication Skills::Grammar": {"mean": 0.7}},
            "email": "leak@example.com",
        },
    }

    with pytest.raises(ValueError):
        validate_cohort_report(report)


# Cohort report must reject identity/PII leakage in group_summary
def test_validate_cohort_report_rejects_pii_in_group_summary():
    report = {
        "metadata": {
            "tool": "Profile Pattern Diagnostics (PPD)",
            "version": "0.1.0",
            "axis": "across-candidate",
            "generated_at_utc": "2025-12-31T00:00:00Z",
            "scope_note": "Diagnostic + descriptive only.",
        },
        "cohort_summary": {"dimensions": {"Communication Skills::Grammar": {"mean": 0.7}}},
        "group_summary": {"groups": {"TeamA": {"candidate": {"id": 123}}}},
    }

    with pytest.raises(ValueError):
        validate_cohort_report(report)
