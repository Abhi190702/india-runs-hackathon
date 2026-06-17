from conftest import make_candidate
from scoring import score_candidate_v2


def test_scores_are_deterministic():
    candidate = make_candidate()
    first = score_candidate_v2(candidate, semantic_score=0.2)
    second = score_candidate_v2(candidate, semantic_score=0.2)
    assert first["final_score"] == second["final_score"]
    assert first["reasoning"] == second["reasoning"]


def test_v2_formula_outputs_expected_fields():
    row = score_candidate_v2(make_candidate(), semantic_score=0.2)
    assert 0.0 <= row["final_score"] <= 1.0
    assert "technical_fit" in row
    assert "hireability_fit" in row
    assert "trust_consistency_fit" in row
