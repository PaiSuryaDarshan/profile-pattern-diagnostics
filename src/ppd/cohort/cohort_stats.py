# ------------------------------------------------------------
# Latest Feature added in  1.1.2 || Cohort Analysis
# ------------------------------------------------------------
from __future__ import annotations

import sqlite3
from typing import Dict, List, Tuple

import numpy as np


def create_cohort_output_tables(dst: sqlite3.Connection) -> None:
    dst.execute(
        """
        CREATE TABLE IF NOT EXISTS cohort_dimension_summary (
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
        CREATE TABLE IF NOT EXISTS cohort_candidate_dimension_percentiles (
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
        CREATE TABLE IF NOT EXISTS cohort_candidate_group_scores (
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
        CREATE TABLE IF NOT EXISTS cohort_group_summary (
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
        CREATE TABLE IF NOT EXISTS cohort_candidate_group_percentiles (
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
        CREATE TABLE IF NOT EXISTS cohort_dimension_breach_rates (
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
        CREATE TABLE IF NOT EXISTS cohort_group_breach_rates (
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
        CREATE TABLE IF NOT EXISTS cohort_pattern_prevalence_overall (
            pattern_label TEXT PRIMARY KEY,
            count INTEGER NOT NULL,
            proportion REAL NOT NULL
        );
        """
    )

    dst.execute(
        """
        CREATE TABLE IF NOT EXISTS cohort_pattern_prevalence_by_group (
            group_key TEXT NOT NULL,
            pattern_label TEXT NOT NULL,
            count INTEGER NOT NULL,
            proportion REAL NOT NULL,

            PRIMARY KEY (group_key, pattern_label)
        );
        """
    )


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
    Percentile ranks in [0,100] using midrank for ties.
    """
    v = np.asarray(values, dtype=float)
    n = len(v)
    if n == 0:
        return np.array([], dtype=float)
    if n == 1:
        return np.array([100.0], dtype=float)

    order = np.argsort(v)
    ranks = np.empty(n, dtype=float)
    sorted_v = v[order]

    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_v[j + 1] == sorted_v[i]:
            j += 1
        mid = (i + 1 + j + 1) / 2.0  # 1-indexed midrank
        ranks[order[i : j + 1]] = mid
        i = j + 1

    return (ranks - 1.0) / (n - 1.0) * 100.0


def compute_and_write_cohort(
    dst: sqlite3.Connection,
    *,
    scores_rows: List[sqlite3.Row],
    groups_order: List[str],
    taus: Dict[str, float],
) -> None:
    """
    Writes:
      - cohort_dimension_summary
      - cohort_candidate_dimension_percentiles
      - cohort_candidate_group_scores
      - cohort_group_summary
      - cohort_candidate_group_percentiles
      - breach rate tables
    """
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

    # Dimension summaries + dimension percentiles + dimension breach rates
    for dim_key, rows in by_dim.items():
        norms = np.array([t[2] for t in rows], dtype=float)
        stats = _summary_stats(norms)

        dst.execute(
            """
            INSERT OR REPLACE INTO cohort_dimension_summary
            (dimension_key, mean, median, std, iqr, min, max, p10, p25, p50, p75, p90)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                dim_key,
                stats["mean"], stats["median"], stats["std"], stats["iqr"],
                stats["min"], stats["max"],
                stats["p10"], stats["p25"], stats["p50"], stats["p75"], stats["p90"],
            ),
        )

        pr = _percentile_rank(norms)
        for (cid, raw, norm), pr_i in zip(rows, pr):
            dst.execute(
                """
                INSERT OR REPLACE INTO cohort_candidate_dimension_percentiles
                (candidate_id, dimension_key, raw_score, norm_score, percentile_rank)
                VALUES (?, ?, ?, ?, ?);
                """,
                (cid, dim_key, float(raw), float(norm), float(pr_i)),
            )

        for tau_name, tau_val in taus.items():
            breach_rate = float(np.mean(norms < float(tau_val)))
            dst.execute(
                """
                INSERT OR REPLACE INTO cohort_dimension_breach_rates
                (dimension_key, tau_name, tau_value, breach_rate)
                VALUES (?, ?, ?, ?);
                """,
                (dim_key, tau_name, float(tau_val), breach_rate),
            )

    # Group scores per candidate
    group_rows: List[Tuple[str, str, float]] = []
    group_values: Dict[str, List[float]] = {g: [] for g in groups_order}

    for (cid, g), vals in by_group_candidate.items():
        gs = float(np.mean(np.asarray(vals, dtype=float)))
        group_rows.append((cid, g, gs))
        group_values.setdefault(g, []).append(gs)

        dst.execute(
            """
            INSERT OR REPLACE INTO cohort_candidate_group_scores
            (candidate_id, group_key, group_score_norm)
            VALUES (?, ?, ?);
            """,
            (cid, g, gs),
        )

    # Group summaries + group percentiles + group breach rates
    for g, vals in group_values.items():
        if not vals:
            continue
        arr = np.asarray(vals, dtype=float)
        stats = _summary_stats(arr)

        dst.execute(
            """
            INSERT OR REPLACE INTO cohort_group_summary
            (group_key, mean, median, std, iqr, min, max, p10, p25, p50, p75, p90)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                g,
                stats["mean"], stats["median"], stats["std"], stats["iqr"],
                stats["min"], stats["max"],
                stats["p10"], stats["p25"], stats["p50"], stats["p75"], stats["p90"],
            ),
        )

        for tau_name, tau_val in taus.items():
            breach_rate = float(np.mean(arr < float(tau_val)))
            dst.execute(
                """
                INSERT OR REPLACE INTO cohort_group_breach_rates
                (group_key, tau_name, tau_value, breach_rate)
                VALUES (?, ?, ?, ?);
                """,
                (g, tau_name, float(tau_val), breach_rate),
            )

        # Percentile ranks within group
        cids = [cid for (cid, gg, _) in group_rows if gg == g]
        gvals = np.asarray([v for (cid, gg, v) in group_rows if gg == g], dtype=float)
        pr = _percentile_rank(gvals)

        for cid, v, pr_i in zip(cids, gvals, pr):
            dst.execute(
                """
                INSERT OR REPLACE INTO cohort_candidate_group_percentiles
                (candidate_id, group_key, group_score_norm, percentile_rank)
                VALUES (?, ?, ?, ?);
                """,
                (cid, g, float(v), float(pr_i)),
            )


def compute_and_write_prevalence(dst: sqlite3.Connection) -> None:
    """
    Uses candidate_group_patterns rows to compute prevalence:
      - overall
      - by group
    One label per row chosen by priority.
    """
    rows = dst.execute(
        """
        SELECT group_key,
               balanced, bottlenecked, polarised, noisy, uniform_low, uniform_high
        FROM candidate_group_patterns;
        """
    ).fetchall()

    def label(r) -> str:
        if r["bottlenecked"]:
            return "bottlenecked"
        if r["polarised"]:
            return "polarised"
        if r["noisy"]:
            return "noisy"
        if r["uniform_low"]:
            return "uniform_low"
        if r["uniform_high"]:
            return "uniform_high"
        if r["balanced"]:
            return "balanced"
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
            INSERT OR REPLACE INTO cohort_pattern_prevalence_overall
            (pattern_label, count, proportion)
            VALUES (?, ?, ?);
            """,
            (lab, int(cnt), float(cnt / total)),
        )

    group_totals: Dict[str, int] = {}
    for (g, _lab), cnt in by_group_counts.items():
        group_totals[g] = group_totals.get(g, 0) + cnt

    for (g, lab), cnt in by_group_counts.items():
        denom = group_totals.get(g, 1)
        dst.execute(
            """
            INSERT OR REPLACE INTO cohort_pattern_prevalence_by_group
            (group_key, pattern_label, count, proportion)
            VALUES (?, ?, ?, ?);
            """,
            (g, lab, int(cnt), float(cnt / denom)),
        )
