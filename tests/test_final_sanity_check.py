import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval"
if str(EVAL) not in sys.path:
    sys.path.insert(0, str(EVAL))

from final_sanity_check import run_checks


def test_final_sanity_check_passes_clean_mock_files():
    tmp_dir = ROOT / "outputs" / "test_final_sanity"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    submission = tmp_dir / "submission.csv"
    debug = tmp_dir / "debug.csv"
    metadata = tmp_dir / "submission_metadata.yaml"

    with open(submission, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for idx in range(1, 101):
            writer.writerow([f"CAND_{idx:07d}", idx, f"{1 - idx * 0.001:.6f}", f"{idx}.0 yrs as AI Engineer; career evidence shows retrieval proof."])

    fields = [
        "rank",
        "candidate_id",
        "current_title",
        "career_evidence_fit",
        "retrieval_ranking_fit",
        "production_system_fit",
        "score_cap",
        "hard_honeypot",
        "cap_reasons",
        "soft_flags",
        "anomaly_penalty",
        "matched_evidence",
    ]
    with open(debug, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for idx in range(1, 101):
            writer.writerow(
                {
                    "rank": idx,
                    "candidate_id": f"CAND_{idx:07d}",
                    "current_title": "AI Engineer",
                    "career_evidence_fit": "0.90",
                    "retrieval_ranking_fit": "0.70",
                    "production_system_fit": "0.55",
                    "score_cap": "1.0",
                    "hard_honeypot": "False",
                    "cap_reasons": "[]",
                    "soft_flags": "[]",
                    "anomaly_penalty": "0.0",
                    "matched_evidence": "retrieval: proof",
                }
            )

    metadata.write_text(
        """
submission_ready: true
team_name: RedrobRank Team
primary_contact:
  name: Demo Lead
  email: lead@redrobrank.dev
  phone: +91-9876543210
github_repo: https://github.com/hazelmayank/india-runs-hackathon
sandbox_link: https://share.streamlit.io/hazelmayank/india-runs-hackathon/main/app/streamlit_app.py
compute:
  cpu_cores: 8
  ram_gb: 16
  python_version: 3.11
  os: Windows
declarations:
  ranking_cpu_only: true
  no_network_calls_during_ranking: true
  no_hosted_llm_calls_during_ranking: true
""".strip(),
        encoding="utf-8",
    )

    sections = run_checks(submission, debug, metadata)
    errors = [error for section in sections.values() for error in section[0]]
    assert errors == []
