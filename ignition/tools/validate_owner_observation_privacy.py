#!/usr/bin/env python3
"""Validate public-safe ESI observation metadata and scan its bounded files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "data/epistemic-governance/owner-observation-esi-001.json"
DEFAULT_SCHEMA = ROOT / "schemas/epistemic-governance/owner-observation-r0.schema.json"
DEFAULT_SCAN_PATHS = (
    ROOT / "data/epistemic-governance/owner-observation-esi-001.json",
    ROOT / "docs/architecture/owner-observation-esi-001.md",
)


def validate(record: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(record)]
    if record.get("status", []).count("OWNER_SUPPLIED") != 1:
        errors.append("observation must contain exactly one OWNER_SUPPLIED status")
    return sorted(set(errors))


def privacy_scan(paths: tuple[Path, ...]) -> list[str]:
    errors: list[str] = []
    forbidden_patterns = (
        re.compile(r"/(?:Users|private|var/folders)/", re.I),
        re.compile(r"screenshot|chat transcript|聊天截图|私人笔记正文|hidden reasoning", re.I),
        re.compile(r"(?:telegram|slack|discord)\s*(?:account|user|id|handle)", re.I),
    )
    for path in paths:
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            # Privacy booleans intentionally name the fields being checked;
            # scan the public narrative and claim fields, not those metadata keys.
            payload.pop("privacy", None)
            text = json.dumps(payload, ensure_ascii=False)
        else:
            text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern.search(text):
                label = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
                errors.append(f"privacy marker found in {label}: {pattern.pattern}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    errors = validate(record, json.loads(args.schema.read_text(encoding="utf-8")))
    errors.extend(privacy_scan(DEFAULT_SCAN_PATHS))
    if errors:
        print("FAIL")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print("OWNER_OBSERVATION_PRIVACY_OK public_safe=true private_content=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
