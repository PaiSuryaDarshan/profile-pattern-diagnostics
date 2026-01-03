# src/ppd/__main__.py

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from ppd.candidate.analyze import analyze_candidate
from ppd.io import read_candidate_json, read_cohort_json, read_cohort_csv, extract_candidate_from_cohort, write_json
from ppd.report.candidate_report import build_candidate_report
from ppd.schema.input_schema import flatten_scores, validate_candidate_input

# NOTE  
# DEPRECATED: replaced by ppd.cohort2. Will be removed after v1.1.4.

from ppd._legacy.cohort.summarize import summarize_cohort

# ------------------------------------------------------------
# SQL materialisation (Replaced CSV/JSON cohort in 0.9.1)
# ------------------------------------------------------------
from ppd.cohort.materialise import materialise_db


def _read_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f: 
        return json.load(f)


def _load_candidate_payload(path: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
    payload = _read_json_file(path)
    identity, nested_scores = validate_candidate_input(payload)
    flat_scores = flatten_scores(nested_scores)

    identity_dict = {
        "id": identity.id,
        "email": identity.email,
        "phone_number": identity.phone_number,
        "linkedin_tag": identity.linkedin_tag,
    }
    return identity_dict, flat_scores


def cmd_candidate(args: argparse.Namespace) -> int:
    identity, scores_flat = _load_candidate_payload(args.input)

    analysis = analyze_candidate(
        scores_flat,
        include_adjacency=not args.no_adjacency,
        include_patterns=not args.no_patterns,
    )

    report = build_candidate_report(
        analysis=analysis,
        candidate_identity=identity,
        include_identity=not args.no_identity,
        version=args.version,
        validate=True,
    )

    write_json(args.output, report)
    return 0


# ------------------------------------------------------------
# NOTE: Replaced by SQL in 0.9.1
# (legacy cohort CSV/JSON commands removed from CLI)
# ------------------------------------------------------------

# def read_cohort_auto(path: str) -> pd.DataFrame:
#     ext = Path(path).suffix.lower()
#     if ext == ".csv":
#         return read_cohort_csv(path)
#     if ext == ".json":
#         return read_cohort_json(path)
#     raise ValueError(f"Unsupported input type: {ext}. Use .csv or .json.")

# def cmd_cohort(args: argparse.Namespace) -> int:
#     df = read_cohort_auto(args.input)
#
#     report = summarize_cohort(
#         df,
#         id_col=args.id_col,
#         group_col=args.group_col,
#         threshold=args.threshold,
#         include_percentiles=args.include_percentiles,
#         include_group_summary=not args.no_groups,
#         group_method=args.group_method,
#         version=args.version,
#         validate_report=True,
#     )
#
#     write_json(args.output, report)
#     return 0

# def cmd_cohort_candidate(args: argparse.Namespace) -> int:
#     path = Path(args.input)
#
#     # --- JSON cohort ---
#     if path.suffix.lower() == ".json":
#         entry = extract_candidate_from_cohort(
#             args.input,
#             candidate_id=args.id,
#         )
#
#         identity = entry.get("candidate", {})
#         scores_nested = entry.get("scores", {})
#         scores_flat = flatten_scores(scores_nested)
#
#     # --- CSV cohort ---
#     else:
#         df = read_cohort_csv(args.input)
#
#         if args.id_col not in df.columns:
#             raise ValueError(f"ID column '{args.id_col}' not found in cohort CSV")
#
#         row = df[df[args.id_col] == args.id]
#         if row.empty:
#             raise KeyError(f"Candidate id '{args.id}' not found in cohort CSV")
#
#         identity = {"id": args.id}
#         scores_flat = {
#             col: float(row.iloc[0][col])
#             for col in df.columns
#             if col != args.id_col
#         }
#
#     analysis = analyze_candidate(
#         scores_flat,
#         include_adjacency=not args.no_adjacency,
#         include_patterns=not args.no_patterns,
#     )
#
#     report = build_candidate_report(
#         analysis=analysis,
#         candidate_identity=identity,
#         include_identity=not args.no_identity,
#         version=args.version,
#         validate=True,
#     )
#
#     write_json(args.output, report)
#     return 0


# ------------------------------------------------------------
# materialise-db (SQLite cohort pipeline)
# ------------------------------------------------------------

def cmd_materialise_db(args: argparse.Namespace) -> int:
    taus: Optional[Dict[str, float]] = None
    if args.taus_json:
        taus_obj = json.loads(args.taus_json)
        if not isinstance(taus_obj, dict):
            raise ValueError("--taus-json must decode to a JSON object/dict")
        taus = {str(k): float(v) for k, v in taus_obj.items()}

    materialise_db(
        in_db=Path(args.in_db),
        out_db=Path(args.out_db),
        store_json_reports=bool(args.store_json_reports),
        taus=taus,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ppd",
        description="Profile Pattern Diagnostics (PPD) — diagnostic, non-predictive profile structure analysis.",
    )

    parser.add_argument(
        "--version",
        default="1.1.2",
        help="Report version string to embed in metadata (default: 1.1.2).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ---------------------------
    # candidate
    # ---------------------------
    p_cand = sub.add_parser(
        "candidate",
        help="Analyze a single candidate JSON (nested categories -> metrics).",
    )
    p_cand.add_argument(
        "--input",
        required=True,
        help="Path to candidate JSON file.",
    )
    p_cand.add_argument(
        "--output",
        required=True,
        help="Path to write candidate report JSON.",
    )
    p_cand.add_argument(
        "--no-identity",
        action="store_true",
        help="Do not include candidate identity block in the output report.",
    )
    p_cand.add_argument(
        "--no-adjacency",
        action="store_true",
        help="Disable adjacency descriptor computation (D).",
    )
    p_cand.add_argument(
        "--no-patterns",
        action="store_true",
        help="Disable pattern classification (balanced/bottlenecked/etc.).",
    )
    p_cand.set_defaults(func=cmd_candidate)

    # ---------------------------
    # cohort (legacy) — removed
    # ---------------------------
    # NOTE: Replaced by SQL in 0.9.1

    # ---------------------------
    # cohort-candidate (legacy) — removed
    # ---------------------------
    # NOTE: Replaced by SQL in 0.9.1

    # ---------------------------
    # materialise-db (SQL)
    # ---------------------------
    p_mat = sub.add_parser(
        "materialise-db",
        help="Materialise an input cohort SQLite DB into an output DB (candidate outputs + cohort outputs).",
    )
    p_mat.add_argument(
        "--in-db",
        required=True,
        help="Input SQLite DB (must contain candidates/dimensions/scores).",
    )
    p_mat.add_argument(
        "--out-db",
        required=True,
        help="Output SQLite DB to create (materialised).",
    )
    p_mat.add_argument(
        "--store-json-reports",
        action="store_true",
        default=False,
        help="Store full JSON candidate reports in candidate_reports table.",
    )
    p_mat.add_argument(
        "--taus-json",
        default=None,
        help='Optional JSON dict of taus, e.g. \'{"tau_operational":0.60,"tau_high":0.80,"tau_low":0.40}\'',
    )
    p_mat.set_defaults(func=cmd_materialise_db)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
