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
from semantic import (
    FAST_MAX_FEATURES,
    FAST_NGRAM_MAX,
    FAST_TEXT_CHARS,
    NORMAL_MAX_FEATURES,
    NORMAL_NGRAM_MAX,
    NORMAL_TEXT_CHARS,
    compute_semantic_scores,
)


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


def _fmt_time(value):
    return f"{value:.2f}"


def _summarize(rows, top, timings, semantic_enabled, semantic_warning, out_path):
    hard_total = sum(1 for row in rows if row["hard_honeypot"])
    hard_top = sum(1 for row in top if row["hard_honeypot"])
    soft_top = sum(len(row.get("soft_flags") or []) for row in top)
    lines = [
        f"candidates loaded: {len(rows)}",
        f"semantic: {'enabled' if semantic_enabled else 'disabled'}",
        f"hard honeypots detected: {hard_total}",
        f"hard honeypots in top 100: {hard_top}",
        f"soft anomaly count in top 100: {soft_top}",
        f"output path: {out_path}",
        f"top score: {top[0]['score'] if top else 'n/a'}",
        f"rank 100 score: {top[-1]['score'] if len(top) >= 100 else 'n/a'}",
        f"load_time: {_fmt_time(timings.get('load_time', 0.0))}",
        f"semantic_time: {_fmt_time(timings.get('semantic_time', 0.0))}",
        f"scoring_time: {_fmt_time(timings.get('scoring_time', 0.0))}",
        f"sorting_time: {_fmt_time(timings.get('sorting_time', 0.0))}",
        f"reasoning_time: {_fmt_time(timings.get('reasoning_time', 0.0))}",
        f"write_time: {_fmt_time(timings.get('write_time', 0.0))}",
        f"total_time: {_fmt_time(timings.get('total_time', 0.0))}",
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
    parser.add_argument("--fast", action="store_true", help="use faster semantic defaults for slower CPU-only machines")
    parser.add_argument("--semantic-max-features", type=int, help="override TF-IDF max_features")
    parser.add_argument("--semantic-ngram-max", type=int, choices=[1, 2], help="override semantic ngram max")
    parser.add_argument("--profile-runtime", action="store_true", help="accepted for explicit profiling; timings are always printed")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--workers", type=int, default=0, help="parallel workers for large local runs; 0 auto-selects")
    args = parser.parse_args(argv)

    start = time.perf_counter()
    timings = {}
    today = parse_today(args.today)
    load_start = time.perf_counter()
    candidates = load_candidates(args.candidates)
    timings["load_time"] = time.perf_counter() - load_start
    if args.strict and len(candidates) < 100:
        raise SystemExit("--strict requires at least 100 candidates")

    semantic_start = time.perf_counter()
    if args.no_semantic:
        semantic_scores = [None] * len(candidates)
        semantic_enabled = False
        semantic_warning = ""
    else:
        semantic_scores, semantic_enabled, semantic_warning = compute_semantic_scores(
            candidates,
            max_features=args.semantic_max_features or (FAST_MAX_FEATURES if args.fast else NORMAL_MAX_FEATURES),
            ngram_max=args.semantic_ngram_max or (FAST_NGRAM_MAX if args.fast else NORMAL_NGRAM_MAX),
            max_candidate_chars=FAST_TEXT_CHARS if args.fast else NORMAL_TEXT_CHARS,
        )
        if not semantic_enabled:
            semantic_scores = [None] * len(candidates)
    timings["semantic_time"] = time.perf_counter() - semantic_start

    workers = args.workers
    if workers <= 0:
        workers = min(8, max(1, os.cpu_count() or 1)) if len(candidates) >= 5000 else 1
    rank_timings = {}
    rows = rank_candidates_v2(
        candidates,
        semantic_scores=semantic_scores,
        today=today,
        include_reasoning=False,
        workers=workers,
        timings=rank_timings,
    )
    timings.update(rank_timings)
    reasoning_start = time.perf_counter()
    for i, row in enumerate(rows[:100]):
        candidate_index = row["_candidate_index"]
        rows[i] = score_candidate_v2(
            candidates[candidate_index],
            semantic_score=semantic_scores[candidate_index],
            today=today,
            include_reasoning=True,
        )
        rows[i]["_candidate_index"] = candidate_index
    timings["reasoning_time"] = time.perf_counter() - reasoning_start
    if args.top != 100:
        rows = rows[: args.top] + rows[args.top:]
    write_start = time.perf_counter()
    top = _write_submission(args.out, rows)

    if args.debug_json:
        write_debug_json(args.debug_json, top)
    if args.debug_csv:
        write_debug_csv(args.debug_csv, top)
    if args.full_debug_csv:
        write_debug_csv(args.full_debug_csv, rows)
    timings["write_time"] = time.perf_counter() - write_start

    timings["total_time"] = time.perf_counter() - start
    print(_summarize(rows, top, timings, semantic_enabled, semantic_warning, args.out))


if __name__ == "__main__":
    main()
