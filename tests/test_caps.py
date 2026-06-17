from conftest import make_candidate
from scoring import score_candidate_v2


def test_wrong_domain_title_gets_cap():
    candidate = make_candidate()
    candidate["profile"]["current_title"] = "HR Manager"
    candidate["career_history"][0]["title"] = "HR Manager"
    candidate["career_history"][0]["description"] = "Managed payroll, onboarding, and HR operations."
    row = score_candidate_v2(candidate, semantic_score=0.0)
    assert row["score_cap"] <= 0.35


def test_hard_honeypot_gets_cap():
    candidate = make_candidate()
    candidate["career_history"][0]["end_date"] = "2025-01-01"
    row = score_candidate_v2(candidate, semantic_score=0.0)
    assert row["score_cap"] <= 0.20


def test_shallow_llm_only_gets_cap():
    candidate = make_candidate()
    candidate["profile"]["summary"] = "Built LangChain chatbot demos with OpenAI API."
    candidate["career_history"][0]["description"] = "Built LangChain chatbot demos with OpenAI API and prompt engineering."
    candidate["skills"] = [{"name": "LangChain", "proficiency": "advanced", "endorsements": 5, "duration_months": 8}]
    row = score_candidate_v2(candidate, semantic_score=0.0)
    assert row["score_cap"] <= 0.48


def test_no_production_evidence_gets_cap():
    candidate = make_candidate()
    candidate["career_history"][0]["description"] = "Explored embeddings and vector search in notebooks."
    row = score_candidate_v2(candidate, semantic_score=0.0)
    assert row["score_cap"] <= 0.65
