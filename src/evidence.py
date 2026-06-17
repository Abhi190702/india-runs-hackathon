"""Source-aware evidence extraction.

V2 treats "where a phrase appeared" as part of the signal. Retrieval mentioned
inside a job description is strong; the same word in a skills list is weak
supporting evidence.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import jd
from parser import clean_text, flatten_candidate

NON_MATCH_RE = re.compile(r"[^a-z0-9@#+]+")
MAX_BUCKET_CHARS = 2200
SKIP_MATCH_SOURCES = {"education_text", "company_industry_text"}


@dataclass(frozen=True)
class Evidence:
    concept_name: str
    phrase: str
    source: str
    source_weight: float
    matched_text_snippet: str
    confidence: float
    is_career_backed: bool

    def to_dict(self):
        return asdict(self)


def extract_evidence_buckets(candidate):
    flat = flatten_candidate(candidate)
    return {
        "current_title_text": flat["current_title_text"],
        "past_title_text": flat["past_title_text"],
        "current_role_description_text": flat["current_role_description_text"],
        "career_description_text": flat["career_description_text"],
        "summary_headline_text": flat["summary_headline_text"],
        "skills_text": flat["skills_text"],
        "education_text": flat["education_text"],
        "company_industry_text": flat["company_industry_text"],
    }


def _normalize_match_text(text):
    return " " + NON_MATCH_RE.sub(" ", str(text).lower()).strip() + " "


def _make_patterns(jd_rules):
    patterns = []
    for concept_name, spec in jd_rules.items():
        concept_weight = abs(float(spec.get("weight", 1.0)))
        phrases = []
        for phrase in spec.get("phrases", []):
            normalized = _normalize_match_text(phrase).strip()
            if normalized:
                phrases.append(normalized)
        if not phrases:
            continue
        phrases = sorted(set(phrases), key=lambda p: (-len(p), p))
        pattern = re.compile(r" (?P<phrase>" + "|".join(re.escape(p) for p in phrases) + r") ")
        patterns.append((concept_name, concept_weight, pattern))
    return patterns


COMPILED_PATTERNS = _make_patterns(jd.CONCEPT_GROUPS)


def _snippet(text, start, end, width=62):
    lo = max(0, start - width)
    hi = min(len(text), end + width)
    snippet = clean_text(text[lo:hi])
    if lo > 0:
        snippet = "..." + snippet
    if hi < len(text):
        snippet = snippet + "..."
    return snippet


def match_concepts_by_source(candidate, jd_rules=None, with_snippets=True):
    jd_rules = jd_rules or jd.CONCEPT_GROUPS
    patterns = COMPILED_PATTERNS if jd_rules is jd.CONCEPT_GROUPS else _make_patterns(jd_rules)
    buckets = extract_evidence_buckets(candidate)
    evidence = []
    seen = set()

    for source, text in buckets.items():
        if not text:
            continue
        if source in SKIP_MATCH_SOURCES:
            continue
        if len(text) > MAX_BUCKET_CHARS:
            text = text[:MAX_BUCKET_CHARS]
        normalized_text = _normalize_match_text(text)
        lower_original = text.lower()
        source_weight = jd.SOURCE_WEIGHTS[source]
        for concept_name, concept_weight, pattern in patterns:
            matches = 0
            for match in pattern.finditer(normalized_text):
                phrase = match.group("phrase")
                first_token = phrase.split()[0]
                start = lower_original.find(phrase)
                if start < 0:
                    start = lower_original.find(first_token)
                if start < 0:
                    start = 0
                end = min(len(text), start + len(phrase))
                key = (concept_name, phrase, source)
                if key in seen:
                    continue
                seen.add(key)
                confidence = min(1.0, source_weight * (0.65 + 0.35 * min(1.0, concept_weight)))
                snippet = _snippet(text, start, end) if with_snippets else phrase
                evidence.append(
                    Evidence(
                        concept_name=concept_name,
                        phrase=phrase,
                        source=source,
                        source_weight=source_weight,
                        matched_text_snippet=snippet,
                        confidence=round(confidence, 4),
                        is_career_backed=source in jd.CAREER_BACKED_SOURCES,
                    )
                )
                matches += 1
                if matches >= 3:
                    break
    evidence.sort(key=lambda e: (-e.confidence, e.concept_name, e.source, e.phrase.lower()))
    return evidence


def summarize_evidence(evidence_list):
    by_concept = {}
    by_source = {}
    career_backed = set()
    skills_only = set()
    all_concepts = set()

    for ev in evidence_list:
        all_concepts.add(ev.concept_name)
        by_source[ev.source] = by_source.get(ev.source, 0) + 1
        current = by_concept.get(ev.concept_name, {"count": 0, "best_confidence": 0.0, "sources": set()})
        current["count"] += 1
        current["best_confidence"] = max(current["best_confidence"], ev.confidence)
        current["sources"].add(ev.source)
        by_concept[ev.concept_name] = current
        if ev.is_career_backed:
            career_backed.add(ev.concept_name)

    for concept in all_concepts:
        sources = by_concept[concept]["sources"]
        if sources and sources <= {"skills_text"}:
            skills_only.add(concept)

    return {
        "by_concept": {
            name: {
                "count": info["count"],
                "best_confidence": round(info["best_confidence"], 4),
                "sources": sorted(info["sources"]),
            }
            for name, info in sorted(by_concept.items())
        },
        "by_source": dict(sorted(by_source.items())),
        "career_backed_concepts": sorted(career_backed),
        "skills_only_concepts": sorted(skills_only),
    }


def get_top_evidence_snippets(evidence_list, limit=5):
    snippets = []
    seen = set()
    for ev in evidence_list:
        if ev.source == "skills_text" and len(snippets) >= max(1, limit - 1):
            continue
        label = jd.CONCEPT_GROUPS.get(ev.concept_name, {}).get("label", ev.concept_name)
        text = f"{label}: {ev.matched_text_snippet}"
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        snippets.append(text)
        if len(snippets) >= limit:
            break
    return snippets


def evidence_to_dicts(evidence_list):
    return [ev.to_dict() for ev in evidence_list]
