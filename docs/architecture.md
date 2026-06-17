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
