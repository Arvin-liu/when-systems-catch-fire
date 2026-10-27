"""Replayable capability admission and revocation semantics."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json

from .control import FileLock


REVOCATION_SCHEMA = "ignition-durability-capability-revocation-r1"
EFFECT_CLASSES = frozenset({"READ_ONLY", "EXTERNAL_SIDE_EFFECT", "UNKNOWN_SIDE_EFFECT"})
GRANT_STATES = frozenset({"ACTIVE", "REVOKED", "EXPIRED"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


class RevocationError(ValueError):
    """Raised when capability admission or replay is unsafe."""


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or ".." in value:
        raise RevocationError(f"{field} is not a canonical identifier")
    return value


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise RevocationError(f"{field} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class CapabilityGrant:
    grant_id: str
    principal_id: str
    namespace_id: str
    capability: str
    effect_class: str
    lease_expires_at: float
    issuer_ref: str
    policy_digest: str
    status: str = "ACTIVE"
    grant_digest: str | None = None

    def __post_init__(self) -> None:
        for field in ("grant_id", "principal_id", "namespace_id", "capability", "issuer_ref"):
            _id(getattr(self, field), field)
        if self.effect_class not in EFFECT_CLASSES:
            raise RevocationError("unknown effect class")
        if not isinstance(self.lease_expires_at, (int, float)) or self.lease_expires_at <= 0:
            raise RevocationError("lease expiry must be positive")
        _digest(self.policy_digest, "policy_digest")
        if self.status not in GRANT_STATES:
            raise RevocationError("unknown grant status")
        expected = sha256_json(self._unsigned_dict())
        if self.grant_digest is not None and self.grant_digest != expected:
            raise RevocationError("grant digest mismatch")
        object.__setattr__(self, "grant_digest", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {"grant_id": self.grant_id, "principal_id": self.principal_id, "namespace_id": self.namespace_id, "capability": self.capability, "effect_class": self.effect_class, "lease_expires_at": self.lease_expires_at, "issuer_ref": self.issuer_ref, "policy_digest": self.policy_digest, "status": self.status}

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "grant_digest": self.grant_digest}


@dataclass(frozen=True)
class RevocationEvent:
    event_id: str
    sequence: int
    grant_id: str
    event_type: str
    occurred_at: float
    actor_ref: str
    reason: str
    grant: Mapping[str, Any] | None
    previous_event_hash: str
    event_hash: str | None = None

    def __post_init__(self) -> None:
        for field in ("event_id", "grant_id", "actor_ref"):
            _id(getattr(self, field), field)
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise RevocationError("revocation sequence must be non-negative")
        if self.event_type not in {"CAPABILITY_GRANTED", "CAPABILITY_REVOKED"}:
            raise RevocationError("unknown revocation event type")
        if not isinstance(self.occurred_at, (int, float)) or self.occurred_at < 0:
            raise RevocationError("occurred_at must be non-negative")
        if not isinstance(self.reason, str) or not self.reason.strip() or any(marker in self.reason.casefold() for marker in ("token ", "secret", "prompt", "hidden reasoning")):
            raise RevocationError("reason must be a public summary")
        if self.event_type == "CAPABILITY_GRANTED" and not isinstance(self.grant, Mapping):
            raise RevocationError("grant event must carry a public grant record")
        if self.event_type == "CAPABILITY_REVOKED" and self.grant is not None:
            raise RevocationError("revoke event must not duplicate grant state")
        _digest(self.previous_event_hash, "previous_event_hash")
        expected = sha256_json(self._unsigned_dict())
        if self.event_hash is not None and self.event_hash != expected:
            raise RevocationError("revocation event hash mismatch")
        object.__setattr__(self, "event_hash", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {"schema": REVOCATION_SCHEMA, "event_id": self.event_id, "sequence": self.sequence, "grant_id": self.grant_id, "event_type": self.event_type, "occurred_at": self.occurred_at, "actor_ref": self.actor_ref, "reason": self.reason, "grant": dict(self.grant) if self.grant is not None else None, "previous_event_hash": self.previous_event_hash}

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "event_hash": self.event_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RevocationEvent":
        required = {"schema", "event_id", "sequence", "grant_id", "event_type", "occurred_at", "actor_ref", "reason", "grant", "previous_event_hash", "event_hash"}
        if set(data) != required or data.get("schema") != REVOCATION_SCHEMA:
            raise RevocationError("revocation event schema mismatch")
        return cls(event_id=data["event_id"], sequence=data["sequence"], grant_id=data["grant_id"], event_type=data["event_type"], occurred_at=data["occurred_at"], actor_ref=data["actor_ref"], reason=data["reason"], grant=data["grant"], previous_event_hash=data["previous_event_hash"], event_hash=data["event_hash"])


ZERO_REVOCATION_HASH = "0" * 64


class RevocationStore:
    """Append-only grant/revoke log; future admission consults its replayed state."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _read_unlocked(self) -> list[RevocationEvent]:
        if not self.path.exists():
            return []
        events: list[RevocationEvent] = []
        previous = ZERO_REVOCATION_HASH
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                event = RevocationEvent.from_dict(json.loads(line))
            except (json.JSONDecodeError, TypeError, RevocationError) as exc:
                raise RevocationError(f"invalid revocation event at line {line_number}") from exc
            if event.sequence != len(events) or event.previous_event_hash != previous:
                raise RevocationError("revocation event sequence/hash chain mismatch")
            events.append(event)
            previous = event.event_hash or ZERO_REVOCATION_HASH
        return events

    def events(self) -> list[RevocationEvent]:
        with FileLock(self.lock_path):
            return self._read_unlocked()

    def _append(self, event: RevocationEvent) -> RevocationEvent:
        with FileLock(self.lock_path):
            existing = self._read_unlocked()
            if event.sequence != len(existing) or event.previous_event_hash != (existing[-1].event_hash if existing else ZERO_REVOCATION_HASH):
                raise RevocationError("revocation append is not the next chain event")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
            return event

    def register(self, grant: CapabilityGrant, *, actor_ref: str = "os-control-plane", occurred_at: float = 0.0) -> RevocationEvent:
        if any(event.grant_id == grant.grant_id for event in self.events()):
            raise RevocationError("grant identity already exists")
        events = self.events()
        return self._append(RevocationEvent(f"revoke-event-{grant.grant_id}-grant", len(events), grant.grant_id, "CAPABILITY_GRANTED", occurred_at, actor_ref, "capability admitted by explicit grant", grant.to_dict(), events[-1].event_hash if events else ZERO_REVOCATION_HASH))

    def revoke(self, grant_id: str, *, actor_ref: str = "os-control-plane", reason: str = "capability revoked", occurred_at: float = 0.0) -> RevocationEvent:
        _id(grant_id, "grant_id")
        state = self.replayed_state()
        if grant_id not in state:
            raise RevocationError("cannot revoke unknown grant")
        if state[grant_id]["status"] == "REVOKED":
            raise RevocationError("grant is already revoked")
        events = self.events()
        return self._append(RevocationEvent(f"revoke-event-{grant_id}-revoke-{len(events)}", len(events), grant_id, "CAPABILITY_REVOKED", occurred_at, actor_ref, reason, None, events[-1].event_hash if events else ZERO_REVOCATION_HASH))

    def replayed_state(self, *, now: float | None = None) -> dict[str, dict[str, Any]]:
        state: dict[str, dict[str, Any]] = {}
        for event in self.events():
            if event.event_type == "CAPABILITY_GRANTED":
                state[event.grant_id] = dict(event.grant or {})
                state[event.grant_id]["status"] = "ACTIVE"
            elif event.event_type == "CAPABILITY_REVOKED" and event.grant_id in state:
                state[event.grant_id]["status"] = "REVOKED"
                state[event.grant_id]["revocation_reason"] = event.reason
        if now is not None:
            for grant in state.values():
                if grant.get("status") == "ACTIVE" and now >= float(grant["lease_expires_at"]):
                    grant["status"] = "EXPIRED"
        return state

    def is_admissible(self, grant_id: str, *, now: float) -> bool:
        state = self.replayed_state(now=now).get(grant_id)
        return bool(state and state.get("status") == "ACTIVE")


@dataclass(frozen=True)
class DispatchAdmission:
    action_id: str
    grant_id: str
    effect_class: str
    state: str
    started: bool = False
    external_effect_retracted: bool = False


class RevocationDispatcher:
    def __init__(self, store: RevocationStore) -> None:
        self.store = store

    def admit_future(self, action_id: str, grant_id: str, *, now: float) -> DispatchAdmission:
        _id(action_id, "action_id")
        state = self.store.replayed_state(now=now).get(grant_id)
        if not state or state.get("status") != "ACTIVE":
            return DispatchAdmission(action_id, grant_id, str(state.get("effect_class", "UNKNOWN_SIDE_EFFECT")) if state else "UNKNOWN_SIDE_EFFECT", "REJECTED_REVOKED_OR_EXPIRED")
        return DispatchAdmission(action_id, grant_id, str(state["effect_class"]), "ADMITTED_QUEUED")

    def revoke_in_flight(self, admission: DispatchAdmission) -> DispatchAdmission:
        state = self.store.replayed_state().get(admission.grant_id)
        effect = admission.effect_class
        if state and state.get("status") == "ACTIVE":
            self.store.revoke(admission.grant_id, reason="operator capability revocation")
        if not admission.started:
            return DispatchAdmission(admission.action_id, admission.grant_id, effect, "CANCEL_BEFORE_START", started=False)
        if effect == "READ_ONLY":
            return DispatchAdmission(admission.action_id, admission.grant_id, effect, "CANCEL", started=True)
        if effect == "EXTERNAL_SIDE_EFFECT":
            return DispatchAdmission(admission.action_id, admission.grant_id, effect, "RECONCILE", started=True, external_effect_retracted=False)
        return DispatchAdmission(admission.action_id, admission.grant_id, effect, "DRAIN_AND_RECONCILE", started=True, external_effect_retracted=False)

    @staticmethod
    def health_degradation_decision(*, degraded_executor: str, substitute_capabilities: tuple[str, ...]) -> dict[str, Any]:
        _id(degraded_executor, "degraded_executor")
        if substitute_capabilities:
            return {"status": "DRAIN_ONLY", "substitute_capabilities": [], "reason": "health degradation cannot widen executor permission"}
        return {"status": "DRAIN_ONLY", "substitute_capabilities": [], "reason": "no automatic substitution authority"}


__all__ = ["CapabilityGrant", "DispatchAdmission", "EFFECT_CLASSES", "GRANT_STATES", "REVOCATION_SCHEMA", "RevocationDispatcher", "RevocationError", "RevocationEvent", "RevocationStore", "ZERO_REVOCATION_HASH"]
