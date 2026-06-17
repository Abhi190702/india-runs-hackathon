from conftest import make_candidate
from scoring import score_candidate_v2


def test_reasoning_non_empty_and_grounded():
    row = score_candidate_v2(make_candidate(), semantic_score=0.0)
    assert row["reasoning"]
    assert "Senior ML Engineer" in row["reasoning"]
    assert "career evidence" in row["reasoning"]
