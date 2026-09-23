#!/usr/bin/env python3
"""Validate packet opacity, common bytes, source pins, and paired case order."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
PACKETS_DIR = TASK_DIR / "packets"
SET_PATH = TASK_DIR / "provenance/packet-set-r0.json"
OUTPUT_SCHEMA_PATH = REPO_ROOT / "ignition/evaluation/heldout/r0.1/successor-visible/successor-output-r0.1.schema.json"
SOURCE_PAYLOAD_DIR = TASK_DIR / "payload"
EXPECTED_PROMPT = (TASK_DIR / "common/neutral-task-prompt.md").read_bytes()
EXPECTED_READ = (TASK_DIR / "common/read-manifest.json").read_bytes()
EXPECTED_FREEZE = (TASK_DIR / "common/freeze-contract.json").read_bytes()
EXPECTED_OUTPUT_SCHEMA = OUTPUT_SCHEMA_PATH.read_bytes()
EXPECTED_CASE_ORDERS = {
    "A": ["CASE-02", "CASE-01", "CASE-03"],
    "B": ["CASE-03", "CASE-02", "CASE-01"],
}
EXPECTED_PACKET_IDS = {
    "A": ["PKT-7C4A9D", "PKT-05E8B2", "PKT-D18F63", "PKT-B6092E"],
    "B": ["PKT-A7C145", "PKT-92DE30", "PKT-40BC81", "PKT-E3157A"],
}
FORBIDDEN_LABELS = ("FACTS_ONLY", "SKILL_ONLY", "METHOD_ARTIFACT", "BROKEN_METHOD", "BROKEN_METHOD_TRACE")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP04: {message}")


def check_sidecar(path: Path, display_path: str) -> None:
    digest = sha256(path)
    expected = f"{digest}  {display_path}\n"
    sidecar = path.with_name(path.name + ".sha256")
    require(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == expected, f"sidecar mismatch: {display_path}")


def packet_manifest(packet_id: str) -> tuple[Path, dict]:
    packet_dir = PACKETS_DIR / packet_id
    require(packet_dir.is_dir() and not packet_dir.is_symlink(), f"packet missing or symlinked: {packet_id}")
    path = packet_dir / "packet-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return path, data


def safe_packet_path(packet_id: str, relative: str) -> Path:
    relative_path = Path(relative)
    require(not relative_path.is_absolute() and ".." not in relative_path.parts, f"unsafe packet path: {packet_id}/{relative}")
    packet_root = PACKETS_DIR / packet_id
    candidate = packet_root / relative_path
    cursor = candidate
    while cursor != packet_root:
        require(not cursor.is_symlink(), f"symlink in packet input path: {packet_id}/{relative}")
        cursor = cursor.parent
    packet_dir = packet_root.resolve()
    path = candidate.resolve()
    require(path.is_relative_to(packet_dir), f"packet path escapes packet root: {packet_id}/{relative}")
    require(path.is_file(), f"packet input missing: {packet_id}/{relative}")
    return path


def main() -> int:
    plan = json.loads(SET_PATH.read_text(encoding="utf-8"))
    require(plan.get("artifact_type") == "EVALUATION_EVIDENCE", "wrong artifact type")
    require(plan.get("step") == "Step04" and plan.get("base_commit") == "8e70ba196739cf1a79600e02ace36f90ad2c130c", "wrong step or base")
    require(plan.get("packet_count") == 8 and plan.get("case_count_per_packet") == 3, "wrong packet or case count")
    require(plan.get("condition_mapping") == "WITHHELD_FOR_EVALUATOR_SEALED_PACKAGE", "condition mapping is not withheld")
    require(plan.get("status", {}).get("future_successor") == "NOT_RUN", "Successor already ran")
    require(plan.get("status", {}).get("future_evaluator") == "NOT_RUN", "Evaluator already ran")
    require(plan.get("status", {}).get("canonical_claim_ids") == [], "canonical claim IDs present")
    require(plan.get("status", {}).get("canonical_promotion") == "NONE", "canonical promotion present")

    blocks = plan.get("replicate_blocks", [])
    require([row.get("replicate_block") for row in blocks] == ["A", "B"], "replicate blocks missing")
    block_by_id = {}
    for row in blocks:
        block = row["replicate_block"]
        require(row.get("packet_ids") == EXPECTED_PACKET_IDS[block], f"packet block membership changed: {block}")
        require(row.get("case_order") == EXPECTED_CASE_ORDERS[block], f"case order changed: {block}")
        for packet_id in row["packet_ids"]:
            require(packet_id not in block_by_id, f"packet listed in multiple blocks: {packet_id}")
            block_by_id[packet_id] = block
    require(len(block_by_id) == 8, "not all eight opaque packets assigned to a replicate block")

    packet_rows = plan.get("packets", [])
    require(len(packet_rows) == 8, "packet index does not list exactly eight packets")
    seen_ids = set()
    profile_materials = {}
    profile_by_block = {"A": [], "B": []}
    case_hashes = {f"CASE-{number:02d}": set() for number in range(1, 4)}
    expected_profiles = {
        (),
        (("reference-material/entry.json", sha256(SOURCE_PAYLOAD_DIR / "item-a.json")),),
        (
            ("reference-material/entry.json", sha256(SOURCE_PAYLOAD_DIR / "item-b.json")),
            ("reference-material/context.md", sha256(SOURCE_PAYLOAD_DIR / "item-b-history.md")),
        ),
        (
            ("reference-material/entry.json", sha256(SOURCE_PAYLOAD_DIR / "item-c.json")),
            ("reference-material/context.md", sha256(SOURCE_PAYLOAD_DIR / "item-c-source.md")),
        ),
    }
    prompt_hashes = set()
    for row in packet_rows:
        packet_id = row.get("packet_id", "")
        require(re.fullmatch(r"PKT-[0-9A-F]{6}", packet_id) is not None, f"packet id is not opaque: {packet_id}")
        require(packet_id not in seen_ids and packet_id in block_by_id, f"duplicate or unassigned packet: {packet_id}")
        seen_ids.add(packet_id)
        require(row.get("replicate_block") == block_by_id[packet_id], f"block index mismatch: {packet_id}")
        require(row.get("case_order") == EXPECTED_CASE_ORDERS[block_by_id[packet_id]], f"case order mismatch in plan: {packet_id}")
        manifest_path, manifest = packet_manifest(packet_id)
        rel_manifest = f"packets/{packet_id}/packet-manifest.json"
        check_sidecar(manifest_path, rel_manifest)
        require(sha256(manifest_path) == row.get("packet_manifest_sha256"), f"manifest hash mismatch: {packet_id}")
        require(manifest.get("packet_id") == packet_id, f"packet self-id mismatch: {packet_id}")
        require(manifest.get("schema_version") == "task207-successor-packet-r0", f"packet version mismatch: {packet_id}")
        require(manifest.get("base_commit") == "8e70ba196739cf1a79600e02ace36f90ad2c130c", f"packet base mismatch: {packet_id}")
        require("condition" not in manifest and "experimental_condition" not in manifest, f"condition field exposed: {packet_id}")
        encoded_manifest = json.dumps(manifest, ensure_ascii=False).upper()
        require(not any(label in encoded_manifest for label in FORBIDDEN_LABELS), f"condition label leaked in manifest: {packet_id}")
        require(manifest.get("status", {}).get("future_successor") == "NOT_RUN", f"future Successor marked run: {packet_id}")
        require(manifest.get("status", {}).get("future_evaluator") == "NOT_RUN", f"future Evaluator marked run: {packet_id}")
        require(manifest.get("status", {}).get("canonical_claim_ids") == [], f"canonical IDs in packet: {packet_id}")
        require(manifest.get("status", {}).get("canonical_promotion") == "NONE", f"canonical promotion in packet: {packet_id}")

        for name, expected_bytes, field, shared_key in (
            ("neutral-task-prompt.md", EXPECTED_PROMPT, "prompt", "shared_prompt_sha256"),
            ("read-manifest.json", EXPECTED_READ, "read_manifest", "shared_read_manifest_sha256"),
            ("freeze-contract.json", EXPECTED_FREEZE, "freeze_contract", "shared_freeze_contract_sha256"),
            ("output-schema.json", EXPECTED_OUTPUT_SCHEMA, "output_schema", "shared_output_schema_sha256"),
        ):
            path = PACKETS_DIR / packet_id / name
            require(path.read_bytes() == expected_bytes, f"shared {name} bytes differ: {packet_id}")
            check_sidecar(path, f"packets/{packet_id}/{name}")
            digest = sha256(path)
            prompt_hashes.add(digest) if name == "neutral-task-prompt.md" else None
            require(manifest.get(field, {}).get("path") == name, f"manifest {field} path mismatch: {packet_id}")
            require(manifest.get(field, {}).get("sha256") == digest, f"manifest {field} hash mismatch: {packet_id}")
            require(plan.get(shared_key) == digest, f"shared {name} hash mismatch in packet set")
        require("skill" not in EXPECTED_PROMPT.decode("utf-8").lower(), "prompt names a skill condition")
        require("method" not in EXPECTED_PROMPT.decode("utf-8").lower(), "prompt names a method condition")
        require(not any(label in EXPECTED_PROMPT.decode("utf-8").upper() for label in FORBIDDEN_LABELS), "condition label leaked in prompt")

        case_order = manifest.get("case_order")
        require(case_order == EXPECTED_CASE_ORDERS[block_by_id[packet_id]], f"packet case order mismatch: {packet_id}")
        case_rows = manifest.get("cases", [])
        require([entry.get("case_id") for entry in case_rows] == case_order, f"case entries differ from case order: {packet_id}")
        require(len(case_rows) == 3, f"packet case count is not three: {packet_id}")
        for entry in case_rows:
            case_id = entry["case_id"]
            require(entry.get("facts_path") == f"cases/{entry['case_id']}/facts.md", f"unexpected facts path: {packet_id}/{case_id}")
            require(entry.get("provenance_path") == f"cases/{entry['case_id']}/provenance.json", f"unexpected provenance path: {packet_id}/{case_id}")
            facts_path = safe_packet_path(packet_id, entry["facts_path"])
            provenance_path = safe_packet_path(packet_id, entry["provenance_path"])
            case_hashes[case_id].add(entry.get("facts_sha256"))
            check_sidecar(facts_path, f"packets/{packet_id}/{entry['facts_path']}")
            check_sidecar(provenance_path, f"packets/{packet_id}/{entry['provenance_path']}")
            require(sha256(facts_path) == entry.get("facts_sha256"), f"facts hash mismatch: {packet_id}/{case_id}")
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            require(provenance.get("case_id") == case_id, f"case provenance id mismatch: {packet_id}/{case_id}")
            require(provenance.get("source_sha256") == entry.get("facts_sha256"), f"case source provenance mismatch: {packet_id}/{case_id}")
            require(provenance.get("source_path") == entry.get("facts_path"), f"case source path mismatch: {packet_id}/{case_id}")

        reference_inputs = manifest.get("reference_inputs", [])
        profile = tuple((item["path"], item["sha256"]) for item in reference_inputs)
        require(profile in expected_profiles, f"reference input does not match a prepared source form: {packet_id}")
        profile_materials[packet_id] = profile
        profile_by_block[block_by_id[packet_id]].append(profile)
        for item in reference_inputs:
            input_path = safe_packet_path(packet_id, item["path"])
            check_sidecar(input_path, f"packets/{packet_id}/{item['path']}")
            require(sha256(input_path) == item.get("sha256"), f"reference input hash mismatch: {packet_id}/{item['path']}")

    require(seen_ids == set(block_by_id), "packet index and replicate blocks differ")
    require(all(len(values) == 1 for values in case_hashes.values()), "case source bytes differ between packets")
    require(len(prompt_hashes) == 1, "common prompt is not byte-identical")
    for block, profiles in profile_by_block.items():
        require(len(profiles) == 4 and len(set(profiles)) == 4, f"each {block} block must contain four distinct input forms")
        require(set(profiles) == expected_profiles, f"each {block} block must contain one of each prepared input form")
    require(profile_by_block["A"] == profile_by_block["B"], "replicate blocks have different input-form sequence")
    require(EXPECTED_CASE_ORDERS["A"] != EXPECTED_CASE_ORDERS["B"], "A/B case orders must differ")

    for root in PACKETS_DIR.iterdir():
        require(root.name in seen_ids, f"unexpected directory under packets/: {root.name}")
    check_sidecar(SET_PATH, "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/provenance/packet-set-r0.json")
    print("TASK207_STEP04_PACKETS_VALID: 8 opaque packets; common prompt byte-identical; A/B order consistent; all artifacts hash-bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
