---
marp: true
theme: default
paginate: true
size: 16:9
---

<!-- _class: lead -->

# RedrobRank V2
## Ranking candidates the way a great recruiter would — not by counting keywords

**Team WildSqaud** · INDIA.RUNS / Redrob — The Data & AI Challenge

`CPU-only` · `No hosted LLM at ranking time` · `Deterministic` · `Explainable`

> How to turn this into a PDF: open in VS Code with the **Marp** extension → "Export slide deck" → PDF.
> (Or paste each `---`-separated section into Google Slides.)

---

# The problem

Recruiters read hundreds of profiles and still miss the right person — **not** because the talent isn't there, but because **keyword filters can't see what actually matters.**

- A "Marketing Manager" who lists 9 AI skills looks perfect to a keyword filter — and is **wrong**.
- A "Senior Data Scientist" who *built a recommendation system in production* never says "RAG" — and is **right**.

**Our goal:** rank the top 100 of 100,000 candidates for a *Senior AI Engineer (Founding Team)* role by understanding **who genuinely fits**.

---

# The hidden challenge: the dataset fights keyword matching

The organizers planted **traps** so naive "embed + cosine sort" fails:

| Trap | What it looks like |
| --- | --- |
| **Keyword stuffers** | Wrong-domain person with every AI buzzword in their skills list |
| **Honeypots (~80)** | Internally *impossible* profiles (8 yrs at a 3-yr-old company; "expert" in 10 skills used 0 months). **>10% in top 100 = disqualification** |
| **Plain-language gems** | Real builders who never use the buzzwords |
| **Behavioral twins** | Identical on paper; differ only in reachability |

A system that just matches words walks into every one of these.

---

# Core insight

> ## Career proof beats keyword claims.

We don't ask *"does the profile contain the word?"* — we ask **"where did the evidence come from, and does the work history prove it?"**

Four principles:
1. **Career-backed evidence matters most** — built > listed.
2. **Retrieval & ranking are central** to this specific role.
3. **Hireability is part of fit** — an unreachable star is not actually available.
4. **Honeypots need logic, not embeddings** — impossibilities are caught by consistency checks.

---

# Architecture — a transparent, multi-stage pipeline

```
candidates.jsonl
   → parser     (clean, flatten 100k profiles)
   → evidence   (source-aware concept matching)
   → features   (technical / hireability / trust → 0..1 each)
   → semantic   (local TF-IDF meaning match, no network)
   → anomalies  (hard honeypots + soft penalties)
   → caps       (ceilings for suspicious profiles)
   → scoring    (weighted fusion, deterministic sort)
   → reasoning  (grounded, honest, per-candidate)
   → submission.csv  (top 100)
```

No black box: **every score traces to inspectable evidence.**

---

# The key idea: source-aware evidence

The same phrase is worth different amounts depending on **where** it appears:

| Evidence source | Weight |
| --- | ---: |
| Job-history description ("built a FAISS search system") | **1.00** |
| Current role description | 1.00 |
| Current / past title | 0.85 / 0.70 |
| Self-written summary | 0.45 |
| **Skills list** ("FAISS") | **0.25** |

➡️ This single design choice **defeats keyword-stuffers** and **surfaces plain-language gems**.

---

# Scoring formula

```
raw   = 0.72·technical + 0.18·hireability + 0.10·trust
final = clamp( min(raw − anomaly_penalty, score_cap), 0, 1 )
```

- **Technical:** career evidence, retrieval/ranking, role title, production systems, experience band.
- **Hireability:** recent activity, recruiter response, notice period, location, relocation.
- **Trust:** profile completeness, skill-duration consistency, data consistency.
- **Anomaly penalty + caps:** push suspicious / impossible profiles down.

A weighted scorecard — fair, tunable, explainable.

---

# How we beat each trap

| Trap | Our defense |
| --- | --- |
| Keyword stuffer | Source-aware evidence (skills weighted 0.25; career 1.00) + wrong-domain caps |
| Honeypot | Pure-logic consistency auditor (tenure vs experience, dates, expert-with-0-months) → hard-floor |
| Plain-language gem | Reads career *descriptions*, not just titles/skills → gems surface |
| Behavioral twin | Hireability signals break the tie |

---

# Results — the ranking is clean and correct

Measured on the full **100,000-candidate** pool:

- ✅ **Top-100 is 100% genuine** AI / ML / Search / NLP / Data titles — **0 wrong-domain**
- ✅ **0 honeypots in the top 100** (69 detected pool-wide, ≈ the ~80 planted)
- ✅ **12 "plain-language gems"** (Senior Data Scientists who built real systems) **surface into the top 100** — we don't bury them
- ✅ **NDCG@10 = 1.00, NDCG@50 = 0.91, P@10 = 1.00** vs our offline recruiter-aligned gold set

---

# Results — fast, reproducible, honest

- ⏱️ **~55 s** for 100k on CPU (budget: 5 min); **~3.4 min** even fully serial
- 🔁 **Deterministic** — identical output across runs (verified), with a **serial fallback** if a sandbox forbids parallelism
- 🚫 **No network, no hosted-LLM calls** during ranking
- 🧪 **20 automated tests** pass
- ✍️ **Grounded reasoning** — quotes each candidate's *own* career text, names honest concerns, **100/100 reasonings unique** (no hallucination, no templating)

---

# Reasoning that a reviewer can trust

> *"7.2 yrs as Senior Machine Learning Engineer at Zomato; career evidence references retrieval/search: …BM25 + dense retrieval (BGE embeddings)…, matching Redrob's retrieval/search and ranking focus. Also recently active, location aligns."*

- References **specific facts** from the profile
- Connects to **specific JD requirements**
- Names **honest concerns** at lower ranks
- **Never invents** skills or employers

---

# Reproducibility & demo

**One command:**
```bash
python src/rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
```

- `requirements.txt`, full source, tests, docs — all in the repo
- **Live Streamlit sandbox** — upload a sample, watch it rank end-to-end
- Real, staged git history (built module-by-module, not a single dump)

---

# Limitations & future work

**Honest about scope:**
- Offline gold is a recruiter-heuristic proxy, not the hidden ground truth — we tune conservatively.
- Semantic layer is lightweight TF-IDF (chosen for the CPU/no-network budget).

**Next:**
- Hand-labeled gold set for tighter offline tuning
- Local cross-encoder re-rank of the top ~200 (where NDCG@10 weight lives)
- Learning-to-rank over the existing transparent features

---

<!-- _class: lead -->

# Thank you

**RedrobRank V2** — *Career proof beats keyword claims.*

GitHub: `github.com/hazelmayank/india-runs-hackathon`
Demo: *(Streamlit sandbox link)*
