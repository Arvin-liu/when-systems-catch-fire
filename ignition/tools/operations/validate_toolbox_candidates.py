#!/usr/bin/env python3
"""Validate optional toolbox candidate cards without changing Current operations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
REPO_ROOT = ROOT.parent
NETWORK_HOST_RE = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
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
    known_ids = current_ids | set(candidate_ids)
    for card in catalog["candidates"]:
        comparison_evidence = card.get("comparison_evidence", {
            "status": "COMPARISON_UNKNOWN",
            "scope": "No same-task comparative assessment is declared in this legacy candidate card.",
            "compared_tool_ids": [],
            "evidence_refs": [],
            "findings": ["Replacement value and remaining unique use cases are unknown; preserve uncertainty."],
        })
        replacement_candidates = card.get("replacement_candidates", [])
        unique_remaining_use_cases = card.get("unique_remaining_use_cases", [])
        compared_implementation_refs = comparison_evidence.get("compared_implementation_refs", [])
        retirement = card.get("deprecation_or_retirement_status", {
            "status": "COMPARISON_UNKNOWN",
            "basis": "No comparative evidence is declared in this legacy candidate card.",
        })
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
        if not set(compared_implementation_refs) <= source_ref_paths:
            errors.append(f"{card['tool_id']}: every compared implementation path must have a source reference")
        for implementation_ref in compared_implementation_refs:
            path = REPO_ROOT / implementation_ref
            if not path.is_file() or path.is_symlink():
                errors.append(f"{card['tool_id']}: compared implementation is missing or is a symlink: {implementation_ref}")
        comparison_refs = set(comparison_evidence["evidence_refs"])
        if not comparison_refs <= source_ref_paths:
            errors.append(f"{card['tool_id']}: every comparison-evidence path must have a hashed source reference")
        for evidence_ref in comparison_refs:
            path = REPO_ROOT / evidence_ref.rstrip("/")
            if not path.exists() or path.is_symlink():
                errors.append(f"{card['tool_id']}: comparison evidence is missing or is a symlink: {evidence_ref}")
        unknown_replacements = set(replacement_candidates) - known_ids
        if unknown_replacements:
            errors.append(f"{card['tool_id']}: replacement candidates are not registered identities: {', '.join(sorted(unknown_replacements))}")
        unknown_comparators = set(comparison_evidence["compared_tool_ids"]) - known_ids
        if unknown_comparators:
            errors.append(f"{card['tool_id']}: compared tool IDs are not registered identities: {', '.join(sorted(unknown_comparators))}")
        if card["tool_id"] in replacement_candidates:
            errors.append(f"{card['tool_id']}: a candidate cannot replace itself")
        comparison_status = comparison_evidence["status"]
        if comparison_status == "COMPARISON_UNKNOWN" and retirement["status"] in {"DEPRECATED", "REMOVED"}:
            errors.append(f"{card['tool_id']}: an unknown comparison cannot support deprecation or removal")
        if comparison_status == "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED":
            if not comparison_evidence["compared_tool_ids"] or not unique_remaining_use_cases:
                errors.append(f"{card['tool_id']}: specialized disposition needs comparator IDs and declared remaining use cases")
            if replacement_candidates:
                errors.append(f"{card['tool_id']}: specialized-no-replacement status conflicts with replacement candidates")
        if comparison_status == "REPLACEMENT_SUPPORTED" and not replacement_candidates:
            errors.append(f"{card['tool_id']}: supported replacement status requires at least one replacement candidate")
        if comparison_status == "RETIREMENT_SUPPORTED" and retirement["status"] not in {"DEPRECATED", "ROUTER_EXCLUDED", "REMOVED"}:
            errors.append(f"{card['tool_id']}: supported retirement evidence must be reflected in the retirement status")
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
            if permissions["write_paths"] or permissions["secrets"] or permissions["billing"] or permissions["external_actions"]:
                errors.append(f"{card['tool_id']}: READ_ONLY_RUN candidate declares a write, secret, billing, or external-action effect")
        network_hosts = card["permissions"].get("network_hosts", [])
        if any(not isinstance(host, str) or len(host) > 253 or not NETWORK_HOST_RE.fullmatch(host) or not any(char.isalpha() for char in host) for host in network_hosts):
            errors.append(f"{card['tool_id']}: network hosts must be exact lowercase DNS names without schemes or wildcards")
        if card["permissions"]["network"] and not network_hosts:
            errors.append(f"{card['tool_id']}: network permission requires at least one exact network host")
        if not card["permissions"]["network"] and network_hosts:
            errors.append(f"{card['tool_id']}: network hosts are declared while network permission is false")
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
