# Scoring Model

```text
raw_score = 0.72 * technical_fit + 0.18 * hireability_fit + 0.10 * trust_consistency_fit
final_score = clamp(min(raw_score - anomaly_penalty, score_cap), 0, 1)
```

`technical_fit` weights career evidence, retrieval/ranking, role title, production systems, skill quality, experience, product/startup context, and coding recency.

`hireability_fit` weights recent activity, recruiter response, response speed, notice, location, work mode, relocation, interview follow-through, offer acceptance, and contact verification.

`trust_consistency_fit` weights profile completeness, skill duration consistency, assessment quality, GitHub signal, career stability, education relevance, and data consistency.

Tie-breakers are deterministic: final score, technical fit, career evidence, retrieval/ranking, production evidence, hireability, lower anomaly penalty, then candidate ID.
