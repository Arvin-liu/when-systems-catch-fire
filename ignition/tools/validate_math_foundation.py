#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


FORMAL_TYPES = {
    "FUNCTION",
    "PREDICATE",
    "RELATION",
    "STATE_TRANSITION",
    "CAUSAL_MODEL",
    "PROBABILISTIC_MODEL",
    "METRIC",
    "ORDER",
    "OPTIMIZATION_PROBLEM",
    "OPERATOR",
    "ALGORITHM",
    "FORMAL_PROPOSITION",
    "NATURAL_LANGUAGE_CANDIDATE",
}

FORMAL_STATUS = {"UNFORMALIZED", "WELL_FORMED", "TYPE_ERROR", "SEMANTICALLY_UNDEFINED", "FORMALIZATION_INCOMPLETE", "COUNTEREXAMPLE_FOUND"}
PROOF_STATUS = {"DEFINITION_ONLY", "UNPROVED_PROPOSITION", "PROVED_IN_DECLARED_SYSTEM", "EXTERNAL_THEOREM", "DISPROVED", "NOT_APPLICABLE"}
EVIDENCE_STATUS = {"SOURCE_ONLY", "CASE_SUPPORTED", "MULTI_CASE_SUPPORTED", "EMPIRICALLY_TESTED", "EXTERNALLY_VALIDATED", "PENDING"}
PROVENANCE_STATUS = {"DIRECT_SOURCE_FOUND", "INDIRECT_SOURCE_ONLY", "MULTIPLE_CONFLICTING_SOURCES", "SOURCE_NOT_FOUND", "GENERATED_WITHOUT_TRACEABLE_SOURCE"}


def validate_entry(entry: dict) -> list[str]:
    errors = []
    required = [
        "id", "title", "object_type", "domain", "codomain", "variables", "units",
        "expression", "semantics", "sources", "proof_obligations", "validation_method",
        "workflow_status", "formal_status", "proof_status", "evidence_status",
        "scope_status", "provenance_status",
    ]
    for key in required:
        if key not in entry or entry[key] in ("", [], {}):
            errors.append(f"missing_or_empty:{key}")
    if entry.get("object_type") not in FORMAL_TYPES:
        errors.append("invalid:object_type")
    if entry.get("formal_status") not in FORMAL_STATUS:
        errors.append("invalid:formal_status")
    if entry.get("proof_status") not in PROOF_STATUS:
        errors.append("invalid:proof_status")
    if entry.get("evidence_status") not in EVIDENCE_STATUS:
        errors.append("invalid:evidence_status")
    if entry.get("provenance_status") not in PROVENANCE_STATUS:
        errors.append("invalid:provenance_status")
    variables = entry.get("variables", [])
    declared = {v.get("name") for v in variables if isinstance(v, dict)}
    expr = entry.get("expression", "")
    for symbol in sorted(set(part for part in [s.strip() for s in expr.replace("(", " ").replace(")", " ").replace(",", " ").split()] if part.isidentifier())):
        if symbol.isupper():
            continue
    if "converged" in entry and entry.get("converged") not in ("", None):
        errors.append("forbidden:converged_standalone")
    if any(word in entry.get("semantics", "") for word in ["证明了", "解决了", "唯一真理"]) and entry.get("proof_status") not in {"PROVED_IN_DECLARED_SYSTEM", "EXTERNAL_THEOREM"}:
        errors.append("strong_claim_without_proof_status")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl_path", type=Path)
    args = parser.parse_args()
    seen = set()
    failures = []
    for line_no, line in enumerate(args.jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry["id"] in seen:
            failures.append((line_no, "duplicate_id"))
        seen.add(entry["id"])
        for err in validate_entry(entry):
            failures.append((line_no, err))
    if failures:
        for line_no, err in failures:
            print(f"line {line_no}: {err}")
        return 1
    print(f"validated {len(seen)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
