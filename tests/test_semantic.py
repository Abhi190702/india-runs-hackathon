from conftest import make_candidate
from semantic import compute_semantic_scores


def test_semantic_returns_one_score_per_candidate():
    candidates = [make_candidate(), make_candidate()]
    scores, enabled, warning = compute_semantic_scores(
        candidates,
        max_features=500,
        ngram_max=1,
        max_candidate_chars=300,
    )
    assert len(scores) == len(candidates)
    assert isinstance(enabled, bool)
    assert isinstance(warning, str)
    assert all(0.0 <= score <= 1.0 for score in scores)
