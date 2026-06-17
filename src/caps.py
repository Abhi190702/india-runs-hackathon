"""Score caps keep suspicious profiles from ranking too high."""

from __future__ import annotations

import jd
from parser import flatten_candidate, lower_text, safe_float


def _add(caps, value, reason):
    caps.append((value, reason))


def compute_score_cap(candidate, features, anomalies, evidence):
    flat = flatten_candidate(candidate)
    caps = []
    soft = set(anomalies.get("soft_flags", []))

    if anomalies.get("hard_honeypot"):
        _add(caps, 0.20, "hard honeypot")

    title = lower_text(flat.get("current_title", ""))
    wrong_title = any(term.lower() in title for term in jd.NEGATIVE_WRONG_DOMAIN)
    if wrong_title and features.get("career_evidence_fit", 0.0) < 0.45:
        _add(caps, 0.35, "wrong-domain title + weak career evidence")

    if "severe keyword stuffing" in soft and features.get("production_system_fit", 0.0) < 0.45:
        _add(caps, 0.42, "severe AI keyword stuffing with no production evidence")

    if "shallow LLM-only" in soft:
        _add(caps, 0.48, "shallow LangChain/OpenAI/chatbot-only profile")

    country = lower_text(flat.get("country", ""))
    if jd.LOCATION["country_ok"] not in country and not flat.get("willing_to_relocate"):
        _add(caps, 0.58, "outside India + not willing to relocate")

    if safe_float(flat.get("years"), 0.0) < 3:
        _add(caps, 0.58, "less than 3 years experience")

    if flat.get("preferred_work_mode") == "remote" and not flat.get("willing_to_relocate"):
        _add(caps, 0.62, "remote-only + not willing to relocate")

    if features.get("production_system_fit", 0.0) < 0.28:
        _add(caps, 0.65, "no production system evidence")

    if "consulting-only weak fit" in soft:
        _add(caps, 0.68, "consulting-only + weak career evidence")

    if "CV/speech/robotics-only without NLP/IR" in soft:
        _add(caps, 0.68, "CV/speech/robotics-only without NLP/IR/retrieval")

    if "inactive >180 days" in soft:
        _add(caps, 0.70, "inactive >180 days")

    notice = flat.get("notice_period_days")
    if notice is not None and safe_float(notice, 0.0) > 120:
        _add(caps, 0.82, "notice >120 days")

    rr = flat.get("recruiter_response_rate")
    if rr is not None and safe_float(rr, 0.0) < 0.20:
        _add(caps, 0.82, "recruiter response rate <0.20")

    if not caps:
        return {"score_cap": 1.0, "cap_reasons": []}

    score_cap = min(value for value, _ in caps)
    reasons = [reason for value, reason in caps if value == score_cap]
    return {"score_cap": score_cap, "cap_reasons": reasons}
