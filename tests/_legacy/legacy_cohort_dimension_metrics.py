import pandas as pd
import pytest

from ppd.cohort.dimension_metrics import (
    compute_breach_rate,
    compute_mean,
    compute_percentiles,
    compute_std_sample,
    summarize_dimensions,
)


# ------------------------------------------------------------------
# core stat helpers
# ------------------------------------------------------------------

# Mean works on simple numeric array
def test_compute_mean_basic():
    import numpy as np

    values = np.array([1.0, 2.0, 3.0], dtype=float)
    assert compute_mean(values) == pytest.approx(2.0)


# Sample std returns None for n < 2
def test_compute_std_sample_returns_none_for_single_value():
    import numpy as np

    values = np.array([1.0], dtype=float)
    assert compute_std_sample(values) is None


# Sample std matches ddof=1
def test_compute_std_sample_basic():
    import numpy as np

    values = np.array([1.0, 2.0, 3.0], dtype=float)
    # sample std for [1,2,3] is 1.0
    assert compute_std_sample(values) == pytest.approx(1.0)


# Breach rate uses strict less-than
def test_compute_breach_rate_strict():
    import numpy as np

    values = np.array([0.2, 0.3, 0.3, 0.4], dtype=float)
    assert compute_breach_rate(values, threshold=0.3) == pytest.approx(0.25)


# Percentiles produce expected keys and values
def test_compute_percentiles_basic():
    import numpy as np

    values = np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=float)
    out = compute_percentiles(values, probs=(0.5,))

    assert "p50" in out
    assert out["p50"] == pytest.approx(2.0)


# ------------------------------------------------------------------
# summarize_dimensions
# ------------------------------------------------------------------

# Summarize dimensions ignores candidate_id and computes stats
def test_summarize_dimensions_ignores_id_col_and_computes_stats():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "A": 0.0, "B": 1.0},
            {"candidate_id": "c2", "A": 1.0, "B": 1.0},
            {"candidate_id": "c3", "A": 2.0, "B": 3.0},
        ]
    )

    out = summarize_dimensions(df, id_col="candidate_id", threshold=1.0, include_percentiles=False)

    assert out["n_candidates"] == 3
    assert "A" in out["dimensions"]
    assert "B" in out["dimensions"]
    assert "candidate_id" not in out["dimensions"]

    # A mean = (0+1+2)/3 = 1
    assert out["dimensions"]["A"]["mean"] == pytest.approx(1.0)

    # A breach_rate threshold=1.0 => values < 1.0 => [0.0] => 1/3
    assert out["dimensions"]["A"]["breach_rate"] == pytest.approx(1.0 / 3.0)

    # B mean = (1+1+3)/3 = 5/3
    assert out["dimensions"]["B"]["mean"] == pytest.approx(5.0 / 3.0)


# Percentiles included when requested
def test_summarize_dimensions_includes_percentiles_when_enabled():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "A": 0.0},
            {"candidate_id": "c2", "A": 1.0},
            {"candidate_id": "c3", "A": 2.0},
            {"candidate_id": "c4", "A": 3.0},
            {"candidate_id": "c5", "A": 4.0},
        ]
    )

    out = summarize_dimensions(df, id_col="candidate_id", include_percentiles=True, percentile_probs=(0.5,))

    assert out["dimensions"]["A"]["percentiles"] is not None
    assert out["dimensions"]["A"]["percentiles"]["p50"] == pytest.approx(2.0)


# Threshold None -> breach_rate None
def test_summarize_dimensions_threshold_none_sets_breach_rate_none():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "A": 0.0},
            {"candidate_id": "c2", "A": 1.0},
        ]
    )

    out = summarize_dimensions(df, id_col="candidate_id", threshold=None)

    assert out["dimensions"]["A"]["breach_rate"] is None


# Non-numeric values should raise
def test_summarize_dimensions_non_numeric_raises():
    df = pd.DataFrame(
        [
            {"candidate_id": "c1", "A": "nope"},
            {"candidate_id": "c2", "A": "still nope"},
        ]
    )

    with pytest.raises(Exception):
        summarize_dimensions(df, id_col="candidate_id")
