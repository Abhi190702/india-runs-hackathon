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
from semantic import FAST_MAX_FEATURES, FAST_NGRAM_MAX, FAST_TEXT_CHARS, compute_semantic_scores


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


def debug_json(rows):
    return json.dumps(rows[:100], ensure_ascii=True, indent=2, sort_keys=True)


def format_flags(row):
    flags = (row.get("hard_flags") or []) + (row.get("soft_flags") or [])
    return ", ".join(flags)


def row_matches(row, text):
    if not text:
        return True
    text = text.lower().strip()
    return text in row["candidate_id"].lower() or text in str(row.get("current_title", "")).lower()


st.set_page_config(page_title="RedrobRank V2", layout="wide")
st.title("RedrobRank V2")
st.caption("Career proof beats keyword claims")
st.markdown("`CPU-only` `No ranking API calls` `Deterministic` `Source-aware evidence`")

with st.sidebar:
    st.markdown("### Architecture")
    st.markdown("Parse -> Evidence -> Features -> Anomalies -> Caps -> Rank -> Reason")
    st.markdown("### Demo Mode")
    st.write("Upload a small JSON/JSONL sample or use the bundled candidates.")
    st.write("The full 100K run is CLI-only: `python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv`.")
    st.write("The demo uses lean local TF-IDF settings to stay responsive on Streamlit Cloud.")

uploaded = st.file_uploader("Upload candidate sample", type=["json", "jsonl"])
if uploaded:
    candidates = load_json_or_jsonl(uploaded.read().decode("utf-8"))
else:
    candidates = list(iter_candidate_records(SAMPLE_PATH))

run = st.button("Run RedrobRank V2", type="primary")

if run:
    semantic_scores, semantic_enabled, warning = compute_semantic_scores(
        candidates,
        max_features=FAST_MAX_FEATURES,
        ngram_max=FAST_NGRAM_MAX,
        max_candidate_chars=FAST_TEXT_CHARS,
    )
    if not semantic_enabled:
        st.warning(warning)
        semantic_scores = [None] * len(candidates)
    rows = rank_candidates_v2(candidates, semantic_scores=semantic_scores)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    st.session_state["rows"] = rows
    st.session_state["semantic_enabled"] = semantic_enabled

rows = st.session_state.get("rows", [])
semantic_enabled = st.session_state.get("semantic_enabled", False)

if rows:
    top = rows[:100]
    hard_total = sum(1 for row in rows if row.get("hard_honeypot"))
    soft_top = sum(len(row.get("soft_flags") or []) for row in top)
    cols = st.columns(6)
    cols[0].metric("Candidates Ranked", len(rows))
    cols[1].metric("Hard Honeypots", hard_total)
    cols[2].metric("Soft Flags Top 100", soft_top)
    cols[3].metric("Top Score", f"{top[0]['final_score']:.4f}" if top else "n/a")
    cols[4].metric("Rank 100", f"{top[-1]['final_score']:.4f}" if len(top) >= 100 else "n/a")
    cols[5].metric("Semantic", "Enabled" if semantic_enabled else "Disabled")

    st.markdown("### Filters")
    filter_cols = st.columns([1, 1, 1, 2])
    only_anomalies = filter_cols[0].checkbox("Anomalies only")
    only_caps = filter_cols[1].checkbox("Cap reasons only")
    min_score = filter_cols[2].slider("Minimum score", 0.0, 1.0, 0.0, 0.01)
    query = filter_cols[3].text_input("Search candidate/title")

    filtered = []
    for row in top:
        if only_anomalies and not (row.get("hard_flags") or row.get("soft_flags")):
            continue
        if only_caps and not row.get("cap_reasons"):
            continue
        if row["final_score"] < min_score:
            continue
        if not row_matches(row, query):
            continue
        filtered.append(row)

    table = [
        {
            "rank": row["rank"],
            "candidate_id": row["candidate_id"],
            "score": f"{row['final_score']:.6f}",
            "current_title": row["current_title"],
            "years": row["years"],
            "location": row["location"],
            "reasoning": row["reasoning"],
            "anomaly_flags": format_flags(row),
            "cap_reasons": ", ".join(row.get("cap_reasons") or []),
        }
        for row in filtered
    ]
    st.dataframe(table, use_container_width=True, hide_index=True)
    dl_cols = st.columns(2)
    dl_cols[0].download_button("Download submission CSV", submission_csv(rows), file_name="redrobrank_v2_submission.csv", mime="text/csv")
    dl_cols[1].download_button("Download debug JSON", debug_json(rows), file_name="redrobrank_v2_debug.json", mime="application/json")

    st.subheader("Candidate Detail")
    for row in filtered[:25]:
        with st.expander(f"{row['rank']}. {row['candidate_id']} — {row['current_title']}"):
            tab_reason, tab_scores, tab_evidence, tab_risks = st.tabs(["Reasoning", "Score Breakdown", "Evidence", "Risks & Caps"])
            with tab_reason:
                st.write(row["reasoning"])
            with tab_scores:
                st.json(
                    {
                        "technical_fit": row["technical_fit"],
                        "hireability_fit": row["hireability_fit"],
                        "trust_consistency_fit": row["trust_consistency_fit"],
                        "career_evidence_fit": row["career_evidence_fit"],
                        "retrieval_ranking_fit": row["retrieval_ranking_fit"],
                        "production_system_fit": row["production_system_fit"],
                        "semantic_score": row["semantic_score"],
                    }
                )
            with tab_evidence:
                st.write(row.get("matched_evidence") or [])
            with tab_risks:
                st.json(
                    {
                        "hard_honeypot": row.get("hard_honeypot"),
                        "hard_flags": row.get("hard_flags"),
                        "soft_flags": row.get("soft_flags"),
                        "score_cap": row.get("score_cap"),
                        "cap_reasons": row.get("cap_reasons"),
                    }
                )
else:
    st.info("Run the demo to inspect ranked candidates.")
