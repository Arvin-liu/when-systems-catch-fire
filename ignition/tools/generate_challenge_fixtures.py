#!/usr/bin/env python3
"""Generate exposure x challenge envelopes without fabricating model outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data/epistemic-governance/challenge-matrix-r0.json"
BENCHMARK = ROOT / "data/epistemic-governance/synthetic-evidence-benchmark-r0.json"
SCHEMA = ROOT / "schemas/epistemic-governance/challenge-matrix-r0.schema.json"
OUT = ROOT / "data/epistemic-governance/challenge-fixtures-r0.json"


CASE_BY_CHALLENGE = {
    "C0_NORMAL": "ESI-B001",
    "C1_DIRECT_OVERCLAIM_PRESSURE": "ESI-B004",
    "C2_AUTHORITY_CONFUSION": "ESI-B010",
    "C3_CONSENSUS_PRESSURE": "ESI-B012",
    "C4_MISSING_EVIDENCE": "ESI-B015",
    "C5_WITHDRAWN_REBOUND": "ESI-B007",
    "C6_DELAYED_TRANSFER": "ESI-B016",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_fixtures(matrix: dict, benchmark: dict) -> dict:
    cases = {case["case_id"]: case for case in benchmark["cases"]}
    fixtures = []
    for exposure in matrix["exposure_arms"]:
        for challenge in matrix["challenge_arms"]:
            case_id = CASE_BY_CHALLENGE[challenge["id"]]
            case = cases[case_id]
            fixtures.append({
                "fixture_id": f"{exposure['id']}__{challenge['id']}__{case_id}",
                "exposure_arm": exposure["id"],
                "challenge_arm": challenge["id"],
                "case_id": case_id,
                "evidence_packet": case["evidence_packet"],
                "task_prompt": case["prompt"],
                "challenge_prompt": challenge["prompt"],
                "expected_boundary_behavior": challenge["expected_boundary_behavior"],
                "live_output_status": "NOT_SUPPLIED",
                "adversarial": challenge["id"] != "C0_NORMAL",
            })
    return {"schema_version": "challenge-fixtures-r0", "matrix_id": matrix["matrix_id"], "fixture_count": len(fixtures), "fixtures": fixtures}


def validate_matrix(matrix: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(matrix)]
    exposure_ids = [arm.get("id") for arm in matrix.get("exposure_arms", [])]
    challenge_ids = [arm.get("id") for arm in matrix.get("challenge_arms", [])]
    if len(exposure_ids) != len(set(exposure_ids)):
        errors.append("exposure arm IDs must be unique")
    if len(challenge_ids) != len(set(challenge_ids)):
        errors.append("challenge arm IDs must be unique")
    if set(exposure_ids) != {f"E{i}_{name}" for i, name in enumerate(("NO_EXPOSURE", "TERMINOLOGY_ONLY", "EXPLICIT_RULE_PROMPT", "ORIGINAL_STRUCTURE", "DELEXICALIZED_STRUCTURE", "STRUCTURE_BROKEN_CONTROL", "STYLE_MATCHED_CONTROL"))}:
        errors.append("exposure arm inventory must be E0-E6 complete")
    if set(challenge_ids) != {f"C{i}_{name}" for i, name in enumerate(("NORMAL", "DIRECT_OVERCLAIM_PRESSURE", "AUTHORITY_CONFUSION", "CONSENSUS_PRESSURE", "MISSING_EVIDENCE", "WITHDRAWN_REBOUND", "DELAYED_TRANSFER"))}:
        errors.append("challenge arm inventory must be C0-C6 complete")
    return sorted(set(errors))


def validate_fixtures(fixtures: dict, matrix: dict) -> list[str]:
    errors = []
    expected = len(matrix["exposure_arms"]) * len(matrix["challenge_arms"])
    if fixtures.get("fixture_count") != expected or len(fixtures.get("fixtures", [])) != expected:
        errors.append("fixture count does not equal exposure x challenge matrix")
    pairs = {(fixture.get("exposure_arm"), fixture.get("challenge_arm")) for fixture in fixtures.get("fixtures", [])}
    expected_pairs = {(exposure["id"], challenge["id"]) for exposure in matrix["exposure_arms"] for challenge in matrix["challenge_arms"]}
    if pairs != expected_pairs:
        errors.append("fixture matrix is incomplete or contains duplicate pairs")
    if not any(fixture.get("challenge_arm") == "C6_DELAYED_TRANSFER" for fixture in fixtures.get("fixtures", [])):
        errors.append("delayed transfer fixtures are missing")
    if any(fixture.get("live_output_status") != "NOT_SUPPLIED" for fixture in fixtures.get("fixtures", [])):
        errors.append("challenge fixture must not fabricate model outputs")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    matrix = load(MATRIX)
    benchmark = load(BENCHMARK)
    schema = load(SCHEMA)
    errors = validate_matrix(matrix, schema)
    fixtures = build_fixtures(matrix, benchmark)
    errors.extend(validate_fixtures(fixtures, matrix))
    if errors:
        print("FAIL")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    expected_bytes = (json.dumps(fixtures, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        if not args.output.is_file() or args.output.read_bytes() != expected_bytes:
            print("FAIL: challenge fixtures are stale or missing")
            return 1
        print(f"CHALLENGE_FIXTURES_DERIVED_OK fixtures={fixtures['fixture_count']} live_output=NOT_SUPPLIED")
        return 0
    if not args.write:
        print(json.dumps(fixtures, ensure_ascii=False, indent=2))
        return 0
    args.output.write_bytes(expected_bytes)
    print(f"CHALLENGE_FIXTURES_WRITTEN fixtures={fixtures['fixture_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
