#!/usr/bin/env python3
"""Validate the explicit schema migration graph and downgrade classifications."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_runtime.migration import FORBIDDEN, LOSSY_REQUIRES_APPROVAL, MIGRATION_SCHEMA, MigrationRegistry


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/schema-migrations-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-schema-migration-r1.schema.json"


def validate(data: dict, schema: dict) -> list[str]:
    from jsonschema import Draft202012Validator
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if data.get("schema_version") != MIGRATION_SCHEMA:
        errors.append("schema migration registry version mismatch")
    try:
        registry = MigrationRegistry.from_dict(data)
        if not any(rule.classification == LOSSY_REQUIRES_APPROVAL for rule in registry.rules):
            errors.append("compatibility matrix lacks a lossy approval-gated downgrade")
        if not any(rule.classification == FORBIDDEN for rule in registry.rules):
            errors.append("compatibility matrix lacks a forbidden downgrade")
        if not registry.path("state-epoch-1", "state-epoch-3"):
            errors.append("three-generation upgrade path is missing")
    except Exception as exc:
        errors.append(str(exc))
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
    print("DURABILITY_MIGRATION_REGISTRY_OK epochs=3 upgrade_path=PASS downgrade_gates=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
