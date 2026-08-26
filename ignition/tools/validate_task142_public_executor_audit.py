#!/usr/bin/env python3
"""Validate one Task142 public executor audit without invoking an executor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/operations/task142-public-executor-audit-r1.schema.json"
EXPECTED_EXECUTORS = {"06": "external.gemini", "07": "external.hermes", "08": "external.openclaw", "09": "external.codex"}


class PublicExecutorAuditError(ValueError):
    """Raised when a public executor audit is incomplete or overclaims."""


def validate(document: dict[str, Any]) -> list[str]:
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker()).iter_errors(document)]
    if errors:
        return errors
    if document["executor_id"] != EXPECTED_EXECUTORS[document["step"]]:
        errors.append("step/executor binding is incorrect")
    if document["auth"]["public_status"] == "PASS" and document["auth"]["public_status_exit"] != 0:
        errors.append("public auth PASS must have exit code 0")
    if document["admission"]["technical_status"] == "ADMITTED" and document["admission"]["blockers"]:
        errors.append("technically admitted audit cannot retain technical blockers")
    if document["admission"]["live_eligibility"] == "ELIGIBLE_FOR_LIVE_READONLY" and document["admission"]["policy_blockers"]:
        errors.append("live-eligible audit cannot retain policy blockers")
    if document["adapter"]["status"] == "NOT_ATTESTED" and document["adapter"].get("adapter_ref") is not None:
        errors.append("unattested adapter cannot carry an adapter reference")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    document = json.loads(args.path.read_text(encoding="utf-8"))
    errors = validate(document)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"TASK142_PUBLIC_EXECUTOR_AUDIT_OK step={document['step']} executor={document['executor_id']} technical={document['admission']['technical_status']} live={document['admission']['live_eligibility']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
