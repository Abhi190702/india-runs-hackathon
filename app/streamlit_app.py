"""Streamlit demo sandbox for RedrobRank V2."""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from parser import iter_candidate_records
from scoring import rank_candidates_v2
from semantic import compute_semantic_scores


SAMPLE_PATH = Path(__file__).with_name("sample_candidates.json")


def load_json_or_jsonl(text):
    text = text.strip()
    if not text:
        return []
    if text[0] == "[":
        data = json.loads(text)
        return data if isinstance(data, list) else []
    if text[0] == "{":
        data = json.loads(text)
        if isinstance(data, dict) and "candidates" in data:
            temp = ROOT / "outputs" / "_streamlit_upload.json"
            temp.parent.mkdir(parents=True, exist_ok=True)
            temp.write_text(text, encoding="utf-8")
            return list(iter_candidate_records(temp))
        return [data]
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def submission_csv(rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    for rank, row in enumerate(rows[:100], start=1):
        writer.writerow([row["candidate_id"], rank, f"{row['final_score']:.6f}", row["reasoning"]])
    return buffer.getvalue()


st.set_page_config(page_title="RedrobRank V2", layout="wide")
st.title("RedrobRank V2")

with st.sidebar:
    st.markdown("### Demo Mode")
    st.write("CPU-only deterministic ranker.")
    st.write("No API calls. No hosted LLM. No network ranking step.")
    st.write("Upload a small JSON/JSONL sample or use the bundled demo candidates.")
    st.write("Full 100K ranking runs locally through `python src/rank.py`.")

uploaded = st.file_uploader("Upload candidate sample", type=["json", "jsonl"])
if uploaded:
    candidates = load_json_or_jsonl(uploaded.read().decode("utf-8"))
else:
    candidates = list(iter_candidate_records(SAMPLE_PATH))

run = st.button("Run RedrobRank V2", type="primary")

if run:
    semantic_scores, semantic_enabled, warning = compute_semantic_scores(candidates)
    if not semantic_enabled:
        st.warning(warning)
        semantic_scores = [None] * len(candidates)
    rows = rank_candidates_v2(candidates, semantic_scores=semantic_scores)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank

    table = [
        {
            "rank": row["rank"],
            "candidate_id": row["candidate_id"],
            "score": f"{row['final_score']:.6f}",
            "current_title": row["current_title"],
            "years": row["years"],
            "location": row["location"],
            "reasoning": row["reasoning"],
            "anomaly_flags": ", ".join(row.get("soft_flags") or row.get("hard_flags") or []),
            "cap_reasons": ", ".join(row.get("cap_reasons") or []),
        }
        for row in rows[:100]
    ]
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Download CSV", submission_csv(rows), file_name="redrobrank_v2_submission.csv", mime="text/csv")

    st.subheader("Candidate Detail")
    for row in rows[:25]:
        with st.expander(f"{row['rank']}. {row['candidate_id']} — {row['current_title']}"):
            metrics = {
                "technical_fit": row["technical_fit"],
                "hireability_fit": row["hireability_fit"],
                "trust_consistency_fit": row["trust_consistency_fit"],
                "career_evidence_fit": row["career_evidence_fit"],
                "retrieval_ranking_fit": row["retrieval_ranking_fit"],
                "production_system_fit": row["production_system_fit"],
                "semantic_score": row["semantic_score"],
            }
            st.json(metrics)
            st.write("Matched evidence")
            st.write(row.get("matched_evidence") or [])
