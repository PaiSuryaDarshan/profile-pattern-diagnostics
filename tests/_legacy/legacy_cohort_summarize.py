import pandas as pd
import pytest

from ppd.cohort.summarize import summarize_cohort


# Summarize cohort without groups
def test_summarize_cohort_without_groups():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "A": 0.0, "B": 1.0},
            {"candidate_id": "c2", "A": 1.0, "B": 1.0},
            {"candidate_id": "c3", "A": 2.0, "B": 3.0},
        ]
    )

    report = summarize_cohort(
        df,
        id_col="candidate_id",
        group_col=None,
        threshold=1.0,
        include_percentiles=False,
        include_group_summary=False,
        validate_report=True,
    )

    assert report["metadata"]["axis"] == "across-candidate"
    assert "cohort_summary" in report
    assert "dimensions" in report["cohort_summary"]
    assert "A" in report["cohort_summary"]["dimensions"]
    assert "B" in report["cohort_summary"]["dimensions"]
    assert "group_summary" not in report


# Summarize cohort with groups
def test_summarize_cohort_with_groups_mean():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "team": "A", "X": 1.0, "Y": 2.0},
            {"candidate_id": "c2", "team": "A", "X": 3.0, "Y": 4.0},
            {"candidate_id": "c3", "team": "B", "X": 10.0, "Y": 20.0},
        ]
    )

    report = summarize_cohort(
        df,
        id_col="candidate_id",
        group_col="team",
        threshold=None,
        include_percentiles=False,
        include_group_summary=True,
        group_method="mean",
        validate_report=True,
    )

    assert report["metadata"]["axis"] == "across-candidate"
    assert "cohort_summary" in report
    assert "group_summary" in report
    assert report["group_summary"] is not None
    assert "groups" in report["group_summary"]
    assert "A" in report["group_summary"]["groups"]
    assert "B" in report["group_summary"]["groups"]

    assert report["group_summary"]["groups"]["A"]["dimensions"]["X"]["mean"] == pytest.approx(2.0)
    assert report["group_summary"]["groups"]["A"]["dimensions"]["Y"]["mean"] == pytest.approx(3.0)


# Percentiles can be included
def test_summarize_cohort_with_percentiles():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "A": 0.0},
            {"candidate_id": "c2", "A": 1.0},
            {"candidate_id": "c3", "A": 2.0},
            {"candidate_id": "c4", "A": 3.0},
            {"candidate_id": "c5", "A": 4.0},
        ]
    )

    report = summarize_cohort(
        df,
        id_col="candidate_id",
        group_col=None,
        threshold=None,
        include_percentiles=True,
        include_group_summary=False,
        validate_report=True,
    )

    assert report["cohort_summary"]["dimensions"]["A"]["percentiles"] is not None
    assert "p50" in report["cohort_summary"]["dimensions"]["A"]["percentiles"]
    assert report["cohort_summary"]["dimensions"]["A"]["percentiles"]["p50"] == pytest.approx(2.0)
