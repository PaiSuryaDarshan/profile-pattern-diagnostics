import numpy as np
import pytest

from ppd.candidate.metrics import (
    compute_argmin_dimensions,
    compute_candidate_metrics,
    compute_candidate_metrics_by_group,
    compute_max,
    compute_mean,
    compute_min,
    compute_population_std,
    compute_range,
)


# ------------------------------------------------------------------
# Basic metric functions (list[float] inputs)
# ------------------------------------------------------------------

# Raises for empty input when computing mean
def test_compute_mean_empty_raises():
    with pytest.raises(ValueError):
        compute_mean([])


# Computes mean correctly for a simple list
def test_compute_mean_simple():
    values = [0.0, 0.5, 1.0]
    result = compute_mean(values)

    assert result == pytest.approx(0.5)


# Raises for empty input when computing population std
def test_compute_population_std_empty_raises():
    with pytest.raises(ValueError):
        compute_population_std([])


# Computes population standard deviation (ddof=0) correctly
def test_compute_population_std_simple():
    values = [0.0, 0.5, 1.0]
    result = compute_population_std(values)

    expected = float(np.std(values, ddof=0))
    assert result == pytest.approx(expected)


# Raises for empty input when computing min
def test_compute_min_empty_raises():
    with pytest.raises(ValueError):
        compute_min([])


# Computes min correctly
def test_compute_min_simple():
    values = [0.2, 0.1, 0.9]
    result = compute_min(values)

    assert result == pytest.approx(0.1)


# Raises for empty input when computing max
def test_compute_max_empty_raises():
    with pytest.raises(ValueError):
        compute_max([])


# Computes max correctly
def test_compute_max_simple():
    values = [0.2, 0.1, 0.9]
    result = compute_max(values)

    assert result == pytest.approx(0.9)


# Raises for empty input when computing range
def test_compute_range_empty_raises():
    with pytest.raises(ValueError):
        compute_range([])


# Computes range correctly (max - min)
def test_compute_range_simple():
    values = [0.2, 0.1, 0.9]
    result = compute_range(values)

    assert result == pytest.approx(0.8)


# ------------------------------------------------------------------
# Argmin dimensions (dict[str, float] inputs)
# ------------------------------------------------------------------

# Raises for empty dict when computing argmin dimensions
def test_compute_argmin_dimensions_empty_raises():
    with pytest.raises(ValueError):
        compute_argmin_dimensions({})


# Returns the minimum dimension names and value correctly
def test_compute_argmin_dimensions_simple():
    scores = {
        "A": 0.7,
        "B": 0.2,
        "C": 0.9,
    }

    dims, val = compute_argmin_dimensions(scores)

    assert dims == ["B"]
    assert val == pytest.approx(0.2)


# On ties for minimum, returns all tied dimensions in encounter order
def test_compute_argmin_dimensions_tie_all_returned():
    scores = {
        "A": 0.2,
        "B": 0.2,
        "C": 0.9,
    }

    dims, val = compute_argmin_dimensions(scores)

    assert dims == ["A", "B"]
    assert val == pytest.approx(0.2)


# ------------------------------------------------------------------
# Candidate metrics (dict[str, float] inputs)
# ------------------------------------------------------------------

# Raises for empty scores dict
def test_compute_candidate_metrics_empty_raises():
    with pytest.raises(ValueError):
        compute_candidate_metrics({})


# Computes the full candidate metrics bundle correctly for a simple case
def test_compute_candidate_metrics_simple():
    scores = {
        "A": 0.0,
        "B": 0.5,
        "C": 1.0,
    }

    metrics = compute_candidate_metrics(scores)

    assert "mean" in metrics
    assert "std_pop" in metrics
    assert "min" in metrics
    assert "min_dimensions" in metrics
    assert "max" in metrics
    assert "range" in metrics
    assert "n_dimensions" in metrics

    assert metrics["mean"] == pytest.approx(0.5)
    assert metrics["std_pop"] == pytest.approx(float(np.std([0.0, 0.5, 1.0], ddof=0)))
    assert metrics["min"] == pytest.approx(0.0)
    assert metrics["min_dimensions"] == ["A"]
    assert metrics["max"] == pytest.approx(1.0)
    assert metrics["range"] == pytest.approx(1.0)
    assert metrics["n_dimensions"] == 3


# ------------------------------------------------------------------
# Candidate metrics by group (dict[str, float] inputs)
# ------------------------------------------------------------------

# Raises for empty scores dict
def test_compute_candidate_metrics_by_group_empty_raises():
    with pytest.raises(ValueError):
        compute_candidate_metrics_by_group({})


# Computes metrics by group correctly for grouped dimensions
def test_compute_candidate_metrics_by_group_grouped_simple():
    scores = {
        "g1::A": 0.0,
        "g1::B": 0.5,
        "g2::C": 1.0,
        "g2::D": 1.0,
    }

    metrics_by_group = compute_candidate_metrics_by_group(scores)

    assert "g1" in metrics_by_group
    assert "g2" in metrics_by_group

    assert metrics_by_group["g1"]["mean"] == pytest.approx(0.25)
    assert metrics_by_group["g1"]["min"] == pytest.approx(0.0)
    assert metrics_by_group["g1"]["max"] == pytest.approx(0.5)
    assert metrics_by_group["g1"]["range"] == pytest.approx(0.5)
    assert metrics_by_group["g1"]["n_dimensions"] == 2

    assert metrics_by_group["g2"]["mean"] == pytest.approx(1.0)
    assert metrics_by_group["g2"]["min"] == pytest.approx(1.0)
    assert metrics_by_group["g2"]["max"] == pytest.approx(1.0)
    assert metrics_by_group["g2"]["range"] == pytest.approx(0.0)
    assert metrics_by_group["g2"]["n_dimensions"] == 2


# Computes metrics by group correctly when no delimiter is present (ungrouped fallback)
def test_compute_candidate_metrics_by_group_ungrouped_simple():
    scores = {
        "A": 0.0,
        "B": 0.5,
        "C": 1.0,
    }

    metrics_by_group = compute_candidate_metrics_by_group(scores)

    assert "ungrouped" in metrics_by_group
    assert metrics_by_group["ungrouped"]["mean"] == pytest.approx(0.5)
    assert metrics_by_group["ungrouped"]["min"] == pytest.approx(0.0)
    assert metrics_by_group["ungrouped"]["max"] == pytest.approx(1.0)
    assert metrics_by_group["ungrouped"]["range"] == pytest.approx(1.0)
    assert metrics_by_group["ungrouped"]["n_dimensions"] == 3
