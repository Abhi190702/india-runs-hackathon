"""CLI entry point for RedrobRank V2.

Required command preserved:
    python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

# Allow running as "python src/rank.py" without installing a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import jd
from debug import ensure_parent, write_debug_csv, write_debug_json
from parser import load_candidates, parse_today
from scoring import rank_candidates_v2, score_candidate_v2
from semantic import compute_semantic_scores


def _write_submission(path, rows):
    ensure_parent(path)
    top = rows[:100]
    for row in top:
        row["score"] = f"{row['final_score']:.6f}"
    top.sort(key=lambda row: (-float(row["score"]), row["candidate_id"]))
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, row in enumerate(top, start=1):
            row["rank"] = rank
            writer.writerow([row["candidate_id"], rank, row["score"], row["reasoning"]])
    return top


def _summarize(rows, top, elapsed, semantic_enabled, semantic_warning, out_path):
    hard_total = sum(1 for row in rows if row["hard_honeypot"])
    hard_top = sum(1 for row in top if row["hard_honeypot"])
    soft_top = sum(len(row.get("soft_flags") or []) for row in top)
    lines = [
        f"candidates loaded: {len(rows)}",
        f"runtime seconds: {elapsed:.2f}",
        f"semantic: {'enabled' if semantic_enabled else 'disabled'}",
        f"hard honeypots detected: {hard_total}",
        f"hard honeypots in top 100: {hard_top}",
        f"soft anomaly count in top 100: {soft_top}",
        f"output path: {out_path}",
        f"top score: {top[0]['score'] if top else 'n/a'}",
        f"rank 100 score: {top[-1]['score'] if len(top) >= 100 else 'n/a'}",
    ]
    if semantic_warning:
        lines.append(semantic_warning)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True, help="JSONL or JSON candidate file")
    parser.add_argument("--out", default="submission.csv")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--today", default=jd.REFERENCE_TODAY)
    parser.add_argument("--debug-json")
    parser.add_argument("--debug-csv")
    parser.add_argument("--full-debug-csv")
    parser.add_argument("--no-semantic", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--workers", type=int, default=0, help="parallel workers for large local runs; 0 auto-selects")
    args = parser.parse_args(argv)

    start = time.perf_counter()
    today = parse_today(args.today)
    candidates = load_candidates(args.candidates)
    if args.strict and len(candidates) < 100:
        raise SystemExit("--strict requires at least 100 candidates")

    if args.no_semantic:
        semantic_scores = [None] * len(candidates)
        semantic_enabled = False
        semantic_warning = ""
    else:
        semantic_scores, semantic_enabled, semantic_warning = compute_semantic_scores(candidates)
        if not semantic_enabled:
            semantic_scores = [None] * len(candidates)

    workers = args.workers
    if workers <= 0:
        workers = min(8, max(1, os.cpu_count() or 1)) if len(candidates) >= 5000 else 1
    rows = rank_candidates_v2(
        candidates,
        semantic_scores=semantic_scores,
        today=today,
        include_reasoning=False,
        workers=workers,
    )
    for i, row in enumerate(rows[:100]):
        candidate_index = row["_candidate_index"]
        rows[i] = score_candidate_v2(
            candidates[candidate_index],
            semantic_score=semantic_scores[candidate_index],
            today=today,
            include_reasoning=True,
        )
        rows[i]["_candidate_index"] = candidate_index
    if args.top != 100:
        rows = rows[: args.top] + rows[args.top:]
    top = _write_submission(args.out, rows)

    if args.debug_json:
        write_debug_json(args.debug_json, top)
    if args.debug_csv:
        write_debug_csv(args.debug_csv, top)
    if args.full_debug_csv:
        write_debug_csv(args.full_debug_csv, rows)

    elapsed = time.perf_counter() - start
    print(_summarize(rows, top, elapsed, semantic_enabled, semantic_warning, args.out))


if __name__ == "__main__":
    main()
