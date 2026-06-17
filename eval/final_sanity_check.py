"""Final submission sanity checks for RedrobRank V2."""

from __future__ import annotations

import argparse
import ast
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import jd


HEADER = ["candidate_id", "rank", "score", "reasoning"]
PLACEHOLDER_RE = re.compile(r"\[.+?\]|your_|example\.com|xxxx|fill|placeholder", re.I)
GENERIC_REASONING = ["great candidate", "strong candidate", "placeholder", "lorem ipsum", "n/a"]


def _parse_bool(value):
    return str(value).strip().lower() in {"true", "yes", "1"}


def _parse_list(value):
    try:
        parsed = ast.literal_eval(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _read_metadata(path):
    data = {}
    stack = [data]
    indents = [0]
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.split("#", 1)[0].rstrip()
            if not line.strip() or line.lstrip().startswith("- "):
                continue
            indent = len(line) - len(line.lstrip(" "))
            while indent < indents[-1] and len(stack) > 1:
                stack.pop()
                indents.pop()
            if ":" not in line:
                continue
            key, value = line.strip().split(":", 1)
            value = value.strip().strip('"').strip("'")
            if value:
                stack[-1][key] = value
            else:
                child = {}
                stack[-1][key] = child
                stack.append(child)
                indents.append(indent + 2)
    return data


def _is_placeholder(value):
    return not str(value or "").strip() or bool(PLACEHOLDER_RE.search(str(value)))


def check_submission(path):
    errors = []
    warnings = []
    path = Path(path)
    if not path.exists():
        return [f"submission missing: {path}"], warnings
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADER:
            errors.append(f"header must be exactly {','.join(HEADER)}")
        rows = list(reader)
    if len(rows) != 100:
        errors.append(f"expected exactly 100 rows, found {len(rows)}")

    seen_ids = set()
    seen_reasoning = set()
    scores = []
    ranks = []
    for row in rows:
        cid = (row.get("candidate_id") or "").strip()
        reasoning = (row.get("reasoning") or "").strip()
        if not cid:
            errors.append("empty candidate_id")
        if cid in seen_ids:
            errors.append(f"duplicate candidate_id: {cid}")
        seen_ids.add(cid)
        try:
            ranks.append(int(row.get("rank") or ""))
        except ValueError:
            errors.append(f"{cid}: rank is not an integer")
        try:
            scores.append(float(row.get("score") or ""))
        except ValueError:
            errors.append(f"{cid}: score is not numeric")
        if not reasoning:
            errors.append(f"{cid}: empty reasoning")
        if len(reasoning) > 500:
            errors.append(f"{cid}: reasoning exceeds 500 chars")
        if reasoning in seen_reasoning:
            errors.append(f"{cid}: repeated reasoning string")
        seen_reasoning.add(reasoning)
        if any(phrase in reasoning.lower() for phrase in GENERIC_REASONING):
            errors.append(f"{cid}: generic placeholder reasoning")

    if sorted(ranks) != list(range(1, 101)):
        errors.append("ranks must be exactly 1..100")
    for left, right in zip(scores, scores[1:]):
        if left < right:
            errors.append("scores must be non-increasing")
            break
    return errors, warnings


def check_debug(path):
    errors = []
    warnings = []
    path = Path(path)
    if not path.exists():
        return [f"debug file missing: {path}"], warnings
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        rows = list(reader)

    required = {"hard_honeypot", "cap_reasons", "soft_flags", "anomaly_penalty"}
    missing = sorted(required - fields)
    if missing:
        errors.append(f"debug missing columns: {', '.join(missing)}")
    if not ({"matched_evidence", "top_evidence"} & fields):
        errors.append("debug missing matched_evidence/top_evidence column")

    hard_top = sum(1 for row in rows[:100] if str(row.get("hard_honeypot")).lower() == "true")
    if hard_top:
        errors.append(f"hard honeypots in top100: {hard_top}")

    wrong_terms = [term.lower() for term in jd.NEGATIVE_WRONG_DOMAIN]
    for idx, row in enumerate(rows[:10], start=1):
        retrieval = float(row.get("retrieval_ranking_fit") or 0)
        career = float(row.get("career_evidence_fit") or 0)
        production = float(row.get("production_system_fit") or 0)
        if retrieval < 0.45 and career < 0.80:
            warnings.append(f"rank {idx}: retrieval_ranking_fit below 0.45")
        if production < 0.35 and career < 0.85:
            warnings.append(f"rank {idx}: production_system_fit below 0.35")
    for idx, row in enumerate(rows[:50], start=1):
        title = str(row.get("current_title") or "").lower()
        career = float(row.get("career_evidence_fit") or 0)
        if any(term.lower() in title for term in wrong_terms) and career < 0.75:
            errors.append(f"rank {idx}: wrong-domain title in top50 without strong evidence")
    for idx, row in enumerate(rows[:100], start=1):
        cap = float(row.get("score_cap") or 1)
        if cap <= 0.35:
            errors.append(f"rank {idx}: score_cap <= 0.35")
    return errors, warnings


def check_metadata(path):
    errors = []
    warnings = []
    path = Path(path)
    if not path.exists():
        return [f"metadata missing: {path}"], warnings
    data = _read_metadata(path)
    primary = data.get("primary_contact") or {}
    compute = data.get("compute") or {}
    declarations = data.get("declarations") or {}

    required_values = {
        "team_name": data.get("team_name"),
        "primary_contact.name": primary.get("name"),
        "primary_contact.email": primary.get("email"),
        "primary_contact.phone": primary.get("phone"),
        "github_repo": data.get("github_repo"),
        "sandbox_link": data.get("sandbox_link"),
        "compute.cpu_cores": compute.get("cpu_cores"),
        "compute.ram_gb": compute.get("ram_gb"),
        "compute.python_version": compute.get("python_version"),
        "compute.os": compute.get("os"),
    }
    for key, value in required_values.items():
        if _is_placeholder(value):
            errors.append(f"metadata placeholder: {key}")

    bool_requirements = {
        "ranking_cpu_only": declarations.get("ranking_cpu_only"),
        "no_network_calls_during_ranking": declarations.get("no_network_calls_during_ranking"),
        "no_hosted_llm_calls_during_ranking": declarations.get("no_hosted_llm_calls_during_ranking"),
    }
    for key, value in bool_requirements.items():
        if not _parse_bool(value):
            errors.append(f"metadata declaration must be true: {key}")

    if not _parse_bool(data.get("submission_ready")):
        warnings.append("submission_ready is false; set true only after metadata and sandbox link are final")
    return errors, warnings


def run_checks(submission, debug, metadata):
    sections = {
        "SUBMISSION": check_submission(submission),
        "DEBUG": check_debug(debug),
        "METADATA": check_metadata(metadata),
    }
    return sections


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", required=True)
    parser.add_argument("--debug", required=True)
    parser.add_argument("--metadata", required=True)
    args = parser.parse_args(argv)

    sections = run_checks(args.submission, args.debug, args.metadata)
    has_errors = False
    for name, (errors, warnings) in sections.items():
        status = "PASS" if not errors else "FAIL"
        print(f"[{status}] {name}")
        for error in errors:
            print(f"  ERROR: {error}")
        for warning in warnings:
            print(f"  WARN: {warning}")
        has_errors = has_errors or bool(errors)
    if has_errors:
        sys.exit(1)
    print("Final sanity check passed.")


if __name__ == "__main__":
    main()
