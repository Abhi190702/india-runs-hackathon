from conftest import make_candidate
from evidence import match_concepts_by_source
from features import compute_all_features


def test_skills_only_evidence_cannot_dominate():
    candidate = make_candidate()
    candidate["profile"]["summary"] = ""
    candidate["career_history"][0]["description"] = "Managed operational reporting and dashboards."
    candidate["skills"] = [
        {"name": "FAISS", "proficiency": "expert", "endorsements": 50, "duration_months": 30},
        {"name": "NDCG", "proficiency": "expert", "endorsements": 50, "duration_months": 30},
        {"name": "Vector Search", "proficiency": "expert", "endorsements": 50, "duration_months": 30},
    ]
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence)
    assert features["retrieval_ranking_fit"] <= 0.45


def test_experience_fit_sweet_spot():
    features = compute_all_features(make_candidate())
    assert features["experience_fit"] == 1.0
