# Methodology

RedrobRank V2 follows one principle: career proof beats keyword claims. It ranks candidates by proof of shipped work, not keyword density. The strongest evidence comes from career descriptions and current role descriptions because those fields describe what a candidate actually built.

Skills are useful but weak. If FAISS, embeddings, ranking, or NDCG appears only in a skills list, the model treats it as supporting evidence rather than career proof. This keeps keyword-stuffed profiles below candidates whose job history shows production retrieval, ranking, search, recommendation, and ML systems.

Behavioral signals are part of fit because a perfect technical match who is inactive, unresponsive, outside the hiring geography, or on a long notice period is less actionable for recruiters.

Source-aware evidence is the core defense against shallow matches:

- Career description evidence beats skills-only evidence because it describes ownership, systems, and outcomes.
- A shallow chatbot-only profile is not enough for this JD unless it also shows retrieval/ranking, evaluation, or production system ownership.
- CV/research-only profiles are adjacent: useful AI background, but not the best match for Redrob's retrieval/search/ranking problem.
