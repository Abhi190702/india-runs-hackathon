"""Deterministic, grounded reasoning strings for submission rows."""

from __future__ import annotations

import jd
from parser import clean_text, flatten_candidate


def _short(text, limit=120):
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _concept_phrase(score_row):
    concepts = score_row.get("matched_concepts") or []
    labels = jd.concept_labels(concepts[:3])
    if not labels:
        return "limited direct retrieval/ranking evidence"
    return ", ".join(labels)


def _availability_note(score_row):
    notes = []
    if score_row.get("recent_activity_fit", 0.0) >= 0.85:
        notes.append("recently active")
    if score_row.get("recruiter_response_fit", 0.0) >= 0.70:
        notes.append("responsive to recruiters")
    if score_row.get("notice_period_fit", 0.0) <= 0.45:
        notes.append("long notice")
    if score_row.get("location_fit", 0.0) >= 0.90:
        notes.append("location aligns")
    return ", ".join(notes[:2])


def _concern(score_row):
    flags = score_row.get("soft_flags") or []
    caps = score_row.get("cap_reasons") or []
    if flags:
        return flags[0]
    if caps:
        return caps[0]
    if score_row.get("retrieval_ranking_fit", 0.0) < 0.35:
        return "retrieval/ranking evidence is thin"
    if score_row.get("production_system_fit", 0.0) < 0.35:
        return "production evidence is limited"
    return ""


def build_reasoning(candidate, score_row):
    flat = flatten_candidate(candidate)
    title = flat.get("current_title") or "professional"
    years = flat.get("years") or 0.0

    if score_row.get("hard_honeypot"):
        reason = score_row.get("hard_flags", ["internal consistency issue"])[0]
        return _short(f"{years:.1f} yrs as {title}; internal inconsistency detected ({reason}), so the profile is de-ranked.", 500)

    snippets = score_row.get("matched_evidence") or []
    evidence_clause = snippets[0] if snippets else _concept_phrase(score_row)
    jd_clause = _concept_phrase(score_row)
    availability = _availability_note(score_row)
    concern = _concern(score_row)

    parts = [
        f"{years:.1f} yrs as {title}",
        f"career evidence shows {_short(evidence_clause, 135)}",
        f"matching Redrob's {jd_clause} focus",
    ]
    if availability:
        parts.append(availability)
    sentence = "; ".join(parts) + "."
    if concern:
        sentence += f" Concern: {_short(concern, 90)}."
    return _short(sentence.replace("\n", " "), 500)
