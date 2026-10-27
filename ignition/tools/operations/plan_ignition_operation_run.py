#!/usr/bin/env python3
"""Plan an Ignition operation run through the canonical lifecycle gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from classify_ignition_run_mode import ModeRoutingError, classify_mode  # noqa: E402


REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
PLAYBOOKS_PATH = "ignition/data/operations/ignition-operation-playbooks-r1.json"
OUTPUT_CONTRACT_PATH = "ignition/data/operations/ignition-run-output-contract-r1.json"
EXPERIMENTAL_TOOL_CARDS_PATH = ROOT / "data/operations/toolbox-candidate-cards-r0.json"
FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/lifecycle-planning-r1.json"
CORE_CURRENT_READS = (
    "ignition/OPERATING-METHOD.md",
    "ignition/AI-START-HERE.md",
    "ignition/data/architecture/current-facts.json",
    "ignition/data/operations/current-snapshot-r1.json",
    "ignition/data/operations/ignition-operation-capability-registry-r1.json",
    OUTPUT_CONTRACT_PATH,
)
LIFECYCLE_STAGES = (
    "ACCEPT_REQUEST",
    "FREEZE_CURRENT",
    "CLASSIFY_MODE",
    "CLASSIFY_INPUT_OBJECT",
    "RESOLVE_OPERATION",
    "CHECK_CAPABILITY_STATUS",
    "BUILD_MINIMAL_READ_PLAN",
    "NORMALIZE_INPUT_AND_PROVENANCE",
    "EXECUTE_OPERATION",
    "CANONICAL_COLLISION / EVIDENCE CHECK",
    "ADVERSARIAL_REVIEW",
    "APPLY_CLAIM_CEILING",
    "RENDER_RESULT",
    "STOP / HANDOFF",
)
NETWORK_HOST_RE = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
MAX_NETWORK_HOSTS = 16
STATUS_DECISIONS = {
    "CURRENT": ("PROCEED", None),
    "CURRENT_BOUNDED": ("PROCEED_BOUNDED", None),
    "OWNER_DEFERRED": ("STOP", "CAPABILITY_OWNER_DEFERRED"),
    "REFERENCE_ONLY": ("STOP", "CAPABILITY_REFERENCE_ONLY"),
    "HISTORICAL": ("STOP", "CAPABILITY_NOT_CURRENT"),
    "UNSUPPORTED": ("STOP", "UNSUPPORTED_OPERATION"),
}
ROUTE_MODES = {"READ_ONLY_RUN", "REPOSITORY_CHANGE_RUN", "EXTERNAL_ACTION_RUN"}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def route_source_path_is_safe(relative_path: str) -> bool:
    """Accept only existing, non-symlink repository paths used by an opt-in card."""
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        return False
    parts = Path(relative_path).parts
    if any(part in {".", ".."} for part in parts):
        return False
    repo_root = ROOT.parent.resolve()
    candidate = repo_root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return False
    if not candidate.exists():
        return False
    if candidate.is_dir():
        for item in candidate.rglob("*"):
            if item.is_symlink():
                return False
    return True


def route_network_host_is_safe(host: str) -> bool:
    """Accept one exact lowercase DNS host; reject URLs, ports, IPs, and wildcards."""
    return (
        isinstance(host, str)
        and len(host) <= 253
        and NETWORK_HOST_RE.fullmatch(host) is not None
        and any(char.isalpha() for char in host)
    )


class RunPlanningError(ValueError):
    """Raised when a run plan request is structurally invalid."""


def _route_strings(value: Any, field: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise RunPlanningError(f"{field} must be a {'nonempty ' if nonempty else ''}array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise RunPlanningError(f"{field} must contain nonblank strings")
    if len(value) != len(set(value)):
        raise RunPlanningError(f"{field} must not contain duplicates")
    return list(value)


def plan_tool_route(task_profile: dict[str, Any], *, include_experimental_tool_ids: list[str] | None = None) -> dict[str, Any]:
    """Select a sufficient set of declared operations for exact typed outputs.

    This is an extension of the existing operation planner: it reads the same
    canonical operation registry and can add only explicitly named experimental
    candidates. It proposes operation IDs; it never invokes them or grants
    authority. Selection is coverage-first and does not claim a global optimum.
    """
    expected_keys = {"task_id", "current_ref", "input_types", "required_outputs", "allowed_execution_modes"}
    extended_keys = expected_keys | {"allowed_network_hosts"}
    if not isinstance(task_profile, dict) or set(task_profile) not in (expected_keys, extended_keys):
        raise RunPlanningError(f"task profile keys must be exactly {sorted(expected_keys)} with optional allowed_network_hosts")
    for field in ("task_id", "current_ref"):
        if not isinstance(task_profile[field], str) or not task_profile[field].strip():
            raise RunPlanningError(f"{field} must be a nonblank string")
    inputs = set(_route_strings(task_profile["input_types"], "input_types"))
    required_outputs = _route_strings(task_profile["required_outputs"], "required_outputs")
    allowed_modes = set(_route_strings(task_profile["allowed_execution_modes"], "allowed_execution_modes"))
    if not allowed_modes <= ROUTE_MODES:
        raise RunPlanningError("allowed_execution_modes contains an unknown mode")
    allowed_network_hosts = _route_strings(
        task_profile.get("allowed_network_hosts", []), "allowed_network_hosts", nonempty=False,
    )
    if len(allowed_network_hosts) > MAX_NETWORK_HOSTS:
        raise RunPlanningError(f"allowed_network_hosts must contain no more than {MAX_NETWORK_HOSTS} entries")
    if any(not route_network_host_is_safe(host) for host in allowed_network_hosts):
        raise RunPlanningError("allowed_network_hosts must contain exact lowercase DNS names without schemes, ports, IPs, or wildcards")
    include_ids = _route_strings(include_experimental_tool_ids or [], "include_experimental_tool_ids", nonempty=False)

    registry_bytes = REGISTRY_PATH.read_bytes()
    candidate_bytes = EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()
    registry = json.loads(registry_bytes.decode("utf-8"))
    candidate_doc = json.loads(candidate_bytes.decode("utf-8"))
    registry_blob = git_blob_sha1(registry_bytes)
    candidate_blob = git_blob_sha1(candidate_bytes)
    if candidate_doc.get("source_registry_path") != "ignition/data/operations/ignition-operation-capability-registry-r1.json":
        raise RunPlanningError("experimental tool cards point at a different Current operation registry")
    if candidate_doc.get("source_registry_blob_sha1") != registry_blob:
        raise RunPlanningError("experimental tool cards are stale against the checked Current registry")
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for operation in registry["operations"]:
        tool_id = operation["operation_id"]
        if operation["current_status"] not in {"CURRENT", "CURRENT_BOUNDED"}:
            rejected.append({"tool_id": tool_id, "reason": "NOT_CURRENT_CALLABLE"})
            continue
        if operation["ai_callability"] == "STATUS_ONLY":
            rejected.append({"tool_id": tool_id, "reason": "STATUS_ONLY"})
            continue
        if operation["external_action_permission"] != "FORBIDDEN":
            rejected.append({"tool_id": tool_id, "reason": "EXTERNAL_ACTION_NOT_ADMITTED"})
            continue
        if operation["default_execution_mode"] not in allowed_modes:
            rejected.append({"tool_id": tool_id, "reason": "EXECUTION_MODE_NOT_ALLOWED"})
            continue
        if not inputs.intersection(operation["accepted_input_types"]):
            rejected.append({"tool_id": tool_id, "reason": "NO_INPUT_TYPE_MATCH"})
            continue
        candidates.append({
            "tool_id": tool_id,
            "kind": "REGISTERED_OPERATION",
            "availability": operation["current_status"],
            "input_types": operation["accepted_input_types"],
            "output_types": operation["output_types"],
            "execution_mode": operation["default_execution_mode"],
            "permission_mode": operation["repository_mutation_permission"],
            "external_action_permission": operation["external_action_permission"],
            "explicit_owner_authorization_required": operation["explicit_owner_authorization_required"],
            "declared_effect_rank": int(
                operation["repository_mutation_permission"] != "FORBIDDEN"
                or operation["external_action_permission"] != "FORBIDDEN"
                or operation["explicit_owner_authorization_required"]
            ),
            "pre_invocation_conditions": sorted(set(
                operation["required_current_reads"]
                + operation["applicable_governance"]
                + [check["path"] for check in operation["validation_checks"]]
            )),
            "dependencies": sorted(set(
                [source["path"] for source in operation["authoritative_sources"]]
                + operation["required_current_reads"]
                + operation["applicable_governance"]
            )),
            "claim_ceiling": operation["claim_ceiling"],
        })

    candidate_entries = candidate_doc.get("candidates") if isinstance(candidate_doc, dict) else None
    if not isinstance(candidate_entries, list):
        raise RunPlanningError("experimental tool card source must contain candidates")
    seen_candidate_ids: set[str] = set()
    for card in candidate_entries:
        if not isinstance(card, dict) or not isinstance(card.get("tool_id"), str):
            raise RunPlanningError("experimental tool card has no stable tool_id")
        tool_id = card["tool_id"]
        if tool_id in seen_candidate_ids:
            raise RunPlanningError("experimental tool IDs must be unique")
        seen_candidate_ids.add(tool_id)
        if tool_id not in include_ids:
            rejected.append({"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"})
            continue
        if card.get("availability") != "EXPERIMENTAL_AVAILABLE":
            rejected.append({"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_AVAILABLE"})
            continue
        if card.get("router_selectable_by_default") is not False:
            raise RunPlanningError(f"experimental card must default off: {tool_id}")
        source_path = card.get("source_path")
        if not route_source_path_is_safe(source_path):
            rejected.append({"tool_id": tool_id, "reason": "IMPLEMENTATION_SOURCE_UNAVAILABLE_OR_UNSAFE"})
            continue
        source_refs = card.get("source_refs")
        if not isinstance(source_refs, list) or any(
            not isinstance(reference, dict) or not route_source_path_is_safe(reference.get("path"))
            for reference in source_refs
        ):
            rejected.append({"tool_id": tool_id, "reason": "SOURCE_REFERENCE_UNAVAILABLE_OR_UNSAFE"})
            continue
        dependencies = card.get("dependencies")
        ref_paths = {reference["path"] for reference in source_refs}
        if not isinstance(dependencies, list) or any(not isinstance(path, str) for path in dependencies) or not set(dependencies) <= ref_paths:
            rejected.append({"tool_id": tool_id, "reason": "DEPENDENCY_NOT_PINNED_BY_SOURCE_REFERENCE"})
            continue
        if tool_id == "ignition.adaptive_toolbox_route_planner":
            rejected.append({"tool_id": tool_id, "reason": "ROUTE_PLANNER_IS_NOT_A_TASK_OPERATION"})
            continue
        if card.get("execution_mode") not in allowed_modes:
            rejected.append({"tool_id": tool_id, "reason": "EXECUTION_MODE_NOT_ALLOWED"})
            continue
        permissions = card.get("permissions")
        permission_keys = {"read_paths", "write_paths", "network", "secrets", "billing", "external_actions"}
        if not isinstance(permissions, dict) or not permission_keys <= set(permissions):
            rejected.append({"tool_id": tool_id, "reason": "PERMISSION_CARD_MISSING"})
            continue
        if any(type(permissions[key]) is not bool for key in ("network", "secrets", "billing", "external_actions")):
            rejected.append({"tool_id": tool_id, "reason": "PERMISSION_CARD_INVALID"})
            continue
        if any(not isinstance(permissions[key], list) or any(not isinstance(path, str) or not route_source_path_is_safe(path) for path in permissions[key]) for key in ("read_paths", "write_paths")):
            rejected.append({"tool_id": tool_id, "reason": "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"})
            continue
        network_hosts = permissions.get("network_hosts", [])
        if not isinstance(network_hosts, list) or len(network_hosts) > MAX_NETWORK_HOSTS or any(not route_network_host_is_safe(host) for host in network_hosts):
            rejected.append({"tool_id": tool_id, "reason": "PERMISSION_NETWORK_HOSTS_INVALID"})
            continue
        if permissions["network"] is not True and network_hosts:
            rejected.append({"tool_id": tool_id, "reason": "PERMISSION_NETWORK_HOSTS_CONFLICT"})
            continue
        if permissions["network"] is True and not network_hosts:
            rejected.append({"tool_id": tool_id, "reason": "PERMISSION_NETWORK_HOSTS_MISSING"})
            continue
        if type(card.get("explicit_owner_authorization_required")) is not bool:
            rejected.append({"tool_id": tool_id, "reason": "OWNER_AUTHORIZATION_CARD_MISSING"})
            continue
        if card["execution_mode"] == "READ_ONLY_RUN" and any((
            bool(permissions.get("write_paths")),
            permissions.get("secrets") is not False,
            permissions.get("billing") is not False,
            permissions.get("external_actions") is not False,
        )):
            rejected.append({"tool_id": tool_id, "reason": "READ_ONLY_PERMISSION_CONFLICT"})
            continue
        if permissions["network"] is True and not set(network_hosts) <= set(allowed_network_hosts):
            rejected.append({"tool_id": tool_id, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"})
            continue
        accepted = _route_strings(card.get("accepted_input_types"), f"{tool_id}.accepted_input_types")
        outputs = _route_strings(card.get("output_types"), f"{tool_id}.output_types")
        only_if = _route_strings(card.get("only_if"), f"{tool_id}.only_if")
        router_conditions = _route_strings(card.get("router_conditions"), f"{tool_id}.router_conditions")
        if not isinstance(card.get("claim_ceiling"), str) or not card["claim_ceiling"].strip():
            raise RunPlanningError(f"experimental card claim ceiling is missing: {tool_id}")
        if not inputs.intersection(accepted):
            rejected.append({"tool_id": tool_id, "reason": "NO_INPUT_TYPE_MATCH"})
            continue
        candidates.append({
            "tool_id": tool_id,
            "kind": "EXPERIMENTAL_OPTIONAL_TOOL",
            "availability": card["availability"],
            "input_types": accepted,
            "output_types": outputs,
            "execution_mode": card["execution_mode"],
            "permission_mode": card.get("permission_mode", "UNKNOWN"),
            "permissions": permissions,
            "explicit_owner_authorization_required": card["explicit_owner_authorization_required"],
            "dependencies": dependencies,
            "declared_effect_rank": int(any((
                bool(permissions.get("write_paths")),
                permissions.get("network") is not False,
                permissions.get("secrets") is not False,
                permissions.get("billing") is not False,
                permissions.get("external_actions") is not False,
            ))),
            "pre_invocation_conditions": sorted(set(only_if + router_conditions)),
            "claim_ceiling": card["claim_ceiling"],
        })

    for unknown_id in sorted(set(include_ids) - seen_candidate_ids):
        rejected.append({"tool_id": unknown_id, "reason": "UNKNOWN_EXPERIMENTAL_ALLOWLIST_ID"})

    remaining = set(required_outputs)
    selected: list[dict[str, Any]] = []
    while remaining:
        useful = []
        for candidate in candidates:
            if any(row["tool_id"] == candidate["tool_id"] for row in selected):
                continue
            coverage = remaining.intersection(candidate["output_types"])
            if coverage:
                mode_rank = {"READ_ONLY_RUN": 0, "REPOSITORY_CHANGE_RUN": 1, "EXTERNAL_ACTION_RUN": 2}.get(candidate["execution_mode"], 3)
                effect_rank = candidate["declared_effect_rank"]
                useful.append((-len(coverage), mode_rank, effect_rank, candidate["tool_id"], candidate, coverage))
        if not useful:
            break
        useful.sort(key=lambda row: row[:4])
        chosen = useful[0][4]
        coverage = sorted(useful[0][5])
        selected.append({**chosen, "covers_required_outputs": coverage})
        remaining.difference_update(coverage)

    covered = sorted(set(required_outputs) - remaining)
    selected_ids = {row["tool_id"] for row in selected}
    skipped_candidates = []
    for candidate in candidates:
        if candidate["tool_id"] in selected_ids:
            continue
        overlaps_required = bool(set(candidate["output_types"]).intersection(required_outputs))
        skipped_candidates.append({
            "tool_id": candidate["tool_id"],
            "reason": "NO_INCREMENTAL_REQUIRED_OUTPUT" if overlaps_required else "NO_REQUIRED_OUTPUT_MATCH",
        })
    decision = "COMPLETE" if not remaining else "INCOMPLETE"
    return {
        "schema_version": "ignition-tool-route-plan-r0",
        "task_id": task_profile["task_id"],
        "current_ref": task_profile["current_ref"],
        "current_ref_binding": "CALLER_SUPPLIED_NOT_RESOLVED_BY_THIS_PLANNER",
        "allowed_network_hosts": allowed_network_hosts,
        "network_authority_binding": "CALLER_SUPPLIED_NOT_AUTHORITY_VERIFIED_BY_THIS_PLANNER" if allowed_network_hosts else "NO_NETWORK_HOSTS_ALLOWED",
        "decision": decision,
        "selected_tools": selected,
        "required_outputs": required_outputs,
        "covered_outputs": covered,
        "unmet_outputs": sorted(remaining),
        "rejected_candidates": sorted(rejected, key=lambda row: (row["tool_id"], row["reason"])),
        "skipped_candidates": sorted(skipped_candidates, key=lambda row: (row["tool_id"], row["reason"])),
        "selection_rule": "COVER_REQUIRED_OUTPUTS_THEN_MINIMIZE_ADDED_PERMISSION; GREEDY_NOT_PROVEN_GLOBAL_OPTIMUM",
        "cost_estimate": {"status": "UNKNOWN", "reason": "No comparable measured cost data is declared for the candidate operations."},
        "expansion_rule": "Add another tool only when a verified result leaves a required output or quality check unmet; preserve prior failures and permissions.",
        "execution_authorized": False,
        "claim_ceiling": "Typed route proposal from the checked local operation registry and optional cards only; the caller-supplied current_ref and allowed_network_hosts are echoed but not authority-verified; no tool invocation, permission grant, Owner approval, scientific validity or Current promotion is established.",
        "source_refs": {
            "current_registry_git_blob_sha1": registry_blob,
            "experimental_candidate_catalog_git_blob_sha1": candidate_blob,
        },
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def plan_run(request: dict[str, Any], operation_id: str, current_ref: str) -> dict[str, Any]:
    if not isinstance(operation_id, str) or not operation_id:
        raise RunPlanningError("operation_id must be a nonblank string")
    if not isinstance(current_ref, str) or not current_ref:
        raise RunPlanningError("current_ref must be a nonblank string")
    try:
        mode = classify_mode(request)
    except ModeRoutingError as exc:
        raise RunPlanningError(str(exc)) from exc

    registry = load_json(REGISTRY_PATH)
    operation = next((row for row in registry["operations"] if row["operation_id"] == operation_id), None)
    if operation is None:
        return {
            "lifecycle": list(LIFECYCLE_STAGES),
            "current_ref": current_ref,
            "run_mode": mode["mode"],
            "operation_id": operation_id,
            "operation_status": "UNREGISTERED",
            "decision": "STOP",
            "stop_reason": "UNSUPPORTED_OPERATION",
            "minimal_read_plan": list(CORE_CURRENT_READS),
            "output_contract_source": OUTPUT_CONTRACT_PATH,
            "side_effects_authorized_by_plan": False,
        }

    decision, stop_reason = STATUS_DECISIONS[operation["current_status"]]
    expected_mode = operation["default_execution_mode"]
    if expected_mode in {"REPOSITORY_CHANGE_RUN", "EXTERNAL_ACTION_RUN"} and mode["mode"] != expected_mode:
        decision = "STOP"
        stop_reason = "OPERATION_MODE_MISMATCH"
    if mode["reason_code"] == "STOP_SPLIT_OR_CLARIFY":
        decision = "STOP"
        stop_reason = "STOP_SPLIT_OR_CLARIFY"

    callable_playbook_reads = [PLAYBOOKS_PATH] if operation["current_status"] in {"CURRENT", "CURRENT_BOUNDED"} else []
    reads = _dedupe(
        list(CORE_CURRENT_READS)
        + callable_playbook_reads
        + operation["required_current_reads"]
        + [source["path"] for source in operation["authoritative_sources"]]
        + operation["applicable_governance"]
        + [check["path"] for check in operation["validation_checks"]]
    )
    return {
        "lifecycle": list(LIFECYCLE_STAGES),
        "current_ref": current_ref,
        "run_mode": mode["mode"],
        "mode_reason": mode["reason_code"],
        "operation_id": operation_id,
        "operation_status": operation["current_status"],
        "operation_class": operation["operation_class"],
        "decision": decision,
        "stop_reason": stop_reason,
        "minimal_read_plan": reads,
        "operation_claim_ceiling": operation["claim_ceiling"],
        "known_limits": operation["known_limits"],
        "playbook_source": PLAYBOOKS_PATH if callable_playbook_reads else None,
        "output_contract_source": OUTPUT_CONTRACT_PATH,
        "side_effects_authorized_by_plan": False,
    }


def validate_fixtures(document: dict[str, Any] | None = None) -> list[str]:
    fixtures = document if document is not None else load_json(FIXTURE_PATH)
    errors: list[str] = []
    cases = fixtures.get("cases", []) if isinstance(fixtures, dict) else []
    if not isinstance(cases, list) or not cases:
        return ["lifecycle fixture cases must be a nonempty array"]
    case_ids: list[str] = []
    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str):
            errors.append("every lifecycle fixture must have a case_id")
            continue
        case_ids.append(case_id)
        try:
            actual = plan_run(case["request"], case["operation_id"], case["current_ref"])
        except (KeyError, RunPlanningError) as exc:
            errors.append(f"{case_id}: planner error: {exc}")
            continue
        for key, expected in case.get("expected", {}).items():
            if actual.get(key) != expected:
                errors.append(f"{case_id}: {key} expected {expected!r}, got {actual.get(key)!r}")
        if actual["minimal_read_plan"][: len(CORE_CURRENT_READS)] != list(CORE_CURRENT_READS):
            errors.append(f"{case_id}: minimum read plan does not start with the canonical core")
        if len(actual["minimal_read_plan"]) != len(set(actual["minimal_read_plan"])):
            errors.append(f"{case_id}: minimum read plan contains duplicates")
        if actual["side_effects_authorized_by_plan"]:
            errors.append(f"{case_id}: planning cannot authorize side effects")
    if len(case_ids) != len(set(case_ids)):
        errors.append("lifecycle fixture case ids must be unique")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--check-fixtures", action="store_true")
    selection.add_argument("--route-request", action="store_true", help="read a JSON task profile from stdin for a read-only route proposal")
    parser.add_argument("--allow-experimental", action="append", default=[], help="explicitly include an experimental tool ID; may be repeated")
    args = parser.parse_args()
    if args.route_request:
        try:
            task_profile = json.load(sys.stdin)
            result = plan_tool_route(task_profile, include_experimental_tool_ids=args.allow_experimental)
        except (OSError, json.JSONDecodeError, RunPlanningError) as exc:
            print(json.dumps({"decision": "INVALID_REQUEST", "error": str(exc)}, ensure_ascii=False, indent=2))
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["decision"] == "COMPLETE" else 2
    errors = validate_fixtures()
    if errors:
        print("IGNITION_OPERATION_LIFECYCLE_FIXTURES_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    cases = load_json(FIXTURE_PATH)["cases"]
    print(f"IGNITION_OPERATION_LIFECYCLE_FIXTURES_OK cases={len(cases)} stages={len(LIFECYCLE_STAGES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
