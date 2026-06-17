"""
metrics.py — The exact scoring metrics the organizers use, so we can grade
ourselves OFFLINE. There is no live leaderboard and only 3 submissions, so a
local gold set + these metrics is the only honest way to know if a change helped.

Composite (from submission_spec):
    0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10

Usage:
    1. Build a gold set: a CSV `eval/gold.csv` with columns candidate_id,tier
       where tier is your hand-judged relevance 0..4 (0 = honeypot/irrelevant,
       4 = perfect fit). Label ~80-120 candidates by hand against the JD.
    2. python eval/metrics.py --submission submission.csv --gold eval/gold.csv
"""

import argparse
import csv
import math


def load_gold(path):
    """candidate_id -> relevance tier (int). Unlabeled ids are treated as 0."""
    gold = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gold[row["candidate_id"].strip()] = float(row["tier"])
    return gold


def load_ranking(path):
    """Return ordered list of candidate_ids from a submission CSV."""
    ids = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ids.append((int(row["rank"]), row["candidate_id"].strip()))
    ids.sort()
    return [cid for _, cid in ids]


def dcg(rels):
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(ranked_ids, gold, k):
    rels = [gold.get(cid, 0.0) for cid in ranked_ids[:k]]
    ideal = sorted(gold.values(), reverse=True)[:k]
    idcg = dcg(ideal)
    return dcg(rels) / idcg if idcg > 0 else 0.0


def precision_at_k(ranked_ids, gold, k, relevant_threshold=3.0):
    hits = sum(1 for cid in ranked_ids[:k] if gold.get(cid, 0.0) >= relevant_threshold)
    return hits / k


def mean_average_precision(ranked_ids, gold, relevant_threshold=1.0):
    n_relevant = sum(1 for v in gold.values() if v >= relevant_threshold)
    if n_relevant == 0:
        return 0.0
    hits = 0
    ap = 0.0
    for i, cid in enumerate(ranked_ids, start=1):
        if gold.get(cid, 0.0) >= relevant_threshold:
            hits += 1
            ap += hits / i
    return ap / n_relevant


def evaluate(ranked_ids, gold):
    ndcg10 = ndcg_at_k(ranked_ids, gold, 10)
    ndcg50 = ndcg_at_k(ranked_ids, gold, 50)
    mapv = mean_average_precision(ranked_ids, gold)
    p10 = precision_at_k(ranked_ids, gold, 10)
    composite = 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * mapv + 0.05 * p10
    return {"NDCG@10": ndcg10, "NDCG@50": ndcg50, "MAP": mapv,
            "P@10": p10, "composite": composite}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()

    gold = load_gold(args.gold)
    ranked = load_ranking(args.submission)
    res = evaluate(ranked, gold)

    print(f"Gold labels: {len(gold)} candidates")
    for k, v in res.items():
        print(f"  {k:10s}: {v:.4f}")


if __name__ == "__main__":
    main()
