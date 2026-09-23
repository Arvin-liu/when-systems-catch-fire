#!/usr/bin/env python3
"""Validate the evaluator-sealed map, package hashes, and runtime receipt contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
SEALED_DIR = TASK_DIR / "evaluator/sealed-r0"
PACKET_SET = TASK_DIR / "provenance/packet-set-r0.json"
MAP_PATH = SEALED_DIR / "condition-map-r0.json"
PACKAGE_PATH = SEALED_DIR / "package-manifest-r0.json"
RUNTIME_SCHEMA = TASK_DIR / "evaluator/runtime-attestation/receipt-r0.schema.json"
RUNTIME_VALIDATOR = TASK_DIR / "tools/validate_runtime_attestation_r0.py"
EXPECTED_CONDITION_LABELS = {"FACTS", "SKILL", "METHOD", "BROKEN_METHOD"}
EXPECTED_PACKAGE_FILES = (
    "evaluator/criteria-r0.md",
    "evaluator/criteria-r0.json",
    "evaluator/runtime-attestation/receipt-r0.schema.json",
    "evaluator/runtime-attestation/interpretation-r0.md",
    "tools/validate_runtime_attestation_r0.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP06: {message}")


def check_sidecar(path: Path, rel: str) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    expected = f"{sha256(path)}  {rel}\n"
    require(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == expected, f"sidecar mismatch: {rel}")


def main() -> int:
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    require(mapping.get("artifact_type") == "EVALUATION_EVIDENCE", "condition map is not typed evidence")
    require(mapping.get("schema_version") == "task207-evaluator-condition-map-r0", "wrong condition map version")
    require(mapping.get("scope") == "EVALUATOR_ONLY_AFTER_TWO_SCORE_SHEETS_ARE_LOCKED", "wrong condition map scope")
    require(mapping.get("condition_count") == 4 and mapping.get("replicates_per_condition") == 2 and mapping.get("packet_count") == 8, "wrong sealed mapping cardinality")
    seen = set()
    actual_map = {label: {} for label in EXPECTED_CONDITION_LABELS}
    profile_by_condition = {label: {} for label in EXPECTED_CONDITION_LABELS}
    packet_set = json.loads(PACKET_SET.read_text(encoding="utf-8"))
    packet_set_rows = {row["packet_id"]: row for row in packet_set["packets"]}
    blocks = {row["replicate_block"]: set(row["packet_ids"]) for row in packet_set["replicate_blocks"]}
    for row in mapping.get("mappings", []):
        label = row.get("condition_label")
        replicate = row.get("replicate")
        packet_id = row.get("opaque_packet_id")
        require(label in EXPECTED_CONDITION_LABELS and replicate in {"A", "B"}, "unexpected condition/replicate mapping")
        require(packet_id in blocks[replicate], f"packet assigned to the wrong replicate block: {label}/{replicate}")
        require(packet_id not in seen, f"packet mapped more than once: {packet_id}")
        seen.add(packet_id)
        packet_manifest_path = TASK_DIR / "packets" / packet_id / "packet-manifest.json"
        require(sha256(packet_manifest_path) == row.get("packet_manifest_sha256"), f"mapped packet hash mismatch: {packet_id}")
        packet_manifest = json.loads(packet_manifest_path.read_text(encoding="utf-8"))
        require(packet_manifest.get("case_order") == row.get("case_order"), f"mapped case order mismatch: {packet_id}")
        packet_profile = [item["sha256"] for item in packet_manifest["reference_inputs"]]
        require(row.get("reference_input_sha256s") == packet_profile, f"mapped input hashes mismatch: {packet_id}")
        profile_by_condition[label][replicate] = tuple(packet_profile)
        actual_map[label][replicate] = packet_id
    require(seen == set(packet_set_rows), "sealed map does not cover all eight packets")
    require(all(set(row) == {"A", "B"} for row in actual_map.values()), "each condition must have A/B assignments")
    require(all(profile["A"] == profile["B"] for profile in profile_by_condition.values()), "A/B packets in a condition carry different input forms")
    all_profiles = [profile["A"] for profile in profile_by_condition.values()]
    require(len(set(all_profiles)) == 4, "conditions do not map to four distinct input forms")
    for label, rows in actual_map.items():
        require(rows["A"] in blocks["A"] and rows["B"] in blocks["B"], f"condition replicate order mismatch: {label}")
    require(mapping.get("condition_mapping_release") == "AFTER_BOTH_INDEPENDENT_EVALUATOR_SCORE_SHEETS_ARE_LOCKED", "release gate changed")
    require(mapping.get("status", {}).get("successor") == "NOT_RUN" and mapping.get("status", {}).get("evaluator") == "NOT_RUN", "Successor/Evaluator already ran")
    require(mapping.get("status", {}).get("canonical_claim_ids") == [] and mapping.get("status", {}).get("canonical_promotion") == "NONE", "canonical promotion present")

    package_rel = PACKAGE_PATH.relative_to(REPO_ROOT).as_posix()
    map_rel = MAP_PATH.relative_to(REPO_ROOT).as_posix()
    check_sidecar(MAP_PATH, map_rel)
    check_sidecar(PACKAGE_PATH, package_rel)
    require(package.get("artifact_type") == "EVALUATION_EVIDENCE", "wrong package artifact type")
    require(package.get("step") == "Step06" and package.get("base_commit") == "8e70ba196739cf1a79600e02ace36f90ad2c130c", "wrong package step/base")
    require(package.get("input_packet_set_sha256") == sha256(PACKET_SET), "packet set hash mismatch")
    require(package.get("condition_map") == {"path": map_rel, "sha256": sha256(MAP_PATH), "sha256_sidecar": f"{map_rel}.sha256"}, "package map pin mismatch")
    protection = package.get("protection_boundary", {})
    require(protection.get("successor_visible") is False, "sealed package marked successor-visible")
    require(protection.get("release_gate") == "AFTER_BOTH_INDEPENDENT_EVALUATOR_SCORE_SHEETS_ARE_LOCKED", "package release gate changed")
    require(protection.get("cryptographic_encryption_or_repository_acl") is False, "package protection overclaimed")
    require(package.get("runtime_receipts_included") == 0, "real runtime receipt must not exist in preparation")
    require(package.get("status", {}).get("cross_model_execution") == "NOT_AUTHORIZED", "cross-model execution authorized")
    require(package.get("status", {}).get("r1") == "NOT_AUTHORIZED", "R1 authorized")
    require(package.get("status", {}).get("successor") == "NOT_RUN" and package.get("status", {}).get("evaluator") == "NOT_RUN", "Successor/Evaluator already ran")
    require(package.get("status", {}).get("canonical_claim_ids") == [] and package.get("status", {}).get("canonical_promotion") == "NONE", "canonical promotion present")
    expected_file_rows = []
    for rel in EXPECTED_PACKAGE_FILES:
        path = TASK_DIR / rel
        expected_file_rows.append({"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": sha256(path)})
    require(package.get("evaluator_and_runtime_contract_files") == expected_file_rows, "package contents or hashes differ from evaluator/runtime allowlist")

    for packet_manifest_path in (TASK_DIR / "packets").glob("*/packet-manifest.json"):
        data = json.loads(packet_manifest_path.read_text(encoding="utf-8"))
        encoded = json.dumps(data, ensure_ascii=False)
        require("condition_label" not in encoded and '"condition"' not in encoded, "condition label leaked into successor packet")
        require("evaluator/sealed-r0" not in encoded and "condition-map-r0" not in encoded, "successor packet references sealed evaluator files")

    schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    command = [sys.executable, str(RUNTIME_VALIDATOR), "--check-contract"]
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    require(result.returncode == 0 and "TASK207_RUNTIME_ATTESTATION_CONTRACT_VALID" in result.stdout, "runtime receipt contract validator failed")
    require(not list((TASK_DIR / "evaluator/runtime-attestation").glob("*.receipt.json")), "a real runtime receipt was collected")
    print("TASK207_STEP06_PACKAGE_VALID: condition map evaluator-separated; runtime receipt contract valid; no receipt or agent run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
