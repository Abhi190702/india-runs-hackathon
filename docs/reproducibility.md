# Reproducibility

Install and run:

```bash
python -m pip install -r requirements.txt
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
python -m pytest -q
python -m compileall src app eval
```

Ranking is deterministic for a fixed input file and reference date (`2026-06-01`). It is CPU-only and makes no network calls. The default semantic layer uses local scikit-learn TF-IDF; `--no-semantic` disables it.
