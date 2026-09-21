#!/usr/bin/env python3
"""Validate Task198 Step04 packet order, byte pins, and condition isolation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "packets"
COMMON = {
    "ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0/packets/common/output-schema-ref.json": "279285bd8da1bfcc799d86425380fd6ef920b7368c6b909736f0ca431e4cb8de",
    "ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0/packets/common/response-contract.json": "d59fe0748aad1abf12424ead1c036847425855df0f62ab108d36e2774e393cff",
    "ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0/packets/common/read-manifest-contract.json": "b8d92913c8ed5f76b9257ad9acc1a4478ded26620bc996ca80de6f7cbbb9c587",
    "ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0/packets/common/freeze-contract.txt": "eef98801f4a00c9fc78976831bb9c71b67dd074054ebcafc312de6a88f34d5c3",
}
ORDER = {
    "A": ["REPL-CASE-03", "REPL-CASE-01", "REPL-CASE-02"],
    "B": ["REPL-CASE-01", "REPL-CASE-02", "REPL-CASE-03"],
}
SEEDS = {
    "A": "IGNITION-20260921-198:A-order:v1",
    "B": "IGNITION-20260921-198:B-order:v1",
}
PACKET_SPECS = {
    "facts-a": ("FACTS_ONLY", "A", "facts", "method-family", "method-traces", "trace-excerpts"),
    "facts-b": ("FACTS_ONLY", "B", "facts", "method-family", "method-traces", "trace-excerpts"),
    "method-a": ("METHOD_TRACE", "A", "method", "trace-excerpts"),
    "method-b": ("METHOD_TRACE", "B", "method", "trace-excerpts"),
    "broken-a": ("BROKEN_METHOD_TRACE_CONTROL", "A", "broken", "method-family", "method-traces"),
    "broken-b": ("BROKEN_METHOD_TRACE_CONTROL", "B", "broken", "method-family", "method-traces"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_path(path: str) -> Path:
    return ROOT.parents[3] / path


def assert_packet(packet_name: str, spec: tuple) -> None:
    condition, replicate, material, *excluded = spec
    directory = PACKETS / packet_name
    manifest_path = directory / "packet-manifest.json"
    digest_path = directory / "packet-manifest.sha256"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["packet_id"] == "IGNITION-20260921-198-" + packet_name.upper()
    assert manifest["condition"] == condition
    assert manifest["replicate"] == replicate
    assert manifest["local_only"] is True
    assert manifest["case_order"] == ORDER[replicate]
    assert manifest["case_order_seed"] == SEEDS[replicate]
    assert manifest["successor_status"] == "NOT_RUN"
    assert manifest["evaluator_status"] == "NOT_RUN"
    assert manifest["canonical_claim_ids"] == []
    assert manifest["canonical_promotion"] == "NONE"
    assert sha256(manifest_path) == digest_path.read_text(encoding="utf-8").split()[0]

    allowlist = manifest["read_allowlist"]
    paths = [item["path"] for item in allowlist]
    assert len(paths) == len(set(paths))
    assert manifest["task_prompt_path"] in paths
    assert {item["path"]: item["sha256"] for item in allowlist if item["path"] in COMMON} == COMMON
    assert not any("evaluator" in path.lower() or "criteria" in path.lower() for path in paths)
    assert not any("ignition-197" in path for path in paths)
    assert not any("__" in item["sha256"] for item in allowlist)

    for item in allowlist:
        actual = repo_path(item["path"])
        assert actual.is_file(), item["path"]
        assert sha256(actual) == item["sha256"], item["path"]

    role_paths = {role: [item["path"] for item in allowlist if item["role"] == role] for role in {item["role"] for item in allowlist}}
    assert len(role_paths.get("case_facts", [])) == 3
    assert len(role_paths.get("case_provenance", [])) == 3
    assert sorted(path.split("/cases/")[1].split("/")[0] for path in role_paths["case_facts"]) == sorted(ORDER[replicate])
    assert sorted(path.split("/cases/")[1].split("/")[0] for path in role_paths["case_provenance"]) == sorted(ORDER[replicate])

    if material == "facts":
        assert "method_trace" not in role_paths
        assert "partial_lineage_excerpt" not in role_paths
        assert "method_history" not in role_paths
        assert "method_provenance" not in role_paths
    elif material == "method":
        assert len(role_paths.get("method_trace", [])) == 3
        assert len(role_paths.get("method_history", [])) == 1
        assert len(role_paths.get("method_provenance", [])) == 1
        assert "partial_lineage_excerpt" not in role_paths
    else:
        assert len(role_paths.get("partial_lineage_excerpt", [])) == 3
        assert "method_trace" not in role_paths
        assert "method_history" not in role_paths
        assert "method_provenance" not in role_paths

    for prefix in excluded:
        assert not any(f"/ignition-198-replicated-method-use-trial-r0/{prefix}/" in path for path in paths)

    output_contract = manifest["output_contract"]
    assert output_contract["response_path"] == "successor-response.jsonl"
    assert output_contract["read_manifest_path"] == "read-manifest.json"
    assert output_contract["freeze_path"] == "freeze-sha256.txt"
    assert output_contract["response_contract_path"] in paths
    assert output_contract["read_manifest_contract_path"] in paths
    assert output_contract["freeze_contract_path"] in paths


def main() -> int:
    receipt = json.loads((ROOT / "case-order-receipt.json").read_text(encoding="utf-8"))
    assert receipt["orders_differ"] is True
    assert receipt["adaptive_reordering"] is False
    assert receipt["conversation_is_replicate_unit"] is True
    assert receipt["within_conversation_cases_are_independent_samples"] is False
    for replicate in ("A", "B"):
        assert receipt["orders"][replicate]["case_order"] == ORDER[replicate]
        keys = receipt["orders"][replicate]["sort_keys"]
        assert [case for _, case in sorted((keys[case], case) for case in ORDER[replicate])] == ORDER[replicate]
        for case in ORDER[replicate]:
            expected = hashlib.sha256(f"{SEEDS[replicate]}|{case}".encode()).hexdigest()
            assert keys[case] == expected

    for packet_name, spec in PACKET_SPECS.items():
        assert_packet(packet_name, spec)

    assert ORDER["A"] != ORDER["B"]
    print("TASK198_STEP04_PACKET_ISOLATION_AND_ORDER_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
