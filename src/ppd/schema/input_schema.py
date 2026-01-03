from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class CandidateIdentity:
    id: int
    email: str
    phone_number: str
    linkedin_tag: str


def validate_candidate_input(payload: Dict[str, Any]) -> Tuple[CandidateIdentity, Dict[str, Dict[str, float]]]:
    """
    Validate candidate JSON payload shape and required identity fields.

    Returns
    -------
    (identity, scores_nested)

    scores_nested has the shape:
        {category: {metric: float}}
    """
    if not isinstance(payload, dict):
        raise ValueError("Candidate payload must be a JSON object (dict).")

    if "candidate" not in payload:
        raise ValueError("Missing required key: 'candidate'.")

    if "scores" not in payload:
        raise ValueError("Missing required key: 'scores'.")

    candidate = payload["candidate"]
    scores = payload["scores"]

    if not isinstance(candidate, dict):
        raise ValueError("'candidate' must be an object (dict).")

    if not isinstance(scores, dict):
        raise ValueError("'scores' must be an object (dict).")

    # --- identity (mandatory) ---
    if "id" not in candidate:
        raise ValueError("Missing required field: candidate.id")
    if "email" not in candidate:
        raise ValueError("Missing required field: candidate.email")
    if "phone_number" not in candidate:
        raise ValueError("Missing required field: candidate.phone_number")
    if "linkedin_tag" not in candidate:
        raise ValueError("Missing required field: candidate.linkedin_tag")

    candidate_id = candidate["id"]
    email = candidate["email"]
    phone_number = candidate["phone_number"]
    linkedin_tag = candidate["linkedin_tag"]

    if isinstance(candidate_id, bool):
        raise ValueError("candidate.id must be an integer or a string (bool is not allowed).")

    if not isinstance(email, str) or email.strip() == "":
        raise ValueError("candidate.email must be a non-empty string.")
    if not isinstance(phone_number, str) or phone_number.strip() == "":
        raise ValueError("candidate.phone_number must be a non-empty string.")
    if not isinstance(linkedin_tag, str) or linkedin_tag.strip() == "":
        raise ValueError("candidate.linkedin_tag must be a non-empty string.")

    identity = CandidateIdentity(
        id=candidate_id,
        email=email,
        phone_number=phone_number,
        linkedin_tag=linkedin_tag,
    )

    # --- scores nested: {category: {metric: float}} ---
    scores_out: Dict[str, Dict[str, float]] = {}

    for category, metric_map in scores.items():
        if not isinstance(category, str) or category.strip() == "":
            raise ValueError("All score categories must be non-empty strings.")

        if not isinstance(metric_map, dict):
            raise ValueError(f"Scores for category '{category}' must be an object (dict).")

        cat = category.strip()
        scores_out[cat] = {}

        for metric, value in metric_map.items():
            if not isinstance(metric, str) or metric.strip() == "":
                raise ValueError(f"All metric names in category '{cat}' must be non-empty strings.")

            if value is None:
                raise ValueError(f"Metric '{cat}::{metric}' is missing a value (None).")

            if isinstance(value, bool):
                raise ValueError(f"Metric '{cat}::{metric}' must be numeric (bool is not allowed).")

            if not isinstance(value, (int, float)):
                raise ValueError(f"Metric '{cat}::{metric}' must be numeric.")

            scores_out[cat][metric.strip()] = float(value)

        if len(scores_out[cat]) == 0:
            raise ValueError(f"Category '{cat}' has no metrics.")

    if len(scores_out) == 0:
        raise ValueError("'scores' contains no categories.")

    return identity, scores_out


def flatten_scores(scores_nested: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Flatten {category: {metric: score}} into a single {dimension: score} mapping.

    Dimension key format:
        "<Category>::<Metric>"

    This avoids collisions when different categories share metric names.
    """
    flat: Dict[str, float] = {}

    for category, metric_map in scores_nested.items():
        for metric, value in metric_map.items():
            key = f"{category}::{metric}"

            if key in flat:
                raise ValueError(f"Duplicate dimension key after flattening: {key}")

            flat[key] = float(value)

    if len(flat) == 0:
        raise ValueError("No scores found after flattening.")

    return flat
