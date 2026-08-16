"""Fail-closed validation for the OS/executor ownership boundary."""

from __future__ import annotations

import argparse
import ast
import copy
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP_PATH = ROOT / "data/agent-federation/os-executor-ownership-r1.json"
POLICY_PATH = ROOT / "data/agent-federation/build-vs-integrate-policy-r1.json"
REGISTRY_PATH = ROOT / "data/agent-federation/executor-component-ownership-r1.json"
FIXTURE_PATH = ROOT / "data/operations/iterations/123/fixtures/reference-executor-freeze-fixtures-r1.json"
PROTECTED_PATH = re.compile(r"(?:browser|gateway|channel|messag|model|provider|subagent|daemon|scheduler|remote[-_]git)", re.I)
REQUIRED_ROLES = {"OS_OWNED", "EXTERNAL_AGENT_OWNED", "ADAPTER_BOUNDARY", "REFERENCE_ONLY", "DEFERRED"}
REQUIRED_FREEZE_FORBIDDEN = {
    "browser", "network", "messaging", "provider", "model", "daemon", "subagent", "mcp_ecosystem", "remote_git",
}
REQUIRED_ADAPTER_BEHAVIORS = {
    "copy_vendor_runtime_loop",
    "persist_vendor_memory",
    "bypass_os_approval",
    "promote_vendor_completion_to_os_validation",
}
REQUIRED_EXCEPTION_FIELDS = {
    "exception_id", "capability_scope", "external_options_considered", "reproduction_steps",
    "observed_failure", "threshold_or_boundary", "least_privilege_impact", "reversibility",
    "owner_review_ref", "decision", "external_executor_or_adapter", "contract_gap",
    "why_adapter_cannot_solve", "minimal_build_scope", "sunset_or_review_condition",
}


class OwnershipValidationError(ValueError):
    pass


def _load(path: Path) -> Mapping[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OwnershipValidationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, Mapping):
        raise OwnershipValidationError(f"{path} must contain an object")
    return data


def _nonempty(value: Any, context: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise OwnershipValidationError(f"{context} must be a non-empty string")


def _string_list(value: Any, context: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise OwnershipValidationError(f"{context} must be a non-empty string array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise OwnershipValidationError(f"{context} must contain only non-empty strings")
    return value


def _path_overlaps(path: str, boundary: str) -> bool:
    normalized_path = str(path).replace("\\", "/").rstrip("/")
    normalized_boundary = str(boundary).replace("\\", "/").rstrip("*").rstrip("/")
    return normalized_path == normalized_boundary or normalized_path.startswith(normalized_boundary + "/")


def _validate_adapter_static_boundary() -> None:
    adapter_root = ROOT / "agent_federation/adapters"
    for path in sorted(adapter_root.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            raise OwnershipValidationError(f"adapter_static_parse_failed:{path.relative_to(ROOT)}:{exc}") from exc
        if any(isinstance(node, ast.While) for node in ast.walk(tree)):
            raise OwnershipValidationError(f"adapter_runtime_loop:{path.relative_to(ROOT)}")


def _validate_exception_record(index: int, exception: Any) -> None:
    if not isinstance(exception, Mapping) or not REQUIRED_EXCEPTION_FIELDS.issubset(set(exception)):
        raise OwnershipValidationError(f"build_vs_integrate_exception[{index}] is incomplete")
    for field in sorted(REQUIRED_EXCEPTION_FIELDS):
        value = exception[field]
        if isinstance(value, str):
            valid = bool(value.strip())
        elif isinstance(value, list):
            valid = bool(value) and all(isinstance(item, str) and item.strip() for item in value)
        elif isinstance(value, Mapping):
            valid = bool(value)
        else:
            valid = False
        if not valid:
            raise OwnershipValidationError(f"build_vs_integrate_exception[{index}].{field} must be non-empty")


def _validate_reference_executor_freeze(
    ownership: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> None:
    reference = ownership.get("reference_executor")
    freeze = ownership.get("reference_executor_freeze")
    if not isinstance(reference, Mapping) or not isinstance(freeze, Mapping):
        raise OwnershipValidationError("reference_executor_freeze_missing")
    if (
        freeze.get("schema_version") != "reference-executor-freeze-r1"
        or freeze.get("freeze_id") != "REFERENCE_EXECUTOR_FREEZE_R1"
    ):
        raise OwnershipValidationError("reference_executor_freeze_identity_invalid")
    if freeze.get("task_id") != "IGNITION-20260816-123":
        raise OwnershipValidationError("reference_executor_freeze_task_invalid")

    allowed = set(_string_list(freeze.get("allowed_capabilities"), "reference_executor_freeze.allowed_capabilities", allow_empty=True))
    forbidden = set(_string_list(freeze.get("forbidden_capabilities"), "reference_executor_freeze.forbidden_capabilities"))
    missing_forbidden = sorted(REQUIRED_FREEZE_FORBIDDEN - forbidden)
    if missing_forbidden:
        raise OwnershipValidationError("missing_forbidden_capability:" + ",".join(missing_forbidden))
    overlap = sorted(allowed & forbidden)
    if overlap:
        raise OwnershipValidationError(f"forbidden_capability:{overlap[0]}")

    product_paths = _string_list(freeze.get("product_paths"), "reference_executor_freeze.product_paths")
    support_paths = _string_list(freeze.get("test_support_paths"), "reference_executor_freeze.test_support_paths")
    for product_path in product_paths:
        if any(_path_overlaps(product_path, support_path) for support_path in support_paths):
            raise OwnershipValidationError(f"test_helper_promoted_to_product:{product_path}")
    if reference.get("canonical_paths") != product_paths:
        raise OwnershipValidationError("reference_executor_product_paths_mismatch")
    if reference.get("test_support_paths") != support_paths:
        raise OwnershipValidationError("reference_executor_test_support_paths_mismatch")
    if freeze.get("adapter_upgrade_surface") != "adapter_mapping":
        raise OwnershipValidationError("vendor_upgrade_surface_must_be_adapter_mapping")
    if freeze.get("kernel_contract_change_requires") != "CONTRACT_GAP_RECEIPT":
        raise OwnershipValidationError("kernel_contract_change_requires_contract_gap_receipt")
    adapter_behaviors = set(
        _string_list(freeze.get("forbidden_adapter_behaviors"), "reference_executor_freeze.forbidden_adapter_behaviors")
    )
    missing_behaviors = sorted(REQUIRED_ADAPTER_BEHAVIORS - adapter_behaviors)
    if missing_behaviors:
        raise OwnershipValidationError("missing_forbidden_adapter_behavior:" + ",".join(missing_behaviors))

    components = registry.get("components", [])
    reference_components = [component for component in components if isinstance(component, Mapping) and component.get("role") == "REFERENCE_ONLY"]
    if len(reference_components) != 1:
        raise OwnershipValidationError("reference_executor_registry_cardinality_invalid")
    registry_reference = reference_components[0]
    if registry_reference.get("canonical_paths") != product_paths:
        raise OwnershipValidationError("reference_executor_registry_product_paths_mismatch")
    if registry_reference.get("test_support_paths") != support_paths:
        raise OwnershipValidationError("reference_executor_registry_test_support_paths_mismatch")

    _validate_adapter_static_boundary()


def _apply_fixture_mutation(ownership: Mapping[str, Any], mutation: Mapping[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(dict(ownership))
    freeze = mutated.get("reference_executor_freeze")
    if not isinstance(freeze, dict):
        raise OwnershipValidationError("reference_executor_freeze_missing")
    kind = mutation.get("kind")
    value = mutation.get("value")
    _nonempty(value, "fixture.mutation.value")
    if kind == "append_allowed_capability":
        freeze.setdefault("allowed_capabilities", []).append(value)
    elif kind == "append_product_path":
        freeze.setdefault("product_paths", []).append(value)
    elif kind == "set_adapter_upgrade_surface":
        freeze["adapter_upgrade_surface"] = value
    else:
        raise OwnershipValidationError(f"unknown_fixture_mutation:{kind}")
    return mutated


def check_reference_freeze_fixtures() -> dict[str, Any]:
    fixtures_doc = _load(FIXTURE_PATH)
    if fixtures_doc.get("schema_version") != "reference-executor-freeze-fixtures-r1":
        raise OwnershipValidationError("reference_freeze_fixture_schema_invalid")
    if fixtures_doc.get("task_id") != "IGNITION-20260816-123":
        raise OwnershipValidationError("reference_freeze_fixture_task_invalid")
    fixtures = fixtures_doc.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) < 3:
        raise OwnershipValidationError("reference_freeze_fixture_count_invalid")

    ownership = _load(OWNERSHIP_PATH)
    policy = _load(POLICY_PATH)
    registry = _load(REGISTRY_PATH)
    checked = 0
    for index, fixture in enumerate(fixtures):
        if not isinstance(fixture, Mapping):
            raise OwnershipValidationError(f"reference_freeze_fixture[{index}] must be an object")
        fixture_id = fixture.get("fixture_id")
        _nonempty(fixture_id, f"reference_freeze_fixture[{index}].fixture_id")
        mutation = fixture.get("mutation")
        if not isinstance(mutation, Mapping):
            raise OwnershipValidationError(f"reference_freeze_fixture[{index}].mutation must be an object")
        if fixture.get("expected_status") != "FAIL":
            raise OwnershipValidationError(f"reference_freeze_fixture[{index}] must expect FAIL")
        expected_error = fixture.get("expected_error")
        _nonempty(expected_error, f"reference_freeze_fixture[{index}].expected_error")
        mutated = _apply_fixture_mutation(ownership, mutation)
        try:
            validate_contracts(ownership=mutated, policy=policy, registry=registry)
        except OwnershipValidationError as exc:
            if expected_error not in str(exc):
                raise OwnershipValidationError(
                    f"reference_freeze_fixture_error_mismatch:{fixture_id}:expected={expected_error}:actual={exc}"
                ) from exc
        else:
            raise OwnershipValidationError(f"reference_freeze_fixture_not_rejected:{fixture_id}")
        checked += 1
    return {"status": "PASS", "negative_fixtures": checked}


def _git_changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=ROOT.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        normalized = line.strip().replace("\\", "/")
        if normalized.startswith("ignition/"):
            normalized = normalized[len("ignition/"):]
        if normalized:
            paths.append(normalized)
    return paths


def validate_contracts(
    ownership: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    changed_paths: Sequence[str] = (),
) -> dict[str, Any]:
    ownership = ownership or _load(OWNERSHIP_PATH)
    policy = policy or _load(POLICY_PATH)
    registry = registry or _load(REGISTRY_PATH)

    if ownership.get("schema_version") != "os-executor-ownership-r1" or ownership.get("contract_id") != "OS_EXECUTOR_OWNERSHIP_R1":
        raise OwnershipValidationError("ownership contract schema or id is invalid")
    if ownership.get("task_id") != "IGNITION-20260816-122" or ownership.get("status") != "CURRENT_WITH_OPEN_OBLIGATIONS":
        raise OwnershipValidationError("ownership contract task or status is invalid")
    roles = ownership.get("roles")
    if not isinstance(roles, Mapping) or set(roles) != REQUIRED_ROLES:
        raise OwnershipValidationError("ownership roles must exactly cover the five role labels")
    if any(not isinstance(items, list) or not items for items in roles.values()):
        raise OwnershipValidationError("every ownership role requires a non-empty list")
    reference = ownership.get("reference_executor")
    if not isinstance(reference, Mapping) or reference.get("identity") != "REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL":
        raise OwnershipValidationError("Reference Executor identity is not frozen")
    if not set(reference.get("forbidden_runtime_layers", ())) >= {
        "browser", "network", "messaging", "provider", "model_client", "daemon", "subagent", "mcp_ecosystem", "remote_git"
    }:
        raise OwnershipValidationError("Reference Executor forbidden runtime layers are incomplete")
    if ownership.get("component_registry_ref") != "data/agent-federation/executor-component-ownership-r1.json":
        raise OwnershipValidationError("ownership component registry reference is not canonical")
    _nonempty(ownership.get("human_core_sentence"), "ownership.human_core_sentence")

    if policy.get("schema_version") != "build-vs-integrate-policy-r1" or policy.get("policy_id") != "BUILD_VS_INTEGRATE_POLICY":
        raise OwnershipValidationError("build-vs-integrate policy schema or id is invalid")
    if policy.get("default_decision") != "INTEGRATE_EXISTING_EXECUTOR":
        raise OwnershipValidationError("default policy must integrate existing executors")
    triggers = policy.get("exception_triggers")
    non_reasons = policy.get("non_reasons")
    if not isinstance(triggers, list) or not triggers or not isinstance(non_reasons, list) or not non_reasons:
        raise OwnershipValidationError("policy triggers and non-reasons must be non-empty")
    if not REQUIRED_EXCEPTION_FIELDS.issubset(set(policy.get("required_exception_fields", ()) or ())):
        raise OwnershipValidationError("policy exception fields are incomplete")
    exceptions = policy.get("exceptions")
    if not isinstance(exceptions, list):
        raise OwnershipValidationError("policy exceptions must be an array")
    for index, exception in enumerate(exceptions):
        _validate_exception_record(index, exception)

    components = registry.get("components")
    if registry.get("schema_version") != "executor-component-ownership-r1" or not isinstance(components, list):
        raise OwnershipValidationError("executor component ownership registry is invalid")
    component_ids: set[str] = set()
    reference_components = 0
    for index, component in enumerate(components):
        if not isinstance(component, Mapping):
            raise OwnershipValidationError(f"component[{index}] must be an object")
        component_id = component.get("component_id")
        _nonempty(component_id, f"component[{index}].component_id")
        if component_id in component_ids:
            raise OwnershipValidationError(f"duplicate component id: {component_id}")
        component_ids.add(component_id)
        if component.get("role") == "REFERENCE_ONLY":
            reference_components += 1
    if reference_components != 1:
        raise OwnershipValidationError("registry must contain exactly one Reference Executor component")
    _validate_reference_executor_freeze(ownership, registry)

    exceptions_by_path: list[str] = []
    for exception in exceptions:
        paths = exception.get("protected_paths", [])
        if isinstance(paths, list):
            exceptions_by_path.extend(path for path in paths if isinstance(path, str))
    violations: list[str] = []
    for path in changed_paths:
        normalized = str(path).replace("\\", "/")
        if normalized.startswith("ignition/"):
            normalized = normalized[len("ignition/"):]
        if not PROTECTED_PATH.search(normalized):
            continue
        if normalized.startswith("agent_federation/adapters/") or normalized.startswith("schemas/agent-federation/"):
            continue
        if any(normalized == allowed or normalized.startswith(allowed.rstrip("*")) for allowed in exceptions_by_path):
            continue
        violations.append(normalized)
    if violations:
        raise OwnershipValidationError(
            "protected external-agent runtime paths require build_vs_integrate_exception: " + ", ".join(sorted(violations))
        )

    return {
        "status": "PASS",
        "contract": ownership["contract_id"],
        "policy": policy["policy_id"],
        "component_count": len(components),
        "reference_executor_components": reference_components,
        "checked_changed_paths": len(changed_paths),
        "protected_path_violations": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changed-path", action="append", default=[], help="path changed by a candidate patch; repeatable")
    parser.add_argument("--check-fixtures", action="store_true", help="run the negative Reference Executor freeze fixtures")
    parser.add_argument("--scan-git-diff", action="store_true", help="include paths changed from origin/main")
    args = parser.parse_args(argv)
    try:
        changed_paths = list(args.changed_path)
        if args.scan_git_diff:
            changed_paths.extend(_git_changed_paths())
        result = validate_contracts(changed_paths=changed_paths)
        if args.check_fixtures:
            result["fixtures"] = check_reference_freeze_fixtures()
    except OwnershipValidationError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
