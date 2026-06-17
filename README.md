# Redrob Hackathon — Intelligent Candidate Discovery & Ranking

Ranks the top 100 of 100,000 candidates for the **Senior AI Engineer — Founding
Team** job description, the way a thoughtful recruiter would: by understanding
who actually *fits* the role, not by counting keywords.

## TL;DR design

This is a **transparent, explainable hybrid ranker** — no black box. Every
candidate's score traces back to specific, inspectable evidence.

```
final_score = fit_score × availability_multiplier × honeypot_gate
```

| Component | File | What it does | Why it matters |
|---|---|---|---|
| **JD rubric** | `src/jd.py` | The job description encoded as structured rules: must-haves, nice-to-haves, **disqualifiers**, location, experience band. | The whole challenge is the gap between what the JD *says* and *means*. This file is that understanding. |
| **Fit scorer** | `src/fit.py` | Weighted JD-concept evidence read from **career descriptions** (not just the skills list) + trajectory (product-vs-services, coding recency, job-hop cadence) + a **disqualifier engine**. | Reading descriptions surfaces "plain-language" fits and resists keyword-stuffers. The disqualifier engine is what most teams skip. |
| **Behavioral signals** | `src/signals.py` | Turns the 23 platform signals into one **availability multiplier** that dims unreachable candidates (inactive, low response rate, not open-to-work, long notice). | The JD: "a perfect-on-paper candidate who hasn't logged in for 6 months ... is not actually available." |
| **Honeypot auditor** | `src/audit.py` | Pure logic that detects **internally impossible** profiles (e.g. 8 yrs at a 3-yr-old company; "expert" in skills used 0 months) and floors them. | ~80 honeypots are planted; >10% in the top 100 = disqualification. Embeddings can't catch these — only consistency checks can. |
| **Reasoning** | `src/reasoning.py` | Builds the per-candidate justification **deterministically from extracted facts**, including honest concerns. | Stage-4 review checks for specific facts, JD connection, honest gaps, and no hallucination. |

## How to reproduce the submission

```bash
# 1. Install deps (CPU-only, lightweight)
python -m pip install -r requirements.txt

# 2. Put the organizers' file at data/candidates.jsonl  (not committed; see .gitignore)

# 3. Produce the ranking (~27 seconds on a laptop CPU)
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv

# 4. Validate format before uploading
python "path/to/validate_submission.py" submission.csv
```

Runs **CPU-only, no network, well under the 5-minute / 16 GB budget.**

## How we grade ourselves (no leaderboard, 3 submissions max)

There is no live feedback, so we measure progress against a **hand-labeled gold
set** using the organizers' exact metric.

```bash
# 1. Generate a labeling sheet (current top-100 + random sample)
python eval/make_label_sheet.py

# 2. Open eval/label_sheet.csv, fill the `tier` column (0-4) by hand,
#    save as eval/gold.csv

# 3. Score the submission against your gold set
python eval/metrics.py --submission submission.csv --gold eval/gold.csv
#    -> NDCG@10, NDCG@50, MAP, P@10, composite (0.50/0.30/0.15/0.05)
```

## Repo layout

```
src/
  jd.py         # the JD as structured rules (start here)
  fit.py        # role-fit scoring + disqualifier engine
  signals.py    # behavioral availability multiplier
  audit.py      # honeypot / consistency auditor
  reasoning.py  # grounded, honest reasoning strings
  rank.py       # entry point: candidates.jsonl -> submission.csv
eval/
  metrics.py            # NDCG/MAP/P@k (the official composite)
  make_label_sheet.py   # build a gold set to hand-label
  diagnose_honeypots.py # which consistency checks fire, and how often
requirements.txt
submission_metadata.yaml
```

## Roadmap (v2)

- **Semantic layer:** precompute sentence-transformer embeddings of candidate
  summaries/descriptions offline, blend cosine similarity into `fit_score`.
  The ranking step still just loads a matrix → stays in budget.
- **Cross-encoder re-rank** of the top ~200 (where NDCG@10 weight lives).
- Expand the hand-labeled gold set to ~150 for tighter offline tuning.

## Notes for reviewers

- No hosted-LLM calls at ranking time; all scoring is local and deterministic.
- Honeypot flag count on the full pool: **~70** (close to the documented ~80),
  with **0** in the top 100.
- AI tool usage is declared honestly in `submission_metadata.yaml`.
