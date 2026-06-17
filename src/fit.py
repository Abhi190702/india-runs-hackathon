"""Compatibility wrapper around the V2 technical fit engine."""

from evidence import match_concepts_by_source
from features import compute_all_features, compute_technical_fit


def score_fit(candidate, today=None):
    evidence = match_concepts_by_source(candidate)
    features = compute_all_features(candidate, evidence=evidence, today=today)
    fit = compute_technical_fit(features)
    ev = {
        "matched_must": features.get("evidence_summary", {}).get("career_backed_concepts", []),
        "matched_nice": [],
        "penalties": [],
        "notes": [],
        "concept_score": round(features.get("retrieval_ranking_fit", 0.0), 3),
        "trajectory_score": round(features.get("career_evidence_fit", 0.0), 3),
        "penalty": 1.0,
        "product_ratio": round(features.get("product_startup_fit", 0.0), 2),
        "years": candidate.get("profile", {}).get("years_of_experience", 0) or 0,
    }
    return fit, ev
