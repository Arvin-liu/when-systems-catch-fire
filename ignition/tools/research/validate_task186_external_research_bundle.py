#!/usr/bin/env python3
"""Validate Task186's pinned source records and research bundle structure."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "ignition/reports/external-research/IGNITION-20260918-186"
STEP_FILES = {
    "00": ["external-source-policy.md", "source-freeze.jsonl", "research-questions.md"],
    "01": ["metarsi-source-freeze.json", "metarsi-mechanism-map.jsonl", "metarsi-primary-source-report.md"],
    "02": ["metarsi-paper-repo-crosscheck.jsonl", "metarsi-paper-repo-crosscheck.md"],
    "03": ["reflection-family-crosswalk.jsonl", "reflection-family-report.md"],
    "04": ["skill-inheritance-crosswalk.jsonl", "skill-inheritance-report.md"],
    "05": ["dspy-harness-optimization-crosswalk.jsonl", "dspy-harness-report.md"],
    "06": ["persistent-memory-mechanism-map.jsonl", "persistent-memory-report.md"],
    "07": ["independent-evaluation-external-map.jsonl", "independent-evaluation-report.md"],
    "08": ["external-mechanism-vocabulary.json", "external-system-mechanism-matrix.jsonl"],
    "09": ["pointfire-external-crosswalk.jsonl", "pointfire-external-crosswalk.md"],
    "10": ["inheritance-distinction-framework.json", "inheritance-distinction-report.md"],
    "11": ["anti-accumulation-mechanisms.jsonl", "anti-accumulation-report.md"],
    "12": ["minimal-experiment-candidates.jsonl", "minimal-experiment-candidates.md"],
    "13": ["external-cognitive-architecture-research-report.md"],
}
EVIDENCE_CLASSES = {"PAPER_CLAIM", "CODE_OBSERVED", "DOC_CLAIM", "SECONDARY_PARAPHRASE", "OUR_INFERENCE"}
IMPLEMENTATION_STATES = {"IMPLEMENTED", "PARTIALLY_IMPLEMENTED", "PAPER_ONLY", "REPO_ONLY", "AMBIGUOUS", "NOT_FOUND"}
POINTFIRE_STATES = {"ALREADY_PRESENT", "PARTIAL_GAP", "REAL_GAP", "NOT_APPLICABLE", "CONFLICTS_WITH_GOVERNANCE", "RESEARCH_ONLY", "UNRESOLVED"}
INHERITANCE_STATES = {"supported by evidence", "partial", "not shown", "not applicable"}
REQUIRED_EXPERIMENT_FIELDS = {
    "research question", "external mechanism inspiration", "Pointfire existing mechanism", "exact gap",
    "smallest reversible test", "holdout/evaluator design", "stop condition", "failure criterion",
    "what result would NOT prove", "expected engineering cost class",
}
DECLARATIONS = {
    "NO_EXTERNAL_SYSTEM_WAS_INTEGRATED",
    "NO_MODEL_RSI_AUTHORIZED",
    "NO_CANONICAL_PROMOTION_PERFORMED",
    "TASK182_R1_ONGOING_OUTPUT_NOT_USED_AS_AUTHORITY",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
        rows.append(value)
    return rows


def check_sources() -> int:
    path = BUNDLE / "source-freeze.jsonl"
    rows = read_jsonl(path)
    errors: list[str] = []
    ids: set[str] = set()
    for row in rows:
        sid = row.get("id")
        if not isinstance(sid, str) or not sid:
            errors.append("source row is missing id")
            continue
        if sid in ids:
            errors.append(f"duplicate source id: {sid}")
        ids.add(sid)
        for field in ("system", "artifact_type", "title", "pin_kind", "pin", "immutable_locator", "license", "accessed_at", "source_quality", "inspected_scope", "negative_results", "unresolved_questions"):
            if field not in row:
                errors.append(f"{sid}: missing {field}")
        kind, pin, locator = row.get("pin_kind"), row.get("pin"), row.get("immutable_locator", "")
        if kind in {"GIT_COMMIT", "POINTFIRE_COMMIT", "HUGGINGFACE_SNAPSHOT"} and (not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{40}", pin)):
            errors.append(f"{sid}: invalid immutable SHA pin")
        if kind == "ARXIV_VERSION" and not (isinstance(pin, str) and re.fullmatch(r"\d{4}\.\d{5}v\d+", pin) and pin in locator):
            errors.append(f"{sid}: arXiv pin must include exact version in locator")
        if kind == "GIT_COMMIT" and isinstance(pin, str) and pin not in locator:
            errors.append(f"{sid}: Git commit pin is not present in locator")
        if kind == "POINTFIRE_COMMIT" and isinstance(pin, str) and pin not in locator:
            errors.append(f"{sid}: Pointfire base pin is not present in locator")
        if kind == "UNVERSIONED_PAGE" and "unversioned" not in row.get("source_quality", "").lower():
            errors.append(f"{sid}: unversioned page must be labeled as such")
        if row.get("accessed_at") != "2026-09-18":
            errors.append(f"{sid}: unexpected source-freeze access date")
        if not isinstance(row.get("negative_results"), list) or not isinstance(row.get("unresolved_questions"), list):
            errors.append(f"{sid}: negative_results and unresolved_questions must be arrays")
    if not rows:
        errors.append("source-freeze.jsonl contains no records")
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    if errors:
        return 1
    print(f"SOURCE_INTEGRITY_OK sources={len(rows)} unique_ids={len(ids)}")
    return 0


def check_bundle() -> int:
    errors: list[str] = []
    if check_sources():
        return 1
    source_ids = {row["id"] for row in read_jsonl(BUNDLE / "source-freeze.jsonl")}
    for step, names in STEP_FILES.items():
        for name in names:
            path = BUNDLE / name
            if not path.is_file():
                errors.append(f"step {step}: missing {name}")
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    jsonl_names = [name for names in STEP_FILES.values() for name in names if name.endswith(".jsonl")]
    json_names = [name for names in STEP_FILES.values() for name in names if name.endswith(".json")]
    rows_by_name: dict[str, list[dict[str, Any]]] = {}
    for name in jsonl_names:
        rows = read_jsonl(BUNDLE / name)
        rows_by_name[name] = rows
        for index, row in enumerate(rows, 1):
            refs = row.get("source_ids", [])
            if isinstance(refs, str):
                refs = [refs]
            if not isinstance(refs, list) or any(ref not in source_ids for ref in refs):
                errors.append(f"{name}:{index}: source_ids contains an unknown source")
            evidence = row.get("evidence_class")
            if evidence is not None and evidence not in EVIDENCE_CLASSES:
                errors.append(f"{name}:{index}: unknown evidence_class {evidence}")
    for name in json_names:
        json.loads((BUNDLE / name).read_text(encoding="utf-8"))
    crosscheck = rows_by_name["metarsi-paper-repo-crosscheck.jsonl"]
    for index, row in enumerate(crosscheck, 1):
        if row.get("implementation_status") not in IMPLEMENTATION_STATES:
            errors.append(f"metarsi-paper-repo-crosscheck.jsonl:{index}: invalid implementation_status")
    pointfire = rows_by_name["pointfire-external-crosswalk.jsonl"]
    for index, row in enumerate(pointfire, 1):
        if row.get("pointfire_status") not in POINTFIRE_STATES:
            errors.append(f"pointfire-external-crosswalk.jsonl:{index}: invalid pointfire_status")
    framework = json.loads((BUNDLE / "inheritance-distinction-framework.json").read_text(encoding="utf-8"))
    for system in framework.get("systems", []):
        for dimension, rating in system.get("ratings", {}).items():
            if rating not in INHERITANCE_STATES:
                errors.append(f"inheritance framework: {system.get('system')} {dimension}: invalid rating")
    candidates = rows_by_name["minimal-experiment-candidates.jsonl"]
    if not 3 <= len(candidates) <= 6:
        errors.append(f"expected 3-6 minimal experiment candidates; found {len(candidates)}")
    for index, candidate in enumerate(candidates, 1):
        missing = REQUIRED_EXPERIMENT_FIELDS - set(candidate)
        if missing:
            errors.append(f"candidate {index}: missing fields {sorted(missing)}")
        if candidate.get("status") not in {"RESEARCH_ONLY_NOT_IMPLEMENTED", "NOT_IMPLEMENTED"}:
            errors.append(f"candidate {index}: status must explicitly say not implemented")
    final_report = (BUNDLE / "external-cognitive-architecture-research-report.md").read_text(encoding="utf-8")
    for declaration in DECLARATIONS:
        if declaration not in final_report:
            errors.append(f"final report missing fixed declaration {declaration}")
    if "EXTERNAL_COGNITIVE_ARCHITECTURE_RESEARCH_COMPLETE" not in final_report:
        errors.append("final report missing exact final state")
    if re.search(r"turn\d+(?:view|search|fetch)?\d+", "\n".join(p.read_text(encoding="utf-8") for p in BUNDLE.glob("*.md"))):
        errors.append("local report contains transient web-tool citation IDs")
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    print(f"RESEARCH_BUNDLE_OK steps={len(STEP_FILES)} source_ids={len(source_ids)} candidates={len(candidates)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-integrity", action="store_true", help="validate stable source identifiers and pins")
    group.add_argument("--check", action="store_true", help="validate the completed 00-13 research bundle")
    args = parser.parse_args()
    return check_sources() if args.source_integrity else check_bundle()


if __name__ == "__main__":
    raise SystemExit(main())
