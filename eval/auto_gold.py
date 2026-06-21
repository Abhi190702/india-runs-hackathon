"""
auto_gold.py — Build a FIRST-PASS (proxy) gold relevance set, independently of
the ranker's weighted formula, so we can measure NDCG offline.

IMPORTANT: this is NOT the hidden ground truth. It is a transparent,
recruiter-style heuristic so the team has *a* number to compare changes against,
and to sanity-check that the ranking matches human intuition. The team should
hand-refine a subset of these labels for the real gold (see eval/make_label_sheet.py).

Relevance tiers (0..4), matching how a recruiter would read the JD:
  4 = genuine senior AI/ML/search/ranking title, 5-9 yrs, career text clearly
      describes BUILDING retrieval / ranking / recsys / search in production
  3 = real AI/ML/data title with relevant built systems but a gap (exp or depth)
  2 = adjacent role (data/backend/SWE/research) that DESCRIBES relevant systems
      -> these are the "plain-language gems" we must not bury
  1 = weakly relevant
  0 = irrelevant, wrong-domain with no real AI work, or honeypot

Deliberately uses different signals than scoring.py (plain title buckets +
career-text verbs + experience), so the comparison isn't fully circular.
"""
import argparse, csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import jd
from parser import iter_candidate_records, flatten_candidate, parse_today, safe_float
from anomalies import _hard_flags  # honeypot = tier 0 (definitional, not ranker-specific)

BUILD_VERBS = ("built", "build", "shipped", "ship", "deployed", "designed",
               "implemented", "developed", "owned", "led", "launched", "scaled")
RELEVANT_SYSTEMS = ("retrieval", "ranking", "rank", "recommendation", "recommender",
                    "search relevance", "semantic search", "embedding", "vector search",
                    "learning to rank", "faiss", "bm25", "personalization", "matching")

SENIOR_AI = ("ai engineer", "machine learning engineer", "ml engineer", "applied scientist",
             "search engineer", "ranking engineer", "recommendation", "nlp engineer",
             "applied ml", "staff machine learning", "senior machine learning",
             "senior ai", "senior nlp", "applied scientist")
ADJACENT = ("data scientist", "data engineer", "backend engineer", "software engineer",
            "research engineer", "developer")
WRONG = ("hr manager", "marketing manager", "sales executive", "content writer",
         "graphic designer", "accountant", "customer support", "operations manager",
         "mechanical engineer", "civil engineer", "business analyst", "project manager")


def career_text(c):
    flat = flatten_candidate(c)
    return (flat.get("current_role_description_text", "") + " " +
            flat.get("career_description_text", "")).lower()


def describes_real_systems(text):
    has_build = any(v in text for v in BUILD_VERBS)
    has_sys = any(s in text for s in RELEVANT_SYSTEMS)
    return has_build and has_sys


def label_candidate(c, today):
    if _hard_flags(c, today):
        return 0  # honeypot
    flat = flatten_candidate(c)
    title = (flat.get("current_title") or "").lower()
    yrs = safe_float(flat.get("years"), 0.0)
    text = career_text(c)
    real = describes_real_systems(text)
    in_band = 5.0 <= yrs <= 9.0
    near_band = 4.0 <= yrs <= 11.0

    is_senior_ai = any(t in title for t in SENIOR_AI)
    is_adjacent = any(t in title for t in ADJACENT)
    is_wrong = any(t in title for t in WRONG)

    if is_wrong and not real:
        return 0
    if is_senior_ai and real and in_band:
        return 4
    if is_senior_ai and (real or near_band):
        return 3
    if is_adjacent and real:
        return 2          # plain-language gem
    if is_senior_ai:
        return 2
    if real and near_band:
        return 2          # gem with off-title
    if is_adjacent:
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="data/candidates.jsonl")
    ap.add_argument("--out", default="eval/gold_auto.csv")
    ap.add_argument("--today", default=jd.REFERENCE_TODAY)
    args = ap.parse_args()
    today = parse_today(args.today)

    counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "tier"])
        for c in iter_candidate_records(args.candidates):
            tier = label_candidate(c, today)
            counts[tier] += 1
            w.writerow([c["candidate_id"], tier])
    total = sum(counts.values())
    print(f"Labeled {total} candidates -> {args.out}")
    for t in (4, 3, 2, 1, 0):
        print(f"  tier {t}: {counts[t]:6d}  ({counts[t]/total:.1%})")


if __name__ == "__main__":
    main()
