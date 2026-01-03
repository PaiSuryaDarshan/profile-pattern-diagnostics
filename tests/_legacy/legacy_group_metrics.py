# tests/test_group_metrics.py

import pandas as pd
import pytest

from ppd._legacy.cohort.group_metrics import summarize_groups


# ------------------------------------------------------------------
# summarize_groups
# ------------------------------------------------------------------

# Basic grouping works and excludes id_col + group_col from dimensions
def test_summarize_groups_basic_excludes_cols():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "team": "A", "X": 0.0, "Y": 1.0},
            {"candidate_id": "c2", "team": "A", "X": 1.0, "Y": 1.0},
            {"candidate_id": "c3", "team": "B", "X": 2.0, "Y": 3.0},
        ]
    )

    out = summarize_groups(df, group_col="team", id_col="candidate_id", threshold=1.0)

    assert out["group_col"] == "team"
    assert "A" in out["groups"]
    assert "B" in out["groups"]

    assert out["groups"]["A"]["n_candidates"] == 2
    assert out["groups"]["B"]["n_candidates"] == 1

    dims_A = out["groups"]["A"]["dimensions"]
    assert "candidate_id" not in dims_A
    assert "team" not in dims_A
    assert "X" in dims_A
    assert "Y" in dims_A

    # Group A: X = [0,1] -> mean 0.5
    assert dims_A["X"]["mean"] == pytest.approx(0.5)

    # Group A: breach_rate with threshold=1.0 -> values < 1.0 => [0] => 1/2
    assert dims_A["X"]["breach_rate"] == pytest.approx(0.5)

    # Group B: single candidate => std_sample None
    dims_B = out["groups"]["B"]["dimensions"]
    assert dims_B["X"]["std_sample"] is None
    assert dims_B["Y"]["std_sample"] is None


# Threshold None -> breach_rate None
def test_summarize_groups_threshold_none_sets_breach_rate_none():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "team": "A", "X": 0.0},
            {"candidate_id": "c2", "team": "A", "X": 1.0},
        ]
    )

    out = summarize_groups(df, group_col="team", id_col="candidate_id", threshold=None)

    assert out["groups"]["A"]["dimensions"]["X"]["breach_rate"] is None


# Missing group column raises
def test_summarize_groups_missing_group_col_raises():
    df = pd.DataFrame([{"candidate_id": "c1", "X": 1.0}])

    with pytest.raises(ValueError):
        summarize_groups(df, group_col="team", id_col="candidate_id")


# Non-numeric values raise
def test_summarize_groups_non_numeric_raises():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "team": "A", "X": "nope"},
            {"candidate_id": "c2", "team": "A", "X": "still nope"},
        ]
    )

    with pytest.raises(Exception):
        summarize_groups(df, group_col="team", id_col="candidate_id")
