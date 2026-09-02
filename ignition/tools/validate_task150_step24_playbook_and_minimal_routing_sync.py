"""Fail-closed validation for Task150 Step24 routing and projection sync."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step24-playbook-and-minimal-routing-sync.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step24-playbook-and-minimal-routing-sync-r1.schema.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
PLAYBOOKS_PATH = ROOT / "data/operations/ignition-operation-playbooks-r1.json"
HUMAN_VIEW_PATH = ROOT / "docs/operations/ignition-operation-playbooks-r1.md"
OPERATING_METHOD_PATH = ROOT / "OPERATING-METHOD.md"
LIFECYCLE_FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/lifecycle-planning-r1.json"
sys.path.insert(0, str(ROOT))

from tools.operations.plan_ignition_operation_run import CORE_CURRENT_READS, plan_run, validate_fixtures  # noqa: E402
from tools.operations.validate_ignition_operation_playbooks import (  # noqa: E402
    render_markdown,
    validate as validate_playbooks,
)
from tools.validate_ignition_operation_capability_registry import validate as validate_registry  # noqa: E402
from tools.validate_ignition_operating_method import validate as validate_operating_method  # noqa: E402


EXPECTED_FORMAL_PREVIOUS_COMMIT = "f71519b986fcb06be1bed41ee4284ab4557c0908"
EXPECTED_OPERATION_ID = "visualization.render_derived_system_view"
EXPECTED_REGISTRY_SHA = "ec285324bbdff4a718f7ffd761a61f8d393b77b8e15967bfd2e207a6d9950ea4"
EXPECTED_PLAYBOOK_SHA = "a567e548225a280b22b620bc04bded91a3bdbcdbabc73ecf571801117be926fe"
EXPECTED_HUMAN_VIEW_SHA = "1c983cfd4da8ff5a39aaecdb87bc1d041574f941d9a87253dab6a27c9a67f7f8"
EXPECTED_OPERATING_METHOD_SHA = "139886003d2e6250e4d55ffe05e913b39d8ba562deadf6d4e5368e811ccd3072"
EXPECTED_LIFECYCLE_FIXTURE_SHA = "1436afdfd3bd88ca933d9889e2c65bd207c269337158af43d9ea7b2acee8743e"
EXPECTED_READS = [
    "ignition/OPERATING-METHOD.md",
    "ignition/AI-START-HERE.md",
    "ignition/data/architecture/current-facts.json",
    "ignition/data/operations/current-snapshot-r1.json",
    "ignition/data/operations/ignition-operation-capability-registry-r1.json",
    "ignition/data/operations/ignition-run-output-contract-r1.json",
    "ignition/data/operations/ignition-operation-playbooks-r1.json",
    "ignition/data/architecture/overall-architecture.json",
    "ignition/data/architecture/interactive-system-map.json",
    "ignition/schemas/operations/task150-step18-scope-split-admission-objects-r1.schema.json",
    "ignition/schemas/operations/task150-step21-fresh-standalone-evidence-r1.schema.json",
    "ignition/schemas/operations/task150-step22-immutable-compatibility-envelope-r1.schema.json",
    "ignition/data/operations/iterations/150/step22-immutable-compatibility-envelope.json",
    "ignition/ITERATION.md",
    "ignition/docs/foundation/claim-governance-and-function-identity.md",
    "ignition/docs/foundation/future-claim-admission-protocol.md",
    "ignition/tools/run_task150_bounded_visualization_adapter.py",
    "ignition/tools/validate_task150_step21_fresh_standalone_evidence.py",
    "ignition/tools/validate_task150_step22_immutable_compatibility_envelope.py",
    "ignition/tests/test_task150_step21_fresh_standalone_evidence.py",
    "ignition/tests/test_task150_step22_immutable_compatibility_envelope.py",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_FORMAL_PREVIOUS_COMMIT:
        errors.append("Step24 must start from the pushed Step23 formal head")

    registry = load_json(REGISTRY_PATH)
    registry_errors = validate_registry(copy.deepcopy(registry))
    if registry_errors:
        errors.append("canonical Registry validator failed: " + "; ".join(registry_errors))
    if sha256(REGISTRY_PATH) != EXPECTED_REGISTRY_SHA:
        errors.append("Capability Registry digest drifted")
    if len(registry.get("operations", [])) != 20:
        errors.append("Capability Registry operation count is not exactly 20")
    operation = next((row for row in registry.get("operations", []) if row.get("operation_id") == EXPECTED_OPERATION_ID), None)
    if operation is None:
        errors.append("provider-neutral visualization operation is not in the capability lookup")
    else:
        expected_operation = {
            "current_status": "CURRENT_BOUNDED",
            "ai_callability": "PUBLIC_BOUNDED",
            "pack_binding": None,
            "default_execution_mode": "READ_ONLY_RUN",
            "repository_mutation_permission": "FORBIDDEN",
            "external_action_permission": "FORBIDDEN",
        }
        for key, expected in expected_operation.items():
            if operation.get(key) != expected:
                errors.append(f"{EXPECTED_OPERATION_ID}: {key} drifted")
        if operation.get("operation_definition_is_provider_neutral") is not None:
            # The field is recorded in the receipt as an explicit boundary even
            # though the Registry schema represents provider neutrality through
            # the provider-neutral operation identity and null Pack binding.
            pass

    playbooks = load_json(PLAYBOOKS_PATH)
    playbook_errors = validate_playbooks(copy.deepcopy(playbooks), check_human_view=True)
    if playbook_errors:
        errors.append("operation playbook validator failed: " + "; ".join(playbook_errors))
    if sha256(PLAYBOOKS_PATH) != EXPECTED_PLAYBOOK_SHA:
        errors.append("canonical operation playbook digest drifted")
    if sha256(HUMAN_VIEW_PATH) != EXPECTED_HUMAN_VIEW_SHA:
        errors.append("generated operation playbook human view digest drifted")
    playbook = next((row for row in playbooks.get("playbooks", []) if row.get("operation_id") == EXPECTED_OPERATION_ID), None)
    if playbook is None:
        errors.append("provider-neutral visualization operation has no callable playbook")
    else:
        required_playbook_fields = {"operation_id", "common_natural_language_intents", "execution_steps", "stop_conditions", "prohibitions"}
        if set(playbook) != required_playbook_fields:
            errors.append("visualization playbook contains duplicated registry fields")
        authored_text = json.dumps(playbook, ensure_ascii=False)
        for token in (
            "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT",
            "architecture analysis",
            "Do not install, auto-update or substitute",
            "canonical architecture map",
        ):
            if token not in authored_text:
                errors.append(f"visualization playbook is missing boundary token: {token}")

    generated = render_markdown(playbooks, registry)
    if generated != HUMAN_VIEW_PATH.read_text(encoding="utf-8"):
        errors.append("generated human playbook view is not reproducible")

    method_errors = validate_operating_method()
    if method_errors:
        errors.append("Operating Method validator failed: " + "; ".join(method_errors))
    if sha256(OPERATING_METHOD_PATH) != EXPECTED_OPERATING_METHOD_SHA:
        errors.append("Operating Method projection digest drifted")
    method_text = OPERATING_METHOD_PATH.read_text(encoding="utf-8")
    if "真实 registry 派生出 16 个 playbooks" not in method_text:
        errors.append("Operating Method does not project the 16-playbook lookup count")
    if "visualization.render_derived_system_view" not in method_text:
        errors.append("Operating Method does not project the visualization operation lookup")
    if "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT" not in method_text:
        errors.append("Operating Method does not project provider-unavailable behavior")
    if "只要求分析架构而没有图请求时，不得因 provider 可用而自动渲染" not in method_text:
        errors.append("Operating Method does not preserve analysis-only non-rendering")

    fixture = load_json(LIFECYCLE_FIXTURE_PATH)
    fixture_errors = validate_fixtures(copy.deepcopy(fixture))
    if fixture_errors:
        errors.append("lifecycle planning fixture validator failed: " + "; ".join(fixture_errors))
    if sha256(LIFECYCLE_FIXTURE_PATH) != EXPECTED_LIFECYCLE_FIXTURE_SHA:
        errors.append("lifecycle routing fixture digest drifted")
    if len(fixture.get("cases", [])) != 10:
        errors.append("lifecycle planning fixture count is not 10")

    request = {"request_envelope": {"user_request": "把当前点火系统结构生成一个可交互视图。"}, "input_objects": []}
    planned = plan_run(request, EXPECTED_OPERATION_ID, "TASK150_STEP24_FORMAL_BRANCH_HEAD_f71519b986fcb06be1bed41ee4284ab4557c0908")
    if planned["run_mode"] != "READ_ONLY_RUN" or planned["operation_status"] != "CURRENT_BOUNDED" or planned["decision"] != "PROCEED_BOUNDED":
        errors.append("typical visualization request did not route to bounded read-only execution")
    if planned["minimal_read_plan"] != EXPECTED_READS:
        errors.append("minimal read plan is not the exact registry-derived Step24 projection")
    if planned["minimal_read_plan"][: len(CORE_CURRENT_READS)] != list(CORE_CURRENT_READS):
        errors.append("minimal read plan lost the canonical core prefix")
    if len(planned["minimal_read_plan"]) != len(set(planned["minimal_read_plan"])):
        errors.append("minimal read plan contains duplicate reads")
    if planned["side_effects_authorized_by_plan"]:
        errors.append("minimal routing plan authorized side effects")
    if planned["output_contract_source"] not in planned["minimal_read_plan"]:
        errors.append("minimal routing plan omitted the unified output contract")

    lookup = document["capability_lookup"]
    if lookup["operation_count"] != len(registry.get("operations", [])):
        errors.append("recorded capability lookup count differs from the canonical Registry")
    if lookup["matched"] is not True or lookup["lookup_key"] != EXPECTED_OPERATION_ID:
        errors.append("recorded capability lookup is not the new operation")

    route = document["request_route"]
    if route["run_mode"] != planned["run_mode"] or route["decision"] != planned["decision"]:
        errors.append("recorded route differs from planner output")
    if route["architecture_analysis_only_auto_render"] or route["side_effects_authorized_by_plan"]:
        errors.append("recorded route widened analysis-only or side-effect boundaries")

    reads = document["minimal_read_plan"]
    if reads["read_count"] != len(reads["reads"]) or reads["reads"] != EXPECTED_READS:
        errors.append("recorded minimal read plan differs from the exact planner output")
    if not reads["core_prefix_is_preserved"] or not reads["deduplicated"]:
        errors.append("recorded minimal read plan lost core ordering or deduplication")

    rules = document["routing_boundaries"]
    for field in (
        "automatic_provider_installation",
        "automatic_provider_substitution",
        "automatic_provider_update",
        "canonical_source_writeback",
        "unadmitted_provider_auto_selection",
        "repository_mutation",
        "external_action",
        "delta_included_in_base_route",
        "architecture_authority",
        "external_truth",
        "production_readiness",
    ):
        if rules[field] is not False:
            errors.append(f"routing boundary widened: {field}")
    if rules["provider_unavailable_result"] != "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT":
        errors.append("provider unavailable behavior drifted")
    if rules["default_renderer"] != "NOT_SELECTED" or rules["aesthetic_endorsement"] != "NOT_CLAIMED":
        errors.append("renderer or aesthetic boundary widened")

    scope = document["scope_freeze"]
    if scope["task150_scope"] != "ARCHIFY_ONLY" or scope["architecture_delta"] != "EXPERIMENTAL_EXTENSION_DEFERRED":
        errors.append("Step24 scope crossed into Delta")
    if scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channel_admission"] != "NO_CHANGE":
        errors.append("Agent Reach or authenticated admission changed")
    if scope["live_external_invocation"] != "OPEN_OWNER_DEFERRED_NOT_RUN" or scope["task151"] != "FORBIDDEN":
        errors.append("live invocation or Task151 boundary changed")
    if document["machine_front_door_assessment"]["decision"] != "NO_CHANGE_WITH_REASON" or not document["machine_front_door_assessment"]["no_archify_brand_promotion"]:
        errors.append("machine front-door restraint was not recorded")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP24_PLAYBOOK_AND_MINIMAL_ROUTING_SYNC_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP24_PLAYBOOK_AND_MINIMAL_ROUTING_SYNC_OK "
        "route=READ_ONLY_RUN->visualization.render_derived_system_view "
        "playbooks=16 reads=21 unavailable=PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT "
        "delta=DEFER default_renderer=NOT_SELECTED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
