"""
gem_check.py — Are we BURYING "plain-language gems"?

The JD says a candidate who doesn't use AI buzzwords but whose career history
shows they built a recommendation/search system at a product company IS a fit.
This script finds such people (adjacent/non-AI title + career text that clearly
describes building retrieval/ranking/recsys/search) and checks where the ranker
scores them relative to our top-100 cutoff.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import jd
from parser import iter_candidate_records, flatten_candidate, parse_today, safe_float
from anomalies import _hard_flags
from scoring import score_candidate_v2

AI_TITLES = ("ai engineer", "machine learning engineer", "ml engineer", "applied scientist",
             "search engineer", "ranking engineer", "recommendation", "nlp engineer",
             "applied ml", "staff machine learning", "senior machine learning",
             "senior ai", "senior nlp")
BUILD = ("built", "build", "shipped", "deployed", "designed", "implemented", "developed", "owned", "led", "launched", "scaled")
SYS = ("retrieval", "ranking", "recommendation", "recommender", "semantic search",
       "embedding", "vector search", "learning to rank", "faiss", "bm25", "personalization", "search relevance")

CUTOFF = 0.7639  # current full-run rank-100 score


def is_gem(c, today):
    if _hard_flags(c, today):
        return False
    flat = flatten_candidate(c)
    title = (flat.get("current_title") or "").lower()
    if any(t in title for t in AI_TITLES):
        return False  # already an AI title, not a "hidden" gem
    yrs = safe_float(flat.get("years"), 0.0)
    if not (4.0 <= yrs <= 11.0):
        return False
    text = (flat.get("current_role_description_text", "") + " " + flat.get("career_description_text", "")).lower()
    return any(b in text for b in BUILD) and any(s in text for s in SYS)


def main():
    today = parse_today(jd.REFERENCE_TODAY)
    gems = []
    n = 0
    for c in iter_candidate_records("data/candidates.jsonl"):
        n += 1
        if is_gem(c, today):
            row = score_candidate_v2(c, semantic_score=None, today=today, include_reasoning=False)
            gems.append((row["final_score"], c["candidate_id"], flatten_candidate(c).get("current_title", "")))
    gems.sort(reverse=True)
    above = [g for g in gems if g[0] >= CUTOFF]
    print(f"scanned {n}; found {len(gems)} non-AI-title gems (built real systems)")
    print(f"gems scoring >= top-100 cutoff ({CUTOFF}): {len(above)}")
    print("\nTop 15 gems by score (note: scored WITHOUT semantic boost, so real scores are slightly higher):")
    for score, cid, title in gems[:15]:
        flag = "  <-- would make top 100" if score >= CUTOFF else ""
        print(f"  {score:.4f}  {cid}  {title}{flag}")


if __name__ == "__main__":
    main()
