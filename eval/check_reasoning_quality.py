"""Lightweight reasoning QA checks for the generated submission."""

from __future__ import annotations

import argparse
import csv
import sys


BAD_PHRASES = [
    "great candidate",
    "strong candidate",
    "placeholder",
    "lorem ipsum",
    "n/a",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", required=True)
    args = parser.parse_args()

    errors = []
    seen = {}
    with open(args.submission, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            cid = row.get("candidate_id", "")
            reasoning = (row.get("reasoning") or "").strip()
            low = reasoning.lower()
            if not reasoning:
                errors.append(f"{cid}: empty reasoning")
            if len(reasoning) > 500:
                errors.append(f"{cid}: reasoning too long")
            if any(phrase in low for phrase in BAD_PHRASES):
                errors.append(f"{cid}: generic/placeholder reasoning")
            if low in seen:
                errors.append(f"{cid}: repeated same sentence as {seen[low]}")
            seen[low] = cid
            if ("anomaly" in low or "honeypot" in low or "concern" in low) and "concern" not in low and "de-ranked" not in low:
                errors.append(f"{cid}: anomaly wording lacks concern/de-rank framing")

    if errors:
        print(f"Reasoning quality failed ({len(errors)} issue(s)):")
        for error in errors[:50]:
            print(f"- {error}")
        sys.exit(1)
    print("Reasoning quality checks passed.")


if __name__ == "__main__":
    main()
