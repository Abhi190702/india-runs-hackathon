"""Submission CSV validator matching the organizer constraints."""

from __future__ import annotations

import csv
from pathlib import Path


HEADER = ["candidate_id", "rank", "score", "reasoning"]


def validate_submission_csv(path, candidate_ids=None):
    errors = []
    path = Path(path)
    rows = []
    candidate_id_set = set(candidate_ids or [])

    if not path.exists():
        return {"ok": False, "errors": [f"{path} does not exist"], "row_count": 0}

    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                return {"ok": False, "errors": ["CSV is empty"], "row_count": 0}
            if header != HEADER:
                errors.append(f"header must be exactly {','.join(HEADER)}")
            for row in reader:
                if any(cell.strip() for cell in row):
                    rows.append(row)
    except UnicodeDecodeError:
        return {"ok": False, "errors": ["CSV must be UTF-8 encoded"], "row_count": 0}

    if len(rows) != 100:
        errors.append(f"expected exactly 100 data rows, found {len(rows)}")

    seen_ids = set()
    seen_ranks = set()
    by_rank = []
    for index, row in enumerate(rows, start=2):
        if len(row) != 4:
            errors.append(f"row {index}: expected 4 columns, found {len(row)}")
            continue
        cid, rank_s, score_s, reasoning = [cell.strip() for cell in row]
        if not cid:
            errors.append(f"row {index}: candidate_id is empty")
        if cid in seen_ids:
            errors.append(f"row {index}: duplicate candidate_id {cid}")
        seen_ids.add(cid)
        if candidate_id_set and cid not in candidate_id_set:
            errors.append(f"row {index}: candidate_id {cid} not found in input")
        try:
            rank = int(rank_s)
            if str(rank) != rank_s or not 1 <= rank <= 100:
                raise ValueError
            if rank in seen_ranks:
                errors.append(f"row {index}: duplicate rank {rank}")
            seen_ranks.add(rank)
        except ValueError:
            errors.append(f"row {index}: rank must be integer 1..100")
            rank = None
        try:
            score = float(score_s)
        except ValueError:
            errors.append(f"row {index}: score must be a float")
            score = None
        if not reasoning:
            errors.append(f"row {index}: reasoning is empty")
        if len(reasoning) > 500:
            errors.append(f"row {index}: reasoning exceeds 500 chars")
        if rank is not None and score is not None:
            by_rank.append((rank, score, cid))

    missing = set(range(1, 101)) - seen_ranks
    if missing:
        errors.append(f"missing ranks: {sorted(missing)}")

    by_rank.sort()
    for left, right in zip(by_rank, by_rank[1:]):
        if left[1] < right[1]:
            errors.append(f"score increases from rank {left[0]} to {right[0]}")
        if left[1] == right[1] and left[2] > right[2]:
            errors.append(f"equal-score tie at ranks {left[0]}/{right[0]} is not candidate_id ascending")

    return {"ok": not errors, "errors": errors, "row_count": len(rows)}
