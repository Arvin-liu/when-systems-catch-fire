#!/usr/bin/env python3
"""Validate the static three-domain release state model."""

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
MODEL_PATH = ROOT / "data/operations/release-state-model-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/release-state-model-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    model = document if document is not None else load_json(MODEL_PATH)
    schema_errors = sorted(
        Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(model),
        key=lambda error: list(error.path),
    )
    errors = [f"{error.json_path}: {error.message}" for error in schema_errors]
    if errors:
        return errors

    domains = model["state_domains"]
    expected_authorities = {
        "content_owned": "FORMAL_COMMIT_CONTENT",
        "ref_observed_publication": "REMOTE_GIT_REF_OBSERVATION",
        "publication_witness": "CONTROL_REPOSITORY_RECEIPT",
    }
    for domain, authority in expected_authorities.items():
        if domains[domain]["authority_class"] != authority:
            errors.append(f"{domain} authority must be {authority}")
    if domains["content_owned"]["runtime_observation_required"]:
        errors.append("content-owned lifecycle must not require runtime observation")
    if not domains["ref_observed_publication"]["runtime_observation_required"]:
        errors.append("ref-observed publication must require runtime observation")
    if not domains["publication_witness"]["runtime_observation_required"]:
        errors.append("publication witness must require runtime observation")

    states = {domain: set(spec["states"]) for domain, spec in domains.items()}
    for transition in model["transition_rules"]:
        if transition["from_state"] not in states[transition["from_domain"]]:
            errors.append(f"unknown transition source state: {transition['transition_id']}")
        if transition["to_state"] not in states[transition["to_domain"]]:
            errors.append(f"unknown transition target state: {transition['transition_id']}")
        if transition["to_domain"] != "content_owned" and transition["creates_formal_commit"]:
            errors.append(f"runtime publication transition creates a formal commit: {transition['transition_id']}")

    if any("PUBLISHED" in state for state in domains["content_owned"]["states"]):
        errors.append("content-owned states must not include PUBLISHED")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate the checked-in model")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("RELEASE_STATE_MODEL_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"RELEASE_STATE_MODEL_OK path={relative(MODEL_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
