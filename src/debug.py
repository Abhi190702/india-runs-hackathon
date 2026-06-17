"""Debug artifact writers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from scoring import debug_value


DEBUG_FIELDS = [
    "candidate_id",
    "rank",
    "final_score",
    "raw_score",
    "technical_fit",
    "hireability_fit",
    "trust_consistency_fit",
    "career_evidence_fit",
    "retrieval_ranking_fit",
    "production_system_fit",
    "role_title_fit",
    "skill_quality_fit",
    "experience_fit",
    "product_startup_fit",
    "coding_recency_fit",
    "anomaly_penalty",
    "score_cap",
    "hard_honeypot",
    "hard_flags",
    "soft_flags",
    "cap_reasons",
    "semantic_score",
    "current_title",
    "years",
    "location",
    "reasoning",
    "matched_evidence",
]


def ensure_parent(path):
    parent = Path(path).parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)


def write_debug_json(path, rows):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=True, indent=2, sort_keys=True)


def write_debug_csv(path, rows):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DEBUG_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: debug_value(row.get(field, "")) for field in DEBUG_FIELDS})
