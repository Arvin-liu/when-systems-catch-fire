#!/usr/bin/env python3
"""Validate the source-bound epistemic transition grammar registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
DEFAULT_REGISTRY = ROOT / "data/epistemic-governance/transition-grammar-r0.json"
DEFAULT_SCHEMA = ROOT / "schemas/epistemic-governance/transition-grammar-r0.schema.json"


def resolve_source(reference: str) -> Path:
    return REPO_ROOT / reference


def validate(registry: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(registry)]
    rules = registry.get("rules", [])
    ids = [rule.get("stable_id") for rule in rules]
    if len(ids) != len(set(ids)):
        errors.append("transition rule stable IDs must be unique")
    required_domains = {"knowledge", "engineering", "publication", "agent", "owner", "cross-cutting"}
    if not required_domains <= {rule.get("domain") for rule in rules}:
        errors.append("transition grammar does not cover all required domains")
    for rule in rules:
        for reference in rule.get("source_refs", []):
            path = resolve_source(reference)
            if reference.startswith("/") or ".." in Path(reference).parts:
                errors.append(f"source reference escapes repository: {reference}")
            elif not path.is_file():
                errors.append(f"missing canonical source reference: {reference}")
        if rule.get("hard_or_soft") == "SOFT_RESEARCH_PROJECTION" and rule.get("status") == "CURRENT":
            errors.append(f"current transition rule must remain canonical hard rule: {rule.get('stable_id')}")
        if not rule.get("forbidden_inference") or not rule.get("unknown_retention_rule"):
            errors.append(f"rule lacks a negative boundary: {rule.get('stable_id')}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path, nargs="?", default=DEFAULT_REGISTRY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = validate(registry, schema)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    source_count = sum(len(rule["source_refs"]) for rule in registry["rules"])
    print(f"TRANSITION_GRAMMAR_OK rules={len(registry['rules'])} source_refs={source_count} provenance=COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
