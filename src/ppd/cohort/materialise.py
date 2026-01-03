# ------------------------------------------------------------
# Latest Feature added in  1.1.2 || Cohort Analysis
# ------------------------------------------------------------
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from ppd.cohort.candidate_pass import (
    GROUPS_ORDER,
    build_candidate_payload,
    create_candidate_output_tables,
    fetch_candidate_ids,
    fetch_scores_long,
    run_candidate_analysis,
    write_candidate_outputs,
)
from ppd.cohort.cohort_stats import (
    compute_and_write_cohort,
    compute_and_write_prevalence,
    create_cohort_output_tables,
)


DEFAULT_TAUS: Dict[str, float] = {
    "tau_operational": 0.60,  # norm scale [0,1]
    "tau_high": 0.80,
    "tau_low": 0.40,
}


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def copy_table(src: sqlite3.Connection, dst: sqlite3.Connection, table: str) -> None:
    # Copy schema
    schema = src.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
        (table,),
    ).fetchone()

    if not schema or not schema["sql"]:
        raise RuntimeError(f"Table not found in source DB: {table}")

    dst.execute(schema["sql"])

    # Figure out which columns are insertable (skip generated/hidden)
    # PRAGMA table_xinfo includes generated columns with hidden != 0
    cols_info = src.execute(f"PRAGMA table_xinfo({table});").fetchall()
    insert_cols = [r["name"] for r in cols_info if int(r["hidden"]) == 0]

    if not insert_cols:
        return

    col_list = ",".join(insert_cols)
    placeholders = ",".join(["?"] * len(insert_cols))

    rows = src.execute(f"SELECT {col_list} FROM {table};").fetchall()
    if not rows:
        return

    dst.executemany(
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders});",
        [tuple(r[c] for c in insert_cols) for r in rows],
    )



def create_metadata_table(dst: sqlite3.Connection) -> None:
    dst.execute(
        """
        CREATE TABLE IF NOT EXISTS db_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )


def set_metadata(dst: sqlite3.Connection, kv: Dict[str, str]) -> None:
    dst.executemany(
        "INSERT OR REPLACE INTO db_metadata (key, value) VALUES (?, ?);",
        list(kv.items()),
    )


def materialise_db(
    *,
    in_db: Path,
    out_db: Path,
    store_json_reports: bool = True,
    taus: Optional[Dict[str, float]] = None,
) -> None:
    """
    Input:  SQLite DB with candidates/dimensions/scores (raw + norm)
    Output: New SQLite DB with:
      - copied inputs
      - candidate outputs (metrics/patterns + optional JSON)
      - cohort outputs (summaries/percentiles/breaches/prevalence)

    This function is intended to be called by CLI.
    """
    taus = dict(taus or DEFAULT_TAUS)

    if out_db.exists():
        out_db.unlink()

    src = connect(in_db)
    dst = connect(out_db)

    try:
        # Copy base tables
        copy_table(src, dst, "candidates")
        copy_table(src, dst, "dimensions")
        copy_table(src, dst, "scores")

        # Create output tables
        create_metadata_table(dst)
        create_candidate_output_tables(dst, store_json_reports=store_json_reports)
        create_cohort_output_tables(dst)

        set_metadata(
            dst,
            {
                "tool": "Profile Pattern Diagnostics (PPD)",
                "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source_db": in_db.name,
                "store_json_reports": str(bool(store_json_reports)),
            },
        )

        # Pull score rows once
        scores_rows = fetch_scores_long(src)
        candidate_ids = fetch_candidate_ids(src)

        # Candidate pass
        for cid in candidate_ids:
            payload = build_candidate_payload(scores_rows, cid)
            report = run_candidate_analysis(payload)
            write_candidate_outputs(
                dst,
                candidate_id=cid,
                report=report,
                store_json_reports=store_json_reports,
            )

        # Cohort pass (dimension + group stats)
        compute_and_write_cohort(
            dst,
            scores_rows=scores_rows,
            groups_order=GROUPS_ORDER,
            taus=taus,
        )

        # Prevalence pass (from candidate_group_patterns)
        compute_and_write_prevalence(dst)

        dst.commit()

    finally:
        src.close()
        dst.close()
