#!/usr/bin/env python3
"""Fail-closed validator for the Task172 Step05/Step06 full routing overlays."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.foundation.knowledge_corpus_admission import admission_for_path
from tools.research.build_task172_full_routing import (
    ALLOWED_ROLES,
    ALLOWED_STATES,
    ALLOWED_USES,
    TAXONOMY,
    TAGGER_VERSION,
    build_rows,
    expected_count,
    paths_for,
    read_json,
    read_jsonl,
    sha256,
)
from tools.research.validate_task172_gate_c import validate as validate_gate_c
from tools.research.validate_task172_gate_r import validate as validate_gate_r
from tools.research.validate_task172_gate_t import validate as validate_gate_t


CAPS = {"unesco_field_codes": 2, "unesco_discipline_codes": 3, "asset_role": 3, "collision_use": 4, "topic": 5}
NEGATIVE_USE = {"COUNTEREXAMPLE", "EVIDENCE_CHECK", "HISTORICAL_CONTEXT"}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _is_ancestor(repo_root: Path, source_head: str) -> bool:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", source_head, "HEAD"], cwd=repo_root, check=False)
    return result.returncode == 0


def _authority_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "canonical_id",
        "title",
        "canonical_title",
        "primary_identity",
        "claim_class",
        "assertion_type",
        "mathematical_maturity",
        "external_evidence_maturity",
        "final_disposition",
        "claimed_status",
        "replication_status",
        "reviewer_state",
        "claim_ceiling",
        "record_sha256",
    )
    return {key: row[key] for key in keys if key in row}


def validate(repo_root: Path, asset_kind: str, step: str) -> None:
    _assert((step, asset_kind) in {("05", "FUNCTION_ASSET"), ("06", "NONFUNCTION_CLAIM")}, "invalid step/asset-kind pairing")
    validate_gate_t(repo_root)
    validate_gate_r(repo_root)
    validate_gate_c(repo_root)

    paths = paths_for(asset_kind, step)
    for key, relative in paths.items():
        _assert((repo_root / relative).is_file(), f"missing {key}: {relative}")
    overlay = repo_root / paths["overlay"]
    freeze = read_json(repo_root / paths["source_freeze"])
    operation = read_json(repo_root / paths["operation"])
    receipt = read_json(repo_root / paths["receipt"])
    report = repo_root / paths["report"]
    rows = read_jsonl(overlay)
    regenerated, authority_path, input_hashes = build_rows(repo_root, asset_kind)

    source_head = str(freeze.get("formal_pre_freeze", {}).get("head", ""))
    _assert(len(source_head) == 40 and _is_ancestor(repo_root, source_head), "source exact head is not a reachable frozen ancestor")
    _assert(freeze.get("schema") == "task172-full-routing-source-freeze-v1", "source-freeze schema drift")
    _assert(freeze.get("freeze_event") == "SCAN_INPUT_FREEZE_REUSE", "scan-sensitive source was not frozen")
    _assert(freeze.get("formal_pre_freeze", {}).get("branch") == "work/IGNITION-20260912-172-knowledge-routing-universal-corpus", "branch binding drift")
    _assert(freeze.get("formal_pre_freeze", {}).get("pull_request") == 218, "PR binding drift")
    _assert(freeze.get("formal_pre_freeze", {}).get("state") == "OPEN + DRAFT + unmerged", "lifecycle ceiling drift")
    _assert(freeze.get("taxonomy_authority", {}).get("fields") == TAXONOMY["fields"], "taxonomy field count drift")
    _assert(freeze.get("taxonomy_authority", {}).get("primary_disciplines") == TAXONOMY["primary_disciplines"], "taxonomy discipline count drift")
    _assert(freeze.get("taxonomy_authority", {}).get("primary_subdisciplines") == TAXONOMY["primary_subdisciplines"], "taxonomy subdiscipline count drift")
    _assert(freeze.get("authority", {}).get("path") == str(authority_path.relative_to(repo_root)), "authority path drift")
    _assert(freeze.get("authority", {}).get("sha256") == sha256(authority_path), "authority source hash drift")
    _assert(freeze.get("derived_outputs", {}).get("overlay_sha256") == sha256(overlay), "freeze overlay hash drift")
    _assert(admission_for_path(str(paths["overlay"])).classification == "GENERATED_PROJECTION_EXCLUDED", "routing overlay crossed Knowledge admission")

    _assert(rows == regenerated, "second deterministic generation differs")
    _assert(len(rows) == expected_count(asset_kind), f"row count drift: {len(rows)}")
    ids = [row.get("canonical_id") for row in rows]
    _assert(len(ids) == len(set(ids)), "duplicate canonical IDs")
    authority_rows = {row["canonical_id"]: row for row in read_jsonl(authority_path)}
    _assert(set(ids) == set(authority_rows), "missing or orphan canonical IDs")

    gate_t = read_json(repo_root / "data/research/task172-gate-t-unesco-1988/primary-1988-parse.json")
    field_codes = {row["code"] for row in gate_t["hierarchy"]["fields"]}
    discipline_codes = {row["code"] for row in gate_t["discipline_records"]}
    for row in rows:
        canonical_id = row["canonical_id"]
        authority = authority_rows[canonical_id]
        _assert(row.get("asset_kind") == asset_kind, f"asset kind drift: {canonical_id}")
        _assert(row.get("source_record_sha") == authority.get("record_sha256"), f"authority fingerprint mismatch: {canonical_id}")
        _assert(row.get("immutable_snapshot") == _authority_snapshot(authority), f"immutable authority snapshot changed: {canonical_id}")
        domain = row.get("domain", {})
        _assert(domain.get("classification_state") in ALLOWED_STATES, f"unknown classification state: {canonical_id}")
        fields = domain.get("unesco_field_codes", [])
        disciplines = domain.get("unesco_discipline_codes", [])
        _assert(len(fields) <= CAPS["unesco_field_codes"] and len(disciplines) <= CAPS["unesco_discipline_codes"], f"UNESCO cap exceeded: {canonical_id}")
        _assert(set(fields) <= field_codes and set(disciplines) <= discipline_codes, f"non-primary taxonomy code: {canonical_id}")
        _assert(len(row.get("asset_role", [])) <= CAPS["asset_role"] and set(row.get("asset_role", [])) <= ALLOWED_ROLES, f"role vocabulary/cap drift: {canonical_id}")
        _assert(len(row.get("collision_use", [])) <= CAPS["collision_use"] and set(row.get("collision_use", [])) <= ALLOWED_USES, f"use vocabulary/cap drift: {canonical_id}")
        _assert(len(row.get("topic", [])) <= CAPS["topic"], f"topic cap exceeded: {canonical_id}")
        if domain.get("classification_state") == "OUT_OF_UNESCO_SCOPE":
            _assert(not fields and not disciplines, f"out-of-scope row has UNESCO codes: {canonical_id}")
        disposition = str(authority.get("final_disposition", "")).upper()
        negative = any(token in disposition for token in ("REJECT", "QUARANTINE", "WITHDRAWN", "UNSUPPORTED", "RETRACTED", "CONTRADICTED", "HISTORICAL_ONLY"))
        if negative:
            _assert(row.get("asset_role") == ["HISTORICAL_CONTEXT"], f"negative record gained positive role: {canonical_id}")
            _assert(set(row.get("collision_use", [])) <= NEGATIVE_USE, f"negative record gained positive use: {canonical_id}")
        if asset_kind == "NONFUNCTION_CLAIM" and authority.get("claim_class") == "EMPIRICAL_OR_LITERATURE_CLAIM" and not negative:
            _assert(row.get("tag_basis", {}).get("evidence_role") == "REPOSITORY_CLAIM_METADATA_REVIEW", f"literature claim evidence role drift: {canonical_id}")
            _assert(row.get("evidence_projection", {}).get("promotion") == "NONE", f"literature claim promoted: {canonical_id}")
        _assert(row.get("tagger_version") == TAGGER_VERSION, f"tagger version drift: {canonical_id}")
        _assert(row.get("review_state") == "FULL_ROUTING_MANUAL_REVIEW_REQUIRED", f"review state escaped: {canonical_id}")
        _assert(row.get("evidence_projection", {}).get("role") == "ROUTING_ONLY_NO_EVIDENCE_PROMOTION", f"evidence boundary drift: {canonical_id}")

    _assert(receipt.get("schema") == "task172-full-routing-build-receipt-v1", "receipt schema drift")
    _assert(receipt.get("source_exact_head") == source_head, "receipt source head drift")
    _assert(receipt.get("asset_kind") == asset_kind and receipt.get("step") == f"Task172 Step{step}", "receipt identity drift")
    _assert(receipt.get("inputs") == input_hashes, "receipt input hashes drift")
    _assert(receipt.get("counts", {}).get("rows") == len(rows), "receipt row count drift")
    _assert(receipt.get("outputs") == {key: sha256(repo_root / relative) for key, relative in paths.items() if key != "receipt"}, "receipt output hashes drift")
    _assert(operation.get("schema") == "task172-full-routing-operation-v1", "operation schema drift")
    _assert(operation.get("source_exact_head") == source_head and operation.get("asset_kind") == asset_kind, "operation identity drift")
    _assert(operation.get("overlay", {}).get("sha256") == sha256(overlay), "operation overlay hash drift")
    _assert(operation.get("source_freeze_sha256") == sha256(repo_root / paths["source_freeze"]), "operation freeze hash drift")
    _assert(operation.get("report_sha256") == sha256(report), "operation report hash drift")
    _assert(operation.get("network") is False and operation.get("canonical_mutation") is False, "routing acquired side effects")
    _assert(receipt.get("network") is False and receipt.get("canonical_mutation") is False, "receipt side-effect boundary drift")
    print(f"TASK172_FULL_ROUTING_VALIDATION_OK step={step} asset_kind={asset_kind} rows={len(rows)} source_head={source_head}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--asset-kind", choices=["FUNCTION_ASSET", "NONFUNCTION_CLAIM"], required=True)
    parser.add_argument("--step", choices=["05", "06"], required=True)
    args = parser.parse_args()
    try:
        validate(args.repo_root.resolve(), args.asset_kind, args.step)
    except AssertionError as exc:
        raise SystemExit(f"TASK172_FULL_ROUTING_VALIDATION_FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
