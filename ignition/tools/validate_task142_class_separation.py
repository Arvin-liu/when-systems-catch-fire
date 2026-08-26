#!/usr/bin/env python3
"""Validate that non-agent local candidates cannot close the live obligation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/operations/task142-class-separation-r1.schema.json"
EXPECTED = {
    "runtime.ollama": "REASONER_RUNTIME",
    "runtime.lm-studio": "REASONER_RUNTIME",
    "runtime.mlx-dspark": "REASONER_RUNTIME",
    "runtime.llama-server-bundled": "REASONER_RUNTIME",
    "tool.github-cli": "TOOL",
    "tool.git": "TOOL",
    "tool.jq": "TOOL",
    "ui.claude-desktop": "UI_SURFACE",
    "ui.qwenworkcn": "UI_SURFACE",
}


def validate(document: dict[str, Any]) -> list[str]:
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker()).iter_errors(document)]
    rows = {row.get("executor_id"): row for row in document.get("candidates", []) if isinstance(row, dict)}
    if set(rows) != set(EXPECTED):
        errors.append("non-agent candidate set is not the fresh nine-candidate set")
    for executor_id, family in EXPECTED.items():
        row = rows.get(executor_id)
        if row is None:
            continue
        if row.get("family") != family:
            errors.append(f"{executor_id} class is not {family}")
        expected_blocker = {"REASONER_RUNTIME": "REASONER_RUNTIME_HAS_NO_AGENT_TOOL_LOOP", "TOOL": "TOOL_ONLY_NOT_EXTERNAL_AGENT", "UI_SURFACE": "UI_OR_NONAUTOMATABLE_NO_STABLE_MACHINE_BOUNDARY"}[family]
        if row.get("blocker") != expected_blocker:
            errors.append(f"{executor_id} blocker is not the class blocker")
        if row.get("validated_completion_eligible") is not False:
            errors.append(f"{executor_id} was incorrectly eligible for validated completion")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    errors = validate(json.loads(args.path.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"TASK142_CLASS_SEPARATION_OK candidates={len(EXPECTED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
