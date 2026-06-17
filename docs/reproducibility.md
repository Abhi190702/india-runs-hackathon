# Reproducibility

Install and run:

```bash
python -m pip install -r requirements.txt
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
python -m pytest -q
python -m compileall src app eval
```

Ranking is deterministic for a fixed input file and reference date (`2026-06-01`). It is CPU-only and makes no network calls. The default semantic layer uses local scikit-learn TF-IDF; `--no-semantic` disables it.

Do not commit `data/candidates.jsonl`, `submission.csv`, or debug outputs. They are local artifacts.

## Final Verification

```bash
python -m pytest -q
python -m compileall src app eval
python -m py_compile app/streamlit_app.py
python src/rank.py --candidates ./app/sample_candidates.json --out ./outputs/sample_submission.csv --debug-json ./outputs/sample_debug.json --debug-csv ./outputs/sample_debug.csv --fast
python -c "from src.validators import validate_submission_csv; print(validate_submission_csv('./outputs/sample_submission.csv'))"
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv --debug-json ./outputs/top100_debug.json --debug-csv ./outputs/top100_debug.csv --profile-runtime
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission_fast.csv --debug-json ./outputs/top100_debug_fast.json --debug-csv ./outputs/top100_debug_fast.csv --fast --profile-runtime
python outputs/validate_submission.py submission.csv
python -c "from src.validators import validate_submission_csv; print(validate_submission_csv('submission.csv'))"
python eval/check_reasoning_quality.py --submission submission.csv
python eval/inspect_top.py --debug outputs/top100_debug.csv --k 25
python eval/final_sanity_check.py --submission submission.csv --debug outputs/top100_debug.csv --metadata submission_metadata.yaml
```

Use fast mode when the machine is slower:

```bash
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission_fast.csv --fast
```

Disable semantic scoring for a pure structured-evidence fallback:

```bash
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv --no-semantic
```
