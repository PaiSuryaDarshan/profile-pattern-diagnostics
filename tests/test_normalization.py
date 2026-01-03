import pytest

from ppd.candidate.normalize import (
    clamp_to_range,
    normalize_score,
    normalize_scores,
)
from ppd.schema.constants import (
    RAW_SCORE_MIN,
    RAW_SCORE_MAX,
)


# ------------------------------------------------------------------
# clamp_to_range
# ------------------------------------------------------------------

# Returns the input unchanged when the score is already within range
def test_clamp_to_range_in_range():
    score = 3.0
    clamped = clamp_to_range(score)

    assert clamped == score


# Clamps values below the minimum score up to RAW_SCORE_MIN
def test_clamp_to_range_below_min():
    score = -2.0
    clamped = clamp_to_range(score)

    assert clamped == RAW_SCORE_MIN


# Clamps values above the maximum score down to RAW_SCORE_MAX
def test_clamp_to_range_above_max():
    score = 7.5
    clamped = clamp_to_range(score)

    assert clamped == RAW_SCORE_MAX


# ------------------------------------------------------------------
# normalize_score (single value)
# ------------------------------------------------------------------

# Correctly normalizes an in-range score without clamping
def test_normalize_score_in_range():
    score = 2.5
    normalized = normalize_score(score)

    assert normalized == score / RAW_SCORE_MAX


# Normalizes an out-of-range score when clamping is enabled
def test_normalize_score_out_of_range_with_clamp():
    score = 10.0
    normalized = normalize_score(score, clamp=True)

    assert normalized == 1.0


# Raises an error for out-of-range input when clamping is disabled
def test_normalize_score_out_of_range_without_clamp_raises():
    score = -1.0

    with pytest.raises(ValueError):
        normalize_score(score, clamp=False)


# ------------------------------------------------------------------
# normalize_scores (iterable)
# ------------------------------------------------------------------

# Normalizes a list of valid scores element-wise
def test_normalize_scores_all_in_range():
    scores = [0.0, 2.5, 5.0]
    normalized = normalize_scores(scores)

    assert normalized[0] == 0.0
    assert normalized[1] == 0.5
    assert normalized[2] == 1.0


# Normalizes a list containing out-of-range values when clamping is enabled
def test_normalize_scores_with_clamp():
    scores = [-1.0, 2.5, 6.0]
    normalized = normalize_scores(scores, clamp=True)

    assert normalized[0] == 0.0
    assert normalized[1] == 0.5
    assert normalized[2] == 1.0


# Raises an error if any value is out of range and clamping is disabled
def test_normalize_scores_without_clamp_raises():
    scores = [1.0, -3.0, 4.0]

    with pytest.raises(ValueError):
        normalize_scores(scores, clamp=False)
