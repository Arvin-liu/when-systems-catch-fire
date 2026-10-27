#!/usr/bin/env python3
"""Fail-closed checks for the Current Volatile Fact Registry R1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - repository bootstrap fallback
    Draft202012Validator = None


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
REGISTRY_PATH = ROOT / "data/operations/current-volatile-fact-registry-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/current-volatile-fact-registry-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(registry: dict[str, Any] | None = None) -> list[str]:
    registry = registry if registry is not None else load_json(REGISTRY_PATH)
    errors: list[str] = []
    if Draft202012Validator is not None:
        errors.extend(error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(registry))
    if "current volatile values" not in registry.get("registry_role", "").lower():
        errors.append("registry role must say that current volatile values are not stored")
    facts = registry.get("facts", [])
    fact_ids = [row.get("fact_id") for row in facts]
    if len(fact_ids) != len(set(fact_ids)):
        errors.append("fact ids must be unique")
    surfaces = registry.get("surfaces", [])
    surface_ids = [row.get("surface_id") for row in surfaces]
    if len(surface_ids) != len(set(surface_ids)):
        errors.append("surface ids must be unique")
    declared_paths = {row.get("path") for row in surfaces}
    for fact in facts:
        source = fact.get("canonical_source", {})
        source_path = source.get("path")
        if not source_path:
            errors.append(f"{fact.get('fact_id')}: canonical source path missing")
        elif not (REPO_ROOT / source_path).is_file():
            errors.append(f"{fact.get('fact_id')}: canonical source missing: {source_path}")
        required = set(fact.get("required_current_surfaces", []))
        missing = sorted(required - set(surface_ids))
        if missing:
            errors.append(f"{fact.get('fact_id')}: required surfaces not registered: {', '.join(missing)}")
        if fact.get("null_behavior") == "UNKNOWN":
            errors.append(f"{fact.get('fact_id')}: UNKNOWN null behavior is not allowed for volatile truth")
    for surface in surfaces:
        path = surface.get("path")
        if path and not (REPO_ROOT / path).is_file():
            errors.append(f"surface missing: {path}")
    if len(declared_paths) != len(surfaces):
        errors.append("surface paths must be unique")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("CURRENT_VOLATILE_FACT_REGISTRY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"CURRENT_VOLATILE_FACT_REGISTRY_OK facts={len(load_json(REGISTRY_PATH)['facts'])} surfaces={len(load_json(REGISTRY_PATH)['surfaces'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
