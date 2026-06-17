"""
audit.py — Honeypot & internal-consistency auditor.

The dataset hides ~80 "honeypots": profiles that are subtly IMPOSSIBLE if you
actually read them (the spec's examples: "8 years of experience at a company
founded 3 years ago", "'expert' proficiency in 10 skills with 0 years used").
They are forced to relevance tier 0 in the ground truth, and ranking them in
your top 100 risks the >10% disqualification rule.

Key idea: a keyword/embedding system CANNOT catch these, because the text reads
fine. You only catch them by checking that the NUMBERS in a profile agree with
each other. That is pure logic — no ML — and it is one of our differentiators.

Each check returns a list of human-readable reasons. `audit_candidate` returns:
    is_honeypot (bool), reasons (list[str])
We hard-floor anything flagged impossible.
"""

from datetime import date


def _parse_date(s):
    if not s:
        return None
    try:
        y, m, d = str(s)[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _months_between(d1, d2):
    if not d1 or not d2:
        return None
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def audit_candidate(c, today):
    """Return (is_honeypot, reasons). `today` is a datetime.date."""
    reasons = []
    profile = c.get("profile", {})
    history = c.get("career_history", []) or []
    skills = c.get("skills", []) or []
    signals = c.get("redrob_signals", {}) or {}

    yoe = profile.get("years_of_experience", 0) or 0

    # --- Check 1: total career length wildly exceeds stated experience -------
    # "8 years at a company founded 3 years ago" surfaces here: the summed job
    # durations imply more career than years_of_experience can support, OR a
    # single tenure is longer than the candidate's whole career.
    total_months = sum((j.get("duration_months") or 0) for j in history)
    # Allow overlap slack (parallel roles) but a 2x blowout is not real.
    if total_months > (yoe * 12) + 18 and total_months > 36:
        reasons.append(
            f"career history sums to {total_months/12:.1f} yrs but profile claims "
            f"{yoe:.1f} yrs experience"
        )

    # --- Check 2: per-job date math is impossible ---------------------------
    for j in history:
        sd = _parse_date(j.get("start_date"))
        ed = _parse_date(j.get("end_date"))
        dur = j.get("duration_months")
        if sd and ed and ed < sd:
            reasons.append(f"job at {j.get('company')} ends before it starts")
        if sd and ed and dur is not None:
            real = _months_between(sd, ed)
            if real is not None and abs(real - dur) > 6:
                reasons.append(
                    f"{j.get('company')}: stated {dur}mo but dates span {real}mo"
                )
        if j.get("is_current") and ed is not None:
            reasons.append(f"{j.get('company')} marked current but has an end date")
        if sd and sd > today:
            reasons.append(f"{j.get('company')} starts in the future")

    # --- Check 3: single tenure longer than entire stated career ------------
    for j in history:
        dur = j.get("duration_months") or 0
        if dur > (yoe * 12) + 18 and dur > 24:
            reasons.append(
                f"{dur/12:.1f}-yr tenure at {j.get('company')} exceeds "
                f"{yoe:.1f}-yr total experience"
            )

    # --- Check 4: "expert" at a skill never actually used -------------------
    expert_zero = [
        s.get("name") for s in skills
        if s.get("proficiency") == "expert" and (s.get("duration_months") or 0) == 0
    ]
    if len(expert_zero) >= 2:
        reasons.append(
            f"'expert' in {len(expert_zero)} skills with 0 months used: "
            f"{', '.join(str(x) for x in expert_zero[:3])}"
        )

    # --- Check 5: experience older than the candidate could plausibly be ----
    # Earliest job start vs stated experience: if someone claims 8 yrs but their
    # earliest role started 3 yrs ago, that's impossible.
    starts = [_parse_date(j.get("start_date")) for j in history]
    starts = [s for s in starts if s]
    if starts:
        earliest = min(starts)
        career_span_yrs = (today - earliest).days / 365.25
        if yoe > career_span_yrs + 2.0 and yoe > 4:
            reasons.append(
                f"claims {yoe:.1f} yrs but earliest role began only "
                f"{career_span_yrs:.1f} yrs ago"
            )

    # NOTE: we deliberately do NOT flag "last_active before signup". In this
    # dataset that ordering is just noise (it fired on ~7,500 otherwise-normal
    # profiles), not an impossible-profile signal. Honeypots are defined by
    # internal profile contradictions, not by signal-timestamp jitter.

    # --- Check 7: education after it could have finished --------------------
    for e in (c.get("education") or []):
        sy, ey = e.get("start_year"), e.get("end_year")
        if sy and ey and ey < sy:
            reasons.append(f"education ends ({ey}) before it starts ({sy})")

    is_honeypot = len(reasons) > 0
    return is_honeypot, reasons
