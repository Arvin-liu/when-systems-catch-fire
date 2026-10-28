#!/usr/bin/env python3
"""Validate Task142 independent exact-validator evidence and rerun its offline tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/operations/task142-independent-validator-r1.schema.json"
TEST = ROOT / "tests/test_task142_first_completion_validator.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    document: dict[str, Any] = json.loads(args.path.read_text(encoding="utf-8"))
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    result = subprocess.run([sys.executable, str(TEST)], cwd=ROOT.parent, env={**__import__("os").environ, "PYTHONPATH": str(ROOT)}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    if result.returncode:
        errors.append("offline exact-validator tests failed")
    if errors:
        for error in errors:
            print(f"- {error}")
        print(result.stdout)
        return 1
    print(f"TASK142_INDEPENDENT_VALIDATOR_OK cases={document['case_count']} passed={document['passed_count']} live_process_started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
