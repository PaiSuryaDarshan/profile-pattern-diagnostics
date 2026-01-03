# tests/test_group_aggregation.py

import pandas as pd
import pytest

from ppd.cohort.group_aggregation import aggregate_by_group


# Aggregates by mean and ignores id_col
def test_aggregate_by_group_mean_basic():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "team": "A", "X": 1.0, "Y": 2.0},
            {"candidate_id": "c2", "team": "A", "X": 3.0, "Y": 4.0},
            {"candidate_id": "c3", "team": "B", "X": 10.0, "Y": 20.0},
        ]
    )

    out = aggregate_by_group(df, group_col="team", id_col="candidate_id", method="mean")

    assert out["group_col"] == "team"
    assert out["method"] == "mean"
    assert "groups" in out
    assert "A" in out["groups"]
    assert "B" in out["groups"]

    assert out["groups"]["A"]["n_candidates"] == 2
    assert out["groups"]["B"]["n_candidates"] == 1

    # Group A means: X=(1+3)/2=2, Y=(2+4)/2=3
    assert out["groups"]["A"]["dimensions"]["X"]["mean"] == pytest.approx(2.0)
    assert out["groups"]["A"]["dimensions"]["Y"]["mean"] == pytest.approx(3.0)

    # Group B means: X=10, Y=20
    assert out["groups"]["B"]["dimensions"]["X"]["mean"] == pytest.approx(10.0)
    assert out["groups"]["B"]["dimensions"]["Y"]["mean"] == pytest.approx(20.0)


# Aggregates by median
def test_aggregate_by_group_median_basic():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "team": "A", "X": 1.0},
            {"candidate_id": "c2", "team": "A", "X": 100.0},
            {"candidate_id": "c3", "team": "A", "X": 3.0},
        ]
    )

    out = aggregate_by_group(df, group_col="team", id_col="candidate_id", method="median")

    # Median of [1,100,3] = 3
    assert out["groups"]["A"]["dimensions"]["X"]["median"] == pytest.approx(3.0)


# Missing group_col should raise
def test_aggregate_by_group_missing_group_col_raises():
    df = pd.DataFrame([{"candidate_id": "c1", "X": 1.0}])

    with pytest.raises(ValueError):
        aggregate_by_group(df, group_col="team", id_col="candidate_id", method="mean")


# Unsupported method should raise
def test_aggregate_by_group_unsupported_method_raises():
    df = pd.DataFrame([{"candidate_id": "c1", "team": "A", "X": 1.0}])

    with pytest.raises(ValueError):
        aggregate_by_group(df, group_col="team", id_col="candidate_id", method="sum")


# Non-numeric dimension should raise
def test_aggregate_by_group_non_numeric_dimension_raises():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "team": "A", "X": "nope"},
            {"candidate_id": "c2", "team": "A", "X": "still nope"},
        ]
    )

    with pytest.raises(Exception):
        aggregate_by_group(df, group_col="team", id_col="candidate_id", method="mean")
