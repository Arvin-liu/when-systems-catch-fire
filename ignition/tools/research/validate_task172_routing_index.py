#!/usr/bin/env python3
"""Fail-closed validator for Task172 Step07 routing/index integration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.foundation.knowledge_corpus_admission import admission_for_path  # noqa: E402
from tools.research.build_task172_full_routing import expected_count  # noqa: E402
from tools.research.build_task172_routing_index import (  # noqa: E402
    BRANCH,
    FACET_OUTPUTS,
    INDEX_REL,
    MANIFEST_REL,
    NONFUNCTION_OVERLAY_REL,
    OPERATION_REL,
    PILOT_REL,
    QUERIES_REL,
    RECEIPT_REL,
    REPORT_REL,
    ROUTING,
    SOURCE_FREEZE_REL,
    TAGS_REL,
    build_index,
    build_pilot,
    expected_rows,
    read_json,
    read_jsonl,
    render_report,
    render_tags,
    sha256,
)
from tools.research.task172_routing import load_index  # noqa: E402
from tools.research.validate_task172_gate_c import validate as validate_gate_c  # noqa: E402
from tools.research.validate_task172_gate_r import validate as validate_gate_r  # noqa: E402
from tools.research.validate_task172_gate_t import validate as validate_gate_t  # noqa: E402


FUNCTION_OVERLAY_REL = ROUTING.relative_to(ROOT) / "function-routing-overlay.jsonl"
FORBIDDEN_PREFIXES = (".github/README.md", "data/operations/iterations/148/")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _is_ancestor(repo_root: Path, source_head: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", source_head, "HEAD"], cwd=repo_root, check=False).returncode == 0


def _authority_rows(repo_root: Path, relative: Path) -> dict[str, dict[str, Any]]:
    return {row["canonical_id"]: row for row in read_jsonl(repo_root / relative)}


def _validate_facets(index: dict[str, Any]) -> None:
    records = index["records"]
    refs = [f"{row['asset_kind']}:{row['canonical_id']}" for row in records]
    _assert(len(refs) == len(set(refs)), "routing index duplicate canonical references")
    for output_name in FACET_OUTPUTS.values():
        facet = index["facets"].get(output_name)
        _assert(isinstance(facet, dict), f"missing facet map: {output_name}")
        for value, values in facet.items():
            _assert(values == sorted(set(values)), f"facet refs are not sorted and unique: {output_name}/{value}")
            _assert(set(values) <= set(refs), f"facet contains orphan refs: {output_name}/{value}")


def validate(repo_root: Path) -> None:
    for rel in (INDEX_REL, SOURCE_FREEZE_REL, MANIFEST_REL, RECEIPT_REL, QUERIES_REL, PILOT_REL, OPERATION_REL, REPORT_REL, TAGS_REL):
        _assert((repo_root / rel).is_file(), f"missing Step07 artifact: {rel}")

    validate_gate_t(repo_root)
    validate_gate_r(repo_root)
    validate_gate_c(repo_root)

    manifest = read_json(repo_root / MANIFEST_REL)
    source_head = str(manifest.get("source_exact_head", ""))
    _assert(len(source_head) == 40 and _is_ancestor(repo_root, source_head), "Step07 source head is not a reachable frozen ancestor")
    _assert(manifest.get("schema") == "task172-step07-routing-index-manifest-v1", "manifest schema drift")
    _assert(manifest.get("step") == "Task172 Step07", "manifest step drift")

    index = read_json(repo_root / INDEX_REL)
    counts = expected_rows(repo_root)
    _assert(index == build_index(repo_root, source_head), "Step07 index is not deterministic")
    _assert(index.get("source_exact_head") == source_head, "index source head drift")
    _assert(index.get("branch") == BRANCH and index.get("pull_request") == 218, "branch/PR binding drift")
    _assert(index.get("operation_id") == "knowledge.collide_object", "operation binding drift")
    _assert(index.get("run_mode") == "READ_ONLY_RUN", "run mode drift")
    _assert(index.get("stats", {}).get("records") == sum(counts.values()), "index total row count drift")
    _assert(index.get("stats", {}).get("function_records") == expected_count("FUNCTION_ASSET", repo_root), "function index count drift")
    _assert(index.get("stats", {}).get("nonfunction_records") == expected_count("NONFUNCTION_CLAIM", repo_root), "nonfunction index count drift")
    _assert(index.get("side_effects") == {"repository_mutation": False, "external_action": False, "registry_write": False}, "index side-effect boundary drift")
    _validate_facets(index)

    authorities = {
        "FUNCTION_ASSET": _authority_rows(repo_root, Path("data/foundation/function-assets/identity-cards.jsonl")),
        "NONFUNCTION_CLAIM": _authority_rows(repo_root, Path("data/foundation/nonfunction-claims/claim-registry.jsonl")),
    }
    for row in index["records"]:
        authority = authorities[row["asset_kind"]].get(row["canonical_id"])
        _assert(authority is not None, f"index orphan canonical ID: {row['canonical_id']}")
        _assert(row["source_record_sha"] == authority.get("record_sha256"), f"index authority fingerprint mismatch: {row['canonical_id']}")
        _assert(len(row["unesco_field_codes"]) <= 2 and len(row["unesco_discipline_codes"]) <= 3, f"index taxonomy cap exceeded: {row['canonical_id']}")
        _assert(len(row["asset_role"]) <= 3 and len(row["collision_use"]) <= 4 and len(row["topic"]) <= 5, f"index facet cap exceeded: {row['canonical_id']}")

    freeze = read_json(repo_root / SOURCE_FREEZE_REL)
    _assert(freeze.get("schema") == "task172-step07-routing-index-source-freeze-v1", "source-freeze schema drift")
    _assert(freeze.get("freeze_event") == "SCAN_INPUT_FREEZE_REUSE", "scan-sensitive source was not frozen")
    _assert(freeze.get("formal_pre_freeze", {}).get("head") == source_head, "source-freeze head drift")
    _assert(freeze.get("formal_pre_freeze", {}).get("branch") == BRANCH, "source-freeze branch drift")
    _assert(freeze.get("formal_pre_freeze", {}).get("pull_request") == 218, "source-freeze PR drift")
    _assert(freeze.get("formal_pre_freeze", {}).get("state") == "OPEN + DRAFT + unmerged", "lifecycle ceiling drift")
    _assert(freeze.get("inputs", {}).get("function_overlay", {}).get("rows") == counts["FUNCTION_ASSET"], "function source count drift")
    _assert(freeze.get("inputs", {}).get("nonfunction_overlay", {}).get("rows") == counts["NONFUNCTION_CLAIM"], "nonfunction source count drift")
    for rel in (FUNCTION_OVERLAY_REL, NONFUNCTION_OVERLAY_REL, QUERIES_REL):
        key = "function_overlay" if rel == FUNCTION_OVERLAY_REL else "nonfunction_overlay" if rel == NONFUNCTION_OVERLAY_REL else "pilot_queries"
        _assert(freeze.get("inputs", {}).get(key, {}).get("sha256") == sha256(repo_root / rel), f"frozen input hash drift: {rel}")
    _assert(freeze.get("derived_outputs", {}).get("index_sha256") == sha256(repo_root / INDEX_REL), "frozen index hash drift")
    _assert(freeze.get("derived_outputs", {}).get("pilot_sha256") == sha256(repo_root / PILOT_REL), "frozen pilot hash drift")
    _assert(admission_for_path(str(INDEX_REL)).classification == "GENERATED_PROJECTION_EXCLUDED", "routing index crossed Knowledge admission")

    pilot = read_json(repo_root / PILOT_REL)
    _assert(pilot == build_pilot(repo_root), "Step07 pilot is not deterministic")
    for case in pilot["cases"]:
        result = case["result"]
        _assert(result["operation_id"] == "knowledge.collide_object" and result["run_mode"] == "READ_ONLY_RUN", f"pilot operation drift: {case['case_id']}")
        _assert(result["selected_count"] <= result["top_k"] <= 1000, f"pilot bound drift: {case['case_id']}")
        _assert(result["candidate_universe_size"] <= len(index["records"]), f"pilot universe drift: {case['case_id']}")
        _assert(result["invalid_selection_count"] == 0, f"pilot invalid canonical IDs: {case['case_id']}")
        _assert(result["exact_validation_status"] == "ALL_SELECTED_EXACT", f"pilot exact validation drift: {case['case_id']}")
        _assert(result["fallback"]["explicit"] is True, f"pilot fallback transparency drift: {case['case_id']}")
        _assert(result["side_effects"] == {"repository_mutation": False, "external_action": False, "registry_write": False}, f"pilot side-effect drift: {case['case_id']}")
    _assert(pilot["hard_checks"]["invalid_id_count"] == 0, "pilot hard check invalid IDs")

    operation = read_json(repo_root / OPERATION_REL)
    _assert(operation.get("schema") == "task172-step07-routing-index-operation-v1", "operation schema drift")
    _assert(operation.get("operation_id") == "knowledge.collide_object", "operation ID drift")
    _assert(operation.get("operation_status") == "CURRENT_BOUNDED", "operation status drift")
    _assert(operation.get("execution_mode") == "READ_ONLY_RUN", "operation mode drift")
    _assert(operation.get("network") is False and operation.get("repository_mutation") is False and operation.get("registry_write") is False and operation.get("canonical_mutation") is False, "operation side-effect boundary drift")
    _assert(operation.get("index", {}).get("sha256") == sha256(repo_root / INDEX_REL), "operation index hash drift")
    _assert(operation.get("source_freeze_sha256") == sha256(repo_root / SOURCE_FREEZE_REL), "operation source-freeze hash drift")
    _assert(operation.get("report_sha256") == sha256(repo_root / REPORT_REL), "operation report hash drift")

    receipt = read_json(repo_root / RECEIPT_REL)
    _assert(receipt.get("schema") == "task172-step07-routing-index-build-receipt-v1", "receipt schema drift")
    _assert(receipt.get("source_exact_head") == source_head, "receipt head drift")
    _assert(receipt.get("network") is False and receipt.get("repository_mutation") is False and receipt.get("registry_write") is False, "receipt side-effect drift")
    for rel in (INDEX_REL, PILOT_REL, TAGS_REL, REPORT_REL, SOURCE_FREEZE_REL, OPERATION_REL):
        _assert(receipt.get("outputs", {}).get(str(rel)) == sha256(repo_root / rel), f"receipt output hash drift: {rel}")

    expected_manifest_outputs = {str(rel): sha256(repo_root / rel) for rel in (INDEX_REL, PILOT_REL, TAGS_REL, REPORT_REL, SOURCE_FREEZE_REL, OPERATION_REL, RECEIPT_REL)}
    _assert(manifest.get("generated_outputs") == expected_manifest_outputs, "manifest output hashes drift")
    _assert((repo_root / TAGS_REL).read_text(encoding="utf-8") == render_tags(index), "human tag entrypoint drift")
    _assert((repo_root / REPORT_REL).read_text(encoding="utf-8") == render_report(index, pilot, source_head), "Step07 report drift")

    changed = subprocess.check_output(["git", "diff", "--name-only", f"{source_head}..HEAD"], cwd=repo_root, text=True).splitlines()
    _assert(not any(path == forbidden or path.startswith(forbidden) for path in changed for forbidden in FORBIDDEN_PREFIXES), "forbidden historical/public path changed")
    print(f"TASK172_STEP07_ROUTING_INDEX_VALIDATION_OK rows={len(index['records'])} pilot_cases={len(pilot['cases'])} source_head={source_head}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        validate(args.repo_root.resolve())
    except AssertionError as exc:
        raise SystemExit(f"TASK172_STEP07_ROUTING_INDEX_VALIDATION_FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
