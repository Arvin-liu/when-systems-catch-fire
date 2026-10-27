#!/usr/bin/env python3
"""Fail-closed validator for the OS durability state taxonomy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/state-taxonomy-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-state-taxonomy-r1.schema.json"
EXPECTED = {
    "CANONICAL_EVENT_SOURCED", "DERIVED_REBUILDABLE", "ADVISORY_SOFT_CONTEXT",
    "EXTERNAL_POINTER_ONLY", "HISTORICAL_SEALED", "EPHEMERAL_PROCESS_LOCAL",
}
FORBIDDEN_AUTHORITY_WORDS = {"permission", "truth", "owner", "safety", "epistemic", "authorize", "authority"}


def validate(data: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    classes = data.get("classes", [])
    ids = [item.get("class_id") for item in classes if isinstance(item, dict)]
    if set(ids) != EXPECTED or len(ids) != len(set(ids)):
        errors.append("taxonomy must contain exactly one entry for each required class")
    if any(item.get("can_be_authority") is not False for item in classes if isinstance(item, dict)):
        errors.append("every durability class must be non-authoritative")
    authority = data.get("authority_model", {})
    if "CANONICAL_EVENT_SOURCED" not in {item.get("class_id") for item in classes if isinstance(item, dict)}:
        errors.append("canonical event class is missing")
    for invariant in data.get("hard_invariants", []):
        if not isinstance(invariant, str) or not invariant.strip():
            errors.append("hard invariants must be non-empty strings")
    if not any("Event Ledger" in item for item in data.get("hard_invariants", [])):
        errors.append("Event Ledger authority invariant is missing")
    if not any("ADVISORY_ONLY" in item and "ESI" in item for item in data.get("hard_invariants", [])):
        errors.append("soft-governance non-authority invariant is missing")
    canonical = set(authority.get("canonical_sources", []))
    if not any("Event Ledger" in item for item in canonical):
        errors.append("canonical source list must name the Event Ledger")
    for item in classes:
        examples = item.get("examples", []) if isinstance(item, dict) else []
        if item.get("class_id") == "EXTERNAL_POINTER_ONLY" and any("secret" in str(value).casefold() or "token" in str(value).casefold() for value in examples):
            errors.append("external pointer examples must remain references, never secret/token contents")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    errors = validate(json.loads(args.data.read_text(encoding="utf-8")), json.loads(args.schema.read_text(encoding="utf-8")))
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("DURABILITY_TAXONOMY_OK classes=6 authority=event-ledger-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
