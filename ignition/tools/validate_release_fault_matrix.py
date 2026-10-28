#!/usr/bin/env python3
"""Validate coverage and bounded classifications for the release fault matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
FIXTURE_PATH = ROOT / "data/operations/iterations/131/fixtures/release-fault-matrix-r1.json"

REQUIRED_CASES = {
    "concurrent-remote-main-advance",
    "stale-fetch-before-ls-remote",
    "wrong-origin-url",
    "missing-origin",
    "candidate-not-ancestor-of-main-target",
    "remote-ref-changes-between-observations",
    "witness-replay-for-old-sha",
    "forged-witness-fields",
    "dirty-fresh-clone",
    "stale-current-compiler-output",
    "non-terminal-current-task",
    "current-surface-split-brain",
    "historical-not-published-token",
}
ALLOWED_OUTCOMES = {"STALE_OBSERVATION", "REMOTE_LS_REMOTE_AUTHORITATIVE", "BLOCKED_WITH_EVIDENCE", "RELEASE_CLOSURE_BLOCKED", "FAIL", "HISTORICAL_ALLOWED"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    matrix = document if document is not None else load_json(FIXTURE_PATH)
    errors: list[str] = []
    rows = matrix.get("matrix", [])
    ids = [row.get("case_id") for row in rows]
    if set(ids) != REQUIRED_CASES:
        errors.append("fault matrix must cover every required adversarial case exactly")
    if len(ids) != len(set(ids)):
        errors.append("fault matrix case ids must be unique")
    for row in rows:
        if row.get("expected_outcome") not in ALLOWED_OUTCOMES:
            errors.append(f"invalid outcome for {row.get('case_id')}")
        if not row.get("stage"):
            errors.append(f"missing stage for {row.get('case_id')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("RELEASE_FAULT_MATRIX_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"RELEASE_FAULT_MATRIX_OK cases={len(REQUIRED_CASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
