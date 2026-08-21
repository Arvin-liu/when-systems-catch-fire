"""OS-owned Steering and Intent R1 contracts.

The steering plane is deliberately separate from the existing run-local
``GoalContract``.  It records where work is heading and why a bounded OS
dispatch may proceed; it does not create Owner authority, domain truth, or an
executor implementation.  Later task steps extend this module with lifecycle,
completion, temporal, arbitration, durability, and federation helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import KernelValidationError, _id, _summary, _tuple_strings, sha256_json


STEERING_SCHEMA = "os-steering-intent-obligation-r1"
INTENT_AUTHORITY_INVARIANT = "INTENT_AUTHORITY_INVARIANT"
GOAL_COMPLETION_NON_INFERENCE_INVARIANT = "GOAL_COMPLETION_NON_INFERENCE_INVARIANT"
STEERING_EXPLAINABILITY_INVARIANT = "STEERING_EXPLAINABILITY_INVARIANT"

INTENT_SOURCE_TYPES = frozenset({
    "OWNER_DECLARED",
    "OWNER_APPROVED_DERIVED",
    "SYSTEM_DERIVED_PROPOSAL",
    "EXTERNAL_REQUESTED_PROPOSAL",
    "HISTORICAL_IMPORTED",
})
INTENT_STATUSES = frozenset({"PROPOSED", "ACTIVE", "PAUSED", "RETIRED", "SUPERSEDED"})
GOAL_STATUSES = frozenset({"PROPOSED", "ACTIVE", "PAUSED", "BLOCKED", "SATISFIED", "ABANDONED", "SUPERSEDED", "FAILED_BOUNDED"})
ONTOLOGY_LAYERS = (
    ("intent", "long-term direction"),
    ("goal", "trackable target state"),
    ("commitment", "accepted obligation"),
    ("episode", "organized attempt"),
    ("run", "bounded execution"),
    ("action", "one executor operation"),
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN = ("api_key", "access_token", "client_secret", "password", "chain-of-thought", "hidden reasoning", "raw_prompt", "prompt_body")


class SteeringValidationError(KernelValidationError):
    """Raised when a steering record would widen authority or lose lineage."""


def _safe_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise SteeringValidationError(f"{field} must be a bounded identifier")
    return value


def _bounded_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise SteeringValidationError(f"{field} must be a non-empty bounded string")
    lowered = value.casefold()
    if any(marker in lowered for marker in _FORBIDDEN) or "prompt" in lowered:
        raise SteeringValidationError(f"{field} contains forbidden private or hidden-reasoning material")
    _summary(value, field)
    return value


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SteeringValidationError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SteeringValidationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise SteeringValidationError(f"{field} must include a timezone")
    return value


def _public_value(value: Any, field: str = "value") -> Any:
    """Copy JSON-compatible public metadata without private prompt material."""

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _bounded_text(value, field)
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value, key=str):
            if not isinstance(key, str) or not key.strip():
                raise SteeringValidationError(f"{field} keys must be non-empty strings")
            if any(marker in key.casefold() for marker in _FORBIDDEN) or "prompt" in key.casefold():
                raise SteeringValidationError(f"{field}.{key} is not a public steering field")
            result[key] = _public_value(value[key], f"{field}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_public_value(item, f"{field}[]") for item in value]
    raise SteeringValidationError(f"{field} must be JSON-compatible")


def _refs(value: Sequence[str], field: str) -> tuple[str, ...]:
    result = _tuple_strings(value, field)
    return tuple(sorted(set(result)))


@dataclass(frozen=True)
class AuthorityProvenance:
    """The typed source chain for a proposed or canonical steering record."""

    source_type: str
    actor_ref: str
    authority_id: str
    reason: str
    evidence_refs: tuple[str, ...] = ()
    authorized: bool = False

    def __post_init__(self) -> None:
        if self.source_type not in INTENT_SOURCE_TYPES:
            raise SteeringValidationError(f"unknown authority source type: {self.source_type}")
        _safe_id(self.actor_ref, "provenance.actor_ref")
        _safe_id(self.authority_id, "provenance.authority_id")
        _bounded_text(self.reason, "provenance.reason")
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "provenance.evidence_refs"))
        if not isinstance(self.authorized, bool):
            raise SteeringValidationError("provenance.authorized must be boolean")
        if self.source_type in {"OWNER_DECLARED", "OWNER_APPROVED_DERIVED"} and not self.authorized:
            raise SteeringValidationError("Owner provenance requires explicit authorization")
        if self.source_type not in {"OWNER_DECLARED", "OWNER_APPROVED_DERIVED"} and self.authorized:
            raise SteeringValidationError("non-Owner proposal cannot carry Owner authorization")

    @property
    def is_owner_authority(self) -> bool:
        return self.authorized and self.source_type in {"OWNER_DECLARED", "OWNER_APPROVED_DERIVED"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "actor_ref": self.actor_ref,
            "authority_id": self.authority_id,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "authorized": self.authorized,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AuthorityProvenance":
        return cls(
            source_type=data["source_type"], actor_ref=data["actor_ref"],
            authority_id=data["authority_id"], reason=data["reason"],
            evidence_refs=tuple(data.get("evidence_refs", ())), authorized=data.get("authorized", False),
        )


@dataclass(frozen=True)
class IntentRecord:
    """A durable direction; proposals never become Owner intent implicitly."""

    intent_id: str
    statement: str
    namespace: str
    provenance: AuthorityProvenance
    status: str = "PROPOSED"
    scope: Mapping[str, Any] = None  # type: ignore[assignment]
    version: int = 1
    supersedes_intent_id: str | None = None
    created_at: str = "1970-01-01T00:00:00+00:00"
    updated_at: str = "1970-01-01T00:00:00+00:00"

    def __post_init__(self) -> None:
        _safe_id(self.intent_id, "intent_id")
        _bounded_text(self.statement, "intent.statement")
        _safe_id(self.namespace, "intent.namespace")
        if self.status not in INTENT_STATUSES:
            raise SteeringValidationError(f"unknown intent status: {self.status}")
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            raise SteeringValidationError("intent.version must be a positive integer")
        if self.supersedes_intent_id is not None:
            _safe_id(self.supersedes_intent_id, "intent.supersedes_intent_id")
            if self.supersedes_intent_id == self.intent_id:
                raise SteeringValidationError("intent cannot supersede itself")
        _timestamp(self.created_at, "intent.created_at")
        _timestamp(self.updated_at, "intent.updated_at")
        object.__setattr__(self, "scope", _public_value(self.scope or {}, "intent.scope"))
        if self.provenance.source_type not in {"OWNER_DECLARED", "OWNER_APPROVED_DERIVED"} and self.status != "PROPOSED":
            raise SteeringValidationError("non-Owner intent proposals must remain PROPOSED")

    @property
    def owner_authoritative(self) -> bool:
        return self.provenance.is_owner_authority

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.intent",
            "intent_id": self.intent_id,
            "statement": self.statement,
            "namespace": self.namespace,
            "provenance": self.provenance.to_dict(),
            "status": self.status,
            "scope": self.scope,
            "version": self.version,
            "supersedes_intent_id": self.supersedes_intent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IntentRecord":
        if data.get("schema") not in {None, f"{STEERING_SCHEMA}.intent"}:
            raise SteeringValidationError("intent schema mismatch")
        return cls(
            intent_id=data["intent_id"], statement=data["statement"], namespace=data["namespace"],
            provenance=AuthorityProvenance.from_dict(data["provenance"]), status=data.get("status", "PROPOSED"),
            scope=data.get("scope", {}), version=data.get("version", 1),
            supersedes_intent_id=data.get("supersedes_intent_id"),
            created_at=data.get("created_at", "1970-01-01T00:00:00+00:00"),
            updated_at=data.get("updated_at", data.get("created_at", "1970-01-01T00:00:00+00:00")),
        )


@dataclass(frozen=True)
class CompletionContract:
    """Independent predicates and authority for deciding Goal satisfaction."""

    contract_id: str
    acceptance_predicates: tuple[str, ...]
    required_evidence_types: tuple[str, ...]
    completion_authority: str
    forbidden_shortcuts: tuple[str, ...]
    review_window_ref: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.contract_id, "completion_contract.contract_id")
        object.__setattr__(self, "acceptance_predicates", _refs(self.acceptance_predicates, "acceptance_predicates"))
        object.__setattr__(self, "required_evidence_types", _refs(self.required_evidence_types, "required_evidence_types"))
        object.__setattr__(self, "forbidden_shortcuts", _refs(self.forbidden_shortcuts, "forbidden_shortcuts"))
        if not self.acceptance_predicates or not self.required_evidence_types:
            raise SteeringValidationError("completion contract requires predicates and evidence types")
        if self.completion_authority not in {"OWNER_ONLY", "VALIDATOR", "EXTERNAL_OBSERVATION"}:
            raise SteeringValidationError("unknown completion authority")
        if self.review_window_ref is not None:
            _safe_id(self.review_window_ref, "completion_contract.review_window_ref")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.completion-contract",
            "contract_id": self.contract_id,
            "acceptance_predicates": list(self.acceptance_predicates),
            "required_evidence_types": list(self.required_evidence_types),
            "completion_authority": self.completion_authority,
            "forbidden_shortcuts": list(self.forbidden_shortcuts),
            "review_window_ref": self.review_window_ref,
        }


@dataclass(frozen=True)
class GoalRecord:
    """A versioned target whose satisfaction is never inferred from a child run."""

    goal_id: str
    intent_id: str
    statement: str
    namespace: str
    completion_contract_id: str
    provenance: AuthorityProvenance
    status: str = "PROPOSED"
    version: int = 1
    parent_goal_id: str | None = None
    created_at: str = "1970-01-01T00:00:00+00:00"
    updated_at: str = "1970-01-01T00:00:00+00:00"
    supersedes_goal_id: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.goal_id, "goal_id")
        _safe_id(self.intent_id, "goal.intent_id")
        _bounded_text(self.statement, "goal.statement")
        _safe_id(self.namespace, "goal.namespace")
        _safe_id(self.completion_contract_id, "goal.completion_contract_id")
        if self.status not in GOAL_STATUSES:
            raise SteeringValidationError(f"unknown goal status: {self.status}")
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            raise SteeringValidationError("goal.version must be a positive integer")
        if self.parent_goal_id is not None:
            _safe_id(self.parent_goal_id, "goal.parent_goal_id")
        if self.supersedes_goal_id is not None:
            _safe_id(self.supersedes_goal_id, "goal.supersedes_goal_id")
            if self.supersedes_goal_id == self.goal_id:
                raise SteeringValidationError("goal cannot supersede itself")
        _timestamp(self.created_at, "goal.created_at")
        _timestamp(self.updated_at, "goal.updated_at")

    def objective_digest(self) -> str:
        return sha256_json({"goal_id": self.goal_id, "intent_id": self.intent_id, "statement": self.statement, "completion_contract_id": self.completion_contract_id, "namespace": self.namespace, "version": self.version})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.goal",
            "goal_id": self.goal_id,
            "intent_id": self.intent_id,
            "statement": self.statement,
            "namespace": self.namespace,
            "completion_contract_id": self.completion_contract_id,
            "provenance": self.provenance.to_dict(),
            "status": self.status,
            "version": self.version,
            "parent_goal_id": self.parent_goal_id,
            "supersedes_goal_id": self.supersedes_goal_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "objective_digest": self.objective_digest(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GoalRecord":
        if data.get("schema") not in {None, f"{STEERING_SCHEMA}.goal"}:
            raise GoalRegistryError("goal schema mismatch")
        return cls(
            goal_id=data["goal_id"], intent_id=data["intent_id"], statement=data["statement"], namespace=data["namespace"],
            completion_contract_id=data["completion_contract_id"], provenance=AuthorityProvenance.from_dict(data["provenance"]),
            status=data.get("status", "PROPOSED"), version=data.get("version", 1), parent_goal_id=data.get("parent_goal_id"),
            created_at=data.get("created_at", "1970-01-01T00:00:00+00:00"), updated_at=data.get("updated_at", "1970-01-01T00:00:00+00:00"),
            supersedes_goal_id=data.get("supersedes_goal_id"),
        )


class IntentRegistryError(SteeringValidationError):
    """Raised when an intent registry operation would lose authority lineage."""


class IntentRegistry:
    """Small append-only-in-spirit registry for canonical and proposed intents."""

    def __init__(self, records: Sequence[IntentRecord] = ()) -> None:
        self._records: dict[str, IntentRecord] = {}
        self._events: list[dict[str, Any]] = []
        for record in records:
            self.register(record)

    @property
    def records(self) -> tuple[IntentRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    def get(self, intent_id: str) -> IntentRecord:
        _safe_id(intent_id, "intent_id")
        try:
            return self._records[intent_id]
        except KeyError as exc:
            raise IntentRegistryError(f"unknown intent: {intent_id}") from exc

    def register(self, record: IntentRecord) -> IntentRecord:
        if not isinstance(record, IntentRecord):
            raise IntentRegistryError("registry accepts IntentRecord only")
        if record.intent_id in self._records:
            raise IntentRegistryError(f"intent already exists: {record.intent_id}")
        if not record.owner_authoritative and record.status != "PROPOSED":
            raise IntentRegistryError("a non-Owner proposal cannot enter the active registry")
        self._records[record.intent_id] = record
        self._events.append({
            "event": "INTENT_REGISTERED",
            "intent_id": record.intent_id,
            "version": record.version,
            "source_type": record.provenance.source_type,
            "owner_authoritative": record.owner_authoritative,
            "authority_digest": authority_digest(record.provenance),
        })
        return record

    def transition(self, intent_id: str, status: str, *, provenance: AuthorityProvenance, reason: str, updated_at: str) -> IntentRecord:
        current = self.get(intent_id)
        if status not in INTENT_STATUSES:
            raise IntentRegistryError(f"unknown target intent status: {status}")
        _bounded_text(reason, "intent.transition.reason")
        _timestamp(updated_at, "intent.transition.updated_at")
        if not provenance.is_owner_authority:
            raise IntentRegistryError("intent lifecycle changes require explicit Owner authority")
        if status in {"ACTIVE", "PAUSED", "RETIRED", "SUPERSEDED"} and not current.owner_authoritative:
            raise IntentRegistryError("a proposal cannot be promoted or lifecycle-mutated as canonical Owner intent")
        if current.status == "RETIRED" and status != "RETIRED":
            raise IntentRegistryError("retired intent cannot be silently reopened")
        updated = replace(current, status=status, version=current.version + 1, updated_at=updated_at)
        self._records[intent_id] = updated
        self._events.append({
            "event": "INTENT_STATUS_CHANGED",
            "intent_id": intent_id,
            "from_status": current.status,
            "to_status": status,
            "from_version": current.version,
            "to_version": updated.version,
            "reason": reason,
            "authority_digest": authority_digest(provenance),
        })
        return updated

    def supersede(self, intent_id: str, replacement: IntentRecord, *, provenance: AuthorityProvenance, reason: str, updated_at: str) -> tuple[IntentRecord, IntentRecord]:
        current = self.get(intent_id)
        if replacement.supersedes_intent_id != intent_id:
            raise IntentRegistryError("replacement must point to the intent it supersedes")
        if not provenance.is_owner_authority or not current.owner_authoritative or not replacement.owner_authoritative:
            raise IntentRegistryError("supersession of canonical intent requires Owner authority on both records")
        if replacement.intent_id in self._records:
            raise IntentRegistryError(f"replacement intent already exists: {replacement.intent_id}")
        old = self.transition(intent_id, "SUPERSEDED", provenance=provenance, reason=reason, updated_at=updated_at)
        self.register(replacement)
        self._events.append({
            "event": "INTENT_SUPERSEDED",
            "intent_id": intent_id,
            "replacement_intent_id": replacement.intent_id,
            "lineage_preserved": True,
            "authority_digest": authority_digest(provenance),
        })
        return old, replacement

    def owner_active(self, *, namespace: str | None = None) -> tuple[IntentRecord, ...]:
        result = tuple(record for record in self.records if record.owner_authoritative and record.status == "ACTIVE" and (namespace is None or record.namespace == namespace))
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.intent-registry",
            "records": [record.to_dict() for record in self.records],
            "events": list(self._events),
            "record_count": len(self._records),
            "owner_authoritative_count": sum(record.owner_authoritative for record in self.records),
            "proposal_count": sum(not record.owner_authoritative for record in self.records),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IntentRegistry":
        if data.get("schema") != f"{STEERING_SCHEMA}.intent-registry":
            raise IntentRegistryError("intent registry schema mismatch")
        registry = cls(IntentRecord.from_dict(row) for row in data.get("records", ()))
        stored_events = data.get("events", [])
        if not isinstance(stored_events, list):
            raise IntentRegistryError("intent registry events must be an array")
        registry._events = [dict(event) for event in stored_events]
        return registry


_GOAL_TRANSITIONS: dict[str, frozenset[str]] = {
    "PROPOSED": frozenset({"ACTIVE", "PAUSED", "BLOCKED", "ABANDONED", "SUPERSEDED"}),
    "ACTIVE": frozenset({"PAUSED", "BLOCKED", "ABANDONED", "SUPERSEDED", "FAILED_BOUNDED"}),
    "PAUSED": frozenset({"ACTIVE", "BLOCKED", "ABANDONED", "SUPERSEDED"}),
    "BLOCKED": frozenset({"ACTIVE", "PAUSED", "ABANDONED", "SUPERSEDED", "FAILED_BOUNDED"}),
    "SATISFIED": frozenset(),
    "ABANDONED": frozenset(),
    "SUPERSEDED": frozenset(),
    "FAILED_BOUNDED": frozenset(),
}


class GoalRegistryError(SteeringValidationError):
    """Raised when a Goal lifecycle transition is invalid or under-authorized."""


class GoalRegistry:
    """Versioned Goal state machine with append-only transition evidence."""

    def __init__(self, goals: Sequence[GoalRecord] = (), contracts: Sequence[CompletionContract] = ()) -> None:
        self._goals: dict[str, GoalRecord] = {}
        self._contracts: dict[str, CompletionContract] = {contract.contract_id: contract for contract in contracts}
        self._events: list[dict[str, Any]] = []
        for goal in goals:
            self.register(goal)

    @property
    def goals(self) -> tuple[GoalRecord, ...]:
        return tuple(self._goals[key] for key in sorted(self._goals))

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    def register_contract(self, contract: CompletionContract) -> CompletionContract:
        if contract.contract_id in self._contracts:
            raise GoalRegistryError(f"completion contract already exists: {contract.contract_id}")
        self._contracts[contract.contract_id] = contract
        return contract

    def get(self, goal_id: str) -> GoalRecord:
        _safe_id(goal_id, "goal_id")
        try:
            return self._goals[goal_id]
        except KeyError as exc:
            raise GoalRegistryError(f"unknown goal: {goal_id}") from exc

    def contract(self, contract_id: str) -> CompletionContract:
        try:
            return self._contracts[contract_id]
        except KeyError as exc:
            raise GoalRegistryError(f"unknown completion contract: {contract_id}") from exc

    def register(self, goal: GoalRecord) -> GoalRecord:
        if goal.goal_id in self._goals:
            raise GoalRegistryError(f"goal already exists: {goal.goal_id}")
        self.contract(goal.completion_contract_id)
        if goal.status == "SATISFIED":
            raise GoalRegistryError("a newly registered goal cannot be SATISFIED without a completion decision")
        self._goals[goal.goal_id] = goal
        self._events.append({"event": "GOAL_REGISTERED", "goal_id": goal.goal_id, "status": goal.status, "version": goal.version, "objective_digest": goal.objective_digest()})
        return goal

    def transition(self, goal_id: str, status: str, *, provenance: AuthorityProvenance, reason: str, evidence_refs: Sequence[str] = (), updated_at: str) -> GoalRecord:
        current = self.get(goal_id)
        if status not in GOAL_STATUSES:
            raise GoalRegistryError(f"unknown goal status: {status}")
        if status not in _GOAL_TRANSITIONS[current.status]:
            raise GoalRegistryError(f"invalid Goal transition {current.status}->{status}")
        _bounded_text(reason, "goal.transition.reason")
        _timestamp(updated_at, "goal.transition.updated_at")
        if status == "SATISFIED":
            raise GoalRegistryError("SATISFIED requires an independent CompletionDecision; child completion is insufficient")
        if status == "ACTIVE" and current.provenance.source_type not in {"OWNER_DECLARED", "OWNER_APPROVED_DERIVED"} and not provenance.is_owner_authority:
            raise GoalRegistryError("activating a proposed Goal requires explicit Owner approval")
        refs = _refs(evidence_refs, "goal.transition.evidence_refs")
        updated = replace(current, status=status, version=current.version + 1, updated_at=updated_at)
        self._goals[goal_id] = updated
        self._events.append({
            "event": "GOAL_STATUS_CHANGED",
            "goal_id": goal_id,
            "from_status": current.status,
            "to_status": status,
            "from_version": current.version,
            "to_version": updated.version,
            "actor_ref": provenance.actor_ref,
            "authority_source_type": provenance.source_type,
            "authority_digest": authority_digest(provenance),
            "reason": reason,
            "evidence_refs": list(refs),
            "completion_inferred": False,
        })
        return updated

    def reopen(self, goal_id: str, replacement: GoalRecord, *, provenance: AuthorityProvenance, reason: str) -> GoalRecord:
        current = self.get(goal_id)
        if current.status not in {"SATISFIED", "ABANDONED", "SUPERSEDED", "FAILED_BOUNDED"}:
            raise GoalRegistryError("only a terminal Goal can be explicitly reopened as a new version")
        if replacement.supersedes_goal_id != goal_id:
            raise GoalRegistryError("reopened Goal must preserve supersedes_goal_id lineage")
        if not provenance.is_owner_authority:
            raise GoalRegistryError("reopening a terminal Goal requires explicit Owner authority")
        self.register(replacement)
        self._events.append({"event": "GOAL_REOPENED_AS_NEW_VERSION", "old_goal_id": goal_id, "new_goal_id": replacement.goal_id, "reason": reason, "lineage_preserved": True, "authority_digest": authority_digest(provenance)})
        return replacement

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.goal-registry",
            "contracts": [self._contracts[key].to_dict() for key in sorted(self._contracts)],
            "goals": [goal.to_dict() for goal in self.goals],
            "events": list(self._events),
            "goal_count": len(self._goals),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GoalRegistry":
        if data.get("schema") != f"{STEERING_SCHEMA}.goal-registry":
            raise GoalRegistryError("goal registry schema mismatch")
        registry = cls(contracts=tuple(CompletionContract(**{
            "contract_id": row["contract_id"],
            "acceptance_predicates": tuple(row["acceptance_predicates"]),
            "required_evidence_types": tuple(row["required_evidence_types"]),
            "completion_authority": row["completion_authority"],
            "forbidden_shortcuts": tuple(row["forbidden_shortcuts"]),
            "review_window_ref": row.get("review_window_ref"),
        }) for row in data.get("contracts", ())))
        for row in data.get("goals", ()):
            registry.register(GoalRecord.from_dict(row))
        events = data.get("events", [])
        if not isinstance(events, list):
            raise GoalRegistryError("goal registry events must be an array")
        registry._events = [dict(event) for event in events]
        return registry


def ontology_contract() -> dict[str, Any]:
    """Return the machine-readable layer and non-inference contract."""

    return {
        "schema": f"{STEERING_SCHEMA}.ontology",
        "layers": [{"kind": kind, "meaning": meaning} for kind, meaning in ONTOLOGY_LAYERS],
        "invariants": {
            INTENT_AUTHORITY_INVARIANT: "Only explicit Owner provenance can create canonical Owner intent or commitment authority.",
            GOAL_COMPLETION_NON_INFERENCE_INVARIANT: "Run, Episode, Action, test, receipt, or Pack result cannot set an upper Goal to SATISFIED.",
            STEERING_EXPLAINABILITY_INVARIANT: "A formal next-work selection must include active goals, blockers, policy inputs, skipped items, and unknowns.",
        },
        "reuse_boundaries": {
            "run_goal_contract": "existing run-local execution contract; not a long-term Goal record",
            "supervisor_episode": "execution coordination/DAG; not a Goal authority",
            "operational_memory": "historical operational context; not Owner intent authority",
            "federation_executor": "replaceable bounded hands; not canonical Goal or Commitment authority",
        },
        "claim_ceiling": "Repository-local ontology and authority contract only; no Owner preference inference or external truth.",
    }


def authority_digest(provenance: AuthorityProvenance) -> str:
    """Digest provenance without including private source content."""

    return hashlib.sha256(json.dumps(provenance.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


__all__ = [
    "STEERING_SCHEMA", "INTENT_AUTHORITY_INVARIANT", "GOAL_COMPLETION_NON_INFERENCE_INVARIANT", "STEERING_EXPLAINABILITY_INVARIANT",
    "INTENT_SOURCE_TYPES", "INTENT_STATUSES", "ONTOLOGY_LAYERS", "SteeringValidationError", "AuthorityProvenance",
    "IntentRecord", "GoalRecord", "CompletionContract", "ontology_contract", "authority_digest",
    "IntentRegistry", "IntentRegistryError",
    "GOAL_STATUSES", "GoalRegistry", "GoalRegistryError",
]
