#!/usr/bin/env python3
"""Fail-closed validation for failure-case evidence and defect claims.

Directory placement, a narrative prediction, or an LLM answer never establishes
an implementation defect. A reproduced defect requires a versioned repository
target, exact input/output, trace, repeatability, an oracle, a frozen claim
ceiling, a preserved first failure and a regression guard.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


VALID_LABELS = {
    "NARRATIVE_HYPOTHESIS", "EVIDENCE_SUPPORTED_COUNTEREXAMPLE",
    "REPRODUCTION_PENDING", "INVALID_OR_UNDERSPECIFIED_CASE",
    "REPRODUCED_IMPLEMENTATION_DEFECT", "NOT_REPRODUCED",
    "EXECUTABLE_TARGET_ABSENT", "EVIDENCE_INCONCLUSIVE",
}
REQUIRED_DIMENSIONS = {"external_evidence", "executable_target", "formalization", "reproduction"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _err(errors: list[str], field: str, message: str) -> None:
    errors.append(f"{field}: {message}")


def _string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def _commit(value: Any) -> bool:
    return isinstance(value, str) and bool(COMMIT.fullmatch(value))


def _check_digest_object(errors: list[str], value: Any, field: str, require_status: bool = False) -> None:
    if not isinstance(value, dict):
        _err(errors, field, "must be an object")
        return
    if not _sha(value.get("sha256")):
        _err(errors, f"{field}.sha256", "must be a lowercase SHA-256 digest")
    if not (_string(value.get("path")) or "value" in value):
        _err(errors, field, "must contain an exact path or an inline value")
    if require_status and not _string(value.get("status")):
        _err(errors, f"{field}.status", "must identify the observed status")


def validate_case(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record: must be an object"]
    for key in ("schema_version", "case_id", "source_path", "case_label"):
        if not _string(record.get(key)):
            _err(errors, key, "is required")
    if record.get("schema_version") != "1.0.0":
        _err(errors, "schema_version", "must be 1.0.0")
    if not (isinstance(record.get("source_path"), str)
            and record["source_path"].startswith("case_failures/examples/")
            and record["source_path"].endswith(".md")):
        _err(errors, "source_path", "must point to a tracked case_failures/examples Markdown source")
    if record.get("case_label") not in VALID_LABELS:
        _err(errors, "case_label", "is not an allowed evidence-gated label")

    dimensions = record.get("status_dimensions")
    if not isinstance(dimensions, dict):
        _err(errors, "status_dimensions", "must contain all four independent dimensions")
        dimensions = {}
    for key in REQUIRED_DIMENSIONS:
        if not _string(dimensions.get(key)):
            _err(errors, f"status_dimensions.{key}", "is required")

    claims_defect = record.get("case_label") == "REPRODUCED_IMPLEMENTATION_DEFECT"
    if dimensions.get("reproduction") == "REPRODUCED_IMPLEMENTATION_DEFECT" and not claims_defect:
        _err(errors, "case_label", "must be REPRODUCED_IMPLEMENTATION_DEFECT when reproduction dimension claims a defect")
    if claims_defect:
        gate = record.get("evidence_gate")
        if not isinstance(gate, dict):
            _err(errors, "evidence_gate", "is required; narrative text cannot establish a defect")
            return errors

        target = gate.get("target")
        if not isinstance(target, dict):
            _err(errors, "evidence_gate.target", "must identify a repository executable")
        else:
            if target.get("kind") != "repository_executable":
                _err(errors, "evidence_gate.target.kind", "LLM output or an untyped target is not an executable target")
            if not _string(target.get("path")):
                _err(errors, "evidence_gate.target.path", "is required")
            if not _commit(target.get("commit")):
                _err(errors, "evidence_gate.target.commit", "must be a full frozen commit, not HEAD or a label")
            if not _string(target.get("interface")):
                _err(errors, "evidence_gate.target.interface", "is required")
            if target.get("case_binding") != record.get("case_id"):
                _err(errors, "evidence_gate.target.case_binding", "must bind the target to this exact case")

        _check_digest_object(errors, gate.get("exact_input"), "evidence_gate.exact_input")
        _check_digest_object(errors, gate.get("actual_output"), "evidence_gate.actual_output", require_status=True)
        _check_digest_object(errors, gate.get("trace"), "evidence_gate.trace")
        if not _string(gate.get("run_id")):
            _err(errors, "evidence_gate.run_id", "is required")
        if (not isinstance(gate.get("repeat_count"), int)
                or isinstance(gate.get("repeat_count"), bool)
                or gate.get("repeat_count", 0) < 2):
            _err(errors, "evidence_gate.repeat_count", "must be an integer of at least 2")

        oracle = gate.get("oracle")
        if not isinstance(oracle, dict) or not _string(oracle.get("kind")) or not _string(oracle.get("basis")):
            _err(errors, "evidence_gate.oracle", "must provide a non-empty adjudication kind and basis")
        if not _string(gate.get("claim_ceiling")) or not _string(record.get("claim_ceiling")):
            _err(errors, "evidence_gate.claim_ceiling", "the reproduced claim must have an explicit ceiling")
        if gate.get("formalization_frozen") is not True:
            _err(errors, "evidence_gate.formalization_frozen", "must be true before a result is accepted")

        first = gate.get("first_failure")
        if not isinstance(first, dict):
            _err(errors, "evidence_gate.first_failure", "must preserve the first failure record")
        else:
            if first.get("preserved") is not True:
                _err(errors, "evidence_gate.first_failure.preserved", "deleted or replaced first failures are invalid")
            if not _string(first.get("path")):
                _err(errors, "evidence_gate.first_failure.path", "is required")
            if not _sha(first.get("sha256")):
                _err(errors, "evidence_gate.first_failure.sha256", "must be a lowercase SHA-256 digest")
            if not _string(first.get("observed_at")):
                _err(errors, "evidence_gate.first_failure.observed_at", "is required")

        regression = gate.get("regression")
        if not isinstance(regression, dict) or regression.get("status") != "REGRESSION_GUARD_ESTABLISHED":
            _err(errors, "evidence_gate.regression.status", "must establish a regression guard")
        else:
            for key in ("test", "command"):
                if not _string(regression.get(key)):
                    _err(errors, f"evidence_gate.regression.{key}", "is required")

        refs = gate.get("external_evidence_refs")
        if not isinstance(refs, list) or not refs or not all(_string(x) for x in refs):
            _err(errors, "evidence_gate.external_evidence_refs", "must identify at least one evidence or oracle reference")
    return errors


def validate_document(payload: dict[str, Any]) -> list[str]:
    if not isinstance(payload, dict):
        return ["document: must be an object"]
    cases = payload.get("cases")
    if cases is None:
        cases = [payload]
    if not isinstance(cases, list) or not cases:
        return ["cases: must be a non-empty list"]
    errors: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(cases):
        case_errors = validate_case(record)
        prefix = f"cases[{index}]"
        errors.extend(f"{prefix}.{item}" for item in case_errors)
        if isinstance(record, dict):
            case_id = record.get("case_id")
            if case_id in seen:
                errors.append(f"{prefix}.case_id: duplicate case id")
            if _string(case_id):
                seen.add(case_id)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL {args.input}: cannot read JSON: {exc}", file=sys.stderr)
        return 2
    errors = validate_document(payload)
    if errors:
        print(f"FAIL {args.input}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS {args.input}: {len(payload.get('cases', [payload]))} case record(s) evidence-gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
