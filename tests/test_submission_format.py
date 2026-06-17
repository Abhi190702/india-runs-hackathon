from pathlib import Path

from rank import main
from validators import validate_submission_csv


def test_final_csv_format_correct():
    root = Path(__file__).resolve().parents[1]
    out = root / "outputs" / "test_submission.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    main(["--candidates", str(root / "app" / "sample_candidates.json"), "--out", str(out), "--no-semantic"])
    result = validate_submission_csv(out)
    assert result["ok"], result["errors"]
