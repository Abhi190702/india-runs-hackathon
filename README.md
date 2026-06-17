<div align="center">

# RedrobRank V2

### Explainable Candidate Discovery Engine for INDIA.RUNS / Redrob Track 1

RedrobRank V2 is a deterministic, CPU-only, source-aware ranking engine that selects the top 100 candidates from 100,000 profiles for the role:

**Senior AI Engineer - Founding Team at Redrob AI**

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![CPU Only](https://img.shields.io/badge/CPU%20Only-Deterministic-2EA44F?style=for-the-badge)](#)
[![No Hosted LLM](https://img.shields.io/badge/No%20Hosted%20LLM-Ranking%20Time-111827?style=for-the-badge)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-Demo%20Ready-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](#)

</div>

---

## Table Of Contents

- [Overview](#overview)
- [Core Philosophy](#core-philosophy)
- [What V2 Improves](#what-v2-improves)
- [Architecture](#architecture)
- [Scoring Formula](#scoring-formula)
- [Source-Aware Evidence](#source-aware-evidence)
- [Feature System](#feature-system)
- [Honeypot And Anomaly Detection](#honeypot-and-anomaly-detection)
- [Score Caps](#score-caps)
- [Semantic Layer](#semantic-layer)
- [Reasoning Engine](#reasoning-engine)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Run The Ranker](#run-the-ranker)
- [Verification Snapshot](#verification-snapshot)
- [Final Verification](#final-verification)
- [Submission Checklist](#submission-checklist)
- [Debugging And Inspection](#debugging-and-inspection)
- [Streamlit Demo](#streamlit-demo)
- [Contributors](#contributors)
- [AI Usage Declaration](#ai-usage-declaration)
- [Limitations](#limitations)
- [Future Work](#future-work)

---

## Overview

The INDIA.RUNS / Redrob Track 1 challenge asks teams to rank the best 100 candidates from a large anonymized profile dataset. The target role is not a generic AI role. It strongly favors candidates who have actually built production retrieval, ranking, matching, recommendation, search, embedding, and ML systems.

RedrobRank V2 is designed around that interpretation.

It does not simply count AI keywords. It checks where the evidence came from, whether the candidate's work history proves the claim, whether behavioral hiring signals suggest the person is reachable, and whether the profile contains impossible or suspicious data patterns.

---

## Core Philosophy

> Career proof beats keyword claims.

The model is built around four ideas:

1. **Career-backed evidence matters most.**  
   A candidate who built a FAISS-based semantic search system in production is much stronger than someone who only lists "FAISS" in a skills section.

2. **Retrieval and ranking are central to the role.**  
   Embeddings, vector search, BM25, hybrid search, ranking metrics, recommendation systems, and search relevance are treated as core signals.

3. **Hireability is part of fit.**  
   A perfect technical candidate who is inactive, unresponsive, outside the target geography, or on a very long notice period is less useful to recruiters.

4. **Honeypots require logic, not embeddings.**  
   Impossible dates, contradictory durations, and inflated skill histories cannot be caught reliably by semantic similarity alone.

---

## What V2 Improves

| Area | V1 | V2 |
| --- | --- | --- |
| Evidence | Merged candidate text | Source-aware evidence buckets |
| Formula | `fit * availability * honeypot_gate` | Weighted technical, hireability, trust, anomaly, cap formula |
| Skills | Could influence blended text | Skills are weak unless career-backed |
| Honeypots | Binary hard gate | Hard honeypots plus soft anomaly penalties |
| Caps | Limited | Explicit caps for suspicious profiles |
| Semantics | Not active | Local TF-IDF semantic boost |
| Debugging | Minimal | Top-100 JSON/CSV debug outputs |
| Reasoning | Basic deterministic text | Grounded evidence-first reasoning |
| Demo | None | Streamlit sandbox |
| Tests | Minimal | Focused pytest suite |
| Docs | Basic README | Architecture, scoring, methodology, honeypot, reproducibility, deployment docs |

---

## Architecture

```text
data/candidates.jsonl
        |
        v
src/parser.py
        |
        v
src/evidence.py
        |
        v
src/features.py
        |
        v
src/semantic.py
        |
        v
src/anomalies.py
        |
        v
src/caps.py
        |
        v
src/scoring.py
        |
        v
src/reasoning.py
        |
        v
src/rank.py
        |
        v
submission.csv
```

### Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `src/parser.py` | Reads JSONL/JSON, handles missing fields, creates stable flattened candidate views |
| `src/evidence.py` | Extracts source-aware JD concept evidence |
| `src/features.py` | Computes normalized technical, hireability, and trust features |
| `src/anomalies.py` | Detects hard honeypots and soft anomalies |
| `src/caps.py` | Applies maximum score caps for suspicious patterns |
| `src/semantic.py` | Adds a lightweight local TF-IDF semantic signal |
| `src/scoring.py` | Applies the V2 scoring formula and deterministic sorting |
| `src/reasoning.py` | Builds short, grounded, non-hallucinated reasoning strings |
| `src/rank.py` | CLI entry point for full ranking and debug artifact generation |
| `src/validators.py` | Internal submission format validation |

---

## Scoring Formula

V2 replaces the old multiplicative formula with a gated weighted model:

```text
raw_score =
0.72 * technical_fit
+ 0.18 * hireability_fit
+ 0.10 * trust_consistency_fit

penalized_score = raw_score - anomaly_penalty

final_score = clamp(
    min(penalized_score, score_cap),
    0.0,
    1.0
)
```

### Technical Fit

```text
technical_fit =
0.24 * career_evidence_fit
+ 0.20 * retrieval_ranking_fit
+ 0.16 * role_title_fit
+ 0.14 * production_system_fit
+ 0.10 * skill_quality_fit
+ 0.08 * experience_fit
+ 0.05 * product_startup_fit
+ 0.03 * coding_recency_fit
```

### Hireability Fit

```text
hireability_fit =
0.20 * recent_activity_fit
+ 0.18 * recruiter_response_fit
+ 0.14 * avg_response_time_fit
+ 0.12 * notice_period_fit
+ 0.12 * location_fit
+ 0.08 * work_mode_fit
+ 0.06 * relocation_fit
+ 0.05 * interview_followthrough_fit
+ 0.03 * offer_acceptance_fit
+ 0.02 * contact_verified_fit
```

### Trust Consistency Fit

```text
trust_consistency_fit =
0.22 * profile_completeness_fit
+ 0.20 * skill_duration_consistency_fit
+ 0.16 * assessment_quality_fit
+ 0.14 * github_signal_fit
+ 0.12 * career_stability_fit
+ 0.08 * education_relevance_fit
+ 0.08 * data_consistency_fit
```

---

## Source-Aware Evidence

V2 extracts concept matches from separate evidence buckets and weights each source differently.

| Evidence Source | Weight | Interpretation |
| --- | ---: | --- |
| `career_description_text` | `1.00` | Strongest proof of shipped work |
| `current_role_description_text` | `1.00` | Strong current responsibility signal |
| `current_title_text` | `0.85` | Important but not enough alone |
| `past_title_text` | `0.70` | Historical role context |
| `summary_headline_text` | `0.45` | Helpful, but self-written |
| `company_industry_text` | `0.35` | Domain context |
| `skills_text` | `0.25` | Supporting evidence only |
| `education_text` | `0.20` | Background context |

Skills-only evidence is intentionally capped. A candidate cannot dominate the ranking by listing AI tools without career-backed proof.

---

## Feature System

The ranker scores candidates across three major dimensions:

### 1. Technical Fit

This measures whether the candidate has the right career proof for the Redrob AI role.

Strong signals include:

- Embeddings and embedding models
- Dense retrieval and semantic search
- Vector search with FAISS, Qdrant, Milvus, Pinecone, Weaviate, Elasticsearch, or OpenSearch
- BM25 and hybrid search
- Reranking, cross-encoders, bi-encoders
- Recommendation systems and learning-to-rank
- Search relevance and candidate matching
- NDCG, MRR, MAP, precision/recall at K
- Production APIs, pipelines, latency, monitoring, and deployed ML systems

### 2. Hireability Fit

This measures whether the candidate is likely reachable and practical to hire.

Signals include:

- Last active date
- Recruiter response rate
- Average response time
- Notice period
- Location
- Work mode preference
- Relocation willingness
- Interview completion
- Offer acceptance
- Verified contact signals

### 3. Trust And Consistency Fit

This measures whether the profile looks complete, internally consistent, and credible.

Signals include:

- Profile completeness
- Skill duration consistency
- Skill assessment quality
- GitHub activity
- Career stability
- Education relevance
- Basic data consistency

---

## Honeypot And Anomaly Detection

The dataset contains planted honeypots. V2 separates hard contradictions from softer risk patterns.

### Hard Honeypots

Hard honeypots are internally impossible profiles, such as:

- Job ends before it starts
- Current job has an end date
- Future job start date
- Current-job duration contradicts elapsed time since start date
- Education ends before it starts
- Single tenure exceeds total stated experience
- Career span contradicts stated experience
- Multiple expert skills with zero months used and weak endorsement proof
- Large date/duration contradictions

### Soft Anomalies

Soft anomalies reduce score but do not automatically eliminate a candidate:

- AI keyword stuffing
- Wrong-domain title with weak career evidence
- Shallow LangChain/OpenAI/chatbot-only profile
- Pure research without production deployment
- Consulting-only weak fit
- CV/speech/robotics-only without NLP/IR/retrieval
- Inactive for more than 180 days
- Very low recruiter response rate
- Notice period over 120 days
- Outside India and not willing to relocate
- Title-chaser/job-hopper pattern
- Manager-only role with no recent hands-on coding evidence

---

## Score Caps

Caps prevent suspicious candidates from floating too high.

Examples:

| Condition | Maximum Score |
| --- | ---: |
| Hard honeypot | `0.20` |
| Wrong-domain title and weak career evidence | `0.35` |
| Severe AI keyword stuffing with no production proof | `0.42` |
| Shallow chatbot-only profile | `0.48` |
| Outside India and not willing to relocate | `0.58` |
| Less than 3 years experience | `0.58` |
| No production system evidence | `0.65` |
| Inactive for more than 180 days | `0.70` |
| Notice period over 120 days | `0.82` |
| Recruiter response rate under 20 percent | `0.82` |

---

## Semantic Layer

The semantic layer is intentionally lightweight and local.

It uses:

```text
TfidfVectorizer from scikit-learn
```

It does not use:

- Hosted APIs
- Hosted LLMs
- GPU inference
- Internet calls
- Sentence-transformers
- Torch

The semantic score is only a small technical-fit boost:

```text
technical_fit_v2 = 0.90 * technical_fit + 0.10 * semantic_score
```

This helps catch relevant profiles that describe good work in plain language, while preventing semantic similarity from overpowering hard evidence.

---

## Reasoning Engine

Every submission row includes a deterministic reasoning string.

Reasoning is built from:

- Current title
- Years of experience
- Top evidence snippets
- Matched JD concepts
- Hireability notes
- Anomaly or cap concerns

The reasoning engine does not invent company names, degrees, metrics, skills, or locations. It only uses extracted candidate facts.

Example shape:

```text
7.2 yrs as Senior Machine Learning Engineer; career evidence shows BM25 + dense retrieval with FAISS and embeddings; matching Redrob's retrieval/search and ranking evaluation focus; long notice.
```

---

## Repository Structure

```text
.
|-- app/
|   |-- sample_candidates.json
|   `-- streamlit_app.py
|-- docs/
|   |-- architecture.md
|   |-- honeypot_detection.md
|   |-- methodology.md
|   |-- reproducibility.md
|   |-- scoring_model.md
|   `-- streamlit_deployment.md
|-- eval/
|   |-- check_reasoning_quality.py
|   |-- compare_runs.py
|   |-- diagnose_honeypots.py
|   |-- inspect_top.py
|   |-- make_label_sheet.py
|   `-- metrics.py
|-- src/
|   |-- anomalies.py
|   |-- audit.py
|   |-- caps.py
|   |-- debug.py
|   |-- evidence.py
|   |-- features.py
|   |-- fit.py
|   |-- jd.py
|   |-- parser.py
|   |-- rank.py
|   |-- reasoning.py
|   |-- scoring.py
|   |-- semantic.py
|   |-- signals.py
|   `-- validators.py
|-- tests/
|-- README.md
|-- requirements.txt
`-- submission_metadata.yaml
```

Ignored local artifacts:

```text
data/
submission.csv
outputs/*
*.jsonl
*.jsonl.gz
```

The organizer dataset is intentionally not committed.

---

## Installation

```bash
python -m pip install -r requirements.txt
```

Requirements:

```text
numpy==1.26.4
scikit-learn==1.4.2
streamlit==1.35.0
pytest==8.2.0
```

---

## Run The Ranker

Place the organizer candidate file at:

```text
data/candidates.jsonl
```

Run:

```bash
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
```

Optional debug run:

```bash
python src/rank.py \
  --candidates ./data/candidates.jsonl \
  --out ./submission.csv \
  --debug-json ./outputs/top100_debug.json \
  --debug-csv ./outputs/top100_debug.csv \
  --profile-runtime
```

Fast mode for slower CPU-only machines:

```bash
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission_fast.csv --fast --profile-runtime
```

Disable semantic layer:

```bash
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv --no-semantic
```

---

## Verification Snapshot

Latest local full verification:

```text
candidates loaded: 100000
semantic: enabled
hard honeypots detected: 69
hard honeypots in top 100: 0
soft anomaly count in top 100: 6
top score: 0.939794
rank 100 score: 0.763930
load_time: 14.70
semantic_time: 38.24
scoring_time: 85.07
total_time: 138.91
fast_total_time: 131.62
```

Validation:

```text
Unit tests: 20 passed
Internal validator: passed
Organizer validator: Submission is valid
Reasoning quality check: passed
Compile checks: passed
Final sanity: submission/debug passed; metadata placeholders still need team details
```

## Final Verification

Commands:

```bash
python -m pytest -q
python -m compileall src app eval
python -m py_compile app/streamlit_app.py
python src/rank.py --candidates ./app/sample_candidates.json --out ./outputs/sample_submission.csv --debug-json ./outputs/sample_debug.json --debug-csv ./outputs/sample_debug.csv --fast
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv --debug-json ./outputs/top100_debug.json --debug-csv ./outputs/top100_debug.csv --profile-runtime
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission_fast.csv --debug-json ./outputs/top100_debug_fast.json --debug-csv ./outputs/top100_debug_fast.csv --fast --profile-runtime
python outputs/validate_submission.py submission.csv
python -c "from src.validators import validate_submission_csv; print(validate_submission_csv('submission.csv'))"
python eval/check_reasoning_quality.py --submission submission.csv
python eval/inspect_top.py --debug outputs/top100_debug.csv --k 25
python eval/final_sanity_check.py --submission submission.csv --debug outputs/top100_debug.csv --metadata submission_metadata.yaml
```

`submission_metadata.yaml` intentionally stays `submission_ready: false` until team contact details and the deployed Streamlit sandbox link are filled.

---

## Submission Checklist

- `submission.csv` has exactly 100 rows and the required header.
- `outputs/top100_debug.csv` has no hard honeypots in top 100.
- `python outputs/validate_submission.py submission.csv` passes.
- `python eval/final_sanity_check.py ...` passes except for intentional metadata placeholders.
- `submission_metadata.yaml` has real team/contact/sandbox details before portal submission.
- `data/candidates.jsonl`, `submission.csv`, and generated debug outputs are not committed.

---

## Debugging And Inspection

Inspect the top candidates:

```bash
python eval/inspect_top.py --debug outputs/top100_debug.csv --k 25
```

Check reasoning quality:

```bash
python eval/check_reasoning_quality.py --submission submission.csv
```

Compare two runs:

```bash
python eval/compare_runs.py --old outputs/v1_debug.csv --new outputs/v2_debug.csv
```

Create a manual labeling sheet:

```bash
python eval/make_label_sheet.py
```

Evaluate against a hand-labeled gold set:

```bash
python eval/metrics.py --submission submission.csv --gold eval/gold.csv
```

---

## Streamlit Demo

Run locally:

```bash
streamlit run app/streamlit_app.py
```

The demo app:

- Uses bundled sample candidates
- Allows JSON/JSONL upload
- Runs the deterministic V2 ranker
- Shows ranking table
- Shows candidate details
- Shows matched evidence
- Provides CSV download
- Does not require the full 100K dataset
- Does not call network APIs

Deploy on Streamlit Community Cloud:

1. Push this repository to GitHub.
2. Go to Streamlit Cloud.
3. Click **Create app**.
4. Select the repository.
5. Set main file path:

```text
app/streamlit_app.py
```

6. Deploy.
7. Add the deployed app link to `submission_metadata.yaml`.

---

## Contributors

<div align="center">

<table>
  <tr>
    <td align="center" width="190">
      <a href="https://github.com/WildTrio">
        <img src="https://github.com/WildTrio.png?size=160" width="120" height="120" alt="WildTrio avatar" />
        <br />
        <sub><b>WildTrio</b></sub>
      </a>
      <br />
      <a href="https://github.com/WildTrio">
        <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
      </a>
    </td>
    <td align="center" width="190">
      <a href="https://github.com/hazelmayank">
        <img src="https://github.com/hazelmayank.png?size=160" width="120" height="120" alt="hazelmayank avatar" />
        <br />
        <sub><b>hazelmayank</b></sub>
      </a>
      <br />
      <a href="https://github.com/hazelmayank">
        <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
      </a>
    </td>
    <td align="center" width="190">
      <a href="https://github.com/Abhi190702">
        <img src="https://github.com/Abhi190702.png?size=160" width="120" height="120" alt="Abhi190702 avatar" />
        <br />
        <sub><b>Abhi190702</b></sub>
      </a>
      <br />
      <a href="https://github.com/Abhi190702">
        <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
      </a>
    </td>
    <td align="center" width="190">
      <a href="https://github.com/Enigma044">
        <img src="https://github.com/Enigma044.png?size=160" width="120" height="120" alt="Enigma044 avatar" />
        <br />
        <sub><b>Enigma044</b></sub>
      </a>
      <br />
      <a href="https://github.com/Enigma044">
        <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
      </a>
    </td>
  </tr>
</table>

</div>

---

## AI Usage Declaration

AI tools were used to help write, refactor, review, and document the deterministic ranking system.

No candidate data is sent to hosted LLMs during ranking. The ranking step is local, CPU-only, deterministic, and does not make network calls.

---

## Limitations

- Hidden ground truth is not available during development.
- Hand-labeled evaluation sets are approximate.
- TF-IDF is explainable and fast, but not a deep cross-encoder.
- Honeypot detection is conservative to avoid false positives.
- Company/domain normalization can be improved.
- Streamlit is a sandbox demo, not the full 100K production runner.

---

## Future Work

- Build a larger hand-labeled validation set.
- Add more soft anomaly detectors for hidden honeypot patterns.
- Add optional local embedding reranking if compute rules allow.
- Add top-200 cross-encoder reranking if allowed by runtime and dependency constraints.
- Improve company, industry, and role-title normalization.
- Expand reasoning templates for more variation in manual review.

---

<div align="center">

**RedrobRank V2: transparent ranking, grounded evidence, deterministic output.**

</div>
