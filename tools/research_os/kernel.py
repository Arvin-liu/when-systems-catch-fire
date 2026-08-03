"""Research Episode State Kernel (Checkpoint B).

A resumable, versioned episode record with an append-only event log. State
transitions are validated against the state machine in
data/research-os/episode-states.json. A report file, word count, elapsed time or
round count NEVER alone causes a terminal transition.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import registries as R


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ALLOWED_NEXT = {
    s: list(meta["allowed_next"]) for s, meta in R.episode_states()["states"].items()
}


def new_episode(
    episode_id: str,
    question_version: str,
    research_type: str,
    strategy_pack: str,
    budgets: dict[str, Any] | None = None,
) -> dict:
    """Create a fresh episode in INTAKE state with an empty append-only log."""
    now = _now()
    ep: dict[str, Any] = {
        "episode_id": episode_id,
        "question_version": question_version,
        "research_type": research_type,
        "strategy_pack": strategy_pack,
        "state": "INTAKE",
        "state_lineage": [],
        "candidate_claims": [],
        "evidence_obligations": [],
        "source_identities": [],
        "independence_groups": [],
        "access_levels": [],
        "calculations_required": [],
        "calculations_completed": [],
        "competing_explanations": [],
        "negative_evidence_search_state": {"searched": False, "results": []},
        "unresolved_residues": [],
        "blockers": [],
        "budgets": budgets or {},
        "current_diagnosis": None,
        "candidate_next_actions": [],
        "selected_action": None,
        "observations": [],
        "information_delta": None,
        "stop_conditions": {},
        "branch_conditions": {},
        "rollback_conditions": {},
        "escalation_conditions": {},
        "provenance": {},
        "versions": {"schema": "research-os/0.1"},
        "event_log": [],
        "created_at": now,
        "updated_at": now,
    }
    _append_event(ep, "state_transition", {"from": None, "to": "INTAKE"}, actor="kernel")
    return ep


def transition(ep: dict, new_state: str, actor: str = "kernel") -> dict:
    """Validate and perform a state transition; append an immutable event."""
    R.assert_state(new_state)
    cur = ep["state"]
    allowed = ALLOWED_NEXT.get(cur, [])
    if new_state not in allowed:
        raise ValueError(
            f"illegal transition {cur} -> {new_state}; allowed for {cur}: {allowed}"
        )
    ep["state_lineage"].append(cur)
    ep["state"] = new_state
    ep["updated_at"] = _now()
    _append_event(ep, "state_transition", {"from": cur, "to": new_state}, actor=actor)
    return ep


def observe(ep: dict, observation: dict, actor: str = "kernel") -> dict:
    """Record an executor observation and append an event (no self-approval)."""
    if "self_approved" in observation or observation.get("mark_episode_complete"):
        raise ValueError("executor may not self-approve or mark the episode complete")
    ep.setdefault("observations", []).append(observation)
    _append_event(
        ep, "observe", {"observation_ref": len(ep["observations"]) - 1}, actor=actor
    )
    ep["updated_at"] = _now()
    return ep


def record_action_selection(ep: dict, selection: dict, actor: str = "kernel") -> dict:
    ep["selected_action"] = selection
    _append_event(
        ep, "plan", {"selected_action": selection.get("selected_action")}, actor=actor
    )
    ep["updated_at"] = _now()
    return ep


def append_information_delta(ep: dict, delta: dict, actor: str = "kernel") -> dict:
    """Record a Q13 IterationDelta-compatible information delta."""
    ep["information_delta"] = delta
    _append_event(ep, "diagnose", {"delta_status": delta.get("delta_status")}, actor=actor)
    ep["updated_at"] = _now()
    return ep


def _append_event(ep: dict, etype: str, payload: dict, actor: str = "kernel") -> dict:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    rec = {
        "event_id": f"evt-{len(ep['event_log']):06d}",
        "timestamp": _now(),
        "type": etype,
        "actor": actor,
        "payload_sha256": hashlib.sha256(blob).hexdigest(),
    }
    ep.setdefault("event_log", []).append(rec)
    return rec


def event_count(ep: dict) -> int:
    return len(ep.get("event_log", []))


def is_terminal(ep: dict) -> bool:
    meta = R.episode_states()["states"].get(ep["state"], {})
    return bool(meta.get("terminal", False))


def save(ep: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ep, fh, indent=2, ensure_ascii=False)


def load(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def clone(ep: dict) -> dict:
    return copy.deepcopy(ep)
