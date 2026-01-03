import copy

from ppd.report.cohort_report import build_cohort_report


# ------------------------------------------------------------------
# build_cohort_report
# ------------------------------------------------------------------

# Builds report with metadata + cohort_summary (always)
def test_build_cohort_report_includes_metadata_and_cohort_summary():
    cohort_summary = {
        "dimensions": {
            "Grammar": {"mean": 0.7, "std_sample": 0.1, "breach_rate": 0.05},
            "Fluency": {"mean": 0.6, "std_sample": 0.2, "breach_rate": 0.10},
        }
    }

    report = build_cohort_report(
        cohort_summary=cohort_summary,
        group_summary=None,
        include_group_summary=False,
        version="0.1.0",
    )

    assert "metadata" in report
    assert "cohort_summary" in report
    assert report["cohort_summary"] == cohort_summary

    assert report["metadata"]["tool"] == "Profile Pattern Diagnostics (PPD)"
    assert report["metadata"]["axis"] == "across-candidate"
    assert report["metadata"]["version"] == "0.1.0"
    assert "generated_at_utc" in report["metadata"]
    assert "scope_note" in report["metadata"]


# Group summary key is omitted when include_group_summary=False
def test_build_cohort_report_omits_group_summary_when_disabled():
    cohort_summary = {"dimensions": {"Grammar": {"mean": 0.7}}}
    group_summary = {"groups": {"TeamA": {"Grammar": {"mean": 0.75}}}}

    report = build_cohort_report(
        cohort_summary=cohort_summary,
        group_summary=group_summary,
        include_group_summary=False,
    )

    assert "group_summary" not in report


# Group summary key exists when enabled, even if None
def test_build_cohort_report_group_summary_is_none_when_missing():
    cohort_summary = {"dimensions": {"Grammar": {"mean": 0.7}}}

    report = build_cohort_report(
        cohort_summary=cohort_summary,
        group_summary=None,
        include_group_summary=True,
    )

    assert "group_summary" in report
    assert report["group_summary"] is None


# Group summary is included when enabled and provided
def test_build_cohort_report_includes_group_summary_when_enabled():
    cohort_summary = {"dimensions": {"Grammar": {"mean": 0.7}}}
    group_summary = {"groups": {"TeamA": {"Grammar": {"mean": 0.75}}}}

    report = build_cohort_report(
        cohort_summary=cohort_summary,
        group_summary=group_summary,
        include_group_summary=True,
    )

    assert "group_summary" in report
    assert report["group_summary"] == group_summary


# Report does not mutate the provided cohort_summary dict
def test_build_cohort_report_does_not_mutate_cohort_summary():
    cohort_summary = {
        "dimensions": {
            "Grammar": {"mean": 0.7, "std_sample": 0.1, "breach_rate": 0.05},
        }
    }
    cohort_summary_before = copy.deepcopy(cohort_summary)

    report = build_cohort_report(
        cohort_summary=cohort_summary,
        group_summary=None,
        include_group_summary=False,
    )

    assert cohort_summary == cohort_summary_before
    assert report["cohort_summary"] == cohort_summary_before


# Report does not mutate the provided group_summary dict
def test_build_cohort_report_does_not_mutate_group_summary():
    cohort_summary = {"dimensions": {"Grammar": {"mean": 0.7}}}
    group_summary = {"groups": {"TeamA": {"Grammar": {"mean": 0.75}}}}

    group_summary_before = copy.deepcopy(group_summary)

    report = build_cohort_report(
        cohort_summary=cohort_summary,
        group_summary=group_summary,
        include_group_summary=True,
    )

    assert group_summary == group_summary_before
    assert report["group_summary"] == group_summary_before
