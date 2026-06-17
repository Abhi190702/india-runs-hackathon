from conftest import make_candidate
from evidence import match_concepts_by_source
from features import compute_all_features
from anomalies import analyze_anomalies


def test_hard_honeypot_detected():
    candidate = make_candidate()
    candidate["career_history"][0]["end_date"] = "2025-01-01"
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence)
    result = analyze_anomalies(candidate, features, evidence)
    assert result["hard_honeypot"] is True
    assert result["anomaly_penalty"] >= 0.5


def test_current_tenure_date_contradiction_is_hard():
    candidate = make_candidate()
    candidate["career_history"][0]["start_date"] = "2025-01-01"
    candidate["career_history"][0]["duration_months"] = 48
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence)
    result = analyze_anomalies(candidate, features, evidence)
    assert result["hard_honeypot"] is True
    assert any("current tenure/date contradiction" in flag for flag in result["hard_flags"])


def test_zero_month_expert_cluster_is_hard():
    candidate = make_candidate()
    candidate["skills"] = [
        {"name": "Python", "proficiency": "expert", "endorsements": 2, "duration_months": 0},
        {"name": "FAISS", "proficiency": "expert", "endorsements": 1, "duration_months": 0},
        {"name": "MLflow", "proficiency": "expert", "endorsements": 3, "duration_months": 0},
        {"name": "NLP", "proficiency": "advanced", "endorsements": 8, "duration_months": 24},
    ]
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence)
    result = analyze_anomalies(candidate, features, evidence)
    assert result["hard_honeypot"] is True
    assert "3+ expert skills with 0 months and weak endorsements" in result["hard_flags"]


def test_inactive_soft_anomaly():
    candidate = make_candidate()
    candidate["redrob_signals"]["last_active_date"] = "2025-01-01"
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence)
    result = analyze_anomalies(candidate, features, evidence)
    assert "inactive >180 days" in result["soft_flags"]
