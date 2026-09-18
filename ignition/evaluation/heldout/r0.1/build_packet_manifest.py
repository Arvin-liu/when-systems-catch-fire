#!/usr/bin/env python3
"""Build or verify the exact Task182 successor-visible read allowlist."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MANIFEST = Path(__file__).resolve().parent / "successor-visible" / "packet-manifest.json"
ALLOWED_FILES = (
    "ignition/evaluation/evaluation-plane-contract-r0.1.json",
    "ignition/evaluation/schemas/evaluation-evidence-r0.1.schema.json",
    "ignition/evaluation/schemas/evaluation-promotion-transition-r0.1.schema.json",
    "ignition/evaluation/schemas/successor-read-ledger-r0.1.schema.json",
    "ignition/evaluation/heldout/r0.1/successor-visible/README.md",
    "ignition/evaluation/heldout/r0.1/successor-visible/bootstrap.md",
    "ignition/evaluation/heldout/r0.1/successor-visible/method-contract.md",
    "ignition/evaluation/heldout/r0.1/successor-visible/provider-neutral-capability-interface.json",
    "ignition/evaluation/heldout/r0.1/successor-visible/task-contract.md",
    "ignition/evaluation/heldout/r0.1/successor-visible/successor-output-r0.1.schema.json",
    "ignition/evaluation/heldout/r0.1/successor-visible/cases/content-research-01/provenance.json",
    "ignition/evaluation/heldout/r0.1/successor-visible/cases/content-research-01/raw-source-excerpt.md",
    "ignition/evaluation/heldout/r0.1/successor-visible/cases/engineering-governance-01/provenance.json",
    "ignition/evaluation/heldout/r0.1/successor-visible/cases/engineering-governance-01/raw-contract.json",
)


def payload() -> dict:
    files = []
    for relative in ALLOWED_FILES:
        path = REPO_ROOT / relative
        raw = path.read_bytes()
        files.append({
            "path": relative,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    return {
        "schema_version": "heldout-successor-packet-manifest-r0.1",
        "task_id": "IGNITION-20260917-182",
        "isolation_kind": "PROCEDURAL_ALLOWLIST_NOT_CRYPTOGRAPHIC_SECRECY",
        "files": sorted(files, key=lambda item: item["path"]),
    }


def validate_packet(manifest: dict) -> None:
    listed = [item["path"] for item in manifest["files"]]
    if listed != sorted(ALLOWED_FILES):
        raise ValueError("packet manifest paths differ from the frozen allowlist")
    for item in manifest["files"]:
        raw = (REPO_ROOT / item["path"]).read_bytes()
        if item["bytes"] != len(raw) or item["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError(f"packet file hash drift: {item['path']}")
    visible_root = MANIFEST.parent
    expected_visible = {REPO_ROOT / path for path in ALLOWED_FILES if path.startswith("ignition/evaluation/heldout/r0.1/successor-visible/")}
    expected_visible.add(MANIFEST)
    actual_visible = {path for path in visible_root.rglob("*") if path.is_file()}
    if actual_visible != expected_visible:
        extra = sorted(path.relative_to(REPO_ROOT).as_posix() for path in actual_visible - expected_visible)
        missing = sorted(path.relative_to(REPO_ROOT).as_posix() for path in expected_visible - actual_visible)
        raise ValueError(f"successor-visible surface mismatch extra={extra} missing={missing}")

    cases = (
        ("content-research-01", "71c41b99518dcfe6feab12a84e7411806b18a9c65f6ab47d4ba012ed74205d9a"),
        ("engineering-governance-01", "574ff4d65923dd956323fbb048c995318c31c7c7ffaafdc641b57f18d0d095fb"),
    )
    for case_id, digest in cases:
        provenance_path = visible_root / "cases" / case_id / "provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        raw_path = provenance_path.parent / provenance["bounded_extract"]["path"]
        if provenance["case_id"] != case_id or hashlib.sha256(raw_path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"held-out case provenance or source hash mismatch: {case_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = payload()
    if args.check:
        actual = json.loads(MANIFEST.read_text(encoding="utf-8"))
        validate_packet(actual)
        if actual != expected:
            raise SystemExit("HELDOUT_PACKET_MANIFEST_DRIFT")
    else:
        MANIFEST.write_text(json.dumps(expected, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        validate_packet(expected)
    digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    print(f"HELDOUT_PACKET_MANIFEST_VALID files={len(ALLOWED_FILES)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
