"""Human-readable Driver Console projection for OS Control Plane R2."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence


DRIVER_CONSOLE_SCHEMA = "os-control-plane-driver-console-r1"
DRIVER_RECOVERY_SURFACE_SCHEMA = "ignition-driver-recovery-surface-r2"
_FORBIDDEN = ("prompt", "chain-of-thought", "hidden reasoning", "api_key", "access_token", "authorization")


class DriverConsoleError(ValueError):
    """A console input is not a bounded public control-plane projection."""


def _public(value: Any, field: str, *, default: str = "not recorded") -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise DriverConsoleError(f"{field} must be a bounded public string")
    return value


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise DriverConsoleError(f"{field} must be an object")
    return value


def _count(mapping: Mapping[str, Any], key: str) -> int:
    value = mapping.get(key, 0)
    if not isinstance(value, int) or value < 0:
        raise DriverConsoleError(f"{key} count must be non-negative")
    return value


def build_driver_snapshot(sources: Mapping[str, Any]) -> dict[str, Any]:
    """Build a bounded machine snapshot from already-owned control surfaces."""

    if not isinstance(sources, Mapping):
        raise DriverConsoleError("console sources must be an object")
    scheduler = _mapping(sources.get("scheduler"), "scheduler")
    queue = _mapping(sources.get("queue"), "queue")
    health = _mapping(sources.get("health"), "health")
    resources = _mapping(sources.get("resources"), "resources")
    dispatch = _mapping(sources.get("dispatch"), "dispatch")
    memory = _mapping(sources.get("memory"), "memory")
    policy = _mapping(sources.get("policy"), "policy")
    terminal = _mapping(scheduler.get("terminal"), "scheduler.terminal")
    terminal_state = _public(terminal.get("state"), "terminal.state", default="RUNNING")
    queue_counts = _mapping(queue.get("state_counts"), "queue.state_counts")
    health_counts = _mapping(health.get("effective_status_counts"), "health.effective_status_counts")
    dispatch_counts = _mapping(dispatch.get("state_counts"), "dispatch.state_counts")
    outstanding: list[str] = []
    if _count(dispatch_counts, "REQUIRES_RECONCILIATION"):
        outstanding.append("external dispatch reconciliation is required")
    if _count(health_counts, "STALE") or _count(health_counts, "UNSAFE_TO_PROBE"):
        outstanding.append("one or more executor health leases cannot be used")
    if _count(resources, "waiting_count"):
        outstanding.append("resource conflicts are waiting for arbitration")
    if queue.get("paused"):
        outstanding.append("queue admission is paused")
    if _count(queue_counts, "EXPIRED_BEFORE_DISPATCH"):
        outstanding.append("queued work expired before dispatch")
    if memory.get("capsule_stale") is True:
        outstanding.append("an operational-memory capsule is stale")
    checkpointed = terminal_state == "CHECKPOINTED_RESUMABLE" or any(item.get("status") == "CHECKPOINTED_RESUMABLE" for item in scheduler.get("children", {}).values() if isinstance(item, Mapping))
    if checkpointed:
        outstanding.append("a checkpoint requires explicit resume")

    if _count(dispatch_counts, "REQUIRES_RECONCILIATION"):
        next_action = "Reconcile the ambiguous external dispatch before any side-effect retry."
    elif _count(health_counts, "STALE") or _count(health_counts, "UNSAFE_TO_PROBE"):
        next_action = "Refresh or replace the executor health lease before routing new work."
    elif _count(resources, "waiting_count"):
        next_action = "Inspect the declared resource conflict and wait for a safe lease boundary."
    elif queue.get("paused"):
        next_action = "Review the pause reason, then explicitly resume queue admission if authorized."
    elif checkpointed:
        next_action = "Review the checkpoint and explicitly resume the bounded scheduler."
    elif terminal_state != "RUNNING":
        next_action = "Retain the receipt and perform the independent validation/review still required by the task contract."
    else:
        next_action = "Admit the next ready item within policy, lease and budget ceilings."

    children = scheduler.get("children", {})
    if not isinstance(children, Mapping):
        raise DriverConsoleError("scheduler.children must be an object")
    child_states: dict[str, int] = {}
    for run_id, child in children.items():
        if not isinstance(run_id, str) or not isinstance(child, Mapping):
            raise DriverConsoleError("scheduler child projection is invalid")
        state = _public(child.get("status"), f"scheduler.children.{run_id}.status")
        child_states[state] = child_states.get(state, 0) + 1

    snapshot = {
        "schema": DRIVER_CONSOLE_SCHEMA,
        "overall_state": terminal_state,
        "episode_id": _public(scheduler.get("episode_id"), "scheduler.episode_id"),
        "next_action": next_action,
        "open_obligations": outstanding,
        "scheduler": {"child_state_counts": dict(sorted(child_states.items())), "max_concurrent_observed": scheduler.get("max_concurrent_observed", 0), "budget_usage": scheduler.get("budget_usage", {})},
        "queue": {"depth": queue.get("depth", 0), "paused": bool(queue.get("paused", False)), "state_counts": dict(sorted(queue_counts.items())), "backpressure_events": queue.get("backpressure_events", 0)},
        "route_health": {"effective_status_counts": dict(sorted(health_counts.items())), "lease_count": health.get("lease_count", 0)},
        "resources": {"active_count": resources.get("active_count", 0), "waiting_count": resources.get("waiting_count", 0), "unknown_side_effect_policy": _public(resources.get("unknown_side_effect_policy"), "resources.unknown_side_effect_policy")},
        "dispatch": {"state_counts": dict(sorted(dispatch_counts.items())), "record_count": dispatch.get("record_count", 0)},
        "memory": {"generation": memory.get("generation", 0), "active_count": memory.get("active_count", 0), "capsule_stale": bool(memory.get("capsule_stale", False))},
        "policy": {"digest": _public(policy.get("digest"), "policy.digest"), "status": _public(policy.get("status"), "policy.status"), "claim_ceiling": _public(policy.get("claim_ceiling"), "policy.claim_ceiling")},
        "boundaries": [
            "This console summarizes owned control-plane records; it is not a second truth source.",
            "It cannot establish external executor success, knowledge truth, Owner acceptance or epistemic acceptance.",
            "External side effects remain reconciliation-bound and policy remains monotonic/narrowing.",
        ],
    }
    return snapshot


def render_driver_console(snapshot: Mapping[str, Any]) -> str:
    if not isinstance(snapshot, Mapping) or snapshot.get("schema") != DRIVER_CONSOLE_SCHEMA:
        raise DriverConsoleError("invalid Driver Console snapshot")
    obligations = snapshot.get("open_obligations") or ["none recorded"]
    if not isinstance(obligations, Sequence) or isinstance(obligations, (str, bytes)):
        raise DriverConsoleError("open_obligations must be a list")
    queue = _mapping(snapshot.get("queue"), "snapshot.queue")
    route = _mapping(snapshot.get("route_health"), "snapshot.route_health")
    resources = _mapping(snapshot.get("resources"), "snapshot.resources")
    dispatch = _mapping(snapshot.get("dispatch"), "snapshot.dispatch")
    memory = _mapping(snapshot.get("memory"), "snapshot.memory")
    policy = _mapping(snapshot.get("policy"), "snapshot.policy")
    lines = [
        "Driver Console — OS Control Plane R2",
        f"Overall: {snapshot.get('overall_state')} (episode={snapshot.get('episode_id')})",
        f"Next action: {snapshot.get('next_action')}",
        f"Queue: depth={queue.get('depth')} paused={queue.get('paused')} states={json.dumps(queue.get('state_counts', {}), ensure_ascii=False, sort_keys=True)}",
        f"Route/health: leases={route.get('lease_count')} effective_states={json.dumps(route.get('effective_status_counts', {}), ensure_ascii=False, sort_keys=True)}",
        f"Resources: active={resources.get('active_count')} waiting_conflicts={resources.get('waiting_count')} unknown-side-effect-policy={resources.get('unknown_side_effect_policy')}",
        f"Dispatch: records={dispatch.get('record_count')} states={json.dumps(dispatch.get('state_counts', {}), ensure_ascii=False, sort_keys=True)}",
        f"Operational memory: generation={memory.get('generation')} active={memory.get('active_count')} capsule_stale={memory.get('capsule_stale')}",
        f"Policy: status={policy.get('status')} digest={policy.get('digest')}",
        "Open obligations:",
        *[f"- {item}" for item in obligations],
        "Boundary: this is a control-plane projection; it cannot establish external success, truth, Owner acceptance or epistemic acceptance.",
    ]
    return "\n".join(lines)


def _public_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) or not item.strip() or any(marker in item.casefold() for marker in _FORBIDDEN) for item in value):
        raise DriverConsoleError(f"{field} must be a public string list")
    return sorted(set(value))


def _state_counts(value: Any, field: str) -> dict[str, int]:
    mapping = _mapping(value, field)
    result: dict[str, int] = {}
    for key, count in mapping.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(count, int) or count < 0:
            raise DriverConsoleError(f"{field} contains an invalid state count")
        result[key] = count
    return dict(sorted(result.items()))


def build_driver_recovery_surface(sources: Mapping[str, Any]) -> dict[str, Any]:
    """Build the human-first R2 recovery projection from owned records only."""

    if not isinstance(sources, Mapping):
        raise DriverConsoleError("recovery surface sources must be an object")
    recovery = _mapping(sources.get("recovery"), "recovery")
    operator_state = _mapping(recovery.get("operator_recovery_state"), "recovery.operator_recovery_state")
    snapshot = _mapping(recovery.get("snapshot"), "recovery.snapshot")
    if not snapshot:
        snapshot = _mapping(sources.get("trusted_snapshot"), "trusted_snapshot")
    schema_epoch = _public(sources.get("schema_epoch", recovery.get("migration", {}).get("to_epoch", "os-durability-r1")), "schema_epoch")
    os_identity = _public(sources.get("os_identity", "OS_CONTROL_PLANE"), "os_identity")
    last_known_good = _mapping(sources.get("last_known_good"), "last_known_good")
    episode_states = sources.get("episode_states", {})
    if not isinstance(episode_states, Mapping):
        raise DriverConsoleError("episode_states must be an object")
    episode_counts: dict[str, int] = {}
    for episode_id, state in episode_states.items():
        if not isinstance(episode_id, str) or not episode_id.strip():
            raise DriverConsoleError("episode id is invalid")
        state = _public(state, f"episode_states.{episode_id}")
        episode_counts[state] = episode_counts.get(state, 0) + 1

    pack_state = _mapping(sources.get("packs"), "packs")
    active_packs = _public_list(pack_state.get("active_versions", recovery.get("namespace_policy_pack", {}).get("packs", {}).get("active", [])), "packs.active_versions")
    executor = _mapping(sources.get("executors", recovery.get("admission")), "executors")
    health = _mapping(sources.get("health", recovery.get("leases")), "health")
    revocation = _mapping(sources.get("revocation"), "revocation")
    accounting = _mapping(sources.get("accounting", recovery.get("accounting")), "accounting")
    budget_pressure = _mapping(sources.get("budget_pressure"), "budget_pressure")
    unresolved = _public_list(sources.get("unresolved_recovery_items", recovery.get("uncertain_dispatch_refs", operator_state.get("unresolved_reconciliation_refs", []))), "unresolved_recovery_items")
    namespace_anomalies = _public_list(sources.get("namespace_delegation_anomalies"), "namespace_delegation_anomalies")
    soft = _mapping(sources.get("soft_governance", operator_state.get("soft_governance")), "soft_governance")
    soft_status = _public(soft.get("status", "ADVISORY_ONLY"), "soft_governance.status")
    if soft_status not in {"ADVISORY_ONLY", "CANDIDATE_ESI_SIGNAL", "READY_NOT_RUN", "NOT_RUN_LIVE_EXTERNAL", "WITHDRAWN"}:
        raise DriverConsoleError("soft governance status must remain advisory/candidate")
    authority_effects = soft.get("authority_effects", ["NONE"])
    if not isinstance(authority_effects, list) or any(effect != "NONE" for effect in authority_effects):
        raise DriverConsoleError("soft governance projection attempts a hard authority effect")
    claim_ceiling = _public(soft.get("claim_ceiling", "ADVISORY_ONLY_CANDIDATE_NOT_TRUTH_OR_AUTHORITY"), "soft_governance.claim_ceiling")
    if not any(word in claim_ceiling.casefold() for word in ("advisory", "candidate", "soft")):
        raise DriverConsoleError("soft governance claim ceiling is not advisory")
    technical_refs = _public_list(sources.get("technical_refs"), "technical_refs")

    if unresolved:
        recommended = ["先处理 unresolved reconciliation，再考虑任何外部副作用重试。"]
    elif namespace_anomalies:
        recommended = ["检查 namespace/delegation 异常，并在显式授权前保持跨 namespace deny。"]
    elif budget_pressure.get("status") in {"PRESSURED", "EXHAUSTED"}:
        recommended = ["检查 quota/budget pressure；priority 不构成无限抢占或预算豁免。"]
    else:
        recommended = ["仅在当前 policy、lease、Pack pin 与 budget ceiling 内继续 bounded local work。"]
    recommended.extend(_public_list(sources.get("additional_operator_actions"), "additional_operator_actions"))

    surface = {
        "schema": DRIVER_RECOVERY_SURFACE_SCHEMA,
        "human_summary": "系统恢复 projection 已生成；它显示当前可继续范围与未决项，不替代 Event Ledger 或 Owner 判断。",
        "os_identity": os_identity,
        "schema_epoch": schema_epoch,
        "recovery_status": _public(recovery.get("status", "NOT_RECORDED"), "recovery.status"),
        "trusted_snapshot": {"id": _public(snapshot.get("id", operator_state.get("trusted_snapshot", "not-recorded")), "trusted_snapshot.id"), "tail_events": snapshot.get("tail_events", recovery.get("ledger_tail_events", 0))},
        "last_known_good": dict(last_known_good),
        "episodes": {"state_counts": dict(sorted(episode_counts.items())), "running": episode_counts.get("RUNNING", 0), "queued": episode_counts.get("QUEUED", 0), "paused": episode_counts.get("PAUSED", 0), "reconciliation": episode_counts.get("REQUIRES_RECONCILIATION", 0)},
        "active_pack_versions": active_packs,
        "executors": {"admission": dict(executor), "health": dict(health), "revocation": dict(revocation)},
        "budget_quota_pressure": {"pressure": dict(budget_pressure), "accounting": {key: accounting[key] for key in sorted(accounting) if key in {"status", "reservation_count", "event_count", "dimension_count"}}},
        "unresolved_recovery_items": unresolved,
        "namespace_delegation_anomalies": namespace_anomalies,
        "soft_governance": {"status": soft_status, "candidate_or_advisory": True, "authority_effects": ["NONE"], "claim_ceiling": claim_ceiling, "pointers": _public_list(soft.get("pointers"), "soft_governance.pointers")},
        "recommended_operator_actions": recommended,
        "technical_refs": technical_refs,
        "boundaries": ["Projection only; Event Ledger and owned stores remain canonical.", "Soft governance/ESI remains advisory or candidate and cannot establish truth, permission, safety release, Owner acceptance or epistemic acceptance.", "External executor completion and unknown side effects remain reconciliation-bound."],
    }
    return surface


def render_driver_recovery_surface(surface: Mapping[str, Any]) -> str:
    if not isinstance(surface, Mapping) or surface.get("schema") != DRIVER_RECOVERY_SURFACE_SCHEMA:
        raise DriverConsoleError("invalid Driver Recovery Surface")
    trusted = _mapping(surface.get("trusted_snapshot"), "surface.trusted_snapshot")
    soft = _mapping(surface.get("soft_governance"), "surface.soft_governance")
    lines = [
        "Driver Recovery Surface R2",
        f"人话：{surface.get('human_summary')}",
        f"OS identity/schema: {surface.get('os_identity')} / {surface.get('schema_epoch')}",
        f"恢复状态: {surface.get('recovery_status')}; trusted snapshot={trusted.get('id')} tail_events={trusted.get('tail_events')}",
        f"Active Packs: {', '.join(surface.get('active_pack_versions') or ['none recorded'])}",
        f"Episodes: {json.dumps(surface.get('episodes', {}), ensure_ascii=False, sort_keys=True)}",
        f"Unresolved recovery items: {', '.join(surface.get('unresolved_recovery_items') or ['none recorded'])}",
        f"Soft governance/ESI: status={soft.get('status')} candidate_or_advisory={soft.get('candidate_or_advisory')} claim_ceiling={soft.get('claim_ceiling')}",
        "Recommended operator actions:",
        *[f"- {item}" for item in surface.get("recommended_operator_actions", [])],
        "Technical records:",
        *[f"- {item}" for item in surface.get("technical_refs", [])],
        "Boundary: this is a projection, not a second canonical state; it cannot establish external success, truth, Owner acceptance or epistemic acceptance.",
    ]
    return "\n".join(lines)


__all__ = ["DRIVER_CONSOLE_SCHEMA", "DRIVER_RECOVERY_SURFACE_SCHEMA", "DriverConsoleError", "build_driver_snapshot", "render_driver_console", "build_driver_recovery_surface", "render_driver_recovery_surface"]
