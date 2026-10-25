#!/usr/bin/env python3
"""Validate optional toolbox candidate cards without changing Current operations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
REPO_ROOT = ROOT.parent
CATALOG = ROOT / "data/operations/toolbox-candidate-cards-r0.json"
SCHEMA = ROOT / "schemas/operations/toolbox-candidate-cards-r0.schema.json"
REGISTRY = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def validate() -> list[str]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(schema).iter_errors(catalog)]
    if errors:
        return errors
    registry_blob = git_blob_sha1(REGISTRY.read_bytes())
    if catalog["source_registry_blob_sha1"] != registry_blob:
        errors.append("candidate cards are not pinned to the checked Current operation registry blob")
    current_ids = {row["operation_id"] for row in registry["operations"]}
    candidate_ids = [row["tool_id"] for row in catalog["candidates"]]
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("candidate tool IDs must be unique")
    if current_ids.intersection(candidate_ids):
        errors.append("candidate tool IDs must not shadow Current operation IDs")
    for card in catalog["candidates"]:
        source = REPO_ROOT / card["source_path"]
        if not source.is_file() or source.is_symlink():
            errors.append(f"{card['tool_id']}: implementation source is missing or is a symlink")
        for ref in card["source_refs"]:
            path = REPO_ROOT / ref["path"].rstrip("/")
            if not path.exists() or path.is_symlink():
                errors.append(f"{card['tool_id']}: source reference is missing or is a symlink: {ref['path']}")
        source_ref_paths = {ref["path"] for ref in card["source_refs"]}
        if not set(card["dependencies"]) <= source_ref_paths:
            errors.append(f"{card['tool_id']}: every declared dependency must have a hashed source reference")
        for dependency in card["dependencies"]:
            path = REPO_ROOT / dependency.rstrip("/")
            if not path.exists() or path.is_symlink():
                errors.append(f"{card['tool_id']}: dependency is missing or is a symlink: {dependency}")
        for check in card["validation"]["focused_checks"]:
            path = REPO_ROOT / check
            if not path.is_file() or path.is_symlink():
                errors.append(f"{card['tool_id']}: focused check is missing or is a symlink: {check}")
        if card["execution_mode"] == "READ_ONLY_RUN":
            permissions = card["permissions"]
            if permissions["write_paths"] or permissions["network"] or permissions["secrets"] or permissions["billing"] or permissions["external_actions"]:
                errors.append(f"{card['tool_id']}: READ_ONLY_RUN candidate declares a write or external effect")
        if card["permissions"]["external_actions"] and not card["explicit_owner_authorization_required"]:
            errors.append(f"{card['tool_id']}: external-action candidate must require explicit Owner authorization")
        if card["availability"] != "EXPERIMENTAL_AVAILABLE" or card["router_selectable_by_default"]:
            errors.append(f"{card['tool_id']}: experimental tools must be available only by explicit selection")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args(argv)
    errors = validate()
    if errors:
        print("TOOLBOX_CANDIDATE_CARDS_INVALID", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
        return 1
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    print(f"TOOLBOX_CANDIDATE_CARDS_OK candidates={len(catalog['candidates'])} current_registry_unchanged=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
