# Architecture

```text
data/candidates.jsonl
  -> src/parser.py
  -> src/evidence.py
  -> src/features.py
  -> src/semantic.py
  -> src/anomalies.py
  -> src/caps.py
  -> src/scoring.py
  -> src/reasoning.py
  -> src/rank.py
  -> submission.csv
```

`parser.py` reads JSONL or JSON and flattens candidate records defensively. `evidence.py` extracts source-aware concept matches. `features.py` computes normalized sub-scores. `semantic.py` adds a small local TF-IDF signal. `anomalies.py` separates hard honeypots from soft risks. `caps.py` limits suspicious profiles. `scoring.py` applies the V2 formula and deterministic sort. `reasoning.py` creates grounded CSV explanations.

| Module | Responsibility |
| --- | --- |
| `parser.py` | Load JSON/JSONL/demo specs and normalize candidate fields |
| `evidence.py` | Match JD concepts by source field and confidence |
| `features.py` | Convert evidence, experience, logistics, and trust signals into sub-scores |
| `semantic.py` | Add small local TF-IDF semantic boost with fast-mode controls |
| `anomalies.py` | Detect hard honeypots and soft anomaly risks |
| `caps.py` | Prevent suspicious profiles from ranking too high |
| `scoring.py` | Compute final score and deterministic ordering |
| `reasoning.py` | Produce grounded <=500 character explanations |
| `rank.py` | CLI orchestration, runtime profiling, CSV/debug writing |
| `eval/` | Validators, sanity checks, label-sheet and offline metrics workflow |
| `app/` | Streamlit demo sandbox for sample/uploaded candidates |

Debug artifacts:

- `outputs/top100_debug.csv` is the judge/team inspection sheet for sub-scores, evidence, flags, caps, and reasoning.
- `outputs/top100_debug.json` keeps the same top-100 details in structured form for the Streamlit/demo workflow.
