"""Compare two RedrobRank debug CSV outputs."""

from __future__ import annotations

import argparse
import csv


def load(path):
    out = {}
    with open(path, encoding="utf-8") as handle:
        for idx, row in enumerate(csv.DictReader(handle), start=1):
            cid = row["candidate_id"]
            row["_rank"] = int(row.get("rank") or idx)
            out[cid] = row
    return out


def as_float(row, key):
    try:
        return float(row.get(key) or 0.0)
    except ValueError:
        return 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    args = parser.parse_args()

    old = load(args.old)
    new = load(args.new)
    entered = sorted(set(new) - set(old))
    left = sorted(set(old) - set(new))
    common = sorted(set(old) & set(new))
    movements = []
    for cid in common:
        movements.append((abs(old[cid]["_rank"] - new[cid]["_rank"]), cid, old[cid]["_rank"], new[cid]["_rank"]))
    movements.sort(reverse=True)

    avg_tech = sum(as_float(r, "technical_fit") for r in new.values()) / max(1, len(new))
    avg_penalty = sum(as_float(r, "anomaly_penalty") for r in new.values()) / max(1, len(new))
    honeypots = sum(1 for r in new.values() if str(r.get("hard_honeypot")).lower() == "true")
    suspicious = sum(1 for r in new.values() if r.get("soft_flags") not in ("", "[]"))

    print(f"old rows: {len(old)}")
    print(f"new rows: {len(new)}")
    print(f"entered top set: {len(entered)}")
    print(f"left top set: {len(left)}")
    print(f"avg technical_fit: {avg_tech:.4f}")
    print(f"avg anomaly_penalty: {avg_penalty:.4f}")
    print(f"honeypots in new set: {honeypots}")
    print(f"suspicious candidates in new set: {suspicious}")
    print("largest rank movements:")
    for _, cid, old_rank, new_rank in movements[:10]:
        print(f"  {cid}: {old_rank} -> {new_rank}")


if __name__ == "__main__":
    main()
