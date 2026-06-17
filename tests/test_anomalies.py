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


def test_inactive_soft_anomaly():
    candidate = make_candidate()
    candidate["redrob_signals"]["last_active_date"] = "2025-01-01"
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence)
    result = analyze_anomalies(candidate, features, evidence)
    assert "inactive >180 days" in result["soft_flags"]
