from parser import flatten_candidate, iter_candidate_records
from pathlib import Path


def test_parser_handles_missing_fields():
    candidate = {"candidate_id": "CAND_0000002"}
    flat = flatten_candidate(candidate)
    assert flat["candidate_id"] == "CAND_0000002"
    assert flat["years"] == 0.0
    assert flat["skills_text"] == ""


def test_parser_expands_demo_fixture():
    path = Path(__file__).resolve().parents[1] / "outputs" / "test_parser_sample.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"expand_to": 3, "candidates": [{"candidate_id": "CAND_0000001", "profile": {}}]}', encoding="utf-8")
    rows = list(iter_candidate_records(path))
    assert len(rows) == 3
    assert rows[0]["candidate_id"] == "CAND_9000001"
