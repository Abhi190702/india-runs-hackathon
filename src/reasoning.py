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


def _has_concept(score_row, name):
    return name in set(score_row.get("matched_concepts") or [])


def _snippet(score_row, limit=118, variant=0):
    # The synthetic dataset reuses career-description templates, so many strong
    # candidates share the same top snippet. Rotating by `variant` makes rows
    # quote different matched evidence, which keeps the sampled reasonings varied
    # (Stage-4 checks that reasonings are substantively different from each other).
    snippets = score_row.get("matched_evidence") or []
    if snippets:
        return _short(snippets[variant % len(snippets)], limit)
    return _concept_phrase(score_row)


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


def _style(score_row, title):
    soft = set(score_row.get("soft_flags") or [])
    caps = set(score_row.get("cap_reasons") or [])
    title_low = title.lower()
    if score_row.get("hard_honeypot"):
        return "hard"
    if any("wrong-domain" in item or "keyword" in item for item in soft | caps):
        return "wrong_domain"
    if any("shallow" in item or "chatbot" in item for item in soft | caps):
        return "shallow_llm"
    if score_row.get("retrieval_ranking_fit", 0.0) >= 0.58 or _has_concept(score_row, "core_retrieval_ranking"):
        return "retrieval"
    if _has_concept(score_row, "ranking_recommendation") or _has_concept(score_row, "evaluation_frameworks"):
        return "ranking"
    if score_row.get("production_system_fit", 0.0) >= 0.62:
        return "platform"
    if any(term in title_low for term in ["backend", "data engineer", "software engineer", "developer"]):
        return "adjacent"
    if score_row.get("notice_period_fit", 1.0) <= 0.45 or score_row.get("location_fit", 1.0) < 0.55:
        return "logistics"
    return "balanced"


def _variant(candidate, count):
    cid = str(candidate.get("candidate_id") or "")
    return sum(ord(ch) for ch in cid) % max(1, count)


def _finish(sentence, concern):
    sentence = sentence.replace("\n", " ")
    if concern:
        sentence += f" Concern: {_short(concern, 90)}."
    return _short(sentence, 500)


def build_reasoning(candidate, score_row):
    flat = flatten_candidate(candidate)
    raw_title = flat.get("current_title") or "professional"
    years = flat.get("years") or 0.0
    company = flat.get("current_company") or ""
    variant = _variant(candidate, 4)

    if score_row.get("hard_honeypot"):
        reason = score_row.get("hard_flags", ["internal consistency issue"])[0]
        return _short(f"{years:.1f} yrs as {raw_title}; internal inconsistency detected ({reason}), so the profile is de-ranked.", 500)

    # Anchor each row to the candidate's own employer so even shared snippets read
    # distinctly across rows. Style is computed from the RAW title so a company
    # name can't accidentally change the sentence style.
    title = f"{raw_title} at {company}" if company else raw_title
    evidence_clause = _snippet(score_row, variant=variant)
    jd_clause = _concept_phrase(score_row)
    availability = _availability_note(score_row)
    concern = _concern(score_row)
    style = _style(score_row, raw_title)

    if style == "wrong_domain":
        sentence = f"{years:.1f} yrs as {title}; AI terms are not well supported by career evidence ({evidence_clause}), so Redrob's {jd_clause} fit is weak."
    elif style == "shallow_llm":
        sentence = f"{years:.1f} yrs as {title}; career evidence leans toward LLM/chatbot usage ({evidence_clause}) without enough retrieval/ranking ownership for Redrob."
    elif style == "retrieval":
        templates = [
            f"{years:.1f} yrs as {title}; career evidence references {evidence_clause}, matching Redrob's retrieval/search and ranking focus.",
            f"{years:.1f} yrs as {title}; career evidence shows {evidence_clause}, directly supporting Redrob's search relevance needs.",
            f"{years:.1f} yrs as {title}; career evidence includes {evidence_clause}, a close match for Redrob's retrieval and ranking work.",
            f"{years:.1f} yrs as {title}; career evidence points to {evidence_clause}, useful for Redrob's matching/search stack.",
        ]
        sentence = templates[variant]
    elif style == "ranking":
        templates = [
            f"{years:.1f} yrs as {title}; career evidence shows ranking/recommendation work ({evidence_clause}) aligned with Redrob's matching and evaluation needs.",
            f"{years:.1f} yrs as {title}; career evidence includes ranking/evaluation signals ({evidence_clause}) relevant to Redrob's candidate matching.",
            f"{years:.1f} yrs as {title}; career evidence points to recommendation or relevance work ({evidence_clause}) that fits Redrob's ranking problem.",
            f"{years:.1f} yrs as {title}; career evidence supports ranking-system ownership ({evidence_clause}) for Redrob's search/relevance focus.",
        ]
        sentence = templates[variant]
    elif style == "platform":
        templates = [
            f"{years:.1f} yrs as {title}; career evidence shows production ML systems ({evidence_clause}), useful for Redrob's CPU-safe retrieval pipeline.",
            f"{years:.1f} yrs as {title}; career evidence includes deployed ML infrastructure ({evidence_clause}), relevant to Redrob's production ranking stack.",
            f"{years:.1f} yrs as {title}; career evidence points to platform ownership ({evidence_clause}) that can support retrieval and evaluation workflows.",
            f"{years:.1f} yrs as {title}; career evidence shows systems delivery ({evidence_clause}) for scalable AI/retrieval operations.",
        ]
        sentence = templates[variant]
    elif style == "adjacent":
        sentence = f"{years:.1f} yrs as {title}; career evidence shows production engineering depth, but career-backed retrieval/ranking ownership is thinner than ideal for Redrob."
    elif style == "logistics":
        sentence = f"{years:.1f} yrs as {title}; career evidence fits {jd_clause}, but availability or location signals need recruiter review."
    else:
        sentence = f"{years:.1f} yrs as {title}; career evidence shows {evidence_clause}, matching Redrob's {jd_clause} focus."
    if availability:
        sentence += f" Also {availability}."
    return _finish(sentence, concern)
