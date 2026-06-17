"""
make_label_sheet.py — Build a hand-labeling sheet so the team can create its own
gold set (there's no leaderboard, so this is how we measure progress).

It pulls the current top-N from a submission plus a random sample (to expose
false positives the ranker missed), and writes a readable CSV with the facts a
human needs to assign a relevance tier 0..4:
    4 = textbook fit (6-8 yrs, built ranking/search/recsys at a product company, active)
    3 = solid fit (relevant, minor gaps)
    2 = adjacent / stretch
    1 = weak
    0 = irrelevant or honeypot

Fill the `tier` column by hand, save as eval/gold.csv, then run eval/metrics.py.
"""
import argparse, csv, json, random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from parser import iter_candidate_records


FIELDS = [
    "candidate_id",
    "tier",
    "current_title",
    "years",
    "location",
    "final_score",
    "career_evidence_fit",
    "retrieval_ranking_fit",
    "production_system_fit",
    "anomaly_penalty",
    "score_cap",
    "soft_flags",
    "cap_reasons",
    "reasoning",
    "top_skills",
    "current_company",
    "summary_snippet",
    "last_active",
    "response_rate",
    "open_to_work",
]


def load_subset(candidates_path, wanted_ids):
    out = {}
    for c in iter_candidate_records(candidates_path):
        if c["candidate_id"] in wanted_ids:
            out[c["candidate_id"]] = c
        if len(out) == len(wanted_ids):
            break
    return out


def load_debug(path):
    if not path:
        return {}
    with open(path, encoding="utf-8", newline="") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def suspicious_ids(debug_rows, limit):
    scored = []
    for cid, row in debug_rows.items():
        anomaly = float(row.get("anomaly_penalty") or 0)
        cap = float(row.get("score_cap") or 1)
        has_flags = row.get("soft_flags") not in ("", "[]") or row.get("cap_reasons") not in ("", "[]")
        if has_flags or anomaly > 0 or cap < 1:
            scored.append((anomaly, 1 - cap, cid))
    scored.sort(reverse=True)
    return [cid for _, _, cid in scored[:limit]]


def row_for(c, debug_row=None):
    p = c.get("profile", {})
    s = c.get("redrob_signals", {})
    debug_row = debug_row or {}
    skills = ", ".join(sk["name"] for sk in (c.get("skills") or [])[:8])
    return {
        "candidate_id": c["candidate_id"], "tier": "",
        "current_title": p.get("current_title", ""),
        "years": p.get("years_of_experience", ""),
        "location": p.get("location", ""),
        "final_score": debug_row.get("final_score", debug_row.get("score", "")),
        "career_evidence_fit": debug_row.get("career_evidence_fit", ""),
        "retrieval_ranking_fit": debug_row.get("retrieval_ranking_fit", ""),
        "production_system_fit": debug_row.get("production_system_fit", ""),
        "anomaly_penalty": debug_row.get("anomaly_penalty", ""),
        "score_cap": debug_row.get("score_cap", ""),
        "soft_flags": debug_row.get("soft_flags", ""),
        "cap_reasons": debug_row.get("cap_reasons", ""),
        "reasoning": debug_row.get("reasoning", ""),
        "top_skills": skills,
        "current_company": p.get("current_company", ""),
        "summary_snippet": (p.get("summary", "")[:180]).replace("\n", " "),
        "last_active": s.get("last_active_date", ""),
        "response_rate": s.get("recruiter_response_rate", ""),
        "open_to_work": s.get("open_to_work_flag", ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="data/candidates.jsonl")
    ap.add_argument("--submission", default="submission.csv")
    ap.add_argument("--include-debug", default="", help="optional debug CSV to enrich rows and sample suspicious candidates")
    ap.add_argument("--out", default="eval/label_sheet.csv")
    ap.add_argument("--random", type=int, default=30, help="extra random candidates")
    ap.add_argument("--extra-random", type=int, help="alias for --random")
    ap.add_argument("--suspicious", type=int, default=0, help="extra suspicious rows from debug CSV")
    args = ap.parse_args()

    top_ids = []
    with open(args.submission, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            top_ids.append(r["candidate_id"].strip())

    debug_rows = load_debug(args.include_debug)
    extra_random = args.extra_random if args.extra_random is not None else args.random

    # random ids by sampling line numbers cheaply
    all_ids = []
    for candidate in iter_candidate_records(args.candidates):
        all_ids.append(candidate["candidate_id"])
    rng = random.Random(42)
    rand_ids = rng.sample(all_ids, min(extra_random, len(all_ids)))
    suspicious_extra = suspicious_ids(debug_rows, args.suspicious)

    wanted = set(top_ids) | set(rand_ids) | set(suspicious_extra)
    subset = load_subset(args.candidates, wanted)

    ordered = []
    for cid in top_ids + suspicious_extra + rand_ids:
        if cid not in ordered:
            ordered.append(cid)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for cid in ordered:
            if cid in subset:
                w.writerow(row_for(subset[cid], debug_rows.get(cid)))

    print(f"Wrote {len(ordered)} rows to {args.out}. "
          f"Fill the 'tier' column (0-4) by hand, save as eval/gold.csv.")


if __name__ == "__main__":
    main()
