###
# Note to maintainers:
# This test is not about:
#  - correctness of metrics
#  - thresholds
#  - interpretation
# Those are already tested elsewhere.
# 
# It is only about this contract:
#  - Can data go in → be read → be written → be read again
#     without corruption or silent shape changes?
# 
# That’s why i called it a called roundtrip here.
###

import json
from pathlib import Path

import pandas as pd
import pytest

from ppd.io import (
    read_candidate_csv,
    read_candidate_json,
    read_cohort_csv,
    write_csv,
    write_json,
)


# ------------------------------------------------------------------
# Candidate IO (CSV / JSON)
# ------------------------------------------------------------------

# Reads long-form candidate CSV (dimension, score) into {dimension: float}
def test_read_candidate_csv_long_form(tmp_path: Path):
    p = tmp_path / "candidate_long.csv"
    p.write_text(
        "dimension,score\n"
        "Grammar,4\n"
        "Fluency,3.5\n"
        "Coherence,5\n",
        encoding="utf-8",
    )

    scores = read_candidate_csv(str(p))

    assert scores["Grammar"] == pytest.approx(4.0)
    assert scores["Fluency"] == pytest.approx(3.5)
    assert scores["Coherence"] == pytest.approx(5.0)


# Reads wide-form candidate CSV (one row, columns are dimensions) into {dimension: float}
def test_read_candidate_csv_wide_form(tmp_path: Path):
    p = tmp_path / "candidate_wide.csv"
    p.write_text(
        "Grammar,Fluency,Coherence\n"
        "4,3.5,5\n",
        encoding="utf-8",
    )

    scores = read_candidate_csv(str(p))

    assert scores["Grammar"] == pytest.approx(4.0)
    assert scores["Fluency"] == pytest.approx(3.5)
    assert scores["Coherence"] == pytest.approx(5.0)


# Reads wide-form candidate CSV that includes an ID column (skips id_col)
def test_read_candidate_csv_wide_form_with_id_col(tmp_path: Path):
    p = tmp_path / "candidate_wide_id.csv"
    p.write_text(
        "candidate_id,Grammar,Fluency,Coherence\n"
        "c1,4,3.5,5\n",
        encoding="utf-8",
    )

    scores = read_candidate_csv(str(p), id_col="candidate_id")

    assert "candidate_id" not in scores
    assert scores["Grammar"] == pytest.approx(4.0)
    assert scores["Fluency"] == pytest.approx(3.5)
    assert scores["Coherence"] == pytest.approx(5.0)


# Reads simple JSON mapping {"A": 3.0, ...} into {dimension: float}
def test_read_candidate_json_simple_mapping(tmp_path: Path):
    p = tmp_path / "candidate.json"
    p.write_text(
        json.dumps({"Grammar": 4, "Fluency": 3.5, "Coherence": 5}),
        encoding="utf-8",
    )

    scores = read_candidate_json(str(p))

    assert scores["Grammar"] == pytest.approx(4.0)
    assert scores["Fluency"] == pytest.approx(3.5)
    assert scores["Coherence"] == pytest.approx(5.0)


# Reads nested JSON {"scores": {...}} into {dimension: float}
def test_read_candidate_json_nested_scores(tmp_path: Path):
    p = tmp_path / "candidate_nested.json"
    p.write_text(
        json.dumps({"scores": {"Grammar": 4, "Fluency": 3.5, "Coherence": 5}}),
        encoding="utf-8",
    )

    scores = read_candidate_json(str(p))

    assert scores["Grammar"] == pytest.approx(4.0)
    assert scores["Fluency"] == pytest.approx(3.5)
    assert scores["Coherence"] == pytest.approx(5.0)


# Candidate JSON roundtrip: write_json then read_candidate_json preserves values
def test_candidate_json_roundtrip(tmp_path: Path):
    original = {"Grammar": 4.0, "Fluency": 3.5, "Coherence": 5.0}

    p = tmp_path / "roundtrip.json"
    write_json(str(p), original)

    scores = read_candidate_json(str(p))

    assert scores["Grammar"] == pytest.approx(4.0)
    assert scores["Fluency"] == pytest.approx(3.5)
    assert scores["Coherence"] == pytest.approx(5.0)


# ------------------------------------------------------------------
# Cohort IO (CSV <-> DataFrame)
# ------------------------------------------------------------------

# Reads cohort CSV into a DataFrame with expected columns and shape
def test_read_cohort_csv(tmp_path: Path):
    p = tmp_path / "cohort.csv"
    p.write_text(
        "candidate_id,Grammar,Fluency,Coherence\n"
        "c1,4,3.5,5\n"
        "c2,2,4,3\n",
        encoding="utf-8",
    )

    df = read_cohort_csv(str(p))

    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 2
    assert "candidate_id" in df.columns
    assert "Grammar" in df.columns
    assert "Fluency" in df.columns
    assert "Coherence" in df.columns


# Cohort CSV roundtrip: write_csv then read_cohort_csv preserves columns and rows
def test_cohort_csv_roundtrip(tmp_path: Path):
    df_original = pd.DataFrame(
        [
            {"candidate_id": "c1", "Grammar": 4.0, "Fluency": 3.5, "Coherence": 5.0},
            {"candidate_id": "c2", "Grammar": 2.0, "Fluency": 4.0, "Coherence": 3.0},
        ]
    )

    p = tmp_path / "cohort_roundtrip.csv"
    write_csv(str(p), df_original, index=False)

    df_loaded = read_cohort_csv(str(p))

    assert list(df_loaded.columns) == list(df_original.columns)
    assert df_loaded.shape == df_original.shape

    # compare row-wise values (explicit, no fancy helpers)
    assert df_loaded.iloc[0]["candidate_id"] == "c1"
    assert float(df_loaded.iloc[0]["Grammar"]) == pytest.approx(4.0)
    assert float(df_loaded.iloc[0]["Fluency"]) == pytest.approx(3.5)
    assert float(df_loaded.iloc[0]["Coherence"]) == pytest.approx(5.0)

    assert df_loaded.iloc[1]["candidate_id"] == "c2"
    assert float(df_loaded.iloc[1]["Grammar"]) == pytest.approx(2.0)
    assert float(df_loaded.iloc[1]["Fluency"]) == pytest.approx(4.0)
    assert float(df_loaded.iloc[1]["Coherence"]) == pytest.approx(3.0)
