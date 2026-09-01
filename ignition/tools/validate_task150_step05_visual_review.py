#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step05 visual-review evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step05-visual-review.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step05-visual-review-r1.schema.json"
EVIDENCE_ROOT = ROOT / "data/operations/iterations/150/visual-evidence"
EXPECTED_PREVIOUS_COMMIT = "e6d29c57ea54817bdebc39f0d83e5c362e6caf46"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors
    if document["formal_previous_commit"] != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step05 must bind the published Step04 formal commit")
    files = document["evidence_files"]
    expected_paths = set()
    for item in files:
        path = REPO_ROOT / item["path"]
        expected_paths.add(path)
        if not path.is_file():
            errors.append(f"missing visual evidence file: {item['path']}")
            continue
        if path.parent != EVIDENCE_ROOT:
            errors.append(f"visual evidence escaped its iteration directory: {item['path']}")
        if path.stat().st_size != item["bytes"]:
            errors.append(f"visual evidence byte count drifted: {item['path']}")
        if sha256(path) != item["sha256"]:
            errors.append(f"visual evidence digest drifted: {item['path']}")
    if len(expected_paths) != 12:
        errors.append("visual evidence must contain exactly twelve distinct files")
    if document["automated_review"]["standalone_visual_check"] != "PASS":
        errors.append("standalone automated visual check must remain PASS")
    if document["automated_review"]["standalone_visual_review"] != "pending":
        errors.append("automated standalone visualReview must remain pending")
    if document["automated_review"]["delta_visual_check"] != "FAIL_UPSTREAM_WRAPPER":
        errors.append("Delta automated result must retain the upstream-wrapper blocker")
    if document["owner_visual_acceptance"] != "OWNER_VISUAL_ACCEPTANCE_PENDING":
        errors.append("agent inspection cannot become Owner aesthetic acceptance")
    checks = document["agent_visual_inspection"]["checks"]
    if checks["delta_three_panel_readability"] != "NOT_ACCEPTED_UPSTREAM_WRAPPER_OVERFLOW_AND_THEME_RESOLUTION":
        errors.append("Delta readability cannot be accepted while the wrapper residual remains")
    scope = document["scope_freeze"]
    if scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION":
        errors.append("Agent Reach or authenticated scope changed")
    if scope["installation"] != "NO_INSTALL_OR_AUTO_UPGRADE":
        errors.append("installation boundary changed")
    if scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation changed")
    if scope["current_admission"] != "NOT_ADMITTED":
        errors.append("visual review cannot admit a Current capability")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP05_VISUAL_REVIEW_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP05_VISUAL_REVIEW_OK standalone=PASS "
        "agent=STANDALONE_PASS_WITH_LIMITS_DELTA_BLOCKED "
        "owner=OWNER_VISUAL_ACCEPTANCE_PENDING"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
