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

FIELDS = ["candidate_id", "tier", "current_title", "years", "location",
          "top_skills", "current_company", "summary_snippet", "last_active",
          "response_rate", "open_to_work"]


def load_subset(candidates_path, wanted_ids):
    out = {}
    with open(candidates_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            if c["candidate_id"] in wanted_ids:
                out[c["candidate_id"]] = c
            if len(out) == len(wanted_ids):
                break
    return out


def row_for(c):
    p = c.get("profile", {})
    s = c.get("redrob_signals", {})
    skills = ", ".join(sk["name"] for sk in (c.get("skills") or [])[:8])
    return {
        "candidate_id": c["candidate_id"], "tier": "",
        "current_title": p.get("current_title", ""),
        "years": p.get("years_of_experience", ""),
        "location": p.get("location", ""),
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
    ap.add_argument("--out", default="eval/label_sheet.csv")
    ap.add_argument("--random", type=int, default=30, help="extra random candidates")
    args = ap.parse_args()

    top_ids = []
    with open(args.submission, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            top_ids.append(r["candidate_id"].strip())

    # random ids by sampling line numbers cheaply
    all_ids = []
    with open(args.candidates, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_ids.append(json.loads(line)["candidate_id"])
    rng = random.Random(42)
    rand_ids = rng.sample(all_ids, args.random)

    wanted = set(top_ids) | set(rand_ids)
    subset = load_subset(args.candidates, wanted)

    ordered = top_ids + [i for i in rand_ids if i not in set(top_ids)]
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for cid in ordered:
            if cid in subset:
                w.writerow(row_for(subset[cid]))

    print(f"Wrote {len(ordered)} rows to {args.out}. "
          f"Fill the 'tier' column (0-4) by hand, save as eval/gold.csv.")


if __name__ == "__main__":
    main()
