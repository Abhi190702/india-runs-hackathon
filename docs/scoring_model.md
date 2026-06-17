# Scoring Model

```text
raw_score = 0.72 * technical_fit + 0.18 * hireability_fit + 0.10 * trust_consistency_fit
final_score = clamp(min(raw_score - anomaly_penalty, score_cap), 0, 1)
```

`technical_fit` weights career evidence, retrieval/ranking, role title, production systems, skill quality, experience, product/startup context, and coding recency.

`hireability_fit` weights recent activity, recruiter response, response speed, notice, location, work mode, relocation, interview follow-through, offer acceptance, and contact verification.

`trust_consistency_fit` weights profile completeness, skill duration consistency, assessment quality, GitHub signal, career stability, education relevance, and data consistency.

`technical_fit` gets 72 percent of the raw score because the role is a Senior AI Engineer founding-team role: proof of shipped retrieval/ranking/production ML work matters more than availability signals. Hireability still matters at 18 percent because recruiters need reachable candidates. Trust/consistency is 10 percent to reward complete, coherent profiles without letting polished but irrelevant profiles win.

When semantic scoring is enabled, it is only 10 percent of `technical_fit`; the other 90 percent remains source-aware structured evidence. This keeps TF-IDF useful for plain-language matches while preventing keyword-heavy profiles from overpowering career proof.

Tie-breakers are deterministic: final score, technical fit, career evidence, retrieval/ranking, production evidence, hireability, lower anomaly penalty, then candidate ID.

## Example Behavior

| Demo | Expected Behavior |
| --- | --- |
| A: career-backed FAISS, BM25, NDCG, production API | High score; strong retrieval/ranking and production evidence |
| B: recommendation/ranking engineer with evaluation metrics | High score; ranking/evaluation evidence carries the fit |
| C: backend/data engineer with pipelines but thin retrieval ownership | Mid score; adjacent production fit |
| D: research/CV-only profile | Lower score; adjacent AI but not ideal for retrieval/ranking |
| E: wrong-domain profile with AI terms in skills | Capped/penalized; keywords are not enough |
| F: impossible dates or expert-zero skill cluster | Hard honeypot; capped at 0.20 |
