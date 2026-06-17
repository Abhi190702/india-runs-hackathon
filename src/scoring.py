"""V2 scoring engine."""

from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor

from anomalies import analyze_anomalies
from caps import compute_score_cap
from evidence import get_top_evidence_snippets, match_concepts_by_source, summarize_evidence
from features import (
    compute_all_features,
    compute_hireability_fit,
    compute_technical_fit,
    compute_trust_consistency_fit,
)
from parser import clamp, flatten_candidate
from reasoning import build_reasoning


PARALLEL_CHUNKSIZE = 512


def _round(value):
    return round(clamp(value), 6)


def score_candidate_v2(candidate, semantic_score=None, today=None, include_reasoning=True):
    flat = flatten_candidate(candidate)
    evidence = match_concepts_by_source(candidate, with_snippets=include_reasoning)
    features = compute_all_features(candidate, evidence=evidence, today=today)
    evidence_summary = summarize_evidence(evidence) if include_reasoning else None

    base_technical_fit = compute_technical_fit(features)
    semantic = clamp(semantic_score if semantic_score is not None else 0.0)
    technical_fit = clamp(0.90 * base_technical_fit + 0.10 * semantic) if semantic_score is not None else base_technical_fit
    hireability_fit = compute_hireability_fit(features)
    trust_consistency_fit = compute_trust_consistency_fit(features)

    anomalies = analyze_anomalies(candidate, features, evidence, today=today)
    cap = compute_score_cap(candidate, features, anomalies, evidence)

    raw_score = clamp(
        0.72 * technical_fit
        + 0.18 * hireability_fit
        + 0.10 * trust_consistency_fit
    )
    penalized_score = raw_score - anomalies["anomaly_penalty"]
    final_score = clamp(min(penalized_score, cap["score_cap"]))

    matched_concepts = []
    matched_evidence = []
    if include_reasoning:
        matched_concepts = [
            name
            for name in evidence_summary["career_backed_concepts"]
            if name not in {"negative_wrong_domain", "weak_or_adjacent_domain"}
        ]
        if not matched_concepts:
            matched_concepts = [
                name
                for name in evidence_summary["by_concept"]
                if name not in {"negative_wrong_domain", "weak_or_adjacent_domain"}
            ]
        matched_evidence = get_top_evidence_snippets(evidence, limit=5)

    row = {
        "candidate_id": flat["candidate_id"],
        "final_score": _round(final_score),
        "raw_score": _round(raw_score),
        "technical_fit": _round(technical_fit),
        "hireability_fit": _round(hireability_fit),
        "trust_consistency_fit": _round(trust_consistency_fit),
        "career_evidence_fit": _round(features["career_evidence_fit"]),
        "retrieval_ranking_fit": _round(features["retrieval_ranking_fit"]),
        "production_system_fit": _round(features["production_system_fit"]),
        "role_title_fit": _round(features["role_title_fit"]),
        "skill_quality_fit": _round(features["skill_quality_fit"]),
        "experience_fit": _round(features["experience_fit"]),
        "product_startup_fit": _round(features["product_startup_fit"]),
        "coding_recency_fit": _round(features["coding_recency_fit"]),
        "recent_activity_fit": _round(features["recent_activity_fit"]),
        "recruiter_response_fit": _round(features["recruiter_response_fit"]),
        "avg_response_time_fit": _round(features["avg_response_time_fit"]),
        "notice_period_fit": _round(features["notice_period_fit"]),
        "location_fit": _round(features["location_fit"]),
        "work_mode_fit": _round(features["work_mode_fit"]),
        "relocation_fit": _round(features["relocation_fit"]),
        "anomaly_penalty": round(anomalies["anomaly_penalty"], 6),
        "score_cap": round(cap["score_cap"], 6),
        "hard_honeypot": anomalies["hard_honeypot"],
        "hard_flags": anomalies["hard_flags"],
        "soft_flags": anomalies["soft_flags"],
        "risk_level": anomalies["risk_level"],
        "cap_reasons": cap["cap_reasons"],
        "matched_evidence": matched_evidence,
        "matched_concepts": matched_concepts,
        "semantic_score": _round(semantic) if semantic_score is not None else 0.0,
        "current_title": flat["current_title"],
        "years": flat["years"],
        "location": flat["location"],
        "country": flat["country"],
    }
    if include_reasoning:
        row["evidence_summary"] = evidence_summary
        row["reasoning"] = build_reasoning(candidate, row)
    else:
        row["reasoning"] = ""
    return row


def sort_key(row):
    return (
        -row["final_score"],
        -row["technical_fit"],
        -row["career_evidence_fit"],
        -row["retrieval_ranking_fit"],
        -row["production_system_fit"],
        -row["hireability_fit"],
        row["anomaly_penalty"],
        row["candidate_id"],
    )


def _score_task(task):
    index, candidate, semantic_score, today, include_reasoning = task
    row = score_candidate_v2(
        candidate,
        semantic_score=semantic_score,
        today=today,
        include_reasoning=include_reasoning,
    )
    row["_candidate_index"] = index
    return row


def rank_candidates_v2(candidates, semantic_scores=None, today=None, include_reasoning=True, workers=1, timings=None):
    semantic_scores = semantic_scores if semantic_scores is not None else [None] * len(candidates)
    tasks = (
        (i, candidate, semantic_scores[i], today, include_reasoning)
        for i, candidate in enumerate(candidates)
    )
    scoring_start = time.perf_counter()
    if workers and workers > 1 and len(candidates) >= 5000 and not include_reasoning:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            rows = list(executor.map(_score_task, tasks, chunksize=PARALLEL_CHUNKSIZE))
    else:
        rows = [_score_task(task) for task in tasks]
    if timings is not None:
        timings["scoring_time"] = time.perf_counter() - scoring_start
    sorting_start = time.perf_counter()
    rows.sort(key=sort_key)
    if timings is not None:
        timings["sorting_time"] = time.perf_counter() - sorting_start
    return rows


def debug_value(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    return value
