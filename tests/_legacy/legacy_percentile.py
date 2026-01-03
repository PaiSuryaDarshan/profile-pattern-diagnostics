# tests/test_percentiles.py

import pytest

from ppd._legacy.cohort.percentiles import (
    compute_percentiles,
    probs_to_keys,
    validate_probs,
)


# ------------------------------------------------------------------
# validate_probs
# ------------------------------------------------------------------

# Valid probs return tuple of floats
def test_validate_probs_valid():
    out = validate_probs([0.1, 0.5, 0.9])

    assert isinstance(out, tuple)
    assert out[0] == pytest.approx(0.1)
    assert out[1] == pytest.approx(0.5)
    assert out[2] == pytest.approx(0.9)


# Empty probs should raise
def test_validate_probs_empty_raises():
    with pytest.raises(ValueError):
        validate_probs([])


# Out-of-range probs should raise
def test_validate_probs_out_of_range_raises():
    with pytest.raises(ValueError):
        validate_probs([1.1])

    with pytest.raises(ValueError):
        validate_probs([-0.1])


# Non-numeric probs should raise
def test_validate_probs_non_numeric_raises():
    with pytest.raises(ValueError):
        validate_probs(["0.5"])  # type: ignore[list-item]


# ------------------------------------------------------------------
# probs_to_keys
# ------------------------------------------------------------------

# Keys are formatted as pXX
def test_probs_to_keys_format():
    keys = probs_to_keys([0.1, 0.25, 0.5])

    assert keys == ["p10", "p25", "p50"]


# ------------------------------------------------------------------
# compute_percentiles
# ------------------------------------------------------------------

# Basic percentiles correct on simple data
def test_compute_percentiles_basic():
    values = [0, 1, 2, 3, 4]
    out = compute_percentiles(values, [0.5])

    assert "p50" in out
    assert out["p50"] == pytest.approx(2.0)


# Multiple percentiles returned with stable keys
def test_compute_percentiles_multiple():
    values = [0, 10, 20, 30, 40]
    out = compute_percentiles(values, [0.1, 0.9])

    assert "p10" in out
    assert "p90" in out
    assert out["p10"] >= 0.0
    assert out["p90"] <= 40.0


# Empty values should raise
def test_compute_percentiles_empty_values_raises():
    with pytest.raises(ValueError):
        compute_percentiles([], [0.5])


# Invalid probs should raise
def test_compute_percentiles_invalid_probs_raises():
    with pytest.raises(ValueError):
        compute_percentiles([1, 2, 3], [2.0])

