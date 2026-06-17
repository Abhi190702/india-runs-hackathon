"""Feature engineering for the V2 scoring formula."""

from __future__ import annotations

import math
import re

import jd
from evidence import match_concepts_by_source, summarize_evidence
from parser import clamp, flatten_candidate, lower_text, parse_today, parse_date, safe_float


RETRIEVAL_GROUPS = {"core_retrieval_ranking"}
RANKING_GROUPS = {"ranking_recommendation"}
EVALUATION_GROUPS = {"evaluation_frameworks"}
PRODUCTION_GROUPS = {"production_ai_systems"}
ML_GROUPS = {"python_ml_core"}
LLM_GROUPS = {"llm_rag"}
POSITIVE_GROUPS = set(jd.positive_concept_names())
RELEVANT_SKILL_TERMS = []
for _group_name in jd.positive_concept_names():
    for _phrase in jd.CONCEPT_GROUPS[_group_name]["phrases"]:
        _term = str(_phrase).lower().strip()
        if _term:
            RELEVANT_SKILL_TERMS.append(_term)
RELEVANT_SKILL_TERMS.extend(["ml", "ai", "nlp", "search", "rank", "python", "torch"])
RELEVANT_SKILL_TERMS = sorted(set(RELEVANT_SKILL_TERMS), key=lambda item: (-len(item), item))
SKILL_RELEVANT_RE = re.compile("|".join(re.escape(term) for term in RELEVANT_SKILL_TERMS if len(term) > 2))


def _concept_best(evidence, concept_names, career_only=False, sources=None):
    names = set(concept_names)
    vals = []
    for ev in evidence:
        if ev.concept_name not in names:
            continue
        if career_only and not ev.is_career_backed:
            continue
        if sources and ev.source not in sources:
            continue
        vals.append(ev.confidence)
    if not vals:
        return 0.0
    vals.sort(reverse=True)
    return clamp(vals[0] + min(0.22, 0.045 * (len(vals) - 1)))


def _has_career_backed(evidence, concept_names):
    names = set(concept_names)
    return any(ev.concept_name in names and ev.is_career_backed for ev in evidence)


def _skills_only_for(evidence, concept_names):
    names = set(concept_names)
    matches = [ev for ev in evidence if ev.concept_name in names]
    return bool(matches) and all(ev.source == "skills_text" for ev in matches)


def _contains_any(text, phrases):
    lo = str(text or "").lower()
    return any(str(p).lower() in lo for p in phrases)


def _career_text(flat):
    return " ".join([flat.get("current_role_description_text", ""), flat.get("career_description_text", "")])


def _action_system_hits(flat):
    if "_action_system_hits" in flat:
        return flat["_action_system_hits"]
    text = _career_text(flat).lower()
    if not text:
        return 0
    systems = (
        jd.CORE_RETRIEVAL_RANKING
        + jd.RANKING_RECOMMENDATION
        + jd.EVALUATION_FRAMEWORKS
        + jd.PRODUCTION_AI_SYSTEMS
    )
    hits = 0
    for system in systems:
        term = system.lower()
        pos = text.find(term)
        while pos >= 0:
            window = text[max(0, pos - 90) : min(len(text), pos + len(term) + 90)]
            if any(verb in window for verb in jd.ACTION_VERBS):
                hits += 1
                break
            pos = text.find(term, pos + len(term))
    flat["_action_system_hits"] = hits
    return hits


def compute_role_title_fit(flat, evidence):
    title = lower_text(flat.get("current_title", ""))
    if any(t in title for t in jd.SENIOR_AI_TITLES):
        return 1.0
    career_fit = flat.get("_career_evidence_fit")
    if career_fit is None:
        career_fit = compute_career_evidence_fit(flat, evidence)
    strong_career = career_fit >= 0.70
    has_search = _has_career_backed(evidence, RETRIEVAL_GROUPS | RANKING_GROUPS)
    if "data scientist" in title or "applied scientist" in title:
        return 0.86 if has_search or strong_career else 0.70
    if "data engineer" in title or "backend engineer" in title:
        return 0.80 if has_search or strong_career else 0.50
    if "software engineer" in title or "developer" in title:
        return 0.55 if strong_career else 0.20
    wrong = any(term.lower() in title for term in jd.NEGATIVE_WRONG_DOMAIN)
    if wrong:
        return 0.30 if strong_career else 0.05
    if any(t in title for t in jd.MANAGER_ONLY_TITLES):
        return 0.45 if strong_career else 0.18
    return 0.35 if strong_career else 0.20


def compute_career_evidence_fit(flat, evidence):
    career_signal = _concept_best(evidence, POSITIVE_GROUPS, career_only=True)
    retrieval_signal = _concept_best(evidence, RETRIEVAL_GROUPS | RANKING_GROUPS | EVALUATION_GROUPS, career_only=True)
    production_signal = _concept_best(evidence, PRODUCTION_GROUPS, career_only=True)
    action_hits = _action_system_hits(flat)
    action_score = clamp(0.18 + 0.16 * action_hits) if action_hits else 0.0
    score = 0.42 * career_signal + 0.30 * retrieval_signal + 0.18 * production_signal + 0.10 * action_score
    if _skills_only_for(evidence, POSITIVE_GROUPS):
        score = min(score, 0.35)
    return clamp(score)


def compute_retrieval_ranking_fit(flat, evidence):
    embeddings_fit = _concept_best(evidence, RETRIEVAL_GROUPS)
    ranking_fit = _concept_best(evidence, RANKING_GROUPS)
    evaluation_fit = _concept_best(evidence, EVALUATION_GROUPS)
    hybrid_fit = 1.0 if _contains_any(_career_text(flat), ["hybrid search", "bm25", "elasticsearch", "opensearch"]) and embeddings_fit > 0 else 0.0
    score = (
        0.30 * embeddings_fit
        + 0.28 * ranking_fit
        + 0.22 * evaluation_fit
        + 0.20 * hybrid_fit
    )
    if _skills_only_for(evidence, RETRIEVAL_GROUPS | RANKING_GROUPS | EVALUATION_GROUPS):
        score = min(score, 0.45)
    return clamp(score)


def compute_production_system_fit(flat, evidence):
    production = _concept_best(evidence, PRODUCTION_GROUPS, career_only=True)
    ownership = 1.0 if _action_system_hits(flat) >= 2 else 0.55 if _action_system_hits(flat) == 1 else 0.0
    api_pipeline = 1.0 if _contains_any(_career_text(flat), ["api", "microservice", "pipeline", "kafka", "airflow", "docker", "kubernetes"]) else 0.0
    score = 0.58 * production + 0.24 * ownership + 0.18 * api_pipeline
    ai_terms = _concept_best(evidence, RETRIEVAL_GROUPS | RANKING_GROUPS | ML_GROUPS | LLM_GROUPS)
    if ai_terms and production < 0.20:
        score = min(score, 0.40)
    return clamp(score)


def _assessment_for_skill(skill_name, assessment_scores):
    lookup = {str(k).lower(): safe_float(v, 0.0) for k, v in assessment_scores.items()}
    name = str(skill_name).lower()
    if name in lookup:
        return lookup[name] / 100.0
    for key, val in lookup.items():
        if key in name or name in key:
            return val / 100.0
    return 0.50


def _skill_relevant(skill_name):
    name = str(skill_name or "").lower()
    return bool(SKILL_RELEVANT_RE.search(name))


def compute_skill_quality_fit(flat, evidence):
    # `flat` intentionally carries only names, so re-score from evidence and let
    # candidate-level `compute_all_features` pass candidate skills below.
    skills = flat.get("_skills", [])
    if not skills:
        return 0.35 if _concept_best(evidence, POSITIVE_GROUPS) else 0.10
    assessment_scores = flat.get("skill_assessment_scores") or {}
    proficiency_map = {"beginner": 0.25, "intermediate": 0.55, "advanced": 0.80, "expert": 1.00}
    scored = []
    for skill in skills:
        name = skill.get("name", "")
        if not _skill_relevant(name):
            continue
        proficiency_score = proficiency_map.get(str(skill.get("proficiency", "")).lower(), 0.45)
        duration_months = max(0.0, safe_float(skill.get("duration_months"), 0.0))
        duration_score = min(1.0, math.log(1 + duration_months) / math.log(61))
        endorsements = max(0.0, safe_float(skill.get("endorsements"), 0.0))
        endorsement_score = min(1.0, math.log(1 + endorsements) / math.log(101))
        assessment_score = _assessment_for_skill(name, assessment_scores)
        scored.append(
            0.35 * proficiency_score
            + 0.30 * duration_score
            + 0.20 * endorsement_score
            + 0.15 * assessment_score
        )
    if not scored:
        return 0.20
    scored.sort(reverse=True)
    return clamp(sum(scored[:8]) / min(8, len(scored)))


def compute_experience_fit(flat):
    years = safe_float(flat.get("years"), 0.0)
    if 5 <= years <= 9:
        return 1.00
    if 4 <= years < 5:
        return 0.90
    if 9 < years <= 11:
        return 0.85
    if 3 <= years < 4:
        return 0.65
    if 11 < years <= 13:
        return 0.60
    if 2 <= years < 3:
        return 0.35
    if 13 < years <= 15:
        return 0.30
    return 0.15


def compute_product_startup_fit(flat):
    text = lower_text(" ".join(flat.get("companies", [])) + " " + flat.get("company_industry_text", ""))
    product = any(term in text for term in jd.PRODUCT_STARTUP_TERMS)
    services = [name for name in flat.get("companies", []) if any(svc in name.lower() for svc in jd.SERVICES_COMPANIES)]
    total = max(1, len(flat.get("companies", [])))
    services_ratio = len(services) / total
    score = 0.78 if product else 0.48
    if "1-10" in text or "11-50" in text or "51-200" in text or "founding" in text:
        score += 0.12
    if services_ratio >= 0.80:
        score -= 0.25
    elif services_ratio >= 0.50:
        score -= 0.10
    return clamp(score)


def compute_coding_recency_fit(flat):
    current_text = lower_text(flat.get("current_title", "") + " " + flat.get("current_role_description_text", ""))
    managerish = any(term in current_text for term in jd.MANAGER_ONLY_TITLES)
    hands_on = any(verb in current_text for verb in jd.ACTION_VERBS) or any(
        term in current_text for term in ["python", "implemented", "deployed", "pipeline", "api", "model"]
    )
    if hands_on and not managerish:
        return 0.92
    if hands_on and managerish:
        return 0.65
    if managerish:
        return 0.30
    return 0.55


def _days_since(value, today):
    parsed = parse_date(value)
    if not parsed:
        return None
    return (today - parsed).days


def compute_recent_activity_fit(flat):
    days = _days_since(flat.get("last_active_date"), parse_today(flat.get("_today")))
    if days is None:
        return 0.55
    if days <= 14:
        return 1.0
    if days <= 45:
        return 0.90
    if days <= 90:
        return 0.72
    if days <= 180:
        return 0.45
    return 0.15


def compute_recruiter_response_fit(flat):
    rr = flat.get("recruiter_response_rate")
    if rr is None:
        return 0.58
    return clamp(0.20 + 0.80 * safe_float(rr, 0.0))


def compute_avg_response_time_fit(flat):
    hours = flat.get("avg_response_time_hours")
    if hours is None:
        return 0.60
    hours = safe_float(hours, 9999)
    if hours <= 12:
        return 1.0
    if hours <= 24:
        return 0.90
    if hours <= 72:
        return 0.72
    if hours <= 168:
        return 0.45
    return 0.20


def compute_notice_period_fit(flat):
    notice = flat.get("notice_period_days")
    if notice is None:
        return 0.70
    notice = safe_float(notice, 180)
    if notice <= 30:
        return 1.0
    if notice <= 60:
        return 0.82
    if notice <= 90:
        return 0.62
    if notice <= 120:
        return 0.40
    return 0.20


def compute_location_fit(flat):
    loc = lower_text(flat.get("location", ""))
    country = lower_text(flat.get("country", ""))
    if any(city in loc for city in jd.LOCATION["preferred"]):
        return 1.0
    if any(city in loc for city in jd.LOCATION["welcome"]):
        return 0.90
    if jd.LOCATION["country_ok"] in country:
        return 0.76
    if flat.get("willing_to_relocate"):
        return 0.55
    return 0.22


def compute_work_mode_fit(flat):
    mode = flat.get("preferred_work_mode", "")
    if mode in {"hybrid", "flexible"}:
        return 0.95
    if mode == "onsite":
        return 0.82
    if mode == "remote":
        return 0.62 if flat.get("willing_to_relocate") else 0.45
    return 0.65


def compute_relocation_fit(flat):
    country = lower_text(flat.get("country", ""))
    if jd.LOCATION["country_ok"] in country:
        return 0.90
    return 0.85 if flat.get("willing_to_relocate") else 0.20


def compute_interview_followthrough_fit(flat):
    value = flat.get("interview_completion_rate")
    return 0.70 if value is None else clamp(value)


def compute_offer_acceptance_fit(flat):
    value = flat.get("offer_acceptance_rate")
    if value is None or safe_float(value, -1) < 0:
        return 0.60
    return clamp(value)


def compute_contact_verified_fit(flat):
    parts = [flat.get("verified_email"), flat.get("verified_phone"), flat.get("linkedin_connected")]
    return clamp(sum(1.0 for p in parts if p) / len(parts))


def compute_profile_completeness_fit(flat):
    value = flat.get("profile_completeness_score")
    if value is not None:
        return clamp(safe_float(value, 0.0) / 100.0)
    present = sum(1 for key in ["headline", "summary", "current_title", "location", "skills_text"] if flat.get(key))
    return present / 5.0


def compute_skill_duration_consistency_fit(flat):
    skills = flat.get("_skills", [])
    if not skills:
        return 0.70
    expert_zero = sum(1 for s in skills if str(s.get("proficiency", "")).lower() == "expert" and safe_float(s.get("duration_months"), 0) <= 0)
    low_duration_advanced = sum(
        1
        for s in skills
        if str(s.get("proficiency", "")).lower() in {"advanced", "expert"} and safe_float(s.get("duration_months"), 0) <= 2
    )
    penalty = min(0.70, 0.12 * expert_zero + 0.06 * low_duration_advanced)
    return clamp(1.0 - penalty)


def compute_assessment_quality_fit(flat):
    scores = flat.get("skill_assessment_scores") or {}
    if not scores:
        return 0.55
    vals = [clamp(safe_float(v, 0.0) / 100.0) for v in scores.values()]
    return clamp(sum(vals) / len(vals)) if vals else 0.55


def compute_github_signal_fit(flat):
    value = safe_float(flat.get("github_activity_score"), -1.0)
    if value < 0:
        return 0.35
    return clamp(value / 100.0)


def compute_career_stability_fit(flat):
    tenures = [safe_float(t, 0.0) for t in flat.get("tenures", []) if safe_float(t, 0.0) > 0]
    if not tenures:
        return 0.55
    avg = sum(tenures) / len(tenures)
    if 24 <= avg <= 60:
        return 1.0
    if 18 <= avg < 24:
        return 0.76
    if 12 <= avg < 18:
        return 0.58
    if avg < 12:
        return 0.35
    if avg <= 96:
        return 0.85
    return 0.65


def compute_education_relevance_fit(flat):
    text = lower_text(flat.get("education_text", ""))
    if any(term in text for term in ["computer science", "machine learning", "artificial intelligence", "data science", "statistics"]):
        base = 0.88
    elif any(term in text for term in ["engineering", "mathematics", "math"]):
        base = 0.68
    elif text.strip():
        base = 0.42
    else:
        base = 0.35
    if "tier_1" in text:
        base += 0.10
    elif "tier_2" in text:
        base += 0.05
    return clamp(base)


def compute_data_consistency_fit(flat):
    score = 1.0
    if flat.get("years", 0) <= 0 and flat.get("career_description_text"):
        score -= 0.20
    if flat.get("notice_period_days") is not None and flat["notice_period_days"] > 180:
        score -= 0.20
    if flat.get("signup_date") and flat.get("last_active_date"):
        signup = parse_date(flat["signup_date"])
        active = parse_date(flat["last_active_date"])
        if signup and active and active < signup:
            score -= 0.08
    return clamp(score)


def compute_all_features(candidate, evidence=None, today=None):
    evidence = evidence if evidence is not None else match_concepts_by_source(candidate)
    flat = flatten_candidate(candidate)
    flat["_skills"] = candidate.get("skills") or []
    flat["_today"] = str(today or jd.REFERENCE_TODAY)
    summary = summarize_evidence(evidence)

    career_evidence_fit = compute_career_evidence_fit(flat, evidence)
    flat["_career_evidence_fit"] = career_evidence_fit

    features = {
        "career_evidence_fit": career_evidence_fit,
        "retrieval_ranking_fit": compute_retrieval_ranking_fit(flat, evidence),
        "production_system_fit": compute_production_system_fit(flat, evidence),
        "skill_quality_fit": compute_skill_quality_fit(flat, evidence),
        "experience_fit": compute_experience_fit(flat),
        "product_startup_fit": compute_product_startup_fit(flat),
        "coding_recency_fit": compute_coding_recency_fit(flat),
        "recent_activity_fit": compute_recent_activity_fit(flat),
        "recruiter_response_fit": compute_recruiter_response_fit(flat),
        "avg_response_time_fit": compute_avg_response_time_fit(flat),
        "notice_period_fit": compute_notice_period_fit(flat),
        "location_fit": compute_location_fit(flat),
        "work_mode_fit": compute_work_mode_fit(flat),
        "relocation_fit": compute_relocation_fit(flat),
        "interview_followthrough_fit": compute_interview_followthrough_fit(flat),
        "offer_acceptance_fit": compute_offer_acceptance_fit(flat),
        "contact_verified_fit": compute_contact_verified_fit(flat),
        "profile_completeness_fit": compute_profile_completeness_fit(flat),
        "skill_duration_consistency_fit": compute_skill_duration_consistency_fit(flat),
        "assessment_quality_fit": compute_assessment_quality_fit(flat),
        "github_signal_fit": compute_github_signal_fit(flat),
        "career_stability_fit": compute_career_stability_fit(flat),
        "education_relevance_fit": compute_education_relevance_fit(flat),
        "data_consistency_fit": compute_data_consistency_fit(flat),
        "evidence_summary": summary,
    }
    features["role_title_fit"] = compute_role_title_fit(flat, evidence)
    return features


def compute_technical_fit(features):
    return clamp(
        0.24 * features["career_evidence_fit"]
        + 0.20 * features["retrieval_ranking_fit"]
        + 0.16 * features["role_title_fit"]
        + 0.14 * features["production_system_fit"]
        + 0.10 * features["skill_quality_fit"]
        + 0.08 * features["experience_fit"]
        + 0.05 * features["product_startup_fit"]
        + 0.03 * features["coding_recency_fit"]
    )


def compute_hireability_fit(features):
    return clamp(
        0.20 * features["recent_activity_fit"]
        + 0.18 * features["recruiter_response_fit"]
        + 0.14 * features["avg_response_time_fit"]
        + 0.12 * features["notice_period_fit"]
        + 0.12 * features["location_fit"]
        + 0.08 * features["work_mode_fit"]
        + 0.06 * features["relocation_fit"]
        + 0.05 * features["interview_followthrough_fit"]
        + 0.03 * features["offer_acceptance_fit"]
        + 0.02 * features["contact_verified_fit"]
    )


def compute_trust_consistency_fit(features):
    return clamp(
        0.22 * features["profile_completeness_fit"]
        + 0.20 * features["skill_duration_consistency_fit"]
        + 0.16 * features["assessment_quality_fit"]
        + 0.14 * features["github_signal_fit"]
        + 0.12 * features["career_stability_fit"]
        + 0.08 * features["education_relevance_fit"]
        + 0.08 * features["data_consistency_fit"]
    )
