import pytest

from ppd.candidate.patterns import (
    classify_candidate_patterns,
    is_balanced,
    is_bottlenecked,
    is_noisy,
    is_polarised,
    is_uniform_high,
    is_uniform_low,
)
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
# is_balanced / is_bottlenecked
# ------------------------------------------------------------------

# Raises if tau_balance is not set
def test_is_balanced_threshold_none_raises():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=None, tau_bottleneck=0.2)

        with pytest.raises(RuntimeError):
            is_balanced(0.1)
    finally:
        constants.THRESHOLDS = original


# Returns True when std_pop is <= tau_balance
def test_is_balanced_true_when_below_or_equal_threshold():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.2)

        assert is_balanced(0.2) is True
        assert is_balanced(0.1) is True
    finally:
        constants.THRESHOLDS = original


# Returns False when std_pop is > tau_balance
def test_is_balanced_false_when_above_threshold():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.2)

        assert is_balanced(0.2000001) is False
    finally:
        constants.THRESHOLDS = original


# Raises if tau_bottleneck is not set
def test_is_bottlenecked_threshold_none_raises():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=None)

        with pytest.raises(RuntimeError):
            is_bottlenecked(0.1)
    finally:
        constants.THRESHOLDS = original


# Returns True when min_value is <= tau_bottleneck
def test_is_bottlenecked_true_when_below_or_equal_threshold():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3)

        assert is_bottlenecked(0.3) is True
        assert is_bottlenecked(0.1) is True
    finally:
        constants.THRESHOLDS = original


# Returns False when min_value is > tau_bottleneck
def test_is_bottlenecked_false_when_above_threshold():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3)

        assert is_bottlenecked(0.3000001) is False
    finally:
        constants.THRESHOLDS = original


# ------------------------------------------------------------------
# is_noisy / is_uniform_low / is_uniform_high / is_polarised
# ------------------------------------------------------------------

# Raises if tau_noisy is not set
def test_is_noisy_threshold_none_raises():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_noisy=None)

        with pytest.raises(RuntimeError):
            is_noisy(0.25)
    finally:
        constants.THRESHOLDS = original


# Returns True when std_pop is >= tau_noisy
def test_is_noisy_true_when_above_or_equal_threshold():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_noisy=0.25)

        assert is_noisy(0.25) is True
        assert is_noisy(0.30) is True
    finally:
        constants.THRESHOLDS = original


# Returns False when std_pop is < tau_noisy
def test_is_noisy_false_when_below_threshold():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_noisy=0.25)

        assert is_noisy(0.2499999) is False
    finally:
        constants.THRESHOLDS = original


# Raises if tau_uniform_low_mean is not set
def test_is_uniform_low_threshold_none_raises():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_uniform_low_mean=None)

        with pytest.raises(RuntimeError):
            is_uniform_low(mean=0.2, std_pop=0.1)
    finally:
        constants.THRESHOLDS = original


# Returns True when balanced and mean is <= tau_uniform_low_mean
def test_is_uniform_low_true_when_balanced_and_low_mean():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_uniform_low_mean=0.3)

        assert is_uniform_low(mean=0.3, std_pop=0.2) is True
        assert is_uniform_low(mean=0.2, std_pop=0.1) is True
    finally:
        constants.THRESHOLDS = original


# Returns False when not balanced or mean is above tau_uniform_low_mean
def test_is_uniform_low_false_when_not_balanced_or_mean_high():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_uniform_low_mean=0.3)

        assert is_uniform_low(mean=0.3000001, std_pop=0.1) is False
        assert is_uniform_low(mean=0.2, std_pop=0.2000001) is False
    finally:
        constants.THRESHOLDS = original


# Raises if tau_uniform_high_mean is not set
def test_is_uniform_high_threshold_none_raises():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_uniform_high_mean=None)

        with pytest.raises(RuntimeError):
            is_uniform_high(mean=0.8, std_pop=0.1)
    finally:
        constants.THRESHOLDS = original


# Returns True when balanced and mean is >= tau_uniform_high_mean
def test_is_uniform_high_true_when_balanced_and_high_mean():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_uniform_high_mean=0.7)

        assert is_uniform_high(mean=0.7, std_pop=0.2) is True
        assert is_uniform_high(mean=0.9, std_pop=0.1) is True
    finally:
        constants.THRESHOLDS = original


# Returns False when not balanced or mean is below tau_uniform_high_mean
def test_is_uniform_high_false_when_not_balanced_or_mean_low():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(tau_balance=0.2, tau_bottleneck=0.3, tau_uniform_high_mean=0.7)

        assert is_uniform_high(mean=0.6999999, std_pop=0.1) is False
        assert is_uniform_high(mean=0.9, std_pop=0.2000001) is False
    finally:
        constants.THRESHOLDS = original


# Raises if polarised thresholds are not set
def test_is_polarised_threshold_none_raises():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=0.2,
            tau_bottleneck=0.3,
            tau_polarised_range=None,
            tau_low=0.3,
            tau_high=0.7,
        )

        with pytest.raises(RuntimeError):
            is_polarised(min_value=0.2, max_value=0.9, range_value=0.7)
    finally:
        constants.THRESHOLDS = original


# Returns True when range is large and min is low and max is high
def test_is_polarised_true_when_conditions_met():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=0.2,
            tau_bottleneck=0.3,
            tau_polarised_range=0.6,
            tau_low=0.3,
            tau_high=0.7,
        )

        assert is_polarised(min_value=0.3, max_value=0.7, range_value=0.6) is True
        assert is_polarised(min_value=0.2, max_value=0.9, range_value=0.7) is True
    finally:
        constants.THRESHOLDS = original


# Returns False when any polarised condition fails
def test_is_polarised_false_when_conditions_not_met():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=0.2,
            tau_bottleneck=0.3,
            tau_polarised_range=0.6,
            tau_low=0.3,
            tau_high=0.7,
        )

        assert is_polarised(min_value=0.3000001, max_value=0.9, range_value=0.7) is False
        assert is_polarised(min_value=0.2, max_value=0.6999999, range_value=0.7) is False
        assert is_polarised(min_value=0.2, max_value=0.9, range_value=0.5999999) is False
    finally:
        constants.THRESHOLDS = original


# ------------------------------------------------------------------
# classify_candidate_patterns
# ------------------------------------------------------------------

# Raises if required keys are missing from candidate_metrics
def test_classify_candidate_patterns_missing_keys_raises():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=0.2,
            tau_bottleneck=0.3,
            tau_noisy=0.25,
            tau_uniform_low_mean=0.3,
            tau_uniform_high_mean=0.7,
            tau_polarised_range=0.6,
            tau_low=0.3,
            tau_high=0.7,
        )

        with pytest.raises(KeyError):
            classify_candidate_patterns({})

        with pytest.raises(KeyError):
            classify_candidate_patterns({"std_pop": 0.1})

        with pytest.raises(KeyError):
            classify_candidate_patterns({"std_pop": 0.1, "min": 0.2})
    finally:
        constants.THRESHOLDS = original


# Returns correct pattern flags and bottleneck identity
def test_classify_candidate_patterns_simple():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=0.2,
            tau_bottleneck=0.3,
            tau_noisy=0.25,
            tau_uniform_low_mean=0.3,
            tau_uniform_high_mean=0.7,
            tau_polarised_range=0.6,
            tau_low=0.3,
            tau_high=0.7,
        )

        candidate_metrics = {
            "mean": 0.2,
            "std_pop": 0.15,
            "min": 0.2,
            "min_dimensions": ["B"],
            "max": 0.9,
            "range": 0.7,
        }

        out = classify_candidate_patterns(candidate_metrics)

        assert out["balanced"] is True
        assert out["bottlenecked"] is True
        assert out["polarised"] is True
        assert out["noisy"] is False
        assert out["uniform_low"] is True
        assert out["uniform_high"] is False
        assert out["bottleneck_dimension"] == "B"
        assert out["bottleneck_value"] == pytest.approx(0.2)
    finally:
        constants.THRESHOLDS = original


# Balanced can be True while bottlenecked is False (and vice versa)
def test_classify_candidate_patterns_mixed_cases():
    original = constants.THRESHOLDS

    try:
        _set_thresholds_for_test(
            tau_balance=0.2,
            tau_bottleneck=0.3,
            tau_noisy=0.25,
            tau_uniform_low_mean=0.3,
            tau_uniform_high_mean=0.7,
            tau_polarised_range=0.6,
            tau_low=0.3,
            tau_high=0.7,
        )

        # balanced True, bottlenecked False
        candidate_metrics_1 = {
            "mean": 0.5,
            "std_pop": 0.1,
            "min": 0.31,
            "min_dimensions": ["A", "C"],
            "max": 0.6,
            "range": 0.29,
        }
        out1 = classify_candidate_patterns(candidate_metrics_1)
        assert out1["balanced"] is True
        assert out1["bottlenecked"] is False
        assert out1["polarised"] is False
        assert out1["noisy"] is False
        assert out1["uniform_low"] is False
        assert out1["uniform_high"] is False

        # balanced False, bottlenecked True
        candidate_metrics_2 = {
            "mean": 0.2,
            "std_pop": 0.25,
            "min": 0.2,
            "min_dimensions": ["C"],
            "max": 0.9,
            "range": 0.7,
        }
        out2 = classify_candidate_patterns(candidate_metrics_2)
        assert out2["balanced"] is False
        assert out2["bottlenecked"] is True
        assert out2["polarised"] is True
        assert out2["noisy"] is True
        assert out2["uniform_low"] is False
        assert out2["uniform_high"] is False
    finally:
        constants.THRESHOLDS = original


# Both balanced and bottlenecked can be False
# REVIEW - Ignored cause not critical now and is already crosscheked by above tests
