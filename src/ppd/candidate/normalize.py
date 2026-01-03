from __future__ import annotations

from typing import Iterable, List

from ppd.schema.constants import (
    CLAMP_OUT_OF_RANGE_INPUTS,
    RAW_SCORE_MAX,
    RAW_SCORE_MIN,
)


def clamp_to_range(score_raw: float) -> float:
    """
    Clamp a raw rubric score to the valid range [RAW_SCORE_MIN, RAW_SCORE_MAX].
    """
    if score_raw < RAW_SCORE_MIN:
        return RAW_SCORE_MIN

    if score_raw > RAW_SCORE_MAX:
        return RAW_SCORE_MAX

    return score_raw


def normalize_score(score_raw: float, *, clamp: bool = CLAMP_OUT_OF_RANGE_INPUTS) -> float:
    """
    Normalize a single raw rubric score to [0, 1] using linear scaling.
    """
    if RAW_SCORE_MAX == 0:
        raise ZeroDivisionError(
            "RAW_SCORE_MAX must be non-zero for normalization."
        )

    if score_raw < RAW_SCORE_MIN or score_raw > RAW_SCORE_MAX:
        if clamp:
            score_raw = clamp_to_range(score_raw)
        else:
            raise ValueError(
                f"Raw score out of range: {score_raw}. "
                f"Expected [{RAW_SCORE_MIN}, {RAW_SCORE_MAX}]."
            )

    return score_raw / RAW_SCORE_MAX


def normalize_scores(
    scores_raw: Iterable[float], *, clamp: bool = CLAMP_OUT_OF_RANGE_INPUTS
) -> List[float]:
    """
    Normalize an iterable of raw rubric scores to [0, 1].
    """
    normalized = []

    for score in scores_raw:
        normalized_score = normalize_score(score, clamp=clamp)
        normalized.append(normalized_score)

    return normalized
