"""Lightweight local TF-IDF semantic layer.

This is deliberately small: it catches relevant plain-language profiles, but it
only blends as a 10% technical-fit boost and never calls network APIs.
"""

from __future__ import annotations

import math

import jd
from parser import flatten_candidate, join_text


def build_jd_semantic_text():
    parts = [
        "Senior AI Engineer founding team",
        "production retrieval ranking embeddings vector search semantic search hybrid search",
        "recommendation systems search relevance candidate matching learning to rank",
        "NDCG MRR MAP offline evaluation online evaluation human relevance labels",
        "Python NLP ML pipelines APIs monitoring latency scalable deployed systems",
    ]
    for name in jd.positive_concept_names():
        parts.extend(jd.CONCEPT_GROUPS[name]["phrases"])
    return join_text(parts)


def candidate_semantic_text(candidate):
    flat = flatten_candidate(candidate)
    text = join_text(
        [
            flat["current_title"],
            flat["headline"],
            flat["summary"],
            flat["current_role_description_text"],
            flat["career_description_text"][:350],
            flat["company_industry_text"],
        ]
    )
    return text[:700]


def compute_semantic_scores(candidates):
    """Return (scores, enabled, warning). Scores are normalized 0..1."""
    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception as exc:
        return [0.0 for _ in candidates], False, f"semantic disabled: {exc}"

    if not candidates:
        return [], True, ""

    jd_text = build_jd_semantic_text()
    candidate_texts = [candidate_semantic_text(c) for c in candidates]
    docs = [jd_text] + candidate_texts
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 1),
        min_df=2,
        max_df=0.88,
        max_features=5000,
        dtype=np.float32,
    )
    matrix = vectorizer.fit_transform(docs)
    sims = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    if sims.size == 0:
        return [], True, ""
    max_sim = float(sims.max())
    min_sim = float(sims.min())
    if math.isclose(max_sim, min_sim):
        normalized = [float(max_sim > 0)] * len(candidates)
    else:
        normalized = [float((s - min_sim) / (max_sim - min_sim)) for s in sims]
    return [max(0.0, min(1.0, s)) for s in normalized], True, ""
