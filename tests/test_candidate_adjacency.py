import pytest

from ppd.candidate.adjacency import compute_adjacency_energy


# ------------------------------------------------------------------
# compute_adjacency_energy
# ------------------------------------------------------------------

# Raises if the ordered dimension list is empty
def test_compute_adjacency_energy_empty_order_raises():
    with pytest.raises(ValueError):
        compute_adjacency_energy([], {"A": 0.1})


# Raises if a required dimension is missing from scores
def test_compute_adjacency_energy_missing_dimension_raises():
    ordered = ["A", "B"]
    scores = {"A": 0.2}

    with pytest.raises(KeyError):
        compute_adjacency_energy(ordered, scores)


# Returns 0.0 for a single dimension (no adjacency variation)
def test_compute_adjacency_energy_single_dimension_is_zero():
    ordered = ["A"]
    scores = {"A": 0.7}

    result = compute_adjacency_energy(ordered, scores)
    assert result == pytest.approx(0.0)


# Computes cyclic adjacency energy correctly for a simple 3-point case
def test_compute_adjacency_energy_three_dimensions_simple():
    ordered = ["A", "B", "C"]
    scores = {"A": 0.0, "B": 1.0, "C": 0.0}

    # diffs: |A-B|=1, |B-C|=1, |C-A|=0 => mean = 2/3
    result = compute_adjacency_energy(ordered, scores)
    assert result == pytest.approx(2.0 / 3.0)


# Order matters: a different ordering should generally produce a different D
def test_compute_adjacency_energy_order_changes_value():
    scores = {"A": 0.0, "B": 1.0, "C": 0.0}

    ordered_1 = ["A", "B", "C"]  # diffs: 1,1,0 => 2/3
    ordered_2 = ["A", "C", "B"]  # diffs: 0,1,1 => 2/3 (same here, so pick a better example)

    scores2 = {"A": 0.0, "B": 0.2, "C": 1.0}
    ordered_1 = ["A", "B", "C"]  # diffs: 0.2, 0.8, 1.0 => mean = 2.0/3
    ordered_2 = ["A", "C", "B"]  # diffs: 1.0, 0.8, 0.2 => mean = 2.0/3 (still same by symmetry)

    scores3 = {"A": 0.0, "B": 0.9, "C": 0.2}
    ordered_1 = ["A", "B", "C"]  # diffs: 0.9, 0.7, 0.2 => mean = 0.6
    ordered_2 = ["A", "C", "B"]  # diffs: 0.2, 0.7, 0.9 => mean = 0.6 (still same...)

    # Use 4 dimensions to avoid symmetry effects
    scores4 = {"A": 0.0, "B": 1.0, "C": 0.0, "D": 0.0}
    ordered_1 = ["A", "B", "C", "D"]  # diffs: 1,1,0,0 => mean = 0.5
    ordered_2 = ["A", "C", "B", "D"]  # diffs: 0,1,1,0 => mean = 0.5 (still same)

    scores5 = {"A": 0.0, "B": 0.8, "C": 0.1, "D": 1.0}
    ordered_1 = ["A", "B", "C", "D"]  # |0-0.8|=0.8, |0.8-0.1|=0.7, |0.1-1|=0.9, |1-0|=1.0 => mean=0.85
    ordered_2 = ["A", "C", "B", "D"]  # |0-0.1|=0.1, |0.1-0.8|=0.7, |0.8-1|=0.2, |1-0|=1.0 => mean=0.5

    d1 = compute_adjacency_energy(ordered_1, scores5)
    d2 = compute_adjacency_energy(ordered_2, scores5)

    assert d1 != pytest.approx(d2)
    assert d1 == pytest.approx(0.85)
    assert d2 == pytest.approx(0.5)

