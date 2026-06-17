"""Quick diagnostic: which audit checks fire most often, and on how many
candidates. Helps us tell true honeypots (~80 expected) from over-flagging."""
import json, sys, collections
sys.path.insert(0, "src")
from datetime import date
from audit import audit_candidate

today = date(2026, 6, 1)
reason_head = collections.Counter()
n_flagged = 0
n = 0
samples = []
with open("data/candidates.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        c = json.loads(line)
        n += 1
        hp, reasons = audit_candidate(c, today)
        if hp:
            n_flagged += 1
            # bucket by the leading phrase of each reason
            for r in reasons:
                key = r.split(" but ")[0].split(":")[0]
                key = " ".join(key.split()[:4])
                reason_head[key] += 1
            if len(samples) < 5:
                samples.append((c["candidate_id"], reasons))

print(f"flagged {n_flagged}/{n} ({n_flagged/n:.1%})")
print("\ntop reason buckets:")
for k, v in reason_head.most_common(12):
    print(f"  {v:6d}  {k}")
print("\nsample flagged:")
for cid, rs in samples:
    print(f"  {cid}: {rs}")
