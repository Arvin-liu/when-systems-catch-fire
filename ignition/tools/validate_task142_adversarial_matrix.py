#!/usr/bin/env python3
"""Run and validate Task142's offline adversarial rejection matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator

try:
    from agent_federation.task142_adversarial import run_matrix
except ImportError:
    from ignition.agent_federation.task142_adversarial import run_matrix


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT = ROOT / "data/operations/iterations/142/step18-adversarial-matrix.json"
SCHEMA = ROOT / "schemas/operations/task142-adversarial-matrix-r1.schema.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any]) -> list[str]:
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load(SCHEMA)).iter_errors(document)]
    fresh = run_matrix()
    if document.get("status") != "PASS" or fresh["status"] != "PASS":
        errors.append("adversarial matrix did not pass")
    if document.get("cases") != fresh["cases"]:
        errors.append("stored adversarial cases differ from the executable matrix")
    if document.get("case_count") != 15 or document.get("negative_case_count") != 15:
        errors.append("Task142 requires exactly 15 negative adversarial cases")
    for field, value in document.get("safety", {}).items():
        if value is not False:
            errors.append(f"offline adversarial matrix safety field is not false: {field}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fresh = run_matrix()
    if args.write:
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(fresh, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    document = load(ARTIFACT) if args.check else fresh
    errors = validate(document)
    if errors:
        print("TASK142_ADVERSARIAL_MATRIX_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK142_ADVERSARIAL_MATRIX_OK cases=15 rejected=15 live_process_started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
