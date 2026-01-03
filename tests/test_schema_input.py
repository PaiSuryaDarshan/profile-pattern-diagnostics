import pytest

from ppd.schema.input_schema import (
    flatten_scores,
    validate_candidate_input,
)


# ------------------------------------------------------------------
# validate_candidate_input
# ------------------------------------------------------------------

# Valid payload passes and returns identity + nested scores
def test_validate_candidate_input_valid_payload():
    payload = {
        "candidate": {
            "id": 123,
            "email": "x@y.com",
            "phone_number": "+44-7000000000",
            "linkedin_tag": "linkedin.com/in/x",
        },
        "scores": {
            "Communication Skills": {"Grammar": 4, "Fluency": 3.5},
            "Cognitive Insights": {"Logical Reasoning": 4},
        },
    }

    identity, scores_nested = validate_candidate_input(payload)

    assert identity.id == 123
    assert identity.email == "x@y.com"
    assert identity.phone_number == "+44-7000000000"
    assert identity.linkedin_tag == "linkedin.com/in/x"

    assert "Communication Skills" in scores_nested
    assert scores_nested["Communication Skills"]["Grammar"] == pytest.approx(4.0)
    assert scores_nested["Communication Skills"]["Fluency"] == pytest.approx(3.5)


# Missing candidate key raises
def test_validate_candidate_input_missing_candidate_raises():
    payload = {"scores": {"Communication Skills": {"Grammar": 4}}}

    with pytest.raises(ValueError):
        validate_candidate_input(payload)


# Missing scores key raises
def test_validate_candidate_input_missing_scores_raises():
    payload = {"candidate": {"id": 1, "email": "x", "phone_number": "y", "linkedin_tag": "z"}}

    with pytest.raises(ValueError):
        validate_candidate_input(payload)


# candidate.id must be int (not string)
def test_validate_candidate_input_id_not_int_raises():
    payload = {
        "candidate": {"id": False, "email": "x@y.com", "phone_number": "y", "linkedin_tag": "z"},
        "scores": {"Communication Skills": {"Grammar": 4}},
    }

    with pytest.raises(ValueError):
        validate_candidate_input(payload)


# candidate.id must not be bool
def test_validate_candidate_input_id_bool_raises():
    payload = {
        "candidate": {"id": True, "email": "x@y.com", "phone_number": "y", "linkedin_tag": "z"},
        "scores": {"Communication Skills": {"Grammar": 4}},
    }

    with pytest.raises(ValueError):
        validate_candidate_input(payload)


# Metric value must be numeric
def test_validate_candidate_input_metric_non_numeric_raises():
    payload = {
        "candidate": {"id": 1, "email": "x@y.com", "phone_number": "y", "linkedin_tag": "z"},
        "scores": {"Communication Skills": {"Grammar": "four"}},
    }

    with pytest.raises(ValueError):
        validate_candidate_input(payload)


# Metric value must not be bool
def test_validate_candidate_input_metric_bool_raises():
    payload = {
        "candidate": {"id": 1, "email": "x@y.com", "phone_number": "y", "linkedin_tag": "z"},
        "scores": {"Communication Skills": {"Grammar": False}},
    }

    with pytest.raises(ValueError):
        validate_candidate_input(payload)


# ------------------------------------------------------------------
# flatten_scores
# ------------------------------------------------------------------

# Flattening produces Category::Metric keys
def test_flatten_scores_creates_namespaced_keys():
    scores_nested = {
        "Communication Skills": {"Grammar": 4.0, "Fluency": 3.5},
        "Cognitive Insights": {"Grammar": 2.0},  # same metric name allowed across categories
    }

    flat = flatten_scores(scores_nested)

    assert flat["Communication Skills::Grammar"] == pytest.approx(4.0)
    assert flat["Communication Skills::Fluency"] == pytest.approx(3.5)
    assert flat["Cognitive Insights::Grammar"] == pytest.approx(2.0)
