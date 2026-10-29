#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step29's exact-head Ready gate."""

from __future__ import annotations

import copy
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.validate_ignition_operation_capability_registry import validate as validate_registry
from tools.validate_task150_step02_minimal_bounded_operation import validate as validate_step02
from tools.validate_task150_step03_renderer_independence import validate as validate_step03
from tools.validate_task150_step04_viewport_residual_repair import validate as validate_step04
from tools.validate_task150_step05_visual_review import validate as validate_step05
from tools.validate_task150_step06_current_architecture_smoke import validate as validate_step06
from tools.validate_task150_step07_architecture_delta_smoke import validate as validate_step07
from tools.validate_task150_step08_provider_failure_fallback import validate as validate_step08
from tools.validate_task150_step09_environment_admission import validate as validate_step09
from tools.validate_task150_step10_license_drift import validate as validate_step10
from tools.validate_task150_step11_capability_registry_candidate_gate import validate as validate_step11
from tools.validate_task150_step12_front_door_restraint import validate as validate_step12
from tools.validate_task150_step13_adversarial import validate as validate_step13
from tools.validate_task150_step14_final_defer_decision import validate as validate_step14
from tools.validate_task150_step15_draft_closeout import validate as validate_step15
from tools.validate_task150_step18_scope_split_admission_objects import validate as validate_step18
from tools.validate_task150_step19_gate_topology_regression import validate as validate_step19
from tools.validate_task150_step20_functional_versus_aesthetic_boundary import validate as validate_step20
from tools.validate_task150_step21_fresh_standalone_evidence import validate as validate_step21
from tools.validate_task150_step22_immutable_compatibility_envelope import validate as validate_step22
from tools.validate_task150_step23_candidate_registry_admission import validate as validate_step23
from tools.validate_task150_step24_playbook_and_minimal_routing_sync import validate as validate_step24
from tools.validate_task150_step25_delta_remains_experimental_deferred import validate as validate_step25
from tools.validate_task150_step26_front_door_and_sync_surface_restraint import validate as validate_step26
from tools.validate_task150_step27_adversarial_split_scope import validate as validate_step27
from tools.validate_task150_step28_owner_adjudication_scope_split import validate as validate_step28


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step29-exact-head-ready-gate.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step29-exact-head-ready-gate-r1.schema.json"
STEP14_PATH = ROOT / "data/operations/iterations/150/step14-final-defer-decision.json"
STEP15_PATH = ROOT / "data/operations/iterations/150/step15-draft-closeout.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
SYSTEM_MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"
ADAPTER_PATH = ROOT / "tools/run_task150_bounded_visualization_adapter.py"
IR_PATH = ROOT / "data/operations/iterations/150/task150-archify-typed-ir-r1.json"
ARTIFACT_HTML_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html"
VISUAL_RECEIPT_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.visual-check.json"
CONTACT_SHEET_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.visual-check.html"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"

EXPECTED_CANDIDATE_HEAD = "6e17db06b793c7ad16a36c4f22c38983cdb8892b"
EXPECTED_BASE_SHA = "d7372c27abe456b5b8c058675630d8038f91b448"
EXPECTED_STEP14_SHA = "ef6465cdc824e9865cf3a2e4b8e366684877a672e0f0e9a5fb791b7cbf8a1482"
EXPECTED_STEP15_SHA = "13894ad61b0b28b0fbcba96d2f562208fd7f2d3f5d83212687dd959c7be4b4c3"
EXPECTED_CANONICAL_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_SYSTEM_MAP_SHA = "3824697a9c781c1ea825f7335bc9461e6fb693e70bb65c042309fd16da173313"
EXPECTED_ADAPTER_SHA = "20f45aafe13ac43328f02627ecf3f49f74fe60cf24f0c907c1b315025760603e"
EXPECTED_IR_SHA = "2788796b4d329251cc67e502b6081b77542388b7f25f99470e400bf6722575ed"
EXPECTED_ARTIFACT_SHA = "da7947e408af2839e51fddc90871de30f84b1846ae1d14809a076a40d55daf45"
EXPECTED_VISUAL_RECEIPT_SHA = "28d0e94c32a962f588c103e58c1f6c83bd23229de6a71f3c1850b70f4ea315dd"
EXPECTED_CONTACT_SHEET_SHA = "e442948b73502bee0139a4a8a01308475cfed6b3798963fe80a63fd219902eb2"
EXPECTED_REGISTRY_SHA = "ec285324bbdff4a718f7ffd761a61f8d393b77b8e15967bfd2e207a6d9950ea4"
EXPECTED_PROVIDER_REF = "06dd052602dd9a369e4d034e24faef0917b5a60c"

PRIOR_VALIDATORS = (
    ("Step02", validate_step02),
    ("Step03", validate_step03),
    ("Step04", validate_step04),
    ("Step05", validate_step05),
    ("Step06", validate_step06),
    ("Step07", validate_step07),
    ("Step08", validate_step08),
    ("Step09", validate_step09),
    ("Step10", validate_step10),
    ("Step11", validate_step11),
    ("Step12", validate_step12),
    ("Step13", validate_step13),
    ("Step14", validate_step14),
    ("Step15", validate_step15),
    ("Step18", validate_step18),
    ("Step19", validate_step19),
    ("Step20", validate_step20),
    ("Step21", validate_step21),
    ("Step22", validate_step22),
    ("Step23", validate_step23),
    ("Step24", validate_step24),
    ("Step25", validate_step25),
    ("Step26", validate_step26),
    ("Step27", validate_step27),
    ("Step28", validate_step28),
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_CANDIDATE_HEAD or document["candidate_head_sha"] != EXPECTED_CANDIDATE_HEAD:
        errors.append("Step29 must bind its Ready gate to the exact Step28 candidate parent head")

    for label, path, expected in (
        ("Step14", STEP14_PATH, EXPECTED_STEP14_SHA),
        ("Step15", STEP15_PATH, EXPECTED_STEP15_SHA),
        ("canonical source", CANONICAL_PATH, EXPECTED_CANONICAL_SHA),
        ("system map", SYSTEM_MAP_PATH, EXPECTED_SYSTEM_MAP_SHA),
        ("adapter", ADAPTER_PATH, EXPECTED_ADAPTER_SHA),
        ("typed IR", IR_PATH, EXPECTED_IR_SHA),
        ("standalone artifact", ARTIFACT_HTML_PATH, EXPECTED_ARTIFACT_SHA),
        ("standalone visual receipt", VISUAL_RECEIPT_PATH, EXPECTED_VISUAL_RECEIPT_SHA),
        ("standalone contact sheet", CONTACT_SHEET_PATH, EXPECTED_CONTACT_SHEET_SHA),
        ("Capability Registry", REGISTRY_PATH, EXPECTED_REGISTRY_SHA),
    ):
        if sha256(path) != expected:
            errors.append(f"{label} hash drifted")

    step14 = load_json(STEP14_PATH)
    step15 = load_json(STEP15_PATH)
    timeline = document["historical_lineage"]
    if step14.get("status") != "DEFER" or step14.get("decision", {}).get("outcome") != "DEFER":
        errors.append("historical Step14 DEFER was rewritten")
    if step14.get("gate_summary", {}).get("delta_viewport_containment_zero_failure") != "FAIL":
        errors.append("historical Step14 Delta viewport blocker was rewritten")
    if step14.get("gate_summary", {}).get("owner_visual_acceptance") != "PENDING":
        errors.append("historical Step14 Owner-pending boundary was rewritten")
    if step15.get("status") != "AWAIT_OWNER_ARCHIFY_BOUNDED_ADMISSION_REVIEW" or not step15.get("pull_request", {}).get("is_draft"):
        errors.append("historical Step15 Draft stop was rewritten")
    if timeline["step14_status"] != "DEFER" or timeline["step15_status"] != "AWAIT_OWNER_ARCHIFY_BOUNDED_ADMISSION_REVIEW":
        errors.append("Step29 historical status summary drifted")

    registry = load_json(REGISTRY_PATH)
    registry_errors = validate_registry(copy.deepcopy(registry))
    if registry_errors:
        errors.append("canonical Capability Registry validator failed: " + "; ".join(registry_errors))
    operation_ids = [row.get("operation_id") for row in registry.get("operations", [])]
    if len(operation_ids) != 20:
        errors.append(f"Capability Registry operation count is {len(operation_ids)}, expected 20")
    if "visualization.render_derived_system_view" not in operation_ids:
        errors.append("provider-neutral base operation is missing")
    if any("delta" in str(operation_id).casefold() or "archify" in str(operation_id).casefold() for operation_id in operation_ids):
        errors.append("Delta or provider-specific operation ID was registered")
    operation = next((row for row in registry.get("operations", []) if row.get("operation_id") == "visualization.render_derived_system_view"), None)
    if operation is None or operation.get("current_status") != "CURRENT_BOUNDED" or operation.get("pack_binding") is not None:
        errors.append("base Registry operation is not provider-neutral CURRENT_BOUNDED")

    for label, validator in PRIOR_VALIDATORS:
        prior_errors = validator()
        if prior_errors:
            errors.append(f"{label} validator failed: " + "; ".join(prior_errors))

    standalone = document["standalone_evidence"]
    if standalone["provider"]["immutable_revision"] != EXPECTED_PROVIDER_REF:
        errors.append("standalone evidence provider ref drifted")
    if standalone["topology"] != {
        "canonical_nodes": 24,
        "derived_nodes": 24,
        "canonical_edges": 24,
        "derived_edges": 24,
        "semantic_relationships_unchanged": True,
        "standalone_containment_failures": 0,
    }:
        errors.append("standalone topology or zero-failure containment evidence drifted")
    if standalone["compatibility"]["delta_visual_residuals"] != 3:
        errors.append("Step25's three Delta wrapper residuals were not preserved")

    regression = document["full_regression"]
    if regression["head_sha"] != EXPECTED_CANDIDATE_HEAD or not is_ancestor(EXPECTED_CANDIDATE_HEAD, subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()):
        errors.append("the tested natural regression head is not in the current Step29 lineage")
    if regression["tests_run"] != 1714 or any(regression[key] != 0 for key in ("failures", "errors", "skipped", "process_returncode")):
        errors.append("full regression does not prove 1714/0/0/0")
    if not regression["clean_before"] or not regression["clean_after"] or regression["generated_output_drift"] != []:
        errors.append("full regression cleanliness or generated-output drift boundary failed")
    if not regression["process_completed_naturally"] or regression["watchdog_used"] or regression["process_killed"] or regression["arbitrary_timeout_used"]:
        errors.append("full regression was not a natural, non-watchdog run")
    if regression["minimum_supported_seconds"] != 14400 or not regression["isolated"]:
        errors.append("full regression natural-window or isolation contract drifted")

    remote = document["remote_observation"]
    checks = remote["status_checks"]["contexts"]
    expected_contexts = [
        ("validate", "foundation-validation", 33628547103, 100242028908),
        ("validate-current-state-sync", "current-state-sync-validation", 33628547130, 100242027789),
        ("lifecycle-validation", "iteration-lifecycle-validation", 33628547125, 100242027779),
        ("layer-a-tests", "iteration-planner-ci", 33628547119, 100242027649),
        ("layer-b-resolver", "iteration-planner-ci", 33628547119, 100242263369),
        ("validate", "q33-governance-validation", 33628547143, 100242027858),
        ("preflight", "repository-path-accounting-preflight", 33628547128, 100242028223),
    ]
    observed_contexts = [
        (item["name"], item["workflow"], item["run_id"], item["job_id"])
        for item in checks
    ]
    if observed_contexts != expected_contexts:
        errors.append(f"required PR check identity drifted: {observed_contexts!r}")
    if any(item["conclusion"] != "SUCCESS" or item["status"] != "COMPLETED" or item["head_sha"] != EXPECTED_CANDIDATE_HEAD for item in checks):
        errors.append("not every required PR check is successful on the exact candidate head")
    if remote["pull_request"]["head_sha"] != EXPECTED_CANDIDATE_HEAD or remote["pull_request"]["is_draft"] is not True or remote["pull_request"]["merged"] is not False:
        errors.append("Step29 PR observation crossed or lost the pre-Ready Draft boundary")

    binding = document["exact_head_binding"]
    if len({binding[key] for key in ("local_head_sha", "tracking_head_sha", "ls_remote_head_sha", "pr_head_sha")}) != 1:
        errors.append("local, tracking, ls-remote and PR heads are not equal")
    if binding["base_sha"] != EXPECTED_BASE_SHA or not binding["base_is_ancestor"] or not binding["worktree_clean"] or not binding["non_shallow"]:
        errors.append("exact-head or base-lineage binding is incomplete")
    try:
        shallow = subprocess.check_output(["git", "rev-parse", "--is-shallow-repository"], cwd=REPO_ROOT, text=True).strip()
        if shallow != "false":
            errors.append("current formal worktree is shallow")
    except (OSError, subprocess.CalledProcessError):
        errors.append("could not verify current formal worktree depth")

    preflight = document["projection_preflight"]
    if preflight["status"] != "PASS" or preflight["check_count"] != 24 or preflight["failed_checks"] != [] or not preflight["release_admission"] or preflight["side_effect_detected"] or not preflight["clean_before"] or not preflight["clean_after"]:
        errors.append("projection preflight record is not a clean 24/24 no-side-effect pass")

    scope = document["scope_freeze"]
    if scope["base_operation"] != "CURRENT_BOUNDED_CANDIDATE" or scope["architecture_delta"] != "EXPERIMENTAL_EXTENSION_DEFERRED":
        errors.append("base and Delta scope are coupled or drifted")
    if scope["aesthetic_endorsement_required_for_functional_admission"] or scope["owner_aesthetic_endorsement"] != "NOT_GRANTED_NOT_CLAIMED":
        errors.append("aesthetic endorsement was made a functional gate or claimed")
    if scope["default_renderer"] != "NOT_SELECTED" or scope["archify_architecture_authority"]:
        errors.append("renderer or provider authority boundary widened")
    if scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channel_admission"] != "NO_CHANGE" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("Agent Reach, authentication or live invocation boundary changed")
    if scope["task151"] != "FORBIDDEN" or not scope["no_live_invocation"] or not scope["no_provider_modification"]:
        errors.append("successor or side-effect guard changed")

    lifecycle = document["lifecycle_boundary"]
    if lifecycle["registry_operation_count"] != 20 or lifecycle["delta_operation_registered"] or lifecycle["formal_ready"] or not lifecycle["ready_transition_authorized_by_step29"]:
        errors.append("Step29 lifecycle authorization or Registry boundary drifted")
    if lifecycle["merged_to_main"] or lifecycle["current_on_main"] or lifecycle["pr_state"] != "OPEN" or not lifecycle["pr_is_draft"]:
        errors.append("Step29 crossed the Ready, merge or Current-on-main boundary")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP29_EXACT_HEAD_READY_GATE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP29_EXACT_HEAD_READY_GATE_OK "
        "candidate=6e17db06 base=CURRENT_BOUNDED_CANDIDATE delta=DEFER "
        "full_regression=1714/0/0/0 remote_checks=7/7 ready_authorized=true "
        "formal_ready=false pr_draft=true default_renderer=NOT_SELECTED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
