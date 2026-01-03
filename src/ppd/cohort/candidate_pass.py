# ------------------------------------------------------------
# Latest Feature added in  1.1.2 || Cohort Analysis
# ------------------------------------------------------------
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List

from ppd.candidate.analyze import analyze_candidate


GROUPS_ORDER = [
    "communication_skills",
    "cognitive_insights",
    "analytical_quantitative_skills",
    "problem_structuring_framework_use",
    "execution_task_reliability",
    "collaboration_professional_interaction",
]


def create_candidate_output_tables(dst: sqlite3.Connection, *, store_json_reports: bool) -> None:
    """
    Candidate-derived outputs:
      - candidate_reports (optional JSON audit)
      - candidate_group_metrics (flat)
      - candidate_group_patterns (flat)
    """
    if store_json_reports:
        dst.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_reports (
                candidate_id TEXT PRIMARY KEY,
                generated_at_utc TEXT NOT NULL,
                report_json TEXT NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
            );
            """
        )

    dst.execute(
        """
        CREATE TABLE IF NOT EXISTS candidate_group_metrics (
            candidate_id TEXT NOT NULL,
            group_key TEXT NOT NULL,

            mean REAL,
            std_pop REAL,
            min REAL,
            max REAL,
            range REAL,
            n_dimensions INTEGER,

            min_dimensions_json TEXT,
            max_dimensions_json TEXT,

            PRIMARY KEY (candidate_id, group_key),
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE IF NOT EXISTS candidate_group_patterns (
            candidate_id TEXT NOT NULL,
            group_key TEXT NOT NULL,

            balanced INTEGER,
            bottlenecked INTEGER,
            polarised INTEGER,
            noisy INTEGER,
            uniform_low INTEGER,
            uniform_high INTEGER,

            bottleneck_dimension TEXT,
            bottleneck_value REAL,
            bottleneck_dimensions_json TEXT,

            PRIMARY KEY (candidate_id, group_key),
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
        );
        """
    )

    dst.execute("CREATE INDEX IF NOT EXISTS idx_cgm_group ON candidate_group_metrics(group_key);")
    dst.execute("CREATE INDEX IF NOT EXISTS idx_cgp_group ON candidate_group_patterns(group_key);")


def fetch_candidate_ids(src: sqlite3.Connection) -> List[str]:
    rows = src.execute("SELECT candidate_id FROM candidates ORDER BY candidate_id;").fetchall()
    return [r["candidate_id"] for r in rows]


def fetch_scores_long(src: sqlite3.Connection) -> List[sqlite3.Row]:
    """
    Returns a long joined view needed for payload building and cohort stats.
    Expects:
      scores(candidate_id, dimension_key, raw_score, norm_score)
      dimensions(dimension_key, group_key, dimension_name)
    """
    return src.execute(
        """
        SELECT
            s.candidate_id,
            s.dimension_key,
            s.raw_score,
            s.norm_score,
            d.group_key,
            d.dimension_name
        FROM scores s
        JOIN dimensions d ON d.dimension_key = s.dimension_key
        ORDER BY s.candidate_id, d.group_key, d.dimension_name;
        """
    ).fetchall()


def build_candidate_payload(scores_rows: List[sqlite3.Row], candidate_id: str) -> dict:
    """
    Builds the payload expected by ppd.candidate.analyze.analyze_candidate:

      {
        "candidate": {"id": "<candidate_id>"},
        "scores": {
          "group_key::dimension_name": raw_score_1_to_5,
          ...
        }
      }
    """
    flat_scores: Dict[str, float] = {}

    for r in scores_rows:
        if r["candidate_id"] != candidate_id:
            continue
        flat_scores[r["dimension_key"]] = float(r["raw_score"])

    return {"candidate": {"id": candidate_id}, "scores": flat_scores}

def run_candidate_analysis(payload: dict) -> dict:
    """
    Calls your canonical candidate pipeline.

    Candidate analyzer expects:
      payload["scores"] == { "group::dimension": float, ... }

    This adapter accepts either:
      - flat scores dict, or
      - nested scores dict {group: {dimension: float}}
    and normalises to the flat form.

    Adapter: Accept either flat or nested score payloads, then call
    ppd.candidate.analyze.analyze_candidate(raw_scores).
    """

    scores = payload.get("scores", {})

    # If nested {group: {dim: v}}, flatten to {"group::dim": v}
    if isinstance(scores, dict) and scores:
        first_val = next(iter(scores.values()))
        if isinstance(first_val, dict):
            flat = {}
            for g, dims in scores.items():
                if not isinstance(dims, dict):
                    continue
                for dim, v in dims.items():
                    flat[f"{g}::{dim}"] = float(v)
            scores = flat

    # If already flat, just ensure float conversion
    if isinstance(scores, dict):
        scores = {k: float(v) for k, v in scores.items()}

    return analyze_candidate(scores)

def write_candidate_outputs(
    dst: sqlite3.Connection,
    *,
    candidate_id: str,
    report: dict,
    store_json_reports: bool,
) -> None:
    """
    Persists candidate report into:
      - candidate_reports (optional JSON)
      - candidate_group_metrics
      - candidate_group_patterns

    Supports BOTH report shapes:
      A) Flat candidate report (current analyze_candidate output):
         report["metrics_by_group"], report["patterns_by_group"]

      B) Wrapped report (older style):
         report["analysis"]["metrics_by_group"], report["analysis"]["patterns_by_group"]
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if store_json_reports:
        dst.execute(
            """
            INSERT OR REPLACE INTO candidate_reports (candidate_id, generated_at_utc, report_json)
            VALUES (?, ?, ?);
            """,
            (candidate_id, now, json.dumps(report, ensure_ascii=False)),
        )

    # --- support both shapes ---
    analysis = report.get("analysis")
    if isinstance(analysis, dict):
        metrics_by_group = analysis.get("metrics_by_group") or {}
        patterns_by_group = analysis.get("patterns_by_group") or {}
    else:
        metrics_by_group = report.get("metrics_by_group") or {}
        patterns_by_group = report.get("patterns_by_group") or {}

    # Metrics table
    for group_key, m in metrics_by_group.items():
        dst.execute(
            """
            INSERT OR REPLACE INTO candidate_group_metrics (
                candidate_id, group_key,
                mean, std_pop, min, max, range, n_dimensions,
                min_dimensions_json, max_dimensions_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                candidate_id,
                group_key,
                m.get("mean"),
                m.get("std_pop"),
                m.get("min"),
                m.get("max"),
                m.get("range"),
                m.get("n_dimensions"),
                json.dumps(m.get("min_dimensions"), ensure_ascii=False),
                json.dumps(m.get("max_dimensions"), ensure_ascii=False),
            ),
        )

    # Patterns table
    if patterns_by_group is None:
        return

    for group_key, p in patterns_by_group.items():
        dst.execute(
            """
            INSERT OR REPLACE INTO candidate_group_patterns (
                candidate_id, group_key,
                balanced, bottlenecked, polarised, noisy, uniform_low, uniform_high,
                bottleneck_dimension, bottleneck_value, bottleneck_dimensions_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                candidate_id,
                group_key,
                int(bool(p.get("balanced"))),
                int(bool(p.get("bottlenecked"))),
                int(bool(p.get("polarised"))),
                int(bool(p.get("noisy"))),
                int(bool(p.get("uniform_low"))),
                int(bool(p.get("uniform_high"))),
                p.get("bottleneck_dimension"),
                p.get("bottleneck_value"),
                json.dumps(p.get("bottleneck_dimensions"), ensure_ascii=False),
            ),
        )
