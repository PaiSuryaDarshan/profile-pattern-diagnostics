import sqlite3

import pytest

from ppd.cohort.candidate_pass import (
    fetch_candidate_ids,
    fetch_scores_long,
    build_candidate_payload,
    run_candidate_analysis,
)


# ------------------------------------------------------------------
# fetch_candidate_ids
# ------------------------------------------------------------------

# Returns candidate IDs sorted alphabetically
def test_fetch_candidate_ids_returns_sorted_ids():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    db.execute("CREATE TABLE candidates (candidate_id TEXT PRIMARY KEY);")
    db.executemany(
        "INSERT INTO candidates(candidate_id) VALUES (?);",
        [("C002",), ("C001",)],
    )

    ids = fetch_candidate_ids(db)

    assert ids == ["C001", "C002"]


# ------------------------------------------------------------------
# fetch_scores_long
# ------------------------------------------------------------------

# Joins scores and dimensions into a long-form view
def test_fetch_scores_long_returns_joined_rows():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    db.execute("CREATE TABLE candidates (candidate_id TEXT PRIMARY KEY);")
    db.execute(
        """
        CREATE TABLE dimensions (
            dimension_key TEXT PRIMARY KEY,
            group_key TEXT,
            dimension_name TEXT
        );
        """
    )
    db.execute(
        """
        CREATE TABLE scores (
            candidate_id TEXT,
            dimension_key TEXT,
            raw_score REAL,
            norm_score REAL
        );
        """
    )

    db.execute("INSERT INTO candidates VALUES ('C001');")
    db.execute("INSERT INTO dimensions VALUES ('g::d', 'g', 'D');")
    db.execute("INSERT INTO scores VALUES ('C001', 'g::d', 4.0, 0.8);")

    rows = fetch_scores_long(db)

    assert len(rows) == 1
    r = rows[0]
    assert r["candidate_id"] == "C001"
    assert r["dimension_key"] == "g::d"
    assert r["group_key"] == "g"
    assert r["raw_score"] == 4.0
    assert r["norm_score"] == 0.8


# ------------------------------------------------------------------
# build_candidate_payload
# ------------------------------------------------------------------

# Builds a flat payload for a single candidate
def test_build_candidate_payload_filters_to_candidate():
    rows = [
        {"candidate_id": "C001", "dimension_key": "a::x", "raw_score": 4.5},
        {"candidate_id": "C001", "dimension_key": "a::y", "raw_score": 4.0},
        {"candidate_id": "C002", "dimension_key": "a::x", "raw_score": 2.0},
    ]

    payload = build_candidate_payload(rows, "C001")

    assert payload["candidate"]["id"] == "C001"
    assert payload["scores"] == {
        "a::x": 4.5,
        "a::y": 4.0,
    }


# ------------------------------------------------------------------
# run_candidate_analysis
# ------------------------------------------------------------------

# Flattens nested scores before calling analyze_candidate
def test_run_candidate_analysis_flattens_nested_scores(monkeypatch):
    captured = {}

    def fake_analyze(scores):
        captured["scores"] = scores
        return {"ok": True}

    monkeypatch.setattr(
        "ppd.cohort.candidate_pass.analyze_candidate",
        fake_analyze,
    )

    payload = {
        "scores": {
            "group1": {
                "dim1": 4.0,
                "dim2": 3.5,
            }
        }
    }

    result = run_candidate_analysis(payload)

    assert result["ok"] is True
    assert captured["scores"] == {
        "group1::dim1": 4.0,
        "group1::dim2": 3.5,
    }


# Ensures flat scores are passed through and coerced to float
def test_run_candidate_analysis_accepts_flat_scores():
    captured = {}

    def fake_analyze(scores):
        captured["scores"] = scores
        return {"ok": True}

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "ppd.cohort.candidate_pass.analyze_candidate",
        fake_analyze,
    )

    payload = {"scores": {"a::b": 5, "c::d": "4.2"}}
    run_candidate_analysis(payload)

    assert captured["scores"]["a::b"] == 5.0
    assert captured["scores"]["c::d"] == 4.2

    monkeypatch.undo()
