"""Print top-K candidate diagnostics from a debug CSV."""

from __future__ import annotations

import argparse
import csv
import sys


FIELDS = [
    "rank",
    "candidate_id",
    "final_score",
    "current_title",
    "years",
    "location",
    "technical_fit",
    "career_evidence_fit",
    "retrieval_ranking_fit",
    "production_system_fit",
    "semantic_score",
    "anomaly_penalty",
    "score_cap",
    "hard_honeypot",
    "soft_flags",
    "cap_reasons",
    "matched_evidence",
    "reasoning",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", required=True)
    parser.add_argument("--k", type=int, default=25)
    args = parser.parse_args()

    with open(args.debug, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))[: args.k]
    for row in rows:
        safe_print("-" * 80)
        for field in FIELDS:
            safe_print(f"{field}: {row.get(field, '')}")


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        print(str(text).encode(encoding, errors="replace").decode(encoding, errors="replace"))


if __name__ == "__main__":
    main()
