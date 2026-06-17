"""Compatibility wrapper for V2 hard honeypot detection."""

from anomalies import analyze_anomalies
from evidence import match_concepts_by_source
from features import compute_all_features


def audit_candidate(candidate, today=None):
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence, today=today)
    result = analyze_anomalies(candidate, features, evidence, today=today)
    return result["hard_honeypot"], result["hard_flags"]
