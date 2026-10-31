#!/usr/bin/env python3
"""Check caller-declared Agent Episode Binding relationships without execution."""

from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-agent-episode-binding-r0.schema.json"
MAX_INPUT_BYTES = 262_144
MAX_FINDINGS = 64
TOOL_ID = "collaboration.validate_agent_episode_binding"
TOOL_VERSION = "0.1.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

CLAIM_CEILING = (
    "Checks one caller-declared Agent Episode Binding plan for schema and cross-reference consistency only. "
    "It does not resolve or read context refs, authenticate the permission ceiling, identify real agents, "
    "dispatch work, enforce channels or resource leases, interpret aggregation policy, validate outputs, "
    "authorize execution, or establish safety or scientific validity."
)


class DuplicateJSONKey(ValueError):
    """Raised when any JSON object repeats a key."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey
        result[key] = value
    return result


def _pointer(path: Any) -> str:
    parts = [str(item).replace("~", "~0").replace("/", "~1") for item in path]
    return "$" + ("/" + "/".join(parts) if parts else "")


def _finding(code: str, path: str) -> dict[str, str]:
    return {"code": code, "path": path}


def _schema_findings(plan: Any) -> list[dict[str, str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    problems = sorted(validator.iter_errors(plan), key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""))
    return [
        _finding("INPUT_SCHEMA_INVALID", _pointer(problem.absolute_path))
        for problem in problems[:MAX_FINDINGS]
    ]


def _index_rows(
    rows: list[dict[str, Any]],
    key: str,
    collection: str,
    errors: list[dict[str, str]],
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    indexed: dict[str, dict[str, Any]] = {}
    positions: dict[str, int] = {}
    for index, row in enumerate(rows):
        value = row[key]
        if value in indexed:
            errors.append(_finding("DUPLICATE_ID", f"$/{collection}/{index}/{key}"))
        else:
            indexed[value] = row
            positions[value] = index
    return indexed, positions


def _contains_path(dependencies: dict[str, list[str]], start: str, target: str) -> bool:
    pending = list(dependencies.get(target, []))
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current == start:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(dependencies.get(current, []))
    return False


def _semantic_findings(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    roles, _ = _index_rows(plan["roles"], "role_id", "roles", errors)
    contexts, _ = _index_rows(plan["contexts"], "context_id", "contexts", errors)
    edges, _ = _index_rows(plan["feedback_edges"], "channel_id", "feedback_edges", errors)
    bindings, binding_pos = _index_rows(plan["write_domain_bindings"], "binding_id", "write_domain_bindings", errors)
    units, unit_pos = _index_rows(plan["work_units"], "work_unit_id", "work_units", errors)
    ceiling = plan["episode_permission_ceiling"]

    for index, role in enumerate(plan["roles"]):
        path = f"$/roles/{index}"
        role_id = role["role_id"]
        for field, allowed in (
            ("allowed_tool_ids", set(ceiling["allowed_tool_ids"])),
            ("allowed_read_domains", set(ceiling["allowed_read_domains"])),
            ("allowed_write_domains", set(ceiling["allowed_write_domains"])),
        ):
            if not set(role[field]) <= allowed:
                errors.append(_finding("ROLE_WIDENS_DECLARED_PERMISSION_CEILING", f"{path}/{field}"))
        if role["role_class"] in {"VALIDATOR", "AUDITOR"} and not role["validation_obligations"]:
            errors.append(_finding("REVIEW_ROLE_HAS_NO_DECLARED_OBLIGATION", f"{path}/validation_obligations"))
        for context_index, context_id in enumerate(role["context_ids"]):
            context = contexts.get(context_id)
            if context is None:
                errors.append(_finding("ROLE_CONTEXT_UNKNOWN", f"{path}/context_ids/{context_index}"))
            elif role_id not in context["authorized_role_ids"]:
                errors.append(_finding("ROLE_CONTEXT_NOT_AUTHORIZED", f"{path}/context_ids/{context_index}"))

    for index, context in enumerate(plan["contexts"]):
        path = f"$/contexts/{index}"
        owner = context["owner_role_id"]
        if owner not in roles:
            errors.append(_finding("CONTEXT_OWNER_UNKNOWN", f"{path}/owner_role_id"))
        if owner not in context["authorized_role_ids"]:
            errors.append(_finding("CONTEXT_OWNER_NOT_AUTHORIZED", f"{path}/authorized_role_ids"))
        for role_index, role_id in enumerate(context["authorized_role_ids"]):
            if role_id not in roles:
                errors.append(_finding("CONTEXT_ROLE_UNKNOWN", f"{path}/authorized_role_ids/{role_index}"))
        if context["visibility"] == "ROLE_PRIVATE" and set(context["authorized_role_ids"]) != {owner}:
            errors.append(_finding("PRIVATE_CONTEXT_SHARED", f"{path}/authorized_role_ids"))
        if not _SHA256_RE.fullmatch(context["sha256"]):
            errors.append(_finding("CONTEXT_DIGEST_INVALID", f"{path}/sha256"))

    for index, edge in enumerate(plan["feedback_edges"]):
        path = f"$/feedback_edges/{index}"
        source_id = edge["source_role_id"]
        source = roles.get(source_id)
        if source is None:
            errors.append(_finding("FEEDBACK_SOURCE_UNKNOWN", f"{path}/source_role_id"))
        if edge["target_role_id"] not in roles:
            errors.append(_finding("FEEDBACK_TARGET_UNKNOWN", f"{path}/target_role_id"))
        if source is not None:
            if edge["can_change_future_inputs"] and not source["can_change_future_inputs"]:
                errors.append(_finding("ROLE_CANNOT_CHANGE_FUTURE_INPUTS", f"{path}/can_change_future_inputs"))
            if edge["can_stop_future_work"] and not source["can_signal_hard_stop"]:
                errors.append(_finding("ROLE_CANNOT_SIGNAL_HARD_STOP", f"{path}/can_stop_future_work"))
            if edge["can_request_owner_review"] and not source["can_request_owner_review"]:
                errors.append(_finding("ROLE_CANNOT_REQUEST_OWNER_REVIEW", f"{path}/can_request_owner_review"))

        channel_class = edge["channel_class"]
        has_control = edge["can_change_future_inputs"] or edge["can_stop_future_work"] or edge["can_request_owner_review"]
        message_kinds = set(edge["allowed_message_kinds"])
        if channel_class == "NO_CHANNEL":
            if message_kinds or has_control or not edge["informational_only"]:
                errors.append(_finding("NO_CHANNEL_DECLARES_MESSAGES_OR_CONTROL", path))
        elif channel_class in {"ONE_WAY_OBSERVATION", "VALIDATION_ONLY"}:
            if not message_kinds or has_control or not edge["informational_only"]:
                errors.append(_finding("INFORMATION_EDGE_DECLARES_CONTROL_EFFECT", path))
        elif channel_class == "HARD_STOP_ONLY":
            if (
                "PROTOCOL_HARD_STOP" not in message_kinds
                or not edge["can_stop_future_work"]
                or edge["can_change_future_inputs"]
                or edge["can_request_owner_review"]
                or edge["informational_only"]
                or not edge["hard_stop_policy_ref"]
            ):
                errors.append(_finding("HARD_STOP_EDGE_INCOMPLETE_OR_OVERBROAD", path))
        elif channel_class == "BIDIRECTIONAL_COORDINATION":
            if not message_kinds or edge["informational_only"]:
                errors.append(_finding("COORDINATION_EDGE_UNDERDECLARED", path))
        if edge["can_stop_future_work"] and "PROTOCOL_HARD_STOP" not in message_kinds:
            errors.append(_finding("STOP_EFFECT_MISSING_TYPED_MESSAGE", f"{path}/allowed_message_kinds"))
        if edge["can_stop_future_work"] and not edge["hard_stop_policy_ref"]:
            errors.append(_finding("STOP_EFFECT_HAS_NO_POLICY_REFERENCE", f"{path}/hard_stop_policy_ref"))
        if edge["hard_stop_policy_ref"] and not edge["can_stop_future_work"]:
            errors.append(_finding("UNUSED_HARD_STOP_POLICY_REFERENCE", f"{path}/hard_stop_policy_ref"))
        if edge["hard_stop_policy_ref"]:
            warnings.append(_finding("HARD_STOP_POLICY_REF_NOT_RESOLVED", f"{path}/hard_stop_policy_ref"))

    seen_role_domains: set[tuple[str, str]] = set()
    effect_rank = {"READ_ONLY": 0, "LOCAL_WRITE": 1, "EXTERNAL_EFFECT": 2, "UNKNOWN_EFFECT": 3}
    for index, binding in enumerate(plan["write_domain_bindings"]):
        path = f"$/write_domain_bindings/{index}"
        role = roles.get(binding["role_id"])
        if role is None:
            errors.append(_finding("WRITE_BINDING_ROLE_UNKNOWN", f"{path}/role_id"))
            continue
        domain = binding["write_domain"]
        if (binding["role_id"], domain) in seen_role_domains:
            errors.append(_finding("DUPLICATE_ROLE_DOMAIN_BINDING", path))
        seen_role_domains.add((binding["role_id"], domain))
        if binding["exclusivity"] == "READ_SHARED":
            if binding["effect_class"] != "READ_ONLY" or domain not in role["allowed_read_domains"]:
                errors.append(_finding("READ_BINDING_EXCEEDS_ROLE_DECLARATION", path))
        else:
            if binding["effect_class"] == "READ_ONLY" or domain not in role["allowed_write_domains"]:
                errors.append(_finding("WRITE_BINDING_EXCEEDS_ROLE_DECLARATION", path))
            if domain not in ceiling["allowed_write_domains"]:
                errors.append(_finding("WRITE_BINDING_EXCEEDS_EPISODE_CEILING", f"{path}/write_domain"))
        if binding["effect_class"] in {"EXTERNAL_EFFECT", "UNKNOWN_EFFECT"}:
            warnings.append(_finding("EFFECT_NEEDS_SEPARATE_ADMISSION", path))

    dependency_map: dict[str, list[str]] = {}
    for index, unit in enumerate(plan["work_units"]):
        path = f"$/work_units/{index}"
        dependencies: list[str] = []
        role = roles.get(unit["role_id"])
        if role is None:
            errors.append(_finding("WORK_UNIT_ROLE_UNKNOWN", f"{path}/role_id"))
        else:
            if not set(unit["input_types"]) <= set(role["allowed_inputs"]):
                errors.append(_finding("WORK_UNIT_INPUT_OUTSIDE_ROLE_DECLARATION", f"{path}/input_types"))
            if not set(unit["output_types"]) <= set(role["allowed_outputs"]):
                errors.append(_finding("WORK_UNIT_OUTPUT_OUTSIDE_ROLE_DECLARATION", f"{path}/output_types"))
            role_contexts = set(role["context_ids"])
            for context_index, context_id in enumerate(unit["context_ids"]):
                if context_id not in role_contexts:
                    errors.append(_finding("WORK_UNIT_CONTEXT_OUTSIDE_ROLE_SCOPE", f"{path}/context_ids/{context_index}"))
        for binding_index, binding_id in enumerate(unit["write_binding_ids"]):
            binding = bindings.get(binding_id)
            if binding is None:
                errors.append(_finding("WORK_UNIT_WRITE_BINDING_UNKNOWN", f"{path}/write_binding_ids/{binding_index}"))
            elif binding["role_id"] != unit["role_id"]:
                errors.append(_finding("WORK_UNIT_USES_ANOTHER_ROLE_WRITE_BINDING", f"{path}/write_binding_ids/{binding_index}"))
            else:
                if unit["effect_class"] != "READ_ONLY" and binding["exclusivity"] != "WRITE_EXCLUSIVE":
                    errors.append(_finding("MUTATING_WORK_UNIT_USES_SHARED_READ_BINDING", f"{path}/write_binding_ids/{binding_index}"))
                if effect_rank[unit["effect_class"]] < effect_rank[binding["effect_class"]]:
                    errors.append(_finding("WORK_UNIT_EFFECT_UNDERSPECIFIES_BINDING", f"{path}/write_binding_ids/{binding_index}"))
        if unit["effect_class"] == "READ_ONLY" and unit["write_binding_ids"]:
            errors.append(_finding("READ_ONLY_WORK_UNIT_HAS_WRITE_BINDING", f"{path}/write_binding_ids"))
        if unit["effect_class"] != "READ_ONLY" and not unit["write_binding_ids"]:
            errors.append(_finding("MUTATING_WORK_UNIT_HAS_NO_WRITE_BINDING", f"{path}/write_binding_ids"))
        if unit["effect_class"] in {"EXTERNAL_EFFECT", "UNKNOWN_EFFECT"}:
            warnings.append(_finding("WORK_UNIT_EFFECT_NEEDS_SEPARATE_ADMISSION", path))
        for dependency_index, dependency in enumerate(unit["depends_on"]):
            if dependency == unit["work_unit_id"]:
                errors.append(_finding("WORK_UNIT_DEPENDS_ON_ITSELF", f"{path}/depends_on/{dependency_index}"))
            elif dependency not in units:
                errors.append(_finding("WORK_UNIT_DEPENDENCY_UNKNOWN", f"{path}/depends_on/{dependency_index}"))
            else:
                dependencies.append(dependency)
        dependency_map[unit["work_unit_id"]] = dependencies

    indegree = {unit_id: len(deps) for unit_id, deps in dependency_map.items()}
    dependents: dict[str, list[str]] = {unit_id: [] for unit_id in units}
    for unit_id, deps in dependency_map.items():
        for dependency in deps:
            dependents[dependency].append(unit_id)
    ready = deque(sorted(unit_id for unit_id, degree in indegree.items() if degree == 0))
    visited = 0
    while ready:
        unit_id = ready.popleft()
        visited += 1
        for dependent in sorted(dependents[unit_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
    if visited != len(units):
        errors.append(_finding("WORK_UNIT_DEPENDENCY_CYCLE", "$/work_units"))

    for first_index, first in enumerate(plan["work_units"]):
        first_bindings = [
            bindings[binding_id]
            for binding_id in first["write_binding_ids"]
            if binding_id in bindings and bindings[binding_id]["exclusivity"] == "WRITE_EXCLUSIVE"
        ]
        first_domains = {binding["write_domain"] for binding in first_bindings}
        for second_index in range(first_index + 1, len(plan["work_units"])):
            second = plan["work_units"][second_index]
            second_domains = {
                bindings[binding_id]["write_domain"]
                for binding_id in second["write_binding_ids"]
                if binding_id in bindings and bindings[binding_id]["exclusivity"] == "WRITE_EXCLUSIVE"
            }
            if not first_domains.intersection(second_domains):
                continue
            if not (
                _contains_path(dependency_map, first["work_unit_id"], second["work_unit_id"])
                or _contains_path(dependency_map, second["work_unit_id"], first["work_unit_id"])
            ):
                errors.append(_finding("UNORDERED_EXCLUSIVE_WRITERS", f"$/work_units/{second_index}/write_binding_ids"))

    errors.sort(key=lambda item: (item["path"], item["code"]))
    warnings.sort(key=lambda item: (item["path"], item["code"]))
    return errors[:MAX_FINDINGS], warnings[:MAX_FINDINGS]


def validate_plan(plan: Any) -> dict[str, Any]:
    """Return declaration-consistency findings; never authorize or execute work."""
    if not isinstance(plan, dict):
        return {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": None,
            "status": "BINDING_PLAN_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": [_finding("INPUT_MUST_BE_OBJECT", "$")],
            "warnings": [],
            "execution_authorized": False,
            "runtime_enforcement_status": "NOT_EVALUATED",
            "claim_ceiling": CLAIM_CEILING,
        }

    schema_findings = _schema_findings(plan)
    if schema_findings:
        return {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": plan.get("episode_id") if isinstance(plan.get("episode_id"), str) else None,
            "status": "BINDING_PLAN_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": schema_findings,
            "warnings": [],
            "execution_authorized": False,
            "runtime_enforcement_status": "NOT_EVALUATED",
            "claim_ceiling": CLAIM_CEILING,
        }

    errors, warnings = _semantic_findings(plan)
    return {
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "episode_id": plan["episode_id"],
        "status": "BINDING_PLAN_DECLARATIONS_CONSISTENT" if not errors else "BINDING_PLAN_INVALID",
        "checks": {
            "input_schema": "PASS",
            "cross_reference_consistency": "PASS" if not errors else "FAIL",
            "aggregation_policy_interpretation": "NOT_EVALUATED",
            "runtime_enforcement": "NOT_EVALUATED",
        },
        "findings": errors,
        "warnings": warnings,
        "execution_authorized": False,
        "runtime_enforcement_status": "NOT_EVALUATED",
        "claim_ceiling": CLAIM_CEILING,
    }


def _read_stdin() -> Any:
    data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds the 262144-byte limit")
    text = data.decode("utf-8")
    return json.loads(text, object_pairs_hook=_unique_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON plan from stdin")
    parser.parse_args(argv)
    try:
        plan = _read_stdin()
        result = validate_plan(plan)
    except DuplicateJSONKey:
        result = {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": None,
            "status": "BINDING_PLAN_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": [_finding("DUPLICATE_JSON_KEY", "$")],
            "warnings": [],
            "execution_authorized": False,
            "runtime_enforcement_status": "NOT_EVALUATED",
            "claim_ceiling": CLAIM_CEILING,
        }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        result = {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": None,
            "status": "BINDING_PLAN_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": [_finding("INPUT_UNAVAILABLE_OR_INVALID", "$")],
            "warnings": [],
            "execution_authorized": False,
            "runtime_enforcement_status": "NOT_EVALUATED",
            "claim_ceiling": CLAIM_CEILING,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "BINDING_PLAN_DECLARATIONS_CONSISTENT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
