from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, List

import pandas as pd

# NOTE from author to self / future maintainer(s): 
# pd.read_json constantly throws an errors about mixed types (and shape errors) when reading candidate JSON files, 
# Using the built-in json module here instead and doing manual validation.
# It's scoped inside the function to avoid any collisions (and keep the namespace clean.)
# If pandas improves this in the future (or if anyone else has a crack at solving this and manages to fix why the code fails with pandas), 
# we can consider switching to the pandas

# NOTE :
# CSV functionality was not maintain after 0.8.6 due constant buggy behaviour 
# and limited use-cases as most web collected data provides in .JSON.
# Functions were left here for possible future use-cases. (If user chooses to adapt them)

def read_candidate_csv(
    path: str,
    *,
    id_col: Optional[str] = None,
    dimension_col: str = "dimension",
    score_col: str = "score",
) -> Dict[str, float]:
    """
    Read a single-candidate CSV and return {dimension: score}.

    Supported shapes:
    1) long-form (recommended): dimension, score
    2) wide-form: one row where columns are dimensions (optionally with an id_col)
    """
    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"CSV is empty: {path}")

    # long-form: has explicit dimension + score columns
    if (dimension_col in df.columns) and (score_col in df.columns):
        scores: Dict[str, float] = {}

        for _, row in df.iterrows():
            dim = row[dimension_col]
            val = row[score_col]

            if pd.isna(dim):
                continue

            dim_str = str(dim).strip()
            if dim_str == "":
                continue

            if pd.isna(val):
                raise ValueError(f"Missing score for dimension '{dim_str}' in {path}")

            try:
                scores[dim_str] = float(val)
            except ValueError:
                raise ValueError(f"Non-numeric score for dimension '{dim_str}': {val}")

        if len(scores) == 0:
            raise ValueError(f"No dimension scores found in {path}")

        return scores

    # wide-form: assume first row has dimension columns
    if len(df) != 1:
        raise ValueError(
            f"Expected a single row for wide-form candidate CSV, got {len(df)} rows: {path}"
        )

    row = df.iloc[0]
    scores: Dict[str, float] = {}

    for col in df.columns:
        if id_col is not None and col == id_col:
            continue

        val = row[col]

        if pd.isna(val):
            raise ValueError(f"Missing score for dimension '{col}' in {path}")

        try:
            scores[str(col)] = float(val)
        except ValueError:
            raise ValueError(f"Non-numeric score for dimension '{col}': {val}")

    if len(scores) == 0:
        raise ValueError(f"No dimension columns found in wide-form CSV: {path}")

    return scores


def read_candidate_json(path: str) -> Dict[str, float]:
    """
    Read a single-candidate JSON file and return {dimension: score}.

    Supported shapes:
    1) {"A": 3.0, "B": 4.5, ...}
    2) {"scores": {"A": 3.0, "B": 4.5, ...}}
    """
    import json

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object (dict) in {path}")

    if "scores" in data and isinstance(data["scores"], dict):
        data = data["scores"]

    scores: Dict[str, float] = {}

    for dim, val in data.items():
        if dim is None:
            continue

        dim_str = str(dim).strip()
        if dim_str == "":
            continue

        if val is None:
            raise ValueError(f"Missing score for dimension '{dim_str}' in {path}")

        try:
            scores[dim_str] = float(val)
        except (TypeError, ValueError):
            raise ValueError(f"Non-numeric score for dimension '{dim_str}': {val}")

    if len(scores) == 0:
        raise ValueError(f"No dimension scores found in {path}")

    return scores

def read_cohort_csv(path: str) -> pd.DataFrame:
    """
    Read a cohort CSV into a DataFrame.

    This is a thin wrapper so the rest of PPD can assume pandas is used for cohorts.
    Validation of schema/columns happens in cohort modules, not here.
    """
    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"Cohort CSV is empty: {path}")

    return df

# NOTE Made in 0.9.1, due to unreliability of CSV output
def read_cohort_json(path: str, *, id_col: str = "id") -> pd.DataFrame:
    """
    Read PPD cohort JSON and return a WIDE DataFrame:
      - 1 row per candidate
      - id column + numeric score columns ONLY

    JSON expected:
      {
        "cohort_metadata": {...},
        "candidates": [
          {
            "candidate": {"id": "...", "email": "...", ...},
            "scores": {
              "group_a": {"metric_1": 4.2, ...},
              "group_b": {"metric_2": 3.7, ...}
            }
          }, ...
        ]
      }

    Output columns:
      - id (default) or id_col
      - flattened score columns like: group__metric (numeric)
    """

    import json

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if p.suffix.lower() != ".json":
        raise ValueError(f"read_cohort_json expects a .json file, got: {p.suffix}")

    with p.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    if not isinstance(obj, dict):
        raise ValueError("Cohort JSON must be a JSON object at the top level.")

    entries = obj.get("candidates")
    if not isinstance(entries, list):
        raise ValueError("Cohort JSON must contain a top-level 'candidates' list.")

    rows = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Each element of 'candidates' must be an object. Bad at index {i}.")

        cand = entry.get("candidate") or {}
        if not isinstance(cand, dict):
            raise ValueError(f"'candidate' must be an object at candidates[{i}].")

        cand_id = cand.get("id")
        if cand_id is None:
            raise ValueError(f"Missing candidate.id at candidates[{i}].")

        scores = entry.get("scores")
        if not isinstance(scores, dict):
            raise ValueError(f"'scores' must be an object at candidates[{i}].")

        # One row per candidate
        row: Dict[str, Any] = {id_col: str(cand_id)}

        # Flatten scores into numeric columns ONLY
        # Column naming: "<group>__<metric>"
        for group_name, metrics in scores.items():
            if not isinstance(metrics, dict):
                raise ValueError(
                    f"Group '{group_name}' must map to an object of metrics at candidates[{i}]."
                )
            for metric_name, value in metrics.items():
                if value is None:
                    continue
                try:
                    row[f"{group_name}__{metric_name}"] = float(value)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Non-numeric score at candidates[{i}] -> {group_name}.{metric_name}: {value!r}"
                    )

        rows.append(row)

    df = pd.DataFrame(rows)

    # Ensure every non-id column is numeric (protect downstream)
    score_cols = [c for c in df.columns if c != id_col]
    if score_cols:
        df[score_cols] = df[score_cols].apply(pd.to_numeric, errors="raise")

    return df

def extract_candidate_from_cohort(
    path: str,
    *,
    candidate_id: str,
    id_col: str = "candidate_id",
) -> Dict[str, Any]:
    """
    Extract a single candidate entry from a cohort file (JSON or CSV).
    """
    p = Path(path)

    # ---------- JSON cohort ----------
    if p.suffix.lower() == ".json":
        import json

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object (dict) in {path}")

        if "candidates" not in data or not isinstance(data["candidates"], list):
            raise ValueError("Invalid cohort JSON: missing 'candidates' list")

        for entry in data["candidates"]:
            if not isinstance(entry, dict):
                continue

            cand = entry.get("candidate", {})
            if isinstance(cand, dict) and cand.get("id") == candidate_id:
                return entry

        raise KeyError(f"Candidate id '{candidate_id}' not found in cohort JSON")

    # ---------- CSV cohort ----------
    df = pd.read_csv(p)

    if df.empty:
        raise ValueError(f"Cohort CSV is empty: {path}")

    if id_col not in df.columns:
        raise ValueError(f"ID column '{id_col}' not found in cohort CSV")

    row = df[df[id_col] == candidate_id]
    if row.empty:
        raise KeyError(f"Candidate id '{candidate_id}' not found in cohort CSV")

    scores = {col: float(row.iloc[0][col]) for col in df.columns if col != id_col}

    return {"candidate": {"id": candidate_id}, "scores": scores}

def write_json(path: str, obj: Any, *, indent: int = 2) -> None:
    """Write a Python object as JSON to disk."""
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)


def write_csv(path: str, df: pd.DataFrame, *, index: bool = False) -> None:
    """Write a DataFrame to CSV."""
    df.to_csv(path, index=index)
