"""Input parsing and defensive flattening helpers for RedrobRank V2."""

from __future__ import annotations

import copy
import json
import re
from datetime import date
from pathlib import Path
from typing import Iterable

import jd

WHITESPACE_RE = re.compile(r"\s+")


def parse_date(value):
    if not value:
        return None
    try:
        y, m, d = str(value)[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def parse_today(value=None):
    value = value or jd.REFERENCE_TODAY
    parsed = parse_date(value)
    if parsed is None:
        raise ValueError(f"Invalid date: {value!r}")
    return parsed


def clamp(value, lo=0.0, hi=1.0):
    try:
        value = float(value)
    except Exception:
        value = lo
    if value != value:
        value = lo
    return max(lo, min(hi, value))


def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        out = float(value)
        return default if out != out else out
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def clean_text(value):
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    return WHITESPACE_RE.sub(" ", text).strip()


def join_text(parts):
    cleaned = []
    for part in parts:
        text = clean_text(part)
        if text:
            cleaned.append(text)
    return clean_text(" ".join(cleaned))


def lower_text(value):
    return f" {clean_text(value).lower()} "


def get_profile(candidate):
    return candidate.get("profile") or {}


def get_signals(candidate):
    return candidate.get("redrob_signals") or {}


def get_history(candidate):
    history = candidate.get("career_history") or []
    return history if isinstance(history, list) else []


def get_skills(candidate):
    skills = candidate.get("skills") or []
    return skills if isinstance(skills, list) else []


def get_education(candidate):
    education = candidate.get("education") or []
    return education if isinstance(education, list) else []


def get_current_job(candidate):
    history = get_history(candidate)
    for job in history:
        if job.get("is_current"):
            return job
    for job in history:
        if not job.get("end_date"):
            return job
    return history[0] if history else {}


def flatten_candidate(candidate):
    """Return a stable flat view used by scoring, reasoning, and debug output."""
    if isinstance(candidate, dict) and "_flat_cache" in candidate:
        return dict(candidate["_flat_cache"])

    profile = get_profile(candidate)
    signals = get_signals(candidate)
    history = get_history(candidate)
    skills = get_skills(candidate)
    education = get_education(candidate)
    current_job = get_current_job(candidate)

    current_title = clean_text(profile.get("current_title") or current_job.get("title"))
    current_company = clean_text(profile.get("current_company") or current_job.get("company"))
    current_industry = clean_text(profile.get("current_industry") or current_job.get("industry"))
    current_description = clean_text(current_job.get("description"))

    current_titles = []
    past_titles = []
    career_descriptions = []
    company_industries = []
    companies = []
    tenures = []

    for job in history:
        title = clean_text(job.get("title"))
        desc = clean_text(job.get("description"))
        industry = clean_text(job.get("industry"))
        company = clean_text(job.get("company"))
        if title:
            if job.get("is_current"):
                current_titles.append(title)
            else:
                past_titles.append(title)
        if desc:
            career_descriptions.append(desc)
        if industry or company:
            company_industries.append(join_text([company, industry, job.get("company_size")]))
        if company:
            companies.append(company)
        tenures.append(safe_int(job.get("duration_months"), 0))

    skill_names = [clean_text(s.get("name")) for s in skills if clean_text(s.get("name"))]
    education_bits = []
    for edu in education:
        education_bits.append(
            join_text(
                [
                    edu.get("degree"),
                    edu.get("field_of_study"),
                    edu.get("institution"),
                    edu.get("tier"),
                ]
            )
        )

    assessment_scores = signals.get("skill_assessment_scores") or {}
    if not isinstance(assessment_scores, dict):
        assessment_scores = {}

    flat = {
        "candidate_id": clean_text(candidate.get("candidate_id")),
        "headline": clean_text(profile.get("headline")),
        "summary": clean_text(profile.get("summary")),
        "location": clean_text(profile.get("location")),
        "country": clean_text(profile.get("country")),
        "years": safe_float(profile.get("years_of_experience"), 0.0),
        "current_title": current_title,
        "current_company": current_company,
        "current_company_size": clean_text(profile.get("current_company_size") or current_job.get("company_size")),
        "current_industry": current_industry,
        "current_description": current_description,
        "current_title_text": join_text([current_title] + current_titles),
        "past_title_text": join_text(past_titles),
        "current_role_description_text": current_description,
        "career_description_text": join_text(career_descriptions),
        "summary_headline_text": join_text([profile.get("headline"), profile.get("summary")]),
        "skills_text": join_text(skill_names),
        "education_text": join_text(education_bits),
        "company_industry_text": join_text(company_industries),
        "skill_names": skill_names,
        "companies": companies,
        "tenures": tenures,
        "last_active_date": signals.get("last_active_date"),
        "signup_date": signals.get("signup_date"),
        "open_to_work_flag": bool(signals.get("open_to_work_flag")),
        "recruiter_response_rate": safe_float(signals.get("recruiter_response_rate"), None),
        "avg_response_time_hours": safe_float(signals.get("avg_response_time_hours"), None),
        "notice_period_days": safe_int(signals.get("notice_period_days"), None),
        "preferred_work_mode": clean_text(signals.get("preferred_work_mode")).lower(),
        "willing_to_relocate": bool(signals.get("willing_to_relocate")),
        "interview_completion_rate": safe_float(signals.get("interview_completion_rate"), None),
        "offer_acceptance_rate": safe_float(signals.get("offer_acceptance_rate"), None),
        "verified_email": bool(signals.get("verified_email")),
        "verified_phone": bool(signals.get("verified_phone")),
        "linkedin_connected": bool(signals.get("linkedin_connected")),
        "profile_completeness_score": safe_float(signals.get("profile_completeness_score"), None),
        "github_activity_score": safe_float(signals.get("github_activity_score"), -1.0),
        "skill_assessment_scores": assessment_scores,
    }
    if isinstance(candidate, dict):
        candidate["_flat_cache"] = dict(flat)
    return flat


def _expand_demo_candidates(spec):
    base = spec.get("candidates") or []
    target = safe_int(spec.get("expand_to"), len(base))
    if not base or target <= len(base):
        return base
    out = []
    for idx in range(target):
        candidate = copy.deepcopy(base[idx % len(base)])
        candidate["candidate_id"] = f"CAND_9{idx + 1:06d}"
        profile = candidate.setdefault("profile", {})
        profile["years_of_experience"] = round(
            safe_float(profile.get("years_of_experience"), 5.0) + (idx % 5) * 0.1,
            1,
        )
        signals = candidate.setdefault("redrob_signals", {})
        if idx % 7 == 0:
            signals["recruiter_response_rate"] = min(1.0, safe_float(signals.get("recruiter_response_rate"), 0.5) + 0.08)
        if idx % 11 == 0:
            signals["notice_period_days"] = min(180, safe_int(signals.get("notice_period_days"), 30) + 15)
        out.append(candidate)
    return out


def _load_json_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_candidate_records(path) -> Iterable[dict]:
    """Yield candidate records from JSONL, JSON array, single JSON, or demo spec."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as handle:
        first = ""
        while True:
            ch = handle.read(1)
            if not ch:
                break
            if not ch.isspace():
                first = ch
                break

    should_try_json = first == "[" or (first == "{" and path.stat().st_size < 10_000_000)
    if should_try_json:
        try:
            data = _load_json_file(path)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
            return
        if isinstance(data, dict) and "candidates" in data:
            for item in _expand_demo_candidates(data):
                if isinstance(item, dict):
                    yield item
            return
        if isinstance(data, dict):
            yield data
            return

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_candidates(path):
    return list(iter_candidate_records(path))
