"""Hard honeypot and soft anomaly detection for RedrobRank V2."""

from __future__ import annotations

import jd
from parser import flatten_candidate, lower_text, parse_date, parse_today, safe_float


PENALTIES = {
    "severe keyword stuffing": 0.18,
    "wrong-domain weak evidence": 0.22,
    "expert skill inflation": 0.15,
    "shallow LLM-only": 0.14,
    "pure research no deployment": 0.12,
    "consulting-only weak fit": 0.08,
    "CV/speech/robotics-only without NLP/IR": 0.10,
    "inactive >180 days": 0.12,
    "very low response rate <0.10": 0.10,
    "notice >120 days": 0.06,
    "outside India no relocation": 0.12,
    "title chaser": 0.08,
    "manager-only no recent coding": 0.08,
    "hard honeypot": 0.50,
}


def _months_between(start, end):
    if not start or not end:
        return None
    return (end.year - start.year) * 12 + (end.month - start.month)


def _is_services_company(name):
    n = (name or "").lower()
    return any(svc in n for svc in jd.SERVICES_COMPANIES)


def _days_since(value, today):
    parsed = parse_date(value)
    if not parsed:
        return None
    return (today - parsed).days


def _has_concept(evidence, names, career_only=False):
    names = set(names)
    return any(ev.concept_name in names and (not career_only or ev.is_career_backed) for ev in evidence)


def _count_skill_inflation(candidate, threshold=2):
    count = 0
    for skill in candidate.get("skills") or []:
        proficiency = str(skill.get("proficiency", "")).lower()
        months = safe_float(skill.get("duration_months"), 0.0)
        if proficiency == "expert" and months <= threshold:
            count += 1
    return count


def _zero_month_expert_skills(candidate, max_endorsements=None):
    skills = []
    for skill in candidate.get("skills") or []:
        proficiency = str(skill.get("proficiency", "")).lower()
        months = safe_float(skill.get("duration_months"), 0.0)
        endorsements = safe_float(skill.get("endorsements"), 0.0)
        if proficiency == "expert" and months <= 0:
            if max_endorsements is None or endorsements <= max_endorsements:
                skills.append(skill.get("name"))
    return skills


def _hard_flags(candidate, today):
    flags = []
    flat = flatten_candidate(candidate)
    history = candidate.get("career_history") or []
    yoe = safe_float(flat.get("years"), 0.0)
    total_months = 0

    for job in history:
        start = parse_date(job.get("start_date"))
        end = parse_date(job.get("end_date"))
        duration = safe_float(job.get("duration_months"), 0.0)
        total_months += duration
        label = job.get("company") or job.get("title") or "job"
        if start and end and end < start:
            flags.append(f"{label} ends before it starts")
        if job.get("is_current") and end:
            flags.append(f"{label} marked current but has an end date")
        if start and start > today:
            flags.append(f"{label} starts in the future")
        real_months = _months_between(start, end)
        if real_months is not None and duration and abs(real_months - duration) > 12:
            flags.append(f"{label} duration/date contradiction")
        if job.get("is_current") and start and not end and duration:
            current_months = _months_between(start, today)
            if current_months is not None and abs(current_months - duration) > 12:
                flags.append(f"{label} current tenure/date contradiction")
        if yoe and duration > yoe * 12 + 18 and duration > 24:
            flags.append(f"{label} tenure exceeds total stated experience")

    if total_months > yoe * 12 + 24 and total_months > 48:
        flags.append("total career months wildly exceed stated experience")

    starts = [parse_date(j.get("start_date")) for j in history]
    starts = [d for d in starts if d]
    if starts and yoe > 4:
        span_years = (today - min(starts)).days / 365.25
        if yoe > span_years + 2.0:
            flags.append("total career span impossible relative to stated years")

    expert_zero = _zero_month_expert_skills(candidate)
    weak_expert_zero = _zero_month_expert_skills(candidate, max_endorsements=3)
    if len(expert_zero) >= 5:
        flags.append("5+ expert skills with 0 months used")
    elif len(weak_expert_zero) >= 3:
        flags.append("3+ expert skills with 0 months and weak endorsements")

    for edu in candidate.get("education") or []:
        start_year = edu.get("start_year")
        end_year = edu.get("end_year")
        if start_year and end_year and end_year < start_year:
            flags.append("education ends before it starts")

    return flags


def analyze_anomalies(candidate, features, evidence, today=None):
    today = parse_today(today)
    flat = flatten_candidate(candidate)
    hard = _hard_flags(candidate, today)
    soft = []

    career_evidence = features.get("career_evidence_fit", 0.0)
    retrieval = features.get("retrieval_ranking_fit", 0.0)
    production = features.get("production_system_fit", 0.0)
    title = lower_text(flat.get("current_title", ""))
    all_text = lower_text(
        " ".join(
            [
                flat.get("current_title", ""),
                flat.get("summary_headline_text", ""),
                flat.get("career_description_text", ""),
                flat.get("skills_text", ""),
            ]
        )
    )

    total_duration = sum(safe_float(j.get("duration_months"), 0.0) for j in candidate.get("career_history") or [])
    if total_duration > safe_float(flat.get("years"), 0.0) * 12 + 12 and total_duration <= safe_float(flat.get("years"), 0.0) * 12 + 30:
        soft.append("total career months slightly exceeds stated experience")

    expert_low = _count_skill_inflation(candidate, threshold=2)
    expert_zero = _count_skill_inflation(candidate, threshold=0)
    hard_skill_inflation = any("expert skills with 0 months" in flag for flag in hard)
    if not hard_skill_inflation and (1 <= expert_zero <= 4 or expert_low >= 3):
        soft.append("expert skill inflation")

    positive_skill_matches = [ev for ev in evidence if ev.source == "skills_text" and ev.concept_name in jd.positive_concept_names()]
    positive_career_matches = [ev for ev in evidence if ev.is_career_backed and ev.concept_name in jd.positive_concept_names()]
    if len(positive_skill_matches) >= 6 and len(positive_career_matches) <= 1:
        soft.append("severe keyword stuffing")

    wrong_title = any(term.lower() in title for term in jd.NEGATIVE_WRONG_DOMAIN)
    if wrong_title and career_evidence < 0.45:
        soft.append("wrong-domain weak evidence")

    career_text = lower_text(flat.get("current_role_description_text", "") + " " + flat.get("career_description_text", ""))
    real_production = any(
        term in career_text
        for term in [
            "production",
            "deployed",
            "shipped",
            "launched",
            "real users",
            "monitoring",
            "latency",
            "throughput",
            "microservice",
            "docker",
            "kubernetes",
            "mlflow",
            "airflow",
            "kafka",
        ]
    )
    llm_only = _has_concept(evidence, {"llm_rag"}) and not _has_concept(
        evidence, {"core_retrieval_ranking", "ranking_recommendation", "evaluation_frameworks"}, career_only=True
    )
    if llm_only and (production < 0.45 or not real_production):
        soft.append("shallow LLM-only")

    research = any(term in all_text for term in ["research scientist", "phd researcher", "postdoc", "academic", "university"])
    if research and production < 0.35:
        soft.append("pure research no deployment")

    companies = flat.get("companies", [])
    if companies and all(_is_services_company(c) for c in companies) and career_evidence < 0.55:
        soft.append("consulting-only weak fit")

    adjacent = _has_concept(evidence, {"weak_or_adjacent_domain"})
    has_ir = _has_concept(evidence, {"core_retrieval_ranking", "ranking_recommendation", "evaluation_frameworks"}, career_only=True)
    has_nlp = "nlp" in all_text or "natural language" in all_text or "information retrieval" in all_text
    if adjacent and not (has_ir or has_nlp):
        soft.append("CV/speech/robotics-only without NLP/IR")

    days = _days_since(flat.get("last_active_date"), today)
    if days is not None and days > 180:
        soft.append("inactive >180 days")

    rr = flat.get("recruiter_response_rate")
    if rr is not None and safe_float(rr, 0.0) < 0.10:
        soft.append("very low response rate <0.10")

    notice = flat.get("notice_period_days")
    if notice is not None and safe_float(notice, 0.0) > 120:
        soft.append("notice >120 days")

    country = lower_text(flat.get("country", ""))
    if jd.LOCATION["country_ok"] not in country and not flat.get("willing_to_relocate"):
        soft.append("outside India no relocation")

    tenures = [safe_float(j.get("duration_months"), 0.0) for j in candidate.get("career_history") or [] if safe_float(j.get("duration_months"), 0.0) > 0]
    if len(tenures) >= jd.TITLE_CHASE_MIN_JOBS and sum(tenures) / len(tenures) < jd.TITLE_CHASE_MAX_AVG_TENURE_MONTHS:
        soft.append("title chaser")

    manager_only = any(term in title for term in jd.MANAGER_ONLY_TITLES)
    if manager_only and features.get("coding_recency_fit", 0.0) < 0.45:
        soft.append("manager-only no recent coding")

    soft = list(dict.fromkeys(soft))
    penalty = 0.0
    if hard:
        penalty += PENALTIES["hard honeypot"]
    for flag in soft:
        penalty += PENALTIES.get(flag, 0.02)
    penalty = min(0.65, penalty)

    if hard:
        risk = "critical"
    elif penalty >= 0.35:
        risk = "high"
    elif penalty >= 0.18:
        risk = "medium"
    elif penalty > 0:
        risk = "low"
    else:
        risk = "none"

    return {
        "hard_honeypot": bool(hard),
        "hard_flags": hard,
        "soft_flags": soft,
        "anomaly_penalty": round(penalty, 6),
        "risk_level": risk,
    }
