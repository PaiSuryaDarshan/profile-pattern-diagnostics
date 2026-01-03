# ------------------------------------------------------------
# Latest Feature added in  1.1.2 || Cohort Analysis
# ------------------------------------------------------------
# Materialise PPD outputs:
# Input SQLite DB (raw cohort) -> Output SQLite DB (enriched)
#
# Output DB contains:
# - copied inputs (candidates, dimensions, scores)
# - candidate outputs (group metrics + patterns + optional JSON report)
# - cohort outputs (dimension/group summaries, percentile ranks, breach rates, prevalence)
#
# ------------------------------------------------------------

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from ppd.candidate.analyze import analyze_candidate

import numpy as np


# --------------------
# Config
# --------------------
HERE = Path(__file__).resolve().parent

IN_DB = HERE / "cohort_diverse_example.db"
OUT_DB = HERE / "cohort_diverse_final.db"

STORE_JSON_REPORTS = True

GROUPS_ORDER = [
    "communication_skills",
    "cognitive_insights",
    "analytical_quantitative_skills",
    "problem_structuring_framework_use",
    "execution_task_reliability",
    "collaboration_professional_interaction",
]

# Thresholds (example names; align these with your policy module later)
TAUS = {
    "tau_operational": 0.60,   # on norm scale [0,1]
    "tau_high": 0.80,
    "tau_low": 0.40,
}


# --------------------
# Plug candidate analysis here
# --------------------
def run_candidate_analysis(payload: dict) -> dict:
    """
    payload:
      {
        "candidate": {"id": "..."},
        "scores": {
            group_key: {dimension_name: raw_score_1_to_5, ...},
            ...
        }
      }

    Returns:
      Full candidate analysis report dict produced by ppd.candidate.analyze
    """

    return analyze_candidate(payload)


# --------------------
# DB helpers
# --------------------
def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def copy_table(src: sqlite3.Connection, dst: sqlite3.Connection, table: str):
    schema = src.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table,)
    ).fetchone()
    if not schema or not schema["sql"]:
        raise RuntimeError(f"Table not found in source DB: {table}")

    dst.execute(schema["sql"])

    rows = src.execute(f"SELECT * FROM {table};").fetchall()
    if rows:
        colnames = rows[0].keys()
        placeholders = ",".join(["?"] * len(colnames))
        dst.executemany(
            f"INSERT INTO {table} ({','.join(colnames)}) VALUES ({placeholders});",
            [tuple(r[c] for c in colnames) for r in rows],
        )


def create_metadata_table(dst: sqlite3.Connection):
    dst.execute(
        """
        CREATE TABLE db_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )


def set_metadata(dst: sqlite3.Connection, kv: Dict[str, str]):
    dst.executemany(
        "INSERT INTO db_metadata (key, value) VALUES (?, ?);",
        list(kv.items()),
    )


def create_candidate_output_tables(dst: sqlite3.Connection):
    if STORE_JSON_REPORTS:
        dst.execute(
            """
            CREATE TABLE candidate_reports (
                candidate_id TEXT PRIMARY KEY,
                generated_at_utc TEXT NOT NULL,
                report_json TEXT NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
            );
            """
        )

    dst.execute(
        """
        CREATE TABLE candidate_group_metrics (
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
        CREATE TABLE candidate_group_patterns (
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


def create_cohort_output_tables(dst: sqlite3.Connection):
    dst.execute(
        """
        CREATE TABLE cohort_dimension_summary (
            dimension_key TEXT PRIMARY KEY,

            mean REAL,
            median REAL,
            std REAL,
            iqr REAL,
            min REAL,
            max REAL,

            p10 REAL,
            p25 REAL,
            p50 REAL,
            p75 REAL,
            p90 REAL
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_candidate_dimension_percentiles (
            candidate_id TEXT NOT NULL,
            dimension_key TEXT NOT NULL,
            raw_score REAL NOT NULL,
            norm_score REAL NOT NULL,
            percentile_rank REAL NOT NULL,

            PRIMARY KEY (candidate_id, dimension_key),
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
            FOREIGN KEY (dimension_key) REFERENCES dimensions(dimension_key)
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_candidate_group_scores (
            candidate_id TEXT NOT NULL,
            group_key TEXT NOT NULL,
            group_score_norm REAL NOT NULL,

            PRIMARY KEY (candidate_id, group_key),
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_group_summary (
            group_key TEXT PRIMARY KEY,

            mean REAL,
            median REAL,
            std REAL,
            iqr REAL,
            min REAL,
            max REAL,

            p10 REAL,
            p25 REAL,
            p50 REAL,
            p75 REAL,
            p90 REAL
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_candidate_group_percentiles (
            candidate_id TEXT NOT NULL,
            group_key TEXT NOT NULL,
            group_score_norm REAL NOT NULL,
            percentile_rank REAL NOT NULL,

            PRIMARY KEY (candidate_id, group_key),
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_dimension_breach_rates (
            dimension_key TEXT NOT NULL,
            tau_name TEXT NOT NULL,
            tau_value REAL NOT NULL,
            breach_rate REAL NOT NULL,

            PRIMARY KEY (dimension_key, tau_name),
            FOREIGN KEY (dimension_key) REFERENCES dimensions(dimension_key)
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_group_breach_rates (
            group_key TEXT NOT NULL,
            tau_name TEXT NOT NULL,
            tau_value REAL NOT NULL,
            breach_rate REAL NOT NULL,

            PRIMARY KEY (group_key, tau_name)
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_pattern_prevalence_overall (
            pattern_label TEXT PRIMARY KEY,
            count INTEGER NOT NULL,
            proportion REAL NOT NULL
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE cohort_pattern_prevalence_by_group (
            group_key TEXT NOT NULL,
            pattern_label TEXT NOT NULL,
            count INTEGER NOT NULL,
            proportion REAL NOT NULL,

            PRIMARY KEY (group_key, pattern_label)
        );
        """
    )


def fetch_candidate_ids(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("SELECT candidate_id FROM candidates ORDER BY candidate_id;").fetchall()
    return [r["candidate_id"] for r in rows]


def fetch_scores_long(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
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
    # scores[group_key][dimension_name] = raw_score
    scores: Dict[str, Dict[str, float]] = {g: {} for g in GROUPS_ORDER}
    for r in scores_rows:
        if r["candidate_id"] != candidate_id:
            continue
        scores.setdefault(r["group_key"], {})
        scores[r["group_key"]][r["dimension_name"]] = float(r["raw_score"])

    return {"candidate": {"id": candidate_id}, "scores": scores}


def write_candidate_outputs(dst: sqlite3.Connection, candidate_id: str, report: dict):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if STORE_JSON_REPORTS:
        dst.execute(
            """
            INSERT INTO candidate_reports (candidate_id, generated_at_utc, report_json)
            VALUES (?, ?, ?);
            """,
            (candidate_id, now, json.dumps(report, ensure_ascii=False)),
        )

    analysis = report.get("analysis", {})
    metrics_by_group = (analysis.get("metrics_by_group") or {})
    patterns_by_group = (analysis.get("patterns_by_group") or {})

    for group_key, m in metrics_by_group.items():
        dst.execute(
            """
            INSERT INTO candidate_group_metrics (
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

    for group_key, p in patterns_by_group.items():
        dst.execute(
            """
            INSERT INTO candidate_group_patterns (
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


# --------------------
# Cohort computations (numpy)
# --------------------
def _summary_stats(x: np.ndarray) -> Dict[str, float]:
    x = np.asarray(x, dtype=float)
    return {
        "mean": float(np.mean(x)),
        "median": float(np.median(x)),
        "std": float(np.std(x, ddof=0)),
        "iqr": float(np.percentile(x, 75) - np.percentile(x, 25)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "p10": float(np.percentile(x, 10)),
        "p25": float(np.percentile(x, 25)),
        "p50": float(np.percentile(x, 50)),
        "p75": float(np.percentile(x, 75)),
        "p90": float(np.percentile(x, 90)),
    }


def _percentile_rank(values: np.ndarray) -> np.ndarray:
    """
    Returns percentile ranks in [0,100] using midrank for ties.
    """
    v = np.asarray(values, dtype=float)
    order = np.argsort(v)
    ranks = np.empty_like(order, dtype=float)

    sorted_v = v[order]
    n = len(v)

    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_v[j + 1] == sorted_v[i]:
            j += 1
        # midrank (1-indexed ranks)
        mid = (i + 1 + j + 1) / 2.0
        ranks[order[i : j + 1]] = mid
        i = j + 1

    return (ranks - 1.0) / (n - 1.0) * 100.0 if n > 1 else np.array([100.0])


def compute_and_write_cohort(dst: sqlite3.Connection, scores_rows: List[sqlite3.Row]):
    # ---- build arrays by dimension_key ----
    by_dim: Dict[str, List[Tuple[str, float, float]]] = {}
    by_group_candidate: Dict[Tuple[str, str], List[float]] = {}

    for r in scores_rows:
        cid = r["candidate_id"]
        dim_key = r["dimension_key"]
        g = r["group_key"]
        raw = float(r["raw_score"])
        norm = float(r["norm_score"])

        by_dim.setdefault(dim_key, []).append((cid, raw, norm))
        by_group_candidate.setdefault((cid, g), []).append(norm)

    # ---- dimension summary + percentiles ----
    for dim_key, rows in by_dim.items():
        norms = np.array([t[2] for t in rows], dtype=float)
        stats = _summary_stats(norms)
        dst.execute(
            """
            INSERT INTO cohort_dimension_summary
            (dimension_key, mean, median, std, iqr, min, max, p10, p25, p50, p75, p90)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (dim_key, stats["mean"], stats["median"], stats["std"], stats["iqr"],
             stats["min"], stats["max"], stats["p10"], stats["p25"], stats["p50"], stats["p75"], stats["p90"]),
        )

        pr = _percentile_rank(norms)
        for (cid, raw, norm), pr_i in zip(rows, pr):
            dst.execute(
                """
                INSERT INTO cohort_candidate_dimension_percentiles
                (candidate_id, dimension_key, raw_score, norm_score, percentile_rank)
                VALUES (?, ?, ?, ?, ?);
                """,
                (cid, dim_key, raw, norm, float(pr_i)),
            )

        # breach rates per tau
        for tau_name, tau_val in TAUS.items():
            breach_rate = float(np.mean(norms < tau_val))
            dst.execute(
                """
                INSERT INTO cohort_dimension_breach_rates
                (dimension_key, tau_name, tau_value, breach_rate)
                VALUES (?, ?, ?, ?);
                """,
                (dim_key, tau_name, float(tau_val), breach_rate),
            )

    # ---- group scores per candidate ----
    group_scores: Dict[str, List[float]] = {g: [] for g in GROUPS_ORDER}
    group_rows: List[Tuple[str, str, float]] = []

    for (cid, g), vals in by_group_candidate.items():
        gs = float(np.mean(np.array(vals, dtype=float)))
        group_rows.append((cid, g, gs))
        group_scores.setdefault(g, []).append(gs)

        dst.execute(
            """
            INSERT INTO cohort_candidate_group_scores (candidate_id, group_key, group_score_norm)
            VALUES (?, ?, ?);
            """,
            (cid, g, gs),
        )

    # ---- group summary + group percentiles ----
    for g, vals in group_scores.items():
        if not vals:
            continue
        arr = np.array(vals, dtype=float)
        stats = _summary_stats(arr)
        dst.execute(
            """
            INSERT INTO cohort_group_summary
            (group_key, mean, median, std, iqr, min, max, p10, p25, p50, p75, p90)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (g, stats["mean"], stats["median"], stats["std"], stats["iqr"],
             stats["min"], stats["max"], stats["p10"], stats["p25"], stats["p50"], stats["p75"], stats["p90"]),
        )

        # breach rates per group per tau
        for tau_name, tau_val in TAUS.items():
            breach_rate = float(np.mean(arr < tau_val))
            dst.execute(
                """
                INSERT INTO cohort_group_breach_rates
                (group_key, tau_name, tau_value, breach_rate)
                VALUES (?, ?, ?, ?);
                """,
                (g, tau_name, float(tau_val), breach_rate),
            )

        # percentile ranks within group
        # compute ranks over all candidates for this group
        # then write candidate rows
        # gather candidate list for this group
        cids = [cid for (cid, gg, _) in group_rows if gg == g]
        gvals = np.array([v for (cid, gg, v) in group_rows if gg == g], dtype=float)
        pr = _percentile_rank(gvals)
        for cid, v, pr_i in zip(cids, gvals, pr):
            dst.execute(
                """
                INSERT INTO cohort_candidate_group_percentiles
                (candidate_id, group_key, group_score_norm, percentile_rank)
                VALUES (?, ?, ?, ?);
                """,
                (cid, g, float(v), float(pr_i)),
            )


def compute_and_write_prevalence(dst: sqlite3.Connection):
    """
    Pattern prevalence is computed from candidate_group_patterns, which we already wrote.
    We pick ONE label per row (priority order).
    """
    rows = dst.execute(
        """
        SELECT group_key,
               balanced, bottlenecked, polarised, noisy, uniform_low, uniform_high
        FROM candidate_group_patterns;
        """
    ).fetchall()

    # priority order (you can adjust)
    def label(r) -> str:
        if r["bottlenecked"]: return "bottlenecked"
        if r["polarised"]: return "polarised"
        if r["noisy"]: return "noisy"
        if r["uniform_low"]: return "uniform_low"
        if r["uniform_high"]: return "uniform_high"
        if r["balanced"]: return "balanced"
        return "other"

    overall_counts: Dict[str, int] = {}
    by_group_counts: Dict[Tuple[str, str], int] = {}

    for r in rows:
        g = r["group_key"]
        lab = label(r)
        overall_counts[lab] = overall_counts.get(lab, 0) + 1
        by_group_counts[(g, lab)] = by_group_counts.get((g, lab), 0) + 1

    total = sum(overall_counts.values()) or 1
    for lab, cnt in overall_counts.items():
        dst.execute(
            """
            INSERT INTO cohort_pattern_prevalence_overall (pattern_label, count, proportion)
            VALUES (?, ?, ?);
            """,
            (lab, cnt, cnt / total),
        )

    # per group
    # denominator: number of candidates rows for that group in patterns table
    group_totals: Dict[str, int] = {}
    for (g, lab), cnt in by_group_counts.items():
        group_totals[g] = group_totals.get(g, 0) + cnt

    for (g, lab), cnt in by_group_counts.items():
        denom = group_totals.get(g, 1)
        dst.execute(
            """
            INSERT INTO cohort_pattern_prevalence_by_group (group_key, pattern_label, count, proportion)
            VALUES (?, ?, ?, ?);
            """,
            (g, lab, cnt, cnt / denom),
        )


def main():
    if OUT_DB.exists():
        OUT_DB.unlink()

    src = connect(IN_DB)
    dst = connect(OUT_DB)

    try:
        # Copy base tables
        copy_table(src, dst, "candidates")
        copy_table(src, dst, "dimensions")
        copy_table(src, dst, "scores")

        # Create metadata + outputs
        create_metadata_table(dst)
        create_candidate_output_tables(dst)
        create_cohort_output_tables(dst)

        set_metadata(
            dst,
            {
                "tool": "Profile Pattern Diagnostics (PPD)",
                "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source_db": str(IN_DB.name),
            },
        )

        # Pull scores once
        scores_rows = fetch_scores_long(src)
        candidate_ids = fetch_candidate_ids(src)

        # Candidate pass
        for cid in candidate_ids:
            payload = build_candidate_payload(scores_rows, cid)
            report = run_candidate_analysis(payload)
            write_candidate_outputs(dst, cid, report)

        # Cohort pass
        compute_and_write_cohort(dst, scores_rows)

        # Prevalence pass (uses candidate_group_patterns)
        compute_and_write_prevalence(dst)

        dst.commit()
        print(f"✅ Final enriched DB written: {OUT_DB}")

    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
