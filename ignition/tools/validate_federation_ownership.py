"""Fail-closed validation for the OS/executor ownership boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP_PATH = ROOT / "data/agent-federation/os-executor-ownership-r1.json"
POLICY_PATH = ROOT / "data/agent-federation/build-vs-integrate-policy-r1.json"
REGISTRY_PATH = ROOT / "data/agent-federation/executor-component-ownership-r1.json"
PROTECTED_PATH = re.compile(r"(?:browser|gateway|channel|messag|model|provider|subagent|daemon|scheduler|remote[-_]git)", re.I)
REQUIRED_ROLES = {"OS_OWNED", "EXTERNAL_AGENT_OWNED", "ADAPTER_BOUNDARY", "REFERENCE_ONLY", "DEFERRED"}
REQUIRED_EXCEPTION_FIELDS = {
    "exception_id", "capability_scope", "external_options_considered", "reproduction_steps",
    "observed_failure", "threshold_or_boundary", "least_privilege_impact", "reversibility",
    "owner_review_ref", "decision",
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
    if not set(reference.get("forbidden_runtime_layers", ())) >= {"browser", "network", "messaging", "provider", "model_client", "daemon", "subagent", "remote_git"}:
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
        if not isinstance(exception, Mapping) or not REQUIRED_EXCEPTION_FIELDS.issubset(set(exception)):
            raise OwnershipValidationError(f"build_vs_integrate_exception[{index}] is incomplete")

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

    exceptions_by_path: list[str] = []
    for exception in exceptions:
        paths = exception.get("protected_paths", [])
        if isinstance(paths, list):
            exceptions_by_path.extend(path for path in paths if isinstance(path, str))
    violations: list[str] = []
    for path in changed_paths:
        normalized = str(path).replace("\\", "/")
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
    args = parser.parse_args(argv)
    try:
        result = validate_contracts(changed_paths=args.changed_path)
    except OwnershipValidationError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
