"""Hireability helpers retained for V1-compatible callers."""

from evidence import match_concepts_by_source
from features import compute_all_features, compute_hireability_fit


def availability_multiplier(candidate, today=None):
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence, today=today)
    hireability = compute_hireability_fit(features)
    notes = []
    if features.get("recent_activity_fit", 1.0) < 0.45:
        notes.append("inactive >180 days")
    if features.get("recruiter_response_fit", 1.0) < 0.35:
        notes.append("low response rate")
    if features.get("notice_period_fit", 1.0) < 0.45:
        notes.append("long notice")
    return hireability, notes
