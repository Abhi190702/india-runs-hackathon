from conftest import make_candidate
from evidence import match_concepts_by_source, summarize_evidence


def test_evidence_source_weights_work():
    candidate = make_candidate()
    evidence = match_concepts_by_source(candidate)
    career = [ev for ev in evidence if ev.source == "career_description_text" and ev.phrase.lower() == "faiss"]
    skills = [ev for ev in evidence if ev.source == "skills_text" and ev.phrase.lower() == "faiss"]
    assert career and skills
    assert career[0].source_weight > skills[0].source_weight
    assert career[0].confidence > skills[0].confidence


def test_evidence_summary_tracks_career_backing():
    summary = summarize_evidence(match_concepts_by_source(make_candidate()))
    assert "core_retrieval_ranking" in summary["career_backed_concepts"]
