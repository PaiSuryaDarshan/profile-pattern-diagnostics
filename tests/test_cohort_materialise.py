import sqlite3
from pathlib import Path

from ppd.cohort.materialise import (
    connect,
    copy_table,
    create_metadata_table,
    set_metadata,
    materialise_db,
)


# ------------------------------------------------------------------
# connect
# ------------------------------------------------------------------

# Opens a SQLite connection with row_factory and foreign keys enabled
def test_connect_sets_row_factory_and_fk(tmp_path):
    db_path = tmp_path / "test.db"
    conn = connect(db_path)

    assert conn.row_factory is sqlite3.Row

    fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    assert fk == 1

    conn.close()


# ------------------------------------------------------------------
# copy_table
# ------------------------------------------------------------------

# Copies schema and rows from source DB to destination DB
def test_copy_table_copies_schema_and_data():
    src = sqlite3.connect(":memory:")
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(":memory:")
    dst.row_factory = sqlite3.Row

    src.execute("CREATE TABLE test_table (id INTEGER, val TEXT);")
    src.execute("INSERT INTO test_table VALUES (1, 'a');")

    copy_table(src, dst, "test_table")

    rows = dst.execute("SELECT * FROM test_table;").fetchall()
    assert len(rows) == 1
    assert rows[0]["id"] == 1
    assert rows[0]["val"] == "a"

    src.close()
    dst.close()


# Raises error if source table does not exist
def test_copy_table_raises_if_table_missing():
    src = sqlite3.connect(":memory:")
    dst = sqlite3.connect(":memory:")

    try:
        copy_table(src, dst, "missing_table")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Table not found" in str(e)

    src.close()
    dst.close()


# ------------------------------------------------------------------
# create_metadata_table
# ------------------------------------------------------------------

# Creates db_metadata table
def test_create_metadata_table_creates_table():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    create_metadata_table(db)

    tables = {
        r["name"]
        for r in db.execute("SELECT name FROM sqlite_master WHERE type='table';")
    }
    assert "db_metadata" in tables

    db.close()


# ------------------------------------------------------------------
# set_metadata
# ------------------------------------------------------------------

# Inserts key-value pairs into db_metadata
def test_set_metadata_inserts_values():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    create_metadata_table(db)

    set_metadata(db, {"a": "1", "b": "2"})

    rows = db.execute("SELECT key, value FROM db_metadata;").fetchall()
    kv = {r["key"]: r["value"] for r in rows}

    assert kv == {"a": "1", "b": "2"}

    db.close()


# ------------------------------------------------------------------
# materialise_db
# ------------------------------------------------------------------

# Creates a fully materialised output DB from a minimal input DB
def test_materialise_db_creates_output_db(tmp_path):
    in_db = tmp_path / "input.db"
    out_db = tmp_path / "output.db"

    # --- create minimal input DB ---
    src = sqlite3.connect(in_db)
    src.row_factory = sqlite3.Row

    src.execute("CREATE TABLE candidates (candidate_id TEXT PRIMARY KEY);")
    src.execute(
        """
        CREATE TABLE dimensions (
            dimension_key TEXT PRIMARY KEY,
            group_key TEXT,
            dimension_name TEXT
        );
        """
    )
    src.execute(
        """
        CREATE TABLE scores (
            candidate_id TEXT,
            dimension_key TEXT,
            raw_score REAL,
            norm_score REAL
        );
        """
    )

    src.execute("INSERT INTO candidates VALUES ('C1');")
    src.execute("INSERT INTO dimensions VALUES ('g::d', 'g', 'D');")
    src.execute("INSERT INTO scores VALUES ('C1', 'g::d', 4.0, 0.8);")
    src.commit()
    src.close()

    # --- run materialisation ---
    materialise_db(
        in_db=in_db,
        out_db=out_db,
        store_json_reports=False,
    )

    # --- validate output DB exists ---
    assert out_db.exists()

    dst = sqlite3.connect(out_db)
    dst.row_factory = sqlite3.Row

    # metadata written
    meta = dst.execute("SELECT key FROM db_metadata;").fetchall()
    keys = {r["key"] for r in meta}
    assert "tool" in keys
    assert "generated_at_utc" in keys
    assert "source_db" in keys

    # base tables copied
    assert dst.execute("SELECT COUNT(*) FROM candidates;").fetchone()[0] == 1
    assert dst.execute("SELECT COUNT(*) FROM dimensions;").fetchone()[0] == 1
    assert dst.execute("SELECT COUNT(*) FROM scores;").fetchone()[0] == 1

    # candidate outputs exist
    assert (
        dst.execute("SELECT COUNT(*) FROM candidate_group_metrics;")
        .fetchone()[0]
        == 1
    )

    # cohort outputs exist
    assert (
        dst.execute("SELECT COUNT(*) FROM cohort_dimension_summary;")
        .fetchone()[0]
        == 1
    )

    dst.close()
