"""
fit.py — Core role-fit scorer (the "does this person match the JD" brain).

This produces a fit score from the candidate's TEXT and CAREER STRUCTURE, using
the rubric in jd.py. Three parts:

  (A) Concept match  — weighted evidence for must-have / nice-to-have concepts,
                       read from summary + skills + the free-text career
                       descriptions. Reading the descriptions (not just the
                       skills list) is how we surface "plain-language Tier-5"
                       gems and avoid rewarding keyword-stuffers.

  (B) Trajectory     — experience band, product-vs-services companies, coding
                       recency, job-hop cadence. Structure, not keywords.

  (C) Disqualifiers  — explicit NEGATIVE evidence from the JD's "do NOT want"
                       list, applied as penalties. Most teams only score
                       positives; the penalties are where we separate true fits
                       from keyword look-alikes.

Returns (fit_score in ~[0,1], evidence dict) so reasoning.py can explain it.
"""

from datetime import date

import jd


def _parse_date(s):
    if not s:
        return None
    try:
        y, m, d = str(s)[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _candidate_text(c):
    """Concatenate the candidate's searchable free text, lowercased."""
    p = c.get("profile", {})
    parts = [p.get("headline", ""), p.get("summary", ""),
             p.get("current_title", ""), p.get("current_industry", "")]
    for j in (c.get("career_history") or []):
        parts.append(j.get("title", ""))
        parts.append(j.get("description", ""))
        parts.append(j.get("industry", ""))
    for s in (c.get("skills") or []):
        parts.append(s.get("name", ""))
    return " " + " ".join(parts).lower() + " "


def _count_concepts(text, group):
    """Return (matched_weight, matched_concept_names) for a rubric group."""
    weight = 0.0
    matched = []
    for name, spec in group.items():
        if any(ph in text for ph in spec["phrases"]):
            weight += spec["weight"]
            matched.append(name)
    return weight, matched


def _is_services_company(name):
    n = (name or "").lower()
    return any(svc in n for svc in jd.SERVICES_COMPANIES)


def score_fit(c, today):
    text = _candidate_text(c)
    profile = c.get("profile", {})
    history = c.get("career_history", []) or []
    ev = {"matched_must": [], "matched_nice": [], "penalties": [], "notes": []}

    # ---- (A) Concept match -------------------------------------------------
    max_must = sum(s["weight"] for s in jd.MUST_HAVE.values())
    must_w, must_m = _count_concepts(text, jd.MUST_HAVE)
    nice_w, nice_m = _count_concepts(text, jd.NICE_TO_HAVE)
    ev["matched_must"], ev["matched_nice"] = must_m, nice_m

    concept_score = must_w / max_must                      # 0..1
    concept_score += min(0.15, 0.04 * nice_w)              # small nice-to-have bump

    # ---- (B) Trajectory ----------------------------------------------------
    yoe = profile.get("years_of_experience", 0) or 0
    E = jd.EXPERIENCE
    if E["ideal_min"] <= yoe <= E["ideal_max"]:
        exp_score = 1.0
    elif E["acceptable_min"] <= yoe <= E["acceptable_max"]:
        exp_score = 0.85
    elif yoe >= E["hard_floor"]:
        # soft decay outside the band
        dist = min(abs(yoe - E["acceptable_min"]), abs(yoe - E["acceptable_max"]))
        exp_score = max(0.35, 0.85 - 0.12 * dist)
    else:
        exp_score = 0.25
        ev["notes"].append(f"only {yoe:.1f} yrs experience")

    # product-vs-services: reward genuine product-company time, flag all-services
    companies = [j.get("company", "") for j in history]
    n_services = sum(1 for n in companies if _is_services_company(n))
    n_total = max(1, len(companies))
    product_ratio = 1.0 - (n_services / n_total)
    if companies and n_services == n_total:
        ev["penalties"].append("entire career at services/consulting firms")
    elif product_ratio >= 0.5:
        ev["notes"].append("product-company experience")

    # coding recency: senior who moved into pure architecture/lead recently
    cur = next((j for j in history if j.get("is_current")), None)
    coding_recent = True
    if cur:
        title = (cur.get("title") or "").lower()
        if any(t in title for t in jd.STALE_IC_TITLES):
            coding_recent = False
            ev["penalties"].append(f"current role '{cur.get('title')}' may be non-IC")

    # job-hop / title-chasing cadence
    tenures = [j.get("duration_months") or 0 for j in history]
    title_chase = False
    if len(tenures) >= jd.TITLE_CHASE_MIN_JOBS:
        avg_tenure = sum(tenures) / len(tenures)
        if avg_tenure < jd.TITLE_CHASE_MAX_AVG_TENURE_MONTHS:
            title_chase = True
            ev["penalties"].append(f"avg tenure {avg_tenure:.0f}mo suggests job-hopping")

    trajectory_score = (
        0.55 * exp_score
        + 0.30 * product_ratio
        + 0.15 * (1.0 if coding_recent else 0.4)
    )

    # ---- (C) Disqualifier penalties (multiplicative) -----------------------
    penalty = 1.0

    # Wrong domain (CV/speech/robotics) ONLY if no NLP/IR signal present.
    has_nlp = "nlp_ir" in must_m
    if any(ph in text for ph in jd.WRONG_DOMAIN["phrases"]) and not has_nlp:
        penalty *= 0.55
        ev["penalties"].append("CV/speech/robotics focus without NLP/IR")

    # Framework enthusiast: LangChain/etc present but thin real ML evidence.
    fw = any(ph in text for ph in jd.FRAMEWORK_ENTHUSIAST["phrases"])
    deep_ml = len([m for m in must_m if m in
                   ("embeddings_retrieval", "ranking_recsys_search", "evaluation_frameworks")])
    if fw and deep_ml == 0:
        penalty *= 0.6
        ev["penalties"].append("LangChain/framework signal without deeper ML evidence")

    # Pure research without production.
    research = any(ph in text for ph in jd.PURE_RESEARCH["phrases"])
    production = "strong_python_production" in must_m
    if research and not production:
        penalty *= 0.6
        ev["penalties"].append("research background without production deployment")

    if title_chase:
        penalty *= 0.8

    # The classic keyword-stuffer trap: skills claim lots of AI, but the TITLES
    # and descriptions never show real AI work. If must-have concept evidence is
    # almost entirely from the skills list while titles are unrelated, dampen.
    titles_text = " ".join((j.get("title") or "") for j in history).lower()
    title_has_ml = any(t in titles_text for t in
                       ("engineer", "scientist", "ml", "ai", "data", "research", "developer"))
    if must_w > 0 and not title_has_ml:
        penalty *= 0.5
        ev["penalties"].append("AI skills listed but job titles show no technical role")

    # ---- Combine -----------------------------------------------------------
    base = 0.6 * concept_score + 0.4 * trajectory_score
    fit = base * penalty
    fit = max(0.0, min(1.0, fit))

    ev["concept_score"] = round(concept_score, 3)
    ev["trajectory_score"] = round(trajectory_score, 3)
    ev["penalty"] = round(penalty, 3)
    ev["product_ratio"] = round(product_ratio, 2)
    ev["years"] = yoe
    return fit, ev
