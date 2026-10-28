#!/usr/bin/env python3
"""Validate Task142's explicit no-invocation adjudication records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/operations/task142-live-attempt-adjudication-r1.schema.json"


def validate(document: dict[str, Any]) -> list[str]:
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker()).iter_errors(document)]
    if document.get("step") == "13" and document.get("reason") != "NO_LIVE_SELECTABLE_EXECUTOR":
        errors.append("Attempt A must be skipped because no live-selectable executor exists")
    if document.get("step") == "14" and document.get("reason") != "ATTEMPT_A_NOT_STARTED_NO_SAFE_FAMILY":
        errors.append("Attempt B must be skipped because Attempt A could not be authorized")
    if document.get("process_started") or document.get("inference_started") or document.get("validated_completion"):
        errors.append("a skipped adjudication cannot claim process, inference or completion")
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
    print(f"TASK142_LIVE_ATTEMPT_ADJUDICATION_OK step={json.loads(args.path.read_text(encoding='utf-8'))['step']} decision=NO_LIVE_INVOCATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
