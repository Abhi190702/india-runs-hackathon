# India.Runs — Idea Submission PPT (filled content)

Paste each slide's content into the matching template slide. Keep bullets short on
the slide; the indented notes are for what you *say*, not what you print.

---

## SLIDE 1 — Title

- **Team Name:** WildSqaud
- **Team Leader Name:** Mayank
- **Problem Statement:** The Data & AI Challenge — *Intelligent Candidate Discovery & Ranking.*
  Rank the **top 100 of 100,000** candidate profiles for a **Senior AI Engineer (Founding Team)** role at Redrob AI — the way a great recruiter would: by understanding who actually fits, **not** by matching keywords.

---

## SLIDE 2 — Solution Overview

**What is your proposed solution?**
- **RedrobRank V2** — a deterministic, CPU-only, fully explainable ranking engine.
- Reads the job description, scores every candidate 0–1, and returns the top 100 with a written reason for each.
- Core philosophy: **"Career proof beats keyword claims."**

**What differentiates it from traditional candidate matching?**
- **Source-aware evidence:** the same skill counts far more when it appears in a candidate's *job history* (weight 1.00) than in their *skills list* (weight 0.25) → defeats keyword-stuffers.
- **Honeypot/anomaly auditor:** pure logic catches *impossible* profiles that embeddings cannot.
- **Hireability signals:** down-weights unreachable candidates (inactive, unresponsive, long notice).
- **No black box:** every score traces to inspectable evidence — built to be *defended*, not just submitted.

---

## SLIDE 3 — JD Understanding & Candidate Evaluation

**Key requirements extracted from the JD:**
- Production **retrieval / ranking / search / recommendation / embeddings** experience.
- Vector search & hybrid search (FAISS, BM25, Pinecone, etc.); evaluation (NDCG/MRR/MAP).
- 5–9 years, product-company background; explicitly **not** keyword-stuffers, pure-research, consulting-only, or title-chasers.

**How we evaluate fit beyond keyword matching:**
- We don't ask *"does the word appear?"* — we ask **"where did the evidence come from, and does the work history prove it?"**
- Most important signals: **career-backed retrieval/ranking evidence**, **production-systems evidence**, **experience band**, plus **hireability** (recent activity, recruiter response, location, notice period).
- Plain-language "gems" (e.g. a Senior Data Scientist who *built a recommender*) are surfaced even without buzzwords.

---

## SLIDE 4 — Ranking Methodology

**Retrieve → score → rank:**
- Parse 100k profiles → extract source-aware concept evidence → compute normalized features → add a local semantic signal → apply anomaly penalties & caps → weighted fusion → deterministic sort → top 100.

**Models / algorithms / heuristics:**
- Rule-driven, inspectable scoring (explainable by design).
- **Local TF-IDF semantic similarity** (scikit-learn) for meaning-match — no network, no hosted LLM.
- Logic-based honeypot/consistency auditor.

**How signals combine into a final ranking:**
```
raw   = 0.72·technical + 0.18·hireability + 0.10·trust
final = clamp( min(raw − anomaly_penalty, score_cap), 0, 1 )
```
- Technical = career evidence, retrieval/ranking, role title, production systems, experience.
- Tie-breaks are deterministic (down to candidate_id) for reproducibility.

---

## SLIDE 5 — Explainability & Data Validation

**How decisions are explained:**
- Every top-100 candidate gets a 1–2 sentence reason that cites **specific facts** from their profile and connects to **specific JD requirements** (and names honest concerns at lower ranks).

**How we prevent hallucinations / unsupported justifications:**
- Reasoning is **assembled deterministically from extracted facts** — it quotes the candidate's *own* career text. It cannot invent skills or employers. Result: **100/100 reasonings unique**, zero fabrication.

**How we handle inconsistent / low-quality / suspicious profiles:**
- **Hard honeypots** (impossible: e.g. 8 yrs at a 3-yr-old company; "expert" in skills used 0 months) → detected by logic and floored.
- **Soft anomalies** (keyword-stuffing, shallow-LLM-only, consulting-only) → penalties.
- **Score caps** → suspicious profiles can't reach the top.
- Result: **0 honeypots in the top 100** (we never trip the >10% disqualification rule).

---

## SLIDE 6 — End-to-End Workflow

```
Job Description
   → JD rubric (must-haves, disqualifiers, weights)
   → Parse 100k candidate profiles
   → Source-aware evidence extraction
   → Features: technical / hireability / trust  (each 0–1)
   → Local TF-IDF semantic boost
   → Anomaly + honeypot detection
   → Score caps for suspicious profiles
   → Weighted scoring + deterministic sort
   → Top 100 + grounded reasoning
   → submission.csv
```
- One command, end-to-end: `python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv`

---

## SLIDE 7 — System Architecture

*(Paste this diagram as an image/text block.)*

```
data/candidates.jsonl
        │
   parser.py        → clean + flatten profiles
   evidence.py      → source-aware concept matching
   features.py      → technical / hireability / trust features
   semantic.py      → local TF-IDF meaning match (no network)
   anomalies.py     → hard honeypots + soft anomalies
   caps.py          → ceilings for suspicious profiles
   scoring.py       → weighted fusion + deterministic sort
   reasoning.py     → grounded, non-hallucinated reasons
   rank.py          → CLI entry point
        │
        ▼
   submission.csv (top 100)   +   Streamlit demo sandbox
```
- Constraints honored: **CPU-only · no network · no hosted-LLM at ranking time · deterministic.**

---

## SLIDE 8 — Results & Performance

**Ranking quality (full 100,000-candidate run):**
- **Top-100 is 100% genuine** AI / ML / Search / NLP / Data titles — **0 wrong-domain, 0 honeypots.**
- **69 honeypots detected** pool-wide (≈ the ~80 planted).
- **12 "plain-language gems"** (non-AI-title builders) correctly surface into the top 100 — not buried.
- **NDCG@10 = 1.00, NDCG@50 = 0.91, P@10 = 1.00** vs our offline recruiter-aligned gold set.
- **100/100 reasonings unique** (no templating, no hallucination).

**Meeting runtime & compute constraints (budget: 5 min, 16 GB, CPU, no network):**
- **~55 sec** for 100k (parallel) · **~3.4 min** fully serial — both well under budget.
- **Deterministic** (identical output across runs) with a **serial fallback** if a sandbox blocks parallelism.
- **20/20 automated tests pass**; official format validator passes.

---

## SLIDE 9 — Technologies Used

| Tech | Why |
| --- | --- |
| **Python 3.11** | Core language; clean, reproducible |
| **scikit-learn (TF-IDF)** | Local semantic similarity — meaning match without any network/API |
| **NumPy** | Fast vector math within the CPU budget |
| **Streamlit** | Live demo sandbox (required deliverable) |
| **pytest** | 20 automated tests for correctness & reproducibility |
| **Git/GitHub** | Versioned, staged history (real iteration, not a single dump) |

- **Deliberately no GPU and no hosted LLM at ranking time** — the system must scale to 200k+ profiles in production within tight latency, so we chose lightweight, local, explainable components.

---

## SLIDE 10 — Submission Assets

- **GitHub repo:** https://github.com/hazelmayank/india-runs-hackathon
- **Live demo (Streamlit sandbox):** https://india-runs-hackathon-d4kd2fvfgaxeqbzen3hhyx.streamlit.app
- **Ranked output:** `submission.csv` (top 100, official format, validator-passed)
- **Docs:** README, architecture, methodology, honeypot, reproducibility notes
- **Reproduce command:** `python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv`

---

## SLIDE 11 — Thank You

**RedrobRank V2 — *Career proof beats keyword claims.***
Team WildSqaud · India.Runs / Redrob — The Data & AI Challenge
