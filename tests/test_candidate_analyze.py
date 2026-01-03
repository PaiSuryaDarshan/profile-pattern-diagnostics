import pytest

from ppd.candidate.analyze import analyze_candidate
from ppd.schema import constants


# ------------------------------------------------------------------
# Helpers (set/reset thresholds safely for tests)
# ------------------------------------------------------------------

def _set_thresholds_for_test(
    tau_balance,
    tau_bottleneck,
    tau_operational=None,
    tau_noisy=None,
    tau_uniform_low_mean=None,
    tau_uniform_high_mean=None,
    tau_polarised_range=None,
    tau_low=None,
    tau_high=None,
):
    constants.THRESHOLDS = constants.Thresholds(
        tau_balance=tau_balance,
        tau_bottleneck=tau_bottleneck,
        tau_operational=tau_operational,
        tau_noisy=tau_noisy,
        tau_uniform_low_mean=tau_uniform_low_mean,
        tau_uniform_high_mean=tau_uniform_high_mean,
        tau_polarised_range=tau_polarised_range,
        tau_low=tau_low,
        tau_high=tau_high,
    )


# ------------------------------------------------------------------
# analyze_candidate
# ------------------------------------------------------------------

# Raises on empty input
def test_analyze_candidate_empty_input_raises():
    with pytest.raises(ValueError):
        analyze_candidate({})


# Produces basic outputs (raw, norm, metrics_by_group) when patterns/adjacency are off
def test_analyze_candidate_basic_no_patterns_no_adjacency():
    raw_scores = {"A": 0.0, "B": 2.5, "C": 5.0}

    result = analyze_candidate(
        raw_scores,
        include_adjacency=False,
        include_patterns=False,
    )

    assert "scores_raw" in result
    assert "scores_norm" in result
    assert "metrics_by_group" in result

    assert result["scores_norm"]["A"] == pytest.approx(0.0)
    assert result["scores_norm"]["B"] == pytest.approx(0.5)
    assert result["scores_norm"]["C"] == pytest.approx(1.0)


# Computes adjacency when an explicit order is provided
def test_analyze_candidate_with_adjacency_explicit_order():
    raw_scores = {"A": 0.0, "B": 5.0, "C": 0.0}
    order = ["A", "B", "C"]

    result = analyze_candidate(
        raw_scores,
        ordered_dimensions=order,
        include_adjacency=True,
        include_patterns=False,
    )

    assert result["adjacency_D"] == pytest.approx(2.0 / 3.0)
    assert result["adjacency_order"] == order


# If adjacency is enabled but no order is provided, adjacency should be None
def test_analyze_candidate_with_adjacency_no_order_results_in_none():
    raw_scores = {"A": 0.0, "B": 2.5, "C": 5.0}

    result = analyze_candidate(
        raw_scores,
        ordered_dimensions=None,
        include_adjacency=True,
        include_patterns=False,
    )

    assert result["adjacency_D"] is None
    assert result["adjacency_order"] is None


# Patterns are None when thresholds are not set
def test_analyze_candidate_patterns_none_when_thresholds_missing():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=None,
            tau_bottleneck=None,
            tau_operational=None,
            tau_noisy=None,
            tau_uniform_low_mean=None,
            tau_uniform_high_mean=None,
            tau_polarised_range=None,
            tau_low=None,
            tau_high=None,
        )

        raw_scores = {"A": 0.0, "B": 2.5, "C": 5.0}

        result = analyze_candidate(
            raw_scores,
            include_adjacency=False,
            include_patterns=True,
        )

        assert result["patterns_by_group"] is None
    finally:
        constants.THRESHOLDS = original


# Patterns are computed when thresholds are set
def test_analyze_candidate_patterns_present_when_thresholds_set():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=0.2,
            tau_bottleneck=0.3,
            tau_operational=None,
            tau_noisy=0.25,
            tau_uniform_low_mean=0.3,
            tau_uniform_high_mean=0.7,
            tau_polarised_range=0.6,
            tau_low=0.3,
            tau_high=0.7,
        )

        raw_scores = {"A": 0.0, "B": 2.5, "C": 5.0}

        result = analyze_candidate(
            raw_scores,
            include_adjacency=False,
            include_patterns=True,
        )

        assert result["patterns_by_group"] is not None
        assert "ungrouped" in result["patterns_by_group"]
        assert "balanced" in result["patterns_by_group"]["ungrouped"]
        assert "bottlenecked" in result["patterns_by_group"]["ungrouped"]
        assert "polarised" in result["patterns_by_group"]["ungrouped"]
        assert "noisy" in result["patterns_by_group"]["ungrouped"]
        assert "uniform_low" in result["patterns_by_group"]["ungrouped"]
        assert "uniform_high" in result["patterns_by_group"]["ungrouped"]
    finally:
        constants.THRESHOLDS = original
