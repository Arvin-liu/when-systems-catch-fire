#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step21 fresh standalone evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step21-fresh-standalone-evidence.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step21-fresh-standalone-evidence-r1.schema.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
SYSTEM_MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"
ADAPTER_PATH = ROOT / "tools/run_task150_bounded_visualization_adapter.py"
IR_PATH = ROOT / "data/operations/iterations/150/task150-archify-typed-ir-r1.json"
DELIVERY_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html"
VISUAL_RECEIPT_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.visual-check.json"
CONTACT_SHEET_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.visual-check.html"
FIXTURE_PATH = ROOT / "data/operations/iterations/150/fixtures/task150-step21-topology-extra-deleted.json"

EXPECTED_FORMAL_HEAD = "68d5d30bda0d8eb9c715ac346ce6476a55c0e288"
EXPECTED_SOURCE_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_SYSTEM_MAP_SHA = "3824697a9c781c1ea825f7335bc9461e6fb693e70bb65c042309fd16da173313"
EXPECTED_ADAPTER_SHA = "20f45aafe13ac43328f02627ecf3f49f74fe60cf24f0c907c1b315025760603e"
EXPECTED_IR_SHA = "2788796b4d329251cc67e502b6081b77542388b7f25f99470e400bf6722575ed"
EXPECTED_ARTIFACT_SHA = "da7947e408af2839e51fddc90871de30f84b1846ae1d14809a076a40d55daf45"
EXPECTED_VISUAL_RECEIPT_SHA = "28d0e94c32a962f588c103e58c1f6c83bd23229de6a71f3c1850b70f4ea315dd"
EXPECTED_CONTACT_SHEET_SHA = "e442948b73502bee0139a4a8a01308475cfed6b3798963fe80a63fd219902eb2"
EXPECTED_PROVIDER_REVISION = "06dd052602dd9a369e4d034e24faef0917b5a60c"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_topology_errors(architecture: dict[str, Any], ir: dict[str, Any]) -> list[str]:
    expected_nodes = [(node["id"], node["label"]) for node in architecture["nodes"]]
    actual_nodes = [(component["id"], component["label"]) for component in ir.get("components", [])]
    expected_edges = [
        (f"canonical-edge-{index:02d}", edge["source"], edge["target"], edge["label"])
        for index, edge in enumerate(architecture["edges"], start=1)
    ]
    actual_edges = [
        (connection["id"], connection.get("from"), connection.get("to"), connection.get("label"))
        for connection in ir.get("connections", [])
    ]
    errors: list[str] = []
    if actual_nodes != expected_nodes:
        errors.append("exact canonical node id/label sequence mismatch")
    if actual_edges != expected_edges:
        errors.append("exact canonical edge id/endpoint/label sequence mismatch")
    return errors


def apply_fixture(ir: dict[str, Any], fixture: dict[str, Any], fixture_id: str) -> dict[str, Any]:
    mutated = copy.deepcopy(ir)
    case = next(item for item in fixture["cases"] if item["id"] == fixture_id)
    action = case["mutation"]["action"]
    component_id = case["mutation"]["component_id"]
    if action == "APPEND_COMPONENT":
        mutated["components"].append({
            "id": component_id,
            "type": "backend",
            "label": "Adversarial extra node",
            "tag": "CANONICAL_DERIVED_PROJECTION",
            "pos": [10, 10],
            "size": [190, 28],
        })
    elif action == "REMOVE_COMPONENT":
        mutated["components"] = [item for item in mutated["components"] if item["id"] != component_id]
    else:
        raise ValueError(f"unknown fixture action: {action}")
    return mutated


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_FORMAL_HEAD:
        errors.append("Step21 must start from the proven Step20 formal head")
    source = document["canonical_source"]
    if source["formal_source_revision"] != EXPECTED_FORMAL_HEAD or source["sha256"] != EXPECTED_SOURCE_SHA:
        errors.append("canonical source binding drifted")
    if sha256(CANONICAL_PATH) != EXPECTED_SOURCE_SHA:
        errors.append("live canonical source hash drifted")
    if sha256(SYSTEM_MAP_PATH) != EXPECTED_SYSTEM_MAP_SHA:
        errors.append("live system-map hash drifted")
    if sha256(ADAPTER_PATH) != EXPECTED_ADAPTER_SHA:
        errors.append("adapter hash drifted")

    provider = document["provider"]
    if provider["immutable_revision"] != EXPECTED_PROVIDER_REVISION:
        errors.append("Step21 provider revision is not the observed immutable Archify ref")
    if provider["architecture_authority"] is not False or provider["automatic_update"] is not False:
        errors.append("provider authority or automatic update boundary widened")

    ir = load_json(IR_PATH)
    if sha256(IR_PATH) != EXPECTED_IR_SHA:
        errors.append("fresh typed IR hash drifted")
    if ir["meta"]["repository"]["revision"] != EXPECTED_FORMAL_HEAD:
        errors.append("typed IR is not bound to the Step20 formal exact head")
    if len(ir.get("components", [])) != 24 or len(ir.get("connections", [])) != 24:
        errors.append("fresh typed IR cardinality drifted")
    architecture = load_json(CANONICAL_PATH)
    if exact_topology_errors(architecture, ir):
        errors.append("fresh typed IR failed exact canonical node/edge equality")

    typed_validation = document["typed_ir_validation"]
    if typed_validation["status"] != "PASS" or typed_validation["checks_passed"] != typed_validation["checks_total"]:
        errors.append("typed IR validation did not pass all checks")

    delivery = document["delivery"]
    if sha256(DELIVERY_PATH) != EXPECTED_ARTIFACT_SHA or delivery["artifact_sha256"] != EXPECTED_ARTIFACT_SHA:
        errors.append("delivered standalone artifact hash drifted")
    if delivery["specification_sha256"] != EXPECTED_IR_SHA or delivery["source_evidence_revision"] != EXPECTED_FORMAL_HEAD:
        errors.append("delivery does not bind the fresh IR and formal source revision")
    if delivery["source_evidence_verified"] is not True or delivery["checks_passed"] != 9 or delivery["checks_total"] != 9:
        errors.append("delivery receipt is incomplete")

    visual = document["standalone_visual_check"]
    if sha256(VISUAL_RECEIPT_PATH) != EXPECTED_VISUAL_RECEIPT_SHA or visual["receipt_sha256"] != EXPECTED_VISUAL_RECEIPT_SHA:
        errors.append("visual-check receipt hash drifted")
    if sha256(CONTACT_SHEET_PATH) != EXPECTED_CONTACT_SHEET_SHA or visual["contact_sheet_sha256"] != EXPECTED_CONTACT_SHEET_SHA:
        errors.append("visual contact-sheet hash drifted")
    visual_receipt = load_json(VISUAL_RECEIPT_PATH)
    if not visual_receipt.get("ok") or visual_receipt.get("status") != "pass":
        errors.append("automated visual-check did not pass")
    if visual_receipt.get("visualReview") != "pending":
        errors.append("visual-check perceptual review state was changed")
    if visual_receipt.get("containment", {}).get("status") != "pass":
        errors.append("standalone containment gate did not pass")
    if visual_receipt.get("readability", {}).get("status") != "pass":
        errors.append("standalone readability gate did not pass")
    if visual_receipt.get("viewerChrome", {}).get("status") != "pass":
        errors.append("standalone viewer-chrome gate did not pass")
    observed_viewports = visual_receipt.get("containment", {}).get("viewports", [])
    if len(observed_viewports) != 4 or not all(item.get("ok") for item in observed_viewports):
        errors.append("required light viewport containment observations are incomplete")
    observed_capture_viewports = visual_receipt.get("captures", {}).get("screenshots", [])
    if len(observed_capture_viewports) != 4 or not all(item.get("ok") for item in observed_capture_viewports):
        errors.append("required light/dark capture observations are incomplete")
    if visual["containment_failures"] != 0 or visual["readability_failures"] != 0 or visual["viewer_chrome_failures"] != 0:
        errors.append("Step21 visual failure census is non-zero")
    if len(visual["required_viewport_observations"]) != 6 or not all(item["ok"] for item in visual["required_viewport_observations"]):
        errors.append("Step21 required viewport summary contains a failure")

    provenance = document["provenance"]
    if not all(value is True for key, value in provenance.items() if key != "architecture_truth_escalation") or provenance["architecture_truth_escalation"] is not False:
        errors.append("provenance binding or architecture-truth boundary drifted")

    repeatability = document["repeatability"]
    if repeatability["adapter_ir_first_sha256"] != EXPECTED_IR_SHA or repeatability["adapter_ir_second_sha256"] != EXPECTED_IR_SHA:
        errors.append("adapter repeatability hashes do not match the fresh IR")
    if repeatability["delivery_artifact_first_sha256"] != EXPECTED_ARTIFACT_SHA or repeatability["delivery_artifact_second_sha256"] != EXPECTED_ARTIFACT_SHA:
        errors.append("delivery repeatability hashes do not match the fresh artifact")
    if not repeatability["ir_identical"] or not repeatability["artifact_identical"] or not repeatability["provider_revision_identical"] or not repeatability["formal_source_revision_identical"]:
        errors.append("repeatability did not pass")

    fixture = load_json(FIXTURE_PATH)
    if document["adversarial_fixtures"]["cases"] != fixture["cases"]:
        errors.append("adversarial fixture receipt does not match the durable fixture")
    for fixture_id in ("extra_node", "deleted_node"):
        mutated = apply_fixture(ir, fixture, fixture_id)
        if not exact_topology_errors(architecture, mutated):
            errors.append(f"{fixture_id} fixture was not rejected by exact topology reconciliation")
    adversarial = document["adversarial_fixtures"]
    if adversarial["provider_process_started"] or adversarial["credentials_or_sessions_accessed"] or adversarial["system_or_repository_mutation"]:
        errors.append("adversarial fixture evaluation crossed a side-effect boundary")

    gates = document["base_gate_results"]
    required_passes = {
        "canonical_source_provenance_complete": "PASS_FRESH",
        "node_edge_semantic_fidelity": "PASS_FRESH",
        "provider_topology_unchanged": "PASS_FRESH",
        "standalone_viewport_containment_zero_failure": "PASS_FRESH_ZERO_FAILURE",
        "canonical_source_unaffected": "PASS_FRESH",
        "environment_admission_no_auto_install": "PASS_FRESH_NO_INSTALL",
        "artifact_digest_and_provenance_receipt": "PASS_FRESH",
        "no_default_renderer": "PASS_SCOPE_LOCKED",
        "no_architecture_truth_escalation": "PASS_FRESH_SCOPE_BOUND",
    }
    for key, expected in required_passes.items():
        if gates.get(key) != expected:
            errors.append(f"base gate {key} is not {expected}")
    if gates.get("immutable_tested_compatibility_envelope") != "PENDING_STEP22":
        errors.append("Step21 must leave the Step22 compatibility gate pending")

    admission = document["admission_decision"]
    if admission["new_base_blocker"] is not False or admission["standalone_visual_evidence"] != "PASS":
        errors.append("Step21 standalone result did not pass without a new base blocker")
    if admission["current_capability"] or admission["registry_write"] or admission["default_renderer"] != "NOT_SELECTED":
        errors.append("Step21 crossed the Current or default-renderer boundary")
    if admission["delta_extension"] != "EXPERIMENTAL_EXTENSION_DEFERRED" or admission["delta_gate"] != "FAIL_DEFERRED":
        errors.append("Delta scope was promoted or its failure relabelled")
    if admission["owner_aesthetic_endorsement"] != "NOT_GRANTED_NOT_CLAIMED":
        errors.append("Step21 claimed an aesthetic decision")

    scope = document["scope_freeze"]
    if scope["task150_scope"] != "ARCHIFY_ONLY" or scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channel_admission"] != "NO_CHANGE":
        errors.append("Task150, Agent Reach or authentication scope changed")
    if scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN" or scope["task151"] != "FORBIDDEN":
        errors.append("live invocation or Task151 scope changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP21_FRESH_STANDALONE_EVIDENCE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP21_FRESH_STANDALONE_EVIDENCE_OK "
        "nodes=24 edges=24 visual_containment=6/6 "
        "repeatability=PASS adversarial_extra_deleted=REJECTED/REJECTED "
        "current=false compatibility=PENDING_STEP22"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
