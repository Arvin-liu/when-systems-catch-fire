#!/usr/bin/env python3
"""Build eight opaque, prompt-neutral Task207 future-trial packets."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
PACKETS_DIR = TASK_DIR / "packets"
CASE_MANIFEST = TASK_DIR / "cases/case-manifest.json"
COMMON_DIR = TASK_DIR / "common"
OUTPUT_SCHEMA = REPO_ROOT / "ignition/evaluation/heldout/r0.1/successor-visible/successor-output-r0.1.schema.json"
OUTPUT_SCHEMA_SHA256 = "fdf46bbe7f92dbc5a8340ad95381a0932b5b55f49f3c88f48f33c502a52c0133"

# The four entries in each replicate block receive the same case order. This
# private build plan does not assign or name an experimental condition.
PACKET_BLOCKS = {
    "A": ("PKT-7C4A9D", "PKT-05E8B2", "PKT-D18F63", "PKT-B6092E"),
    "B": ("PKT-A7C145", "PKT-92DE30", "PKT-40BC81", "PKT-E3157A"),
}
CASE_ORDERS = {
    "A": ("CASE-02", "CASE-01", "CASE-03"),
    "B": ("CASE-03", "CASE-02", "CASE-01"),
}

MATERIAL_SOURCE = {
    "skill": ((TASK_DIR / "payload/item-a.json", "reference-material/entry.json"),),
    "trace": (
        (TASK_DIR / "payload/item-b.json", "reference-material/entry.json"),
        (TASK_DIR / "payload/item-b-history.md", "reference-material/context.md"),
    ),
    "fragment": (
        (TASK_DIR / "payload/item-c.json", "reference-material/entry.json"),
        (TASK_DIR / "payload/item-c-source.md", "reference-material/context.md"),
    ),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_json(path: Path, data: dict) -> None:
    write_bytes(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sidecar(path: Path, display_path: str) -> str:
    digest = sha256(path)
    write_bytes(path.with_name(path.name + ".sha256"), f"{digest}  {display_path}\n".encode("utf-8"))
    return digest


def copy_with_sidecar(source: Path, target: Path, display_path: str) -> str:
    write_bytes(target, source.read_bytes())
    return sidecar(target, display_path)


def main() -> int:
    if PACKETS_DIR.exists():
        raise SystemExit(f"refusing to replace existing packet directory: {PACKETS_DIR}")
    if sha256(OUTPUT_SCHEMA) != OUTPUT_SCHEMA_SHA256:
        raise SystemExit("pinned R0.1 output schema changed")

    case_manifest = json.loads(CASE_MANIFEST.read_text(encoding="utf-8"))
    case_rows = {row["case_id"]: row for row in case_manifest["cases"]}
    source_case_ids = ("DISENTANGLE-CASE-01", "DISENTANGLE-CASE-02", "DISENTANGLE-CASE-03")
    alias_by_source = {source_id: f"CASE-{index:02d}" for index, source_id in enumerate(source_case_ids, 1)}
    prompt_bytes = (COMMON_DIR / "neutral-task-prompt.md").read_bytes()
    read_manifest_bytes = (COMMON_DIR / "read-manifest.json").read_bytes()
    freeze_contract_bytes = (COMMON_DIR / "freeze-contract.json").read_bytes()
    output_schema_bytes = OUTPUT_SCHEMA.read_bytes()

    packet_index = []
    for replicate, packet_ids in PACKET_BLOCKS.items():
        for packet_id in packet_ids:
            packet_dir = PACKETS_DIR / packet_id
            packet_dir.mkdir(parents=True)
            for name, data in (
                ("neutral-task-prompt.md", prompt_bytes),
                ("read-manifest.json", read_manifest_bytes),
                ("freeze-contract.json", freeze_contract_bytes),
                ("output-schema.json", output_schema_bytes),
            ):
                write_bytes(packet_dir / name, data)
                sidecar(packet_dir / name, f"packets/{packet_id}/{name}")

            case_entries = []
            for alias in CASE_ORDERS[replicate]:
                source_id = source_case_ids[int(alias[-2:]) - 1]
                row = case_rows[source_id]
                source_facts = REPO_ROOT / row["facts_path"]
                source_provenance = REPO_ROOT / row["provenance_path"]
                facts_path = packet_dir / "cases" / alias / "facts.md"
                facts_text = source_facts.read_text(encoding="utf-8").replace(source_id, alias)
                write_bytes(facts_path, facts_text.encode("utf-8"))
                facts_hash = sidecar(facts_path, f"packets/{packet_id}/cases/{alias}/facts.md")

                provenance = json.loads(source_provenance.read_text(encoding="utf-8"))
                provenance["case_id"] = alias
                provenance["source_ref"] = f"synthetic://ignition-207/packet-case-set-r0/{alias.lower()}"
                provenance["source_path"] = f"cases/{alias}/facts.md"
                provenance["source_sha256"] = facts_hash
                provenance["packet_alias_of"] = source_id
                provenance_path = facts_path.with_name("provenance.json")
                write_json(provenance_path, provenance)
                provenance_hash = sidecar(provenance_path, f"packets/{packet_id}/cases/{alias}/provenance.json")
                case_entries.append(
                    {
                        "case_id": alias,
                        "facts_path": f"cases/{alias}/facts.md",
                        "facts_sha256": facts_hash,
                        "facts_sha256_sidecar": f"cases/{alias}/facts.md.sha256",
                        "provenance_path": f"cases/{alias}/provenance.json",
                        "provenance_sha256": provenance_hash,
                        "provenance_sha256_sidecar": f"cases/{alias}/provenance.json.sha256",
                    }
                )

            material_paths = []
            # The four packet forms are encoded only by the supplied material.
            # Their labels and the packet-to-condition map are withheld.
            material_form = packet_ids.index(packet_id)
            source_map = (None, "skill", "trace", "fragment")
            for source, target_rel in MATERIAL_SOURCE[source_map[material_form]] if source_map[material_form] else ():
                target = packet_dir / target_rel
                digest = copy_with_sidecar(source, target, f"packets/{packet_id}/{target_rel}")
                material_paths.append(
                    {
                        "path": target_rel,
                        "sha256": digest,
                        "sha256_sidecar": f"{target_rel}.sha256",
                    }
                )

            prompt_hash = sidecar(packet_dir / "neutral-task-prompt.md", f"packets/{packet_id}/neutral-task-prompt.md")
            read_hash = sidecar(packet_dir / "read-manifest.json", f"packets/{packet_id}/read-manifest.json")
            freeze_hash = sidecar(packet_dir / "freeze-contract.json", f"packets/{packet_id}/freeze-contract.json")
            schema_hash = sidecar(packet_dir / "output-schema.json", f"packets/{packet_id}/output-schema.json")
            packet_manifest = {
                "artifact_type": "EVALUATION_EVIDENCE",
                "task_id": "IGNITION-20260923-207",
                "schema_version": "task207-successor-packet-r0",
                "packet_id": packet_id,
                "base_commit": "8e70ba196739cf1a79600e02ace36f90ad2c130c",
                "prompt": {"path": "neutral-task-prompt.md", "sha256": prompt_hash},
                "read_manifest": {"path": "read-manifest.json", "sha256": read_hash},
                "freeze_contract": {"path": "freeze-contract.json", "sha256": freeze_hash},
                "output_schema": {"path": "output-schema.json", "sha256": schema_hash},
                "case_order": [row["case_id"] for row in case_entries],
                "cases": case_entries,
                "reference_inputs": material_paths,
                "status": {
                    "future_successor": "NOT_RUN",
                    "future_evaluator": "NOT_RUN",
                    "canonical_claim_ids": [],
                    "canonical_promotion": "NONE",
                },
            }
            write_json(packet_dir / "packet-manifest.json", packet_manifest)
            packet_manifest_hash = sidecar(packet_dir / "packet-manifest.json", f"packets/{packet_id}/packet-manifest.json")
            packet_index.append(
                {
                    "packet_id": packet_id,
                    "replicate_block": replicate,
                    "packet_manifest": f"packets/{packet_id}/packet-manifest.json",
                    "packet_manifest_sha256": packet_manifest_hash,
                    "case_order": [row["case_id"] for row in case_entries],
                }
            )

    step04 = {
        "artifact_type": "EVALUATION_EVIDENCE",
        "task_id": "IGNITION-20260923-207",
        "step": "Step04",
        "schema_version": "task207-packet-set-r0",
        "base_commit": "8e70ba196739cf1a79600e02ace36f90ad2c130c",
        "packet_count": 8,
        "case_count_per_packet": 3,
        "replicate_blocks": [
            {"replicate_block": name, "packet_ids": list(PACKET_BLOCKS[name]), "case_order": list(CASE_ORDERS[name])}
            for name in ("A", "B")
        ],
        "packets": packet_index,
        "shared_prompt_sha256": sha256_bytes(prompt_bytes),
        "shared_read_manifest_sha256": sha256_bytes(read_manifest_bytes),
        "shared_freeze_contract_sha256": sha256_bytes(freeze_contract_bytes),
        "shared_output_schema_sha256": sha256_bytes(output_schema_bytes),
        "condition_mapping": "WITHHELD_FOR_EVALUATOR_SEALED_PACKAGE",
        "status": {
            "future_successor": "NOT_RUN",
            "future_evaluator": "NOT_RUN",
            "canonical_claim_ids": [],
            "canonical_promotion": "NONE",
        },
    }
    order_path = TASK_DIR / "provenance/packet-set-r0.json"
    write_json(order_path, step04)
    sidecar(order_path, "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/provenance/packet-set-r0.json")
    print("TASK207_STEP04_PACKETS_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
