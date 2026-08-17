"""Human-readable Driver Console projection for OS Control Plane R2."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence


DRIVER_CONSOLE_SCHEMA = "os-control-plane-driver-console-r1"
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


__all__ = ["DRIVER_CONSOLE_SCHEMA", "DriverConsoleError", "build_driver_snapshot", "render_driver_console"]
