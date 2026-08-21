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

from .durability import CanonicalSnapshot, CanonicalSnapshotStore
from .event_ledger import EventLedger
from .migration import APPLIED, DRY_RUN, SAFE, MigrationRegistry, MigrationResult, MigrationRule, StateMigrator
from .namespace import DelegationGrant, NamespaceBinding, NamespaceGuard, NamespaceIsolationError, PrincipalIdentity


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


COMPLETION_OUTCOMES = frozenset({"SATISFIED", "PARTIAL", "UNVERIFIABLE", "REJECTED"})
COMMITMENT_STATUSES = frozenset({"PROPOSED", "ACCEPTED", "ACTIVE", "DUE", "BLOCKED", "FULFILLED", "WAIVED", "BREACHED", "SUPERSEDED"})


@dataclass(frozen=True)
class CompletionDecision:
    """A separately authorized decision; it is the only input that can satisfy a Goal."""

    goal_id: str
    goal_version: int
    contract_id: str
    outcome: str
    authority_source_type: str
    authority_actor_ref: str
    reason: str
    predicate_results: Mapping[str, bool]
    evidence_types: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    forbidden_shortcuts_detected: tuple[str, ...]
    decided_at: str
    decision_sha256: str = ""

    def __post_init__(self) -> None:
        _safe_id(self.goal_id, "completion_decision.goal_id")
        if not isinstance(self.goal_version, int) or self.goal_version < 1:
            raise SteeringValidationError("completion_decision.goal_version must be positive")
        _safe_id(self.contract_id, "completion_decision.contract_id")
        if self.outcome not in COMPLETION_OUTCOMES:
            raise SteeringValidationError(f"unknown completion outcome: {self.outcome}")
        if self.authority_source_type not in INTENT_SOURCE_TYPES:
            raise SteeringValidationError("completion decision has unknown authority source")
        _safe_id(self.authority_actor_ref, "completion_decision.authority_actor_ref")
        _bounded_text(self.reason, "completion_decision.reason")
        if not isinstance(self.predicate_results, Mapping) or any(not isinstance(key, str) or not isinstance(value, bool) for key, value in self.predicate_results.items()):
            raise SteeringValidationError("completion_decision.predicate_results must map strings to booleans")
        object.__setattr__(self, "predicate_results", {key: bool(self.predicate_results[key]) for key in sorted(self.predicate_results)})
        object.__setattr__(self, "evidence_types", _refs(self.evidence_types, "completion_decision.evidence_types"))
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "completion_decision.evidence_refs"))
        object.__setattr__(self, "forbidden_shortcuts_detected", _refs(self.forbidden_shortcuts_detected, "completion_decision.forbidden_shortcuts_detected"))
        _timestamp(self.decided_at, "completion_decision.decided_at")
        expected = sha256_json(self.unsigned_dict())
        if self.decision_sha256 and self.decision_sha256 != expected:
            raise SteeringValidationError("completion decision digest mismatch")
        object.__setattr__(self, "decision_sha256", expected)

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.completion-decision",
            "goal_id": self.goal_id,
            "goal_version": self.goal_version,
            "contract_id": self.contract_id,
            "outcome": self.outcome,
            "authority_source_type": self.authority_source_type,
            "authority_actor_ref": self.authority_actor_ref,
            "reason": self.reason,
            "predicate_results": dict(self.predicate_results),
            "evidence_types": list(self.evidence_types),
            "evidence_refs": list(self.evidence_refs),
            "forbidden_shortcuts_detected": list(self.forbidden_shortcuts_detected),
            "decided_at": self.decided_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "decision_sha256": self.decision_sha256}


def evaluate_completion(goal: "GoalRecord", contract: CompletionContract, evidence: Mapping[str, Any], *, authority: AuthorityProvenance, decided_at: str) -> CompletionDecision:
    """Evaluate a contract without treating a run receipt as upper-level completion."""

    if goal.completion_contract_id != contract.contract_id:
        raise SteeringValidationError("completion contract does not belong to Goal")
    if not isinstance(evidence, Mapping):
        raise SteeringValidationError("completion evidence must be an object")
    public = _public_value(evidence, "completion.evidence")
    raw_predicates = public.get("predicate_results", public.get("predicates", {}))
    if not isinstance(raw_predicates, Mapping):
        raise SteeringValidationError("completion predicate_results must be an object")
    predicate_results = {str(key): value is True for key, value in raw_predicates.items()}
    evidence_types = tuple(str(item) for item in public.get("evidence_types", ()))
    evidence_refs = tuple(str(item) for item in public.get("evidence_refs", ()))
    shortcut_flags = tuple(str(item) for item in public.get("shortcut_flags", ()))
    forbidden = tuple(sorted(set(shortcut_flags).intersection(contract.forbidden_shortcuts)))
    required_present = set(contract.required_evidence_types).issubset(set(evidence_types))
    predicates_present = all(predicate_results.get(predicate) is True for predicate in contract.acceptance_predicates)
    authority_ok = (
        (contract.completion_authority == "OWNER_ONLY" and authority.is_owner_authority)
        or (contract.completion_authority == "VALIDATOR" and authority.source_type == "SYSTEM_DERIVED_PROPOSAL" and authority.actor_ref.startswith("validator."))
        or (contract.completion_authority == "EXTERNAL_OBSERVATION" and authority.source_type == "EXTERNAL_REQUESTED_PROPOSAL")
    )
    run_pass = bool(public.get("run_pass", False))
    if forbidden:
        outcome, reason = "REJECTED", "forbidden shortcut cannot satisfy independent completion contract"
    elif run_pass and not (required_present and predicates_present):
        outcome, reason = "UNVERIFIABLE", "run or episode PASS is not an independent Goal completion"
    elif not authority_ok:
        outcome, reason = "UNVERIFIABLE", "completion authority does not match the contract"
    elif required_present and predicates_present:
        outcome, reason = "SATISFIED", "all independent predicates and evidence requirements passed"
    elif any(predicate_results.values()) or evidence_types:
        outcome, reason = "PARTIAL", "some completion evidence exists but the contract is incomplete"
    else:
        outcome, reason = "UNVERIFIABLE", "no independent completion evidence was supplied"
    return CompletionDecision(goal.goal_id, goal.version, contract.contract_id, outcome, authority.source_type, authority.actor_ref, reason, predicate_results, evidence_types, evidence_refs, forbidden, decided_at)


def _optional_timestamp(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _timestamp(value, field)


@dataclass(frozen=True)
class CommitmentRecord:
    """A stronger-than-Goal obligation with explicit issuer/beneficiary semantics."""

    commitment_id: str
    goal_id: str
    issuer_ref: str
    beneficiary_ref: str
    namespace: str
    scope: Mapping[str, Any]
    fulfillment_contract_id: str
    provenance: AuthorityProvenance
    status: str = "PROPOSED"
    due_at: str | None = None
    not_before: str | None = None
    review_after: str | None = None
    version: int = 1
    supersedes_commitment_id: str | None = None
    created_at: str = "1970-01-01T00:00:00+00:00"
    updated_at: str = "1970-01-01T00:00:00+00:00"

    def __post_init__(self) -> None:
        _safe_id(self.commitment_id, "commitment_id")
        _safe_id(self.goal_id, "commitment.goal_id")
        _safe_id(self.issuer_ref, "commitment.issuer_ref")
        _safe_id(self.beneficiary_ref, "commitment.beneficiary_ref")
        _safe_id(self.namespace, "commitment.namespace")
        object.__setattr__(self, "scope", _public_value(self.scope, "commitment.scope"))
        _safe_id(self.fulfillment_contract_id, "commitment.fulfillment_contract_id")
        if self.status not in COMMITMENT_STATUSES:
            raise SteeringValidationError(f"unknown commitment status: {self.status}")
        for field in ("due_at", "not_before", "review_after"):
            object.__setattr__(self, field, _optional_timestamp(getattr(self, field), f"commitment.{field}"))
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            raise SteeringValidationError("commitment.version must be positive")
        if self.supersedes_commitment_id is not None:
            _safe_id(self.supersedes_commitment_id, "commitment.supersedes_commitment_id")
            if self.supersedes_commitment_id == self.commitment_id:
                raise SteeringValidationError("commitment cannot supersede itself")
        _timestamp(self.created_at, "commitment.created_at")
        _timestamp(self.updated_at, "commitment.updated_at")
        if self.status in {"ACCEPTED", "ACTIVE", "DUE", "FULFILLED", "WAIVED", "BREACHED"} and not self.provenance.is_owner_authority:
            raise SteeringValidationError("canonical accepted commitment requires explicit Owner authority")

    def authority_digest(self) -> str:
        return authority_digest(self.provenance)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.commitment",
            "commitment_id": self.commitment_id,
            "goal_id": self.goal_id,
            "issuer_ref": self.issuer_ref,
            "beneficiary_ref": self.beneficiary_ref,
            "namespace": self.namespace,
            "scope": self.scope,
            "fulfillment_contract_id": self.fulfillment_contract_id,
            "provenance": self.provenance.to_dict(),
            "status": self.status,
            "due_at": self.due_at,
            "not_before": self.not_before,
            "review_after": self.review_after,
            "version": self.version,
            "supersedes_commitment_id": self.supersedes_commitment_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "authority_digest": self.authority_digest(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CommitmentRecord":
        if data.get("schema") not in {None, f"{STEERING_SCHEMA}.commitment"}:
            raise SteeringValidationError("commitment schema mismatch")
        return cls(
            commitment_id=data["commitment_id"], goal_id=data["goal_id"], issuer_ref=data["issuer_ref"], beneficiary_ref=data["beneficiary_ref"],
            namespace=data["namespace"], scope=data.get("scope", {}), fulfillment_contract_id=data["fulfillment_contract_id"],
            provenance=AuthorityProvenance.from_dict(data["provenance"]), status=data.get("status", "PROPOSED"), due_at=data.get("due_at"),
            not_before=data.get("not_before"), review_after=data.get("review_after"), version=data.get("version", 1),
            supersedes_commitment_id=data.get("supersedes_commitment_id"), created_at=data.get("created_at", "1970-01-01T00:00:00+00:00"),
            updated_at=data.get("updated_at", data.get("created_at", "1970-01-01T00:00:00+00:00")),
        )


class CommitmentLedgerError(SteeringValidationError):
    """Raised when an obligation would be accepted without authority or evidence."""


class CommitmentLedger:
    """Replayable commitment ledger; its records are not Knowledge or memory."""

    def __init__(self, commitments: Sequence[CommitmentRecord] = ()) -> None:
        self._commitments: dict[str, CommitmentRecord] = {}
        self._events: list[dict[str, Any]] = []
        for commitment in commitments:
            self.register(commitment)

    @property
    def commitments(self) -> tuple[CommitmentRecord, ...]:
        return tuple(self._commitments[key] for key in sorted(self._commitments))

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    def get(self, commitment_id: str) -> CommitmentRecord:
        _safe_id(commitment_id, "commitment_id")
        try:
            return self._commitments[commitment_id]
        except KeyError as exc:
            raise CommitmentLedgerError(f"unknown commitment: {commitment_id}") from exc

    def register(self, commitment: CommitmentRecord) -> CommitmentRecord:
        if commitment.commitment_id in self._commitments:
            raise CommitmentLedgerError(f"commitment already exists: {commitment.commitment_id}")
        if commitment.status != "PROPOSED" and not commitment.provenance.is_owner_authority:
            raise CommitmentLedgerError("only PROPOSED commitments may enter without Owner authority")
        self._commitments[commitment.commitment_id] = commitment
        self._events.append({"event": "COMMITMENT_REGISTERED", "commitment_id": commitment.commitment_id, "status": commitment.status, "authority_digest": commitment.authority_digest()})
        return commitment

    def accept(self, commitment_id: str, *, authority: AuthorityProvenance, reason: str, accepted_at: str) -> CommitmentRecord:
        current = self.get(commitment_id)
        if current.status != "PROPOSED":
            raise CommitmentLedgerError("only PROPOSED commitment can be accepted")
        if not authority.is_owner_authority:
            raise CommitmentLedgerError("Agent or executor cannot self-accept an Owner commitment")
        _bounded_text(reason, "commitment.accept.reason")
        _timestamp(accepted_at, "commitment.accept.accepted_at")
        updated = replace(current, status="ACCEPTED", provenance=authority, version=current.version + 1, updated_at=accepted_at)
        self._commitments[commitment_id] = updated
        self._events.append({"event": "COMMITMENT_ACCEPTED", "commitment_id": commitment_id, "from_status": current.status, "to_status": "ACCEPTED", "reason": reason, "authority_digest": authority_digest(authority), "agent_self_acceptance": False})
        return updated

    def activate(self, commitment_id: str, *, authority: AuthorityProvenance, reason: str, updated_at: str) -> CommitmentRecord:
        current = self.get(commitment_id)
        if current.status != "ACCEPTED":
            raise CommitmentLedgerError("only ACCEPTED commitment can become ACTIVE")
        if not authority.is_owner_authority:
            raise CommitmentLedgerError("commitment activation requires Owner authority")
        _bounded_text(reason, "commitment.activate.reason")
        updated = replace(current, status="ACTIVE", version=current.version + 1, updated_at=updated_at)
        self._commitments[commitment_id] = updated
        self._events.append({"event": "COMMITMENT_ACTIVATED", "commitment_id": commitment_id, "reason": reason, "authority_digest": authority_digest(authority)})
        return updated

    def mark(self, commitment_id: str, status: str, *, authority: AuthorityProvenance, reason: str, updated_at: str) -> CommitmentRecord:
        current = self.get(commitment_id)
        if status not in {"DUE", "BLOCKED", "BREACHED"}:
            raise CommitmentLedgerError("use accept, fulfill, waive, or supersede for terminal commitment operations")
        if current.status not in {"ACCEPTED", "ACTIVE", "DUE", "BLOCKED"}:
            raise CommitmentLedgerError(f"cannot mark commitment from {current.status}")
        _bounded_text(reason, "commitment.mark.reason")
        _timestamp(updated_at, "commitment.mark.updated_at")
        updated = replace(current, status=status, version=current.version + 1, updated_at=updated_at)
        self._commitments[commitment_id] = updated
        self._events.append({"event": "COMMITMENT_STATUS_CHANGED", "commitment_id": commitment_id, "from_status": current.status, "to_status": status, "reason": reason, "authority_digest": authority_digest(authority)})
        return updated

    def fulfill(self, commitment_id: str, *, authority: AuthorityProvenance, evidence_refs: Sequence[str], reason: str, fulfilled_at: str) -> CommitmentRecord:
        current = self.get(commitment_id)
        if current.status not in {"ACCEPTED", "ACTIVE", "DUE", "BLOCKED"}:
            raise CommitmentLedgerError("only open commitment can be fulfilled")
        refs = _refs(evidence_refs, "commitment.fulfill.evidence_refs")
        if not refs:
            raise CommitmentLedgerError("fulfillment requires evidence references")
        if not authority.is_owner_authority and authority.source_type != "SYSTEM_DERIVED_PROPOSAL":
            raise CommitmentLedgerError("fulfillment authority is not recognized")
        _bounded_text(reason, "commitment.fulfill.reason")
        _timestamp(fulfilled_at, "commitment.fulfill.fulfilled_at")
        updated = replace(current, status="FULFILLED", version=current.version + 1, updated_at=fulfilled_at)
        self._commitments[commitment_id] = updated
        self._events.append({"event": "COMMITMENT_FULFILLED", "commitment_id": commitment_id, "from_status": current.status, "evidence_refs": list(refs), "reason": reason, "authority_digest": authority_digest(authority)})
        return updated

    def waive(self, commitment_id: str, *, authority: AuthorityProvenance, reason: str, waived_at: str) -> CommitmentRecord:
        current = self.get(commitment_id)
        if current.status in {"FULFILLED", "WAIVED", "SUPERSEDED"}:
            raise CommitmentLedgerError("terminal commitment cannot be waived")
        if not authority.is_owner_authority:
            raise CommitmentLedgerError("only Owner may waive a commitment")
        _bounded_text(reason, "commitment.waive.reason")
        updated = replace(current, status="WAIVED", provenance=authority, version=current.version + 1, updated_at=waived_at)
        self._commitments[commitment_id] = updated
        self._events.append({"event": "COMMITMENT_WAIVED", "commitment_id": commitment_id, "reason": reason, "authority_digest": authority_digest(authority)})
        return updated

    def supersede(self, commitment_id: str, replacement: CommitmentRecord, *, authority: AuthorityProvenance, reason: str, updated_at: str) -> tuple[CommitmentRecord, CommitmentRecord]:
        current = self.get(commitment_id)
        if replacement.supersedes_commitment_id != commitment_id:
            raise CommitmentLedgerError("replacement must preserve commitment lineage")
        if not authority.is_owner_authority:
            raise CommitmentLedgerError("only Owner may supersede a commitment")
        if replacement.commitment_id in self._commitments:
            raise CommitmentLedgerError("replacement commitment already exists")
        _bounded_text(reason, "commitment.supersede.reason")
        old = replace(current, status="SUPERSEDED", version=current.version + 1, provenance=authority, updated_at=updated_at)
        self._commitments[commitment_id] = old
        self.register(replacement)
        self._events.append({"event": "COMMITMENT_SUPERSEDED", "commitment_id": commitment_id, "replacement_commitment_id": replacement.commitment_id, "lineage_preserved": True, "reason": reason, "authority_digest": authority_digest(authority)})
        return old, replacement

    def to_dict(self) -> dict[str, Any]:
        return {"schema": f"{STEERING_SCHEMA}.commitment-ledger", "commitments": [item.to_dict() for item in self.commitments], "events": list(self._events), "commitment_count": len(self._commitments)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CommitmentLedger":
        if data.get("schema") != f"{STEERING_SCHEMA}.commitment-ledger":
            raise CommitmentLedgerError("commitment ledger schema mismatch")
        ledger = cls(CommitmentRecord.from_dict(row) for row in data.get("commitments", ()))
        events = data.get("events", [])
        if not isinstance(events, list):
            raise CommitmentLedgerError("commitment events must be an array")
        ledger._events = [dict(event) for event in events]
        return ledger


TEMPORAL_STATES = frozenset({"UNKNOWN", "NOT_YET", "ACTIVE_WINDOW", "DUE", "REVIEW_DUE", "GRACE", "OVERDUE", "STALE"})
DEPENDENCY_EDGE_TYPES = frozenset({"PREREQUISITE", "ENABLES", "CONFLICTS_WITH", "SUPERSEDES", "SHARES_RESOURCE", "REVIEW_AFTER", "BLOCKS", "BLOCKED_BY"})
_CYCLE_EDGE_TYPES = frozenset({"PREREQUISITE", "ENABLES", "SUPERSEDES", "BLOCKS", "BLOCKED_BY"})
_ACTIVE_DEPENDENCY_EDGE_TYPES = frozenset({"PREREQUISITE", "ENABLES", "BLOCKS", "BLOCKED_BY"})


def _parse_dt(value: str, field: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise SteeringValidationError(f"{field} must include a timezone")
    return parsed


@dataclass(frozen=True)
class TemporalWindow:
    """Explicit time semantics; it describes state but never runs a daemon."""

    window_id: str
    timezone: str
    source_type: str
    source_ref: str
    not_before: str | None = None
    deadline: str | None = None
    review_after: str | None = None
    grace_seconds: int = 0
    recurrence: Mapping[str, Any] | None = None
    unknown_time: bool = False

    def __post_init__(self) -> None:
        _safe_id(self.window_id, "temporal.window_id")
        _bounded_text(self.timezone, "temporal.timezone")
        if self.source_type not in INTENT_SOURCE_TYPES:
            raise SteeringValidationError("temporal source_type is not recognized")
        _safe_id(self.source_ref, "temporal.source_ref")
        for field in ("not_before", "deadline", "review_after"):
            object.__setattr__(self, field, _optional_timestamp(getattr(self, field), f"temporal.{field}"))
        if not isinstance(self.grace_seconds, int) or isinstance(self.grace_seconds, bool) or self.grace_seconds < 0:
            raise SteeringValidationError("temporal.grace_seconds must be a non-negative integer")
        object.__setattr__(self, "recurrence", _public_value(self.recurrence, "temporal.recurrence") if self.recurrence is not None else None)
        if not isinstance(self.unknown_time, bool):
            raise SteeringValidationError("temporal.unknown_time must be boolean")
        if self.unknown_time and any(value is not None for value in (self.not_before, self.deadline, self.review_after)):
            raise SteeringValidationError("unknown temporal window cannot also claim explicit timestamps")
        if not self.unknown_time and all(value is None for value in (self.not_before, self.deadline, self.review_after)):
            raise SteeringValidationError("missing time must be explicitly marked unknown_time")
        if self.not_before and self.deadline and _parse_dt(self.deadline, "temporal.deadline") < _parse_dt(self.not_before, "temporal.not_before"):
            raise SteeringValidationError("deadline cannot precede not_before")
        if self.review_after and self.deadline and _parse_dt(self.review_after, "temporal.review_after") < _parse_dt(self.deadline, "temporal.deadline"):
            raise SteeringValidationError("review_after cannot precede deadline")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.temporal-window",
            "window_id": self.window_id,
            "timezone": self.timezone,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "not_before": self.not_before,
            "deadline": self.deadline,
            "review_after": self.review_after,
            "grace_seconds": self.grace_seconds,
            "recurrence": self.recurrence,
            "unknown_time": self.unknown_time,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TemporalWindow":
        if data.get("schema") not in {None, f"{STEERING_SCHEMA}.temporal-window"}:
            raise SteeringValidationError("temporal window schema mismatch")
        return cls(
            window_id=data["window_id"], timezone=data["timezone"], source_type=data["source_type"], source_ref=data["source_ref"],
            not_before=data.get("not_before"), deadline=data.get("deadline"), review_after=data.get("review_after"),
            grace_seconds=data.get("grace_seconds", 0), recurrence=data.get("recurrence"), unknown_time=data.get("unknown_time", False),
        )


@dataclass(frozen=True)
class TemporalEvaluation:
    window_id: str
    evaluated_at: str
    state: str
    reason: str
    source_type: str
    deadline: str | None
    grace_until: str | None

    def __post_init__(self) -> None:
        _safe_id(self.window_id, "temporal.evaluation.window_id")
        _timestamp(self.evaluated_at, "temporal.evaluation.evaluated_at")
        if self.state not in TEMPORAL_STATES:
            raise SteeringValidationError("unknown temporal evaluation state")
        _bounded_text(self.reason, "temporal.evaluation.reason")
        if self.source_type not in INTENT_SOURCE_TYPES:
            raise SteeringValidationError("temporal evaluation source_type is not recognized")
        _optional_timestamp(self.deadline, "temporal.evaluation.deadline")
        _optional_timestamp(self.grace_until, "temporal.evaluation.grace_until")

    def to_dict(self) -> dict[str, Any]:
        return {"schema": f"{STEERING_SCHEMA}.temporal-evaluation", "window_id": self.window_id, "evaluated_at": self.evaluated_at, "state": self.state, "reason": self.reason, "source_type": self.source_type, "deadline": self.deadline, "grace_until": self.grace_until}


def evaluate_temporal(window: TemporalWindow, *, now: str) -> TemporalEvaluation:
    """Classify a fixed temporal window; unknown timestamps remain unknown."""

    _timestamp(now, "temporal.now")
    current = _parse_dt(now, "temporal.now")
    if window.unknown_time:
        return TemporalEvaluation(window.window_id, now, "UNKNOWN", "time source is unknown; OS must not fill or infer it", window.source_type, window.deadline, None)
    if window.not_before and current < _parse_dt(window.not_before, "temporal.not_before"):
        return TemporalEvaluation(window.window_id, now, "NOT_YET", "not_before window has not opened", window.source_type, window.deadline, None)
    if window.deadline:
        deadline = _parse_dt(window.deadline, "temporal.deadline")
        grace_until = deadline.timestamp() + window.grace_seconds
        grace_dt = datetime.fromtimestamp(grace_until, tz=deadline.tzinfo)
        if current > grace_dt:
            return TemporalEvaluation(window.window_id, now, "STALE", "deadline and grace window have elapsed", window.source_type, window.deadline, grace_dt.isoformat())
        if current > deadline:
            return TemporalEvaluation(window.window_id, now, "GRACE", "deadline elapsed but explicit grace window remains", window.source_type, window.deadline, grace_dt.isoformat())
        if current == deadline:
            return TemporalEvaluation(window.window_id, now, "DUE", "current time equals explicit deadline", window.source_type, window.deadline, grace_dt.isoformat())
    if window.review_after and current >= _parse_dt(window.review_after, "temporal.review_after"):
        return TemporalEvaluation(window.window_id, now, "REVIEW_DUE", "review_after boundary has arrived", window.source_type, window.deadline, None)
    return TemporalEvaluation(window.window_id, now, "ACTIVE_WINDOW", "window is open and explicit deadline is not yet due", window.source_type, window.deadline, None)


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_kind: str
    namespace: str
    status: str = "ACTIVE"
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.node_id, "graph.node_id")
        if self.node_kind not in {"INTENT", "GOAL", "COMMITMENT"}:
            raise SteeringValidationError("graph node kind must be INTENT, GOAL, or COMMITMENT")
        _safe_id(self.namespace, "graph.namespace")
        _bounded_text(self.status, "graph.status")
        if self.superseded_by is not None:
            _safe_id(self.superseded_by, "graph.superseded_by")

    def to_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "node_kind": self.node_kind, "namespace": self.namespace, "status": self.status, "superseded_by": self.superseded_by}


@dataclass(frozen=True)
class DependencyEdge:
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    reason: str
    shared_scope_ref: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.edge_id, "graph.edge_id")
        _safe_id(self.source_id, "graph.edge.source_id")
        _safe_id(self.target_id, "graph.edge.target_id")
        if self.source_id == self.target_id:
            raise SteeringValidationError("dependency edge cannot point to itself")
        if self.edge_type not in DEPENDENCY_EDGE_TYPES:
            raise SteeringValidationError(f"unknown dependency edge type: {self.edge_type}")
        _bounded_text(self.reason, "graph.edge.reason")
        if self.shared_scope_ref is not None:
            _safe_id(self.shared_scope_ref, "graph.edge.shared_scope_ref")

    def to_dict(self) -> dict[str, Any]:
        return {"edge_id": self.edge_id, "source_id": self.source_id, "target_id": self.target_id, "edge_type": self.edge_type, "reason": self.reason, "shared_scope_ref": self.shared_scope_ref}


class GoalDependencyGraphError(SteeringValidationError):
    """Raised when a long-term dependency graph is not safely traversable."""


class GoalDependencyGraph:
    """Goal/Commitment graph; intentionally not the Supervisor Run DAG."""

    def __init__(self, nodes: Sequence[GraphNode] = (), edges: Sequence[DependencyEdge] = ()) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, DependencyEdge] = {}
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)

    @property
    def nodes(self) -> tuple[GraphNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[DependencyEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def add_node(self, node: GraphNode) -> GraphNode:
        if node.node_id in self._nodes:
            raise GoalDependencyGraphError(f"duplicate graph node: {node.node_id}")
        if node.superseded_by is not None and node.superseded_by == node.node_id:
            raise GoalDependencyGraphError("node cannot supersede itself")
        self._nodes[node.node_id] = node
        return node

    def add_edge(self, edge: DependencyEdge) -> DependencyEdge:
        if edge.edge_id in self._edges:
            raise GoalDependencyGraphError(f"duplicate graph edge: {edge.edge_id}")
        source = self._nodes.get(edge.source_id)
        target = self._nodes.get(edge.target_id)
        if source is None or target is None:
            raise GoalDependencyGraphError("dependency edge references a dangling node")
        if source.namespace != target.namespace and edge.shared_scope_ref is None:
            raise GoalDependencyGraphError("cross-namespace dependency requires explicit shared_scope_ref")
        if source.status == "SUPERSEDED" and edge.edge_type in _ACTIVE_DEPENDENCY_EDGE_TYPES:
            raise GoalDependencyGraphError("superseded node cannot create a new active dependency")
        self._edges[edge.edge_id] = edge
        try:
            self.validate()
        except Exception:
            self._edges.pop(edge.edge_id, None)
            raise
        return edge

    def outgoing(self, node_id: str, *, edge_types: Sequence[str] | None = None, include_superseded: bool = False) -> tuple[DependencyEdge, ...]:
        _safe_id(node_id, "graph.node_id")
        allowed = set(edge_types or DEPENDENCY_EDGE_TYPES)
        if any(edge_type not in DEPENDENCY_EDGE_TYPES for edge_type in allowed):
            raise GoalDependencyGraphError("unknown requested edge type")
        result = []
        for edge in self.edges:
            if edge.source_id != node_id or edge.edge_type not in allowed:
                continue
            target = self._nodes[edge.target_id]
            if target.status == "SUPERSEDED" and not include_superseded:
                continue
            result.append(edge)
        return tuple(result)

    def traverse(self, root_id: str, *, edge_types: Sequence[str] | None = None, include_superseded: bool = False) -> tuple[str, ...]:
        if root_id not in self._nodes:
            raise GoalDependencyGraphError(f"unknown graph root: {root_id}")
        visited: set[str] = set()
        queue = [root_id]
        while queue:
            current = queue.pop(0)
            for edge in self.outgoing(current, edge_types=edge_types, include_superseded=include_superseded):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append(edge.target_id)
            queue.sort()
        return tuple(sorted(visited))

    def validate(self) -> list[str]:
        errors: list[str] = []
        for edge in self.edges:
            if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
                errors.append(f"DANGLING_REF:{edge.edge_id}")
            elif self._nodes[edge.source_id].namespace != self._nodes[edge.target_id].namespace and edge.shared_scope_ref is None:
                errors.append(f"NAMESPACE_BOUNDARY:{edge.edge_id}")
        adjacency: dict[str, list[str]] = {node_id: [] for node_id in self._nodes}
        for edge in self.edges:
            if edge.edge_type in _CYCLE_EDGE_TYPES and edge.source_id in adjacency and edge.target_id in adjacency:
                adjacency[edge.source_id].append(edge.target_id)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise GoalDependencyGraphError("dependency graph contains a cycle")
            if node_id in visited:
                return
            visiting.add(node_id)
            for target_id in sorted(adjacency[node_id]):
                visit(target_id)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in sorted(adjacency):
            visit(node_id)
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {"schema": f"{STEERING_SCHEMA}.goal-dependency-graph", "graph_kind": "LONG_TERM_STEERING", "nodes": [node.to_dict() for node in self.nodes], "edges": [edge.to_dict() for edge in self.edges], "node_count": len(self._nodes), "edge_count": len(self._edges)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GoalDependencyGraph":
        if data.get("schema") != f"{STEERING_SCHEMA}.goal-dependency-graph" or data.get("graph_kind") != "LONG_TERM_STEERING":
            raise GoalDependencyGraphError("graph schema or graph_kind mismatch")
        return cls(tuple(GraphNode(**row) for row in data.get("nodes", ())), tuple(DependencyEdge(**row) for row in data.get("edges", ())))


RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "IRREVERSIBLE")
PRIORITY_COMMITMENT_ORDER = {"BREACHED": 0, "DUE": 1, "ACTIVE": 2, "ACCEPTED": 3, "BLOCKED": 4, "PROPOSED": 5, "FULFILLED": 6, "WAIVED": 7, "SUPERSEDED": 8}


@dataclass(frozen=True)
class OwnerOverride:
    override_id: str
    goal_id: str
    rank: int
    reason: str
    provenance: AuthorityProvenance
    created_at: str
    active: bool = True

    def __post_init__(self) -> None:
        _safe_id(self.override_id, "priority.override_id")
        _safe_id(self.goal_id, "priority.override.goal_id")
        if not isinstance(self.rank, int) or isinstance(self.rank, bool) or self.rank < 0:
            raise SteeringValidationError("priority override rank must be non-negative")
        _bounded_text(self.reason, "priority.override.reason")
        if not self.provenance.is_owner_authority:
            raise SteeringValidationError("priority override requires explicit Owner authority")
        _timestamp(self.created_at, "priority.override.created_at")
        if not isinstance(self.active, bool):
            raise SteeringValidationError("priority override active must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {"override_id": self.override_id, "goal_id": self.goal_id, "rank": self.rank, "reason": self.reason, "provenance": self.provenance.to_dict(), "created_at": self.created_at, "active": self.active}


@dataclass(frozen=True)
class PriorityInputs:
    goal_id: str
    owner_rank: int | None
    commitment_status: str = "PROPOSED"
    dependency_criticality: int = 0
    risk_level: str = "LOW"
    resource_available: bool = True
    blocked: bool = False
    permission_eligible: bool = True
    fairness_age: int = 0
    deadline_state: str = "UNKNOWN"
    owner_override: OwnerOverride | None = None
    approval_required: bool = False
    unknowns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _safe_id(self.goal_id, "priority.goal_id")
        if self.owner_rank is not None and (not isinstance(self.owner_rank, int) or isinstance(self.owner_rank, bool) or self.owner_rank < 0):
            raise SteeringValidationError("owner_rank must be non-negative or None")
        if self.commitment_status not in COMMITMENT_STATUSES:
            raise SteeringValidationError("priority commitment_status is invalid")
        if not isinstance(self.dependency_criticality, int) or isinstance(self.dependency_criticality, bool) or self.dependency_criticality < 0:
            raise SteeringValidationError("dependency_criticality must be non-negative")
        if self.risk_level not in RISK_LEVELS:
            raise SteeringValidationError("priority risk_level is invalid")
        for field in ("resource_available", "blocked", "permission_eligible", "approval_required"):
            if not isinstance(getattr(self, field), bool):
                raise SteeringValidationError(f"priority.{field} must be boolean")
        if not isinstance(self.fairness_age, int) or isinstance(self.fairness_age, bool) or self.fairness_age < 0:
            raise SteeringValidationError("fairness_age must be non-negative")
        _bounded_text(self.deadline_state, "priority.deadline_state")
        object.__setattr__(self, "unknowns", _refs(self.unknowns, "priority.unknowns"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "owner_rank": self.owner_rank,
            "commitment_status": self.commitment_status,
            "dependency_criticality": self.dependency_criticality,
            "risk_level": self.risk_level,
            "resource_available": self.resource_available,
            "blocked": self.blocked,
            "permission_eligible": self.permission_eligible,
            "fairness_age": self.fairness_age,
            "deadline_state": self.deadline_state,
            "owner_override": self.owner_override.to_dict() if self.owner_override is not None else None,
            "approval_required": self.approval_required,
            "unknowns": list(self.unknowns),
        }


@dataclass(frozen=True)
class PriorityDecision:
    goal_id: str
    eligible: bool
    lexicographic_key: tuple[int, ...]
    reasons: tuple[str, ...]
    owner_override_visible: bool
    owner_override_retractable: bool
    telemetry_score: float | None
    authority: str
    inputs: PriorityInputs

    def __post_init__(self) -> None:
        _safe_id(self.goal_id, "priority.decision.goal_id")
        if not isinstance(self.eligible, bool):
            raise SteeringValidationError("priority decision eligible must be boolean")
        if not isinstance(self.lexicographic_key, tuple) or any(not isinstance(value, int) for value in self.lexicographic_key):
            raise SteeringValidationError("priority lexicographic key must be integer tuple")
        object.__setattr__(self, "reasons", _refs(self.reasons, "priority.decision.reasons"))
        if not isinstance(self.owner_override_visible, bool) or not isinstance(self.owner_override_retractable, bool):
            raise SteeringValidationError("priority override visibility flags must be boolean")
        if self.telemetry_score is not None and not isinstance(self.telemetry_score, (int, float)):
            raise SteeringValidationError("priority telemetry_score must be numeric")
        _bounded_text(self.authority, "priority.decision.authority")

    def to_dict(self) -> dict[str, Any]:
        return {"schema": f"{STEERING_SCHEMA}.priority-decision", "goal_id": self.goal_id, "eligible": self.eligible, "lexicographic_key": list(self.lexicographic_key), "reasons": list(self.reasons), "owner_override_visible": self.owner_override_visible, "owner_override_retractable": self.owner_override_retractable, "telemetry_score": self.telemetry_score, "authority": self.authority, "inputs": self.inputs.to_dict()}


class PriorityPolicy:
    """Explainable policy; no opaque score is allowed to be the authority."""

    def evaluate(self, inputs: PriorityInputs) -> PriorityDecision:
        reasons: list[str] = []
        eligible = True
        if not inputs.permission_eligible:
            eligible = False
            reasons.append("permission_ineligible")
        if inputs.blocked:
            eligible = False
            reasons.append("blocked")
        if not inputs.resource_available:
            eligible = False
            reasons.append("resource_unavailable")
        if inputs.risk_level in {"HIGH", "IRREVERSIBLE"} and inputs.approval_required:
            reasons.append("high_risk_requires_explicit_approval")
        if inputs.deadline_state in {"DUE", "OVERDUE", "STALE", "GRACE"}:
            reasons.append(f"temporal_{inputs.deadline_state.casefold()}")
        if inputs.commitment_status in {"DUE", "BREACHED"}:
            reasons.append(f"commitment_{inputs.commitment_status.casefold()}")
        if inputs.unknowns:
            reasons.append("unknown_inputs_preserved")
        override_rank = inputs.owner_override.rank if inputs.owner_override and inputs.owner_override.active else 10**6
        owner_rank = inputs.owner_rank if inputs.owner_rank is not None else 10**5
        commitment_rank = PRIORITY_COMMITMENT_ORDER[inputs.commitment_status]
        deadline_rank = {"OVERDUE": 0, "STALE": 1, "DUE": 2, "GRACE": 3, "REVIEW_DUE": 4, "ACTIVE_WINDOW": 5, "NOT_YET": 6, "UNKNOWN": 7}.get(inputs.deadline_state, 8)
        risk_rank = {"IRREVERSIBLE": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[inputs.risk_level]
        key = (0 if eligible else 1, override_rank, owner_rank, commitment_rank, deadline_rank, -inputs.dependency_criticality, risk_rank, -inputs.fairness_age)
        telemetry_score = float((10**6 - min(override_rank, 10**6)) + (10**5 - min(owner_rank, 10**5)) + inputs.dependency_criticality + inputs.fairness_age)
        if not reasons:
            reasons.append("eligible_with_explicit_inputs")
        return PriorityDecision(inputs.goal_id, eligible, key, tuple(reasons), inputs.owner_override is not None, inputs.owner_override is not None, telemetry_score, "LEXICOGRAPHIC_RULES_R1", inputs)

    def order(self, candidates: Sequence[PriorityInputs]) -> tuple[PriorityDecision, ...]:
        decisions = [self.evaluate(candidate) for candidate in candidates]
        return tuple(sorted(decisions, key=lambda decision: (decision.lexicographic_key, decision.goal_id)))

    def retract_override(self, override: OwnerOverride) -> OwnerOverride:
        if not override.provenance.is_owner_authority:
            raise SteeringValidationError("only Owner override can be retracted")
        return replace(override, active=False)


CONFLICT_TYPES = frozenset({
    "RESOURCE_CONTENTION",
    "PERMISSION_VS_DEADLINE",
    "DEADLINE_VS_SAFETY",
    "OVERRIDE_VS_AUTOMATION",
    "MUTUALLY_EXCLUSIVE_GOALS",
    "SUPERSEDED_INTENT",
    "EXECUTOR_UNAVAILABLE",
})
ARBITRATION_OUTCOMES = frozenset({"SELECTED", "BLOCKED", "DEFERRED", "RECONCILIATION_REQUIRED", "HUMAN_REVIEW"})


@dataclass(frozen=True)
class ConflictCandidate:
    """A candidate plus state that can make an otherwise valid priority unsafe."""

    priority_inputs: PriorityInputs
    intent_status: str = "ACTIVE"
    mutually_exclusive_group: str | None = None
    executor_available: bool = True
    stale: bool = False
    superseded: bool = False
    safety_critical: bool = False

    @property
    def goal_id(self) -> str:
        return self.priority_inputs.goal_id

    def __post_init__(self) -> None:
        if self.intent_status not in INTENT_STATUSES:
            raise SteeringValidationError("conflict candidate intent_status is invalid")
        if self.mutually_exclusive_group is not None:
            _safe_id(self.mutually_exclusive_group, "conflict.mutually_exclusive_group")
        for field in ("executor_available", "stale", "superseded", "safety_critical"):
            if not isinstance(getattr(self, field), bool):
                raise SteeringValidationError(f"conflict.{field} must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "priority_inputs": self.priority_inputs.to_dict(),
            "intent_status": self.intent_status,
            "mutually_exclusive_group": self.mutually_exclusive_group,
            "executor_available": self.executor_available,
            "stale": self.stale,
            "superseded": self.superseded,
            "safety_critical": self.safety_critical,
        }


@dataclass(frozen=True)
class ArbitrationReceipt:
    arbitration_id: str
    conflict_type: str
    outcome: str
    selected_goal_id: str | None
    decisions: tuple[PriorityDecision, ...]
    reasons: tuple[str, ...]
    reconciliation_required: bool
    created_at: str
    authority: str = "LEXICOGRAPHIC_RULES_R1_WITH_EXPLICIT_RECONCILIATION"

    def __post_init__(self) -> None:
        _safe_id(self.arbitration_id, "arbitration_id")
        if self.conflict_type not in CONFLICT_TYPES:
            raise SteeringValidationError("arbitration conflict_type is invalid")
        if self.outcome not in ARBITRATION_OUTCOMES:
            raise SteeringValidationError("arbitration outcome is invalid")
        if self.selected_goal_id is not None:
            _safe_id(self.selected_goal_id, "arbitration.selected_goal_id")
        if not isinstance(self.decisions, tuple) or not self.decisions:
            raise SteeringValidationError("arbitration requires priority decisions")
        object.__setattr__(self, "reasons", _refs(self.reasons, "arbitration.reasons"))
        if not isinstance(self.reconciliation_required, bool):
            raise SteeringValidationError("arbitration reconciliation_required must be boolean")
        _timestamp(self.created_at, "arbitration.created_at")
        _bounded_text(self.authority, "arbitration.authority")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.arbitration-receipt",
            "arbitration_id": self.arbitration_id,
            "conflict_type": self.conflict_type,
            "outcome": self.outcome,
            "selected_goal_id": self.selected_goal_id,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "reasons": list(self.reasons),
            "reconciliation_required": self.reconciliation_required,
            "created_at": self.created_at,
            "authority": self.authority,
        }


class ConflictArbiter:
    """Resolve only what explicit policy inputs permit; preserve unsafe conflicts."""

    def __init__(self, policy: PriorityPolicy | None = None) -> None:
        self.policy = policy or PriorityPolicy()

    def arbitrate(self, arbitration_id: str, conflict_type: str, candidates: Sequence[ConflictCandidate], *, created_at: str) -> ArbitrationReceipt:
        _safe_id(arbitration_id, "arbitration_id")
        if conflict_type not in CONFLICT_TYPES:
            raise SteeringValidationError("unknown arbitration conflict_type")
        _timestamp(created_at, "arbitration.created_at")
        candidate_list = tuple(candidates)
        if not candidate_list:
            raise SteeringValidationError("arbitration requires at least one candidate")
        if len({candidate.goal_id for candidate in candidate_list}) != len(candidate_list):
            raise SteeringValidationError("arbitration candidate goal_ids must be unique")

        decisions = self.policy.order(tuple(candidate.priority_inputs for candidate in candidate_list))
        by_goal = {candidate.goal_id: candidate for candidate in candidate_list}
        reasons: list[str] = []
        usable: list[tuple[PriorityDecision, ConflictCandidate]] = []
        has_permission_block = False
        has_reconciliation = False
        has_human_review = False

        for decision in decisions:
            candidate = by_goal[decision.goal_id]
            owner_override_active = bool(candidate.priority_inputs.owner_override and candidate.priority_inputs.owner_override.active)
            if candidate.superseded or candidate.intent_status == "SUPERSEDED":
                has_reconciliation = True
                reasons.append(f"superseded_intent:{candidate.goal_id}")
                continue
            if candidate.stale and not owner_override_active:
                has_reconciliation = True
                reasons.append(f"stale_priority:{candidate.goal_id}")
                continue
            if not candidate.executor_available:
                has_reconciliation = True
                reasons.append(f"executor_unavailable:{candidate.goal_id}")
                continue
            if not decision.eligible:
                if not candidate.priority_inputs.permission_eligible:
                    has_permission_block = True
                reasons.extend(f"{reason}:{candidate.goal_id}" for reason in decision.reasons if reason in {"permission_ineligible", "blocked", "resource_unavailable"})
                continue
            if candidate.safety_critical and candidate.priority_inputs.approval_required and not owner_override_active:
                has_human_review = True
                reasons.append(f"safety_requires_owner_review:{candidate.goal_id}")
                continue
            usable.append((decision, candidate))

        if has_human_review:
            outcome = "HUMAN_REVIEW"
            selected_goal_id = None
            reasons.append("unsafe_safety_conflict_not_auto_resolved")
        elif usable:
            selected_goal_id = usable[0][0].goal_id
            outcome = "SELECTED"
            reasons.append(f"selected_by_lexicographic_policy:{selected_goal_id}")
            if conflict_type == "MUTUALLY_EXCLUSIVE_GOALS" or any(candidate.mutually_exclusive_group for _, candidate in usable):
                reasons.append("mutually_exclusive_losers_deferred")
            if has_reconciliation:
                reasons.append("stale_or_unavailable_candidates_preserved_for_reconciliation")
        elif has_reconciliation:
            outcome = "RECONCILIATION_REQUIRED"
            selected_goal_id = None
            reasons.append("no_safe_candidate_after_state_reconciliation")
        elif has_permission_block:
            outcome = "BLOCKED"
            selected_goal_id = None
            reasons.append("permission_ceiling_blocks_arbitration")
        else:
            outcome = "DEFERRED"
            selected_goal_id = None
            reasons.append("no_eligible_candidate")

        return ArbitrationReceipt(arbitration_id, conflict_type, outcome, selected_goal_id, decisions, tuple(reasons), outcome == "RECONCILIATION_REQUIRED" or has_reconciliation, created_at)


@dataclass(frozen=True)
class NextWorkCandidate:
    """Human-facing selection metadata kept beside the policy candidate."""

    conflict_candidate: ConflictCandidate
    pack_ref: str | None = None
    executor_ref: str | None = None
    budget_available: bool = True
    blockers: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()

    @property
    def goal_id(self) -> str:
        return self.conflict_candidate.goal_id

    def __post_init__(self) -> None:
        for field in ("pack_ref", "executor_ref"):
            value = getattr(self, field)
            if value is not None:
                _safe_id(value, f"why_next.{field}")
        if not isinstance(self.budget_available, bool):
            raise SteeringValidationError("why_next.budget_available must be boolean")
        object.__setattr__(self, "blockers", _refs(self.blockers, "why_next.blockers"))
        object.__setattr__(self, "unknowns", _refs(self.unknowns, "why_next.unknowns"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "conflict_candidate": self.conflict_candidate.to_dict(),
            "pack_ref": self.pack_ref,
            "executor_ref": self.executor_ref,
            "budget_available": self.budget_available,
            "blockers": list(self.blockers),
            "unknowns": list(self.unknowns),
        }


@dataclass(frozen=True)
class SkippedGoal:
    goal_id: str
    reasons: tuple[str, ...]
    eligible: bool
    lexicographic_key: tuple[int, ...]

    def __post_init__(self) -> None:
        _safe_id(self.goal_id, "why_next.skipped_goal_id")
        object.__setattr__(self, "reasons", _refs(self.reasons, "why_next.skipped_reasons"))
        if not isinstance(self.eligible, bool):
            raise SteeringValidationError("why_next skipped eligible must be boolean")
        if not isinstance(self.lexicographic_key, tuple) or any(not isinstance(value, int) for value in self.lexicographic_key):
            raise SteeringValidationError("why_next skipped lexicographic key must be integer tuple")

    def to_dict(self) -> dict[str, Any]:
        return {"goal_id": self.goal_id, "reasons": list(self.reasons), "eligible": self.eligible, "lexicographic_key": list(self.lexicographic_key)}


@dataclass(frozen=True)
class DecisionTrace:
    """Complete answer to why the OS selected, deferred, or blocked next work."""

    trace_id: str
    selected_goal_id: str | None
    why_now: str
    why_selected: str
    skipped_goals: tuple[SkippedGoal, ...]
    blockers: tuple[str, ...]
    permission_budget_resource: tuple[str, ...]
    owner_override_ref: str | None
    pack_ref: str | None
    executor_ref: str | None
    unknowns: tuple[str, ...]
    arbitration: ArbitrationReceipt
    created_at: str
    authority: str = "STEERING_EXPLAINABILITY_INVARIANT"

    def __post_init__(self) -> None:
        _safe_id(self.trace_id, "why_next.trace_id")
        if self.selected_goal_id is not None:
            _safe_id(self.selected_goal_id, "why_next.selected_goal_id")
        _bounded_text(self.why_now, "why_next.why_now")
        _bounded_text(self.why_selected, "why_next.why_selected")
        object.__setattr__(self, "blockers", _refs(self.blockers, "why_next.blockers"))
        object.__setattr__(self, "permission_budget_resource", _refs(self.permission_budget_resource, "why_next.permission_budget_resource"))
        object.__setattr__(self, "unknowns", _refs(self.unknowns, "why_next.unknowns"))
        if self.owner_override_ref is not None:
            _safe_id(self.owner_override_ref, "why_next.owner_override_ref")
        if self.pack_ref is not None:
            _safe_id(self.pack_ref, "why_next.pack_ref")
        if self.executor_ref is not None:
            _safe_id(self.executor_ref, "why_next.executor_ref")
        _timestamp(self.created_at, "why_next.created_at")
        _bounded_text(self.authority, "why_next.authority")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.decision-trace",
            "trace_id": self.trace_id,
            "selected_goal_id": self.selected_goal_id,
            "why_now": self.why_now,
            "why_selected": self.why_selected,
            "skipped_goals": [item.to_dict() for item in self.skipped_goals],
            "blockers": list(self.blockers),
            "permission_budget_resource": list(self.permission_budget_resource),
            "owner_override_ref": self.owner_override_ref,
            "pack_ref": self.pack_ref,
            "executor_ref": self.executor_ref,
            "unknowns": list(self.unknowns),
            "arbitration": self.arbitration.to_dict(),
            "created_at": self.created_at,
            "authority": self.authority,
        }


class SteeringEngine:
    """Build an auditable next-work trace from explicit steering inputs."""

    def __init__(self, arbiter: ConflictArbiter | None = None) -> None:
        self.arbiter = arbiter or ConflictArbiter()

    def select_next(self, trace_id: str, conflict_type: str, candidates: Sequence[NextWorkCandidate], *, created_at: str) -> DecisionTrace:
        _safe_id(trace_id, "why_next.trace_id")
        candidate_list = tuple(candidates)
        if not candidate_list:
            raise SteeringValidationError("why_next requires at least one candidate")
        adjusted: list[ConflictCandidate] = []
        for candidate in candidate_list:
            priority = candidate.conflict_candidate.priority_inputs
            if not candidate.budget_available and priority.resource_available:
                priority = replace(priority, resource_available=False, unknowns=priority.unknowns + ("budget_unavailable",))
            adjusted.append(replace(candidate.conflict_candidate, priority_inputs=priority))
        arbitration = self.arbiter.arbitrate(f"{trace_id}.arbitration", conflict_type, adjusted, created_at=created_at)
        by_goal = {candidate.goal_id: candidate for candidate in candidate_list}
        skipped: list[SkippedGoal] = []
        blockers: list[str] = []
        permission_budget_resource: list[str] = []
        unknowns: list[str] = []
        selected_candidate = by_goal.get(arbitration.selected_goal_id) if arbitration.selected_goal_id else None

        for candidate in candidate_list:
            decision = next(item for item in arbitration.decisions if item.goal_id == candidate.goal_id)
            permission_budget_resource.extend((
                f"{candidate.goal_id}:permission={'eligible' if decision.inputs.permission_eligible else 'ineligible'}",
                f"{candidate.goal_id}:budget={'available' if candidate.budget_available else 'unavailable'}",
                f"{candidate.goal_id}:resource={'available' if decision.inputs.resource_available else 'unavailable'}",
            ))
            blockers.extend(f"{candidate.goal_id}:{blocker}" for blocker in candidate.blockers)
            unknowns.extend(candidate.unknowns)
            unknowns.extend(decision.inputs.unknowns)
            if candidate.goal_id != arbitration.selected_goal_id:
                reasons = list(decision.reasons)
                if candidate.goal_id in {item.goal_id for item in adjusted if item.stale or item.superseded or item.intent_status == "SUPERSEDED"}:
                    reasons.append("state_requires_reconciliation")
                if not candidate.conflict_candidate.executor_available:
                    reasons.append("executor_unavailable")
                if not candidate.budget_available:
                    reasons.append("budget_unavailable")
                skipped.append(SkippedGoal(candidate.goal_id, tuple(reasons or ("not_selected_by_policy",)), decision.eligible, decision.lexicographic_key))
        blockers.extend(reason for reason in arbitration.reasons if any(marker in reason for marker in ("blocked", "permission", "resource", "reconciliation", "unavailable", "safety")))
        if selected_candidate is not None:
            selected_decision = next(item for item in arbitration.decisions if item.goal_id == selected_candidate.goal_id)
            selected_reasons = ", ".join(selected_decision.reasons)
            why_now = f"{selected_candidate.goal_id} is next because explicit commitment/deadline/dependency inputs are {selected_reasons}."
            why_selected = f"Selected by {selected_decision.authority} with lexicographic key {selected_decision.lexicographic_key}; telemetry score has no authority."
            owner_override_ref = None
            if selected_decision.inputs.owner_override and selected_decision.inputs.owner_override.active:
                owner_override_ref = selected_decision.inputs.owner_override.override_id
                why_selected += f" Owner override {owner_override_ref} is visible and retractable."
            pack_ref = selected_candidate.pack_ref
            executor_ref = selected_candidate.executor_ref
        else:
            why_now = f"No candidate can be safely selected under {arbitration.outcome}; explicit conflict state is preserved."
            why_selected = f"No next action selected: {', '.join(arbitration.reasons)}."
            owner_override_ref = None
            pack_ref = None
            executor_ref = None

        return DecisionTrace(trace_id, arbitration.selected_goal_id, why_now, why_selected, tuple(sorted(skipped, key=lambda item: item.goal_id)), tuple(blockers), tuple(permission_budget_resource), owner_override_ref, pack_ref, executor_ref, tuple(unknowns), arbitration, created_at)


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

    def mark_satisfied(self, decision: CompletionDecision) -> GoalRecord:
        current = self.get(decision.goal_id)
        if decision.outcome != "SATISFIED":
            raise GoalRegistryError("only a SATISFIED CompletionDecision can close a Goal")
        if decision.goal_version != current.version or decision.contract_id != current.completion_contract_id:
            raise GoalRegistryError("completion decision is stale or uses the wrong contract")
        if current.status not in {"PROPOSED", "ACTIVE", "PAUSED", "BLOCKED"}:
            raise GoalRegistryError("only an open Goal can be satisfied")
        updated = replace(current, status="SATISFIED", version=current.version + 1, updated_at=decision.decided_at)
        self._goals[current.goal_id] = updated
        self._events.append({
            "event": "GOAL_SATISFIED",
            "goal_id": current.goal_id,
            "from_status": current.status,
            "to_status": "SATISFIED",
            "from_version": current.version,
            "to_version": updated.version,
            "completion_decision_sha256": decision.decision_sha256,
            "authority_actor_ref": decision.authority_actor_ref,
            "evidence_refs": list(decision.evidence_refs),
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


@dataclass(frozen=True)
class HandoffIdentity:
    run_id: str
    executor_instance_id: str
    sequence: int = 0

    def __post_init__(self) -> None:
        _safe_id(self.run_id, "handoff.run_id")
        _safe_id(self.executor_instance_id, "handoff.executor_instance_id")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 0:
            raise SteeringValidationError("handoff.sequence must be a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "executor_instance_id": self.executor_instance_id, "sequence": self.sequence}


@dataclass(frozen=True)
class EpisodeGoalBinding:
    """A non-authoritative link between one Goal and Supervisor execution records."""

    binding_id: str
    episode_id: str
    primary_goal_id: str
    secondary_goal_ids: tuple[str, ...]
    objective_digest: str
    run_ids: tuple[str, ...]
    episode_status: str
    goal_status_at_bind: str
    handoff_identity_digest: str
    handoff_identities: tuple[HandoffIdentity, ...]
    run_outcomes: tuple[tuple[str, str], ...]
    created_at: str
    updated_at: str
    completion_inference: str = "INDEPENDENT_CONTRACT_REQUIRED"

    def __post_init__(self) -> None:
        for value, field in ((self.binding_id, "binding_id"), (self.episode_id, "episode_id"), (self.primary_goal_id, "primary_goal_id")):
            _safe_id(value, field)
        object.__setattr__(self, "secondary_goal_ids", _refs(self.secondary_goal_ids, "binding.secondary_goal_ids"))
        if self.primary_goal_id in self.secondary_goal_ids:
            raise SteeringValidationError("primary Goal cannot also be a secondary Goal")
        object.__setattr__(self, "run_ids", _refs(self.run_ids, "binding.run_ids"))
        if not self.run_ids:
            raise SteeringValidationError("Goal-Episode binding requires at least one run")
        if not isinstance(self.objective_digest, str) or not _HEX.fullmatch(self.objective_digest):
            raise SteeringValidationError("binding.objective_digest must be a SHA-256 digest")
        _bounded_text(self.episode_status, "binding.episode_status")
        if self.goal_status_at_bind not in GOAL_STATUSES:
            raise SteeringValidationError("binding.goal_status_at_bind is invalid")
        if not isinstance(self.handoff_identity_digest, str) or not _HEX.fullmatch(self.handoff_identity_digest):
            raise SteeringValidationError("binding.handoff_identity_digest must be a SHA-256 digest")
        identities = tuple(self.handoff_identities)
        if {item.run_id for item in identities} != set(self.run_ids):
            raise SteeringValidationError("handoff identities must cover exactly the bound runs")
        object.__setattr__(self, "handoff_identities", tuple(sorted(identities, key=lambda item: item.run_id)))
        outcomes = tuple(self.run_outcomes)
        if any(run_id not in self.run_ids or not isinstance(outcome, str) or not outcome.strip() for run_id, outcome in outcomes):
            raise SteeringValidationError("run outcomes must reference bound runs")
        if len({run_id for run_id, _ in outcomes}) != len(outcomes):
            raise SteeringValidationError("each bound run can have only one current outcome")
        object.__setattr__(self, "run_outcomes", tuple(sorted(outcomes)))
        _timestamp(self.created_at, "binding.created_at")
        _timestamp(self.updated_at, "binding.updated_at")
        if self.completion_inference != "INDEPENDENT_CONTRACT_REQUIRED":
            raise SteeringValidationError("execution binding cannot change completion authority")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.episode-goal-binding",
            "binding_id": self.binding_id,
            "episode_id": self.episode_id,
            "primary_goal_id": self.primary_goal_id,
            "secondary_goal_ids": list(self.secondary_goal_ids),
            "objective_digest": self.objective_digest,
            "run_ids": list(self.run_ids),
            "episode_status": self.episode_status,
            "goal_status_at_bind": self.goal_status_at_bind,
            "handoff_identity_digest": self.handoff_identity_digest,
            "handoff_identities": [item.to_dict() for item in self.handoff_identities],
            "run_outcomes": [{"run_id": run_id, "outcome": outcome} for run_id, outcome in self.run_outcomes],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completion_inference": self.completion_inference,
        }


class GoalEpisodeBinder:
    """Maintain Goal/Episode links without letting execution mutate Goal authority."""

    def __init__(self) -> None:
        self._bindings: dict[str, EpisodeGoalBinding] = {}
        self._events: list[dict[str, Any]] = []

    @property
    def bindings(self) -> tuple[EpisodeGoalBinding, ...]:
        return tuple(self._bindings[key] for key in sorted(self._bindings))

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    def get(self, binding_id: str) -> EpisodeGoalBinding:
        _safe_id(binding_id, "binding_id")
        try:
            return self._bindings[binding_id]
        except KeyError as exc:
            raise SteeringValidationError(f"unknown Goal-Episode binding: {binding_id}") from exc

    @staticmethod
    def _identity_digest(episode_id: str, primary_goal_id: str, run_ids: Sequence[str]) -> str:
        return sha256_json({"episode_id": episode_id, "primary_goal_id": primary_goal_id, "run_ids": sorted(run_ids)})

    def bind(self, goal: GoalRecord, episode_id: str, run_ids: Sequence[str], *, secondary_goal_ids: Sequence[str] = (), executor_instances: Mapping[str, str] | None = None, created_at: str) -> EpisodeGoalBinding:
        if not isinstance(goal, GoalRecord):
            raise SteeringValidationError("Goal-Episode binding requires a GoalRecord")
        _safe_id(episode_id, "episode_id")
        normalized_runs = _refs(run_ids, "binding.run_ids")
        if not normalized_runs:
            raise SteeringValidationError("Goal-Episode binding requires at least one run")
        binding_id = f"binding:{episode_id}:{goal.goal_id}"
        if binding_id in self._bindings:
            raise SteeringValidationError(f"Goal-Episode binding already exists: {binding_id}")
        instances = executor_instances or {}
        if set(instances) - set(normalized_runs):
            raise SteeringValidationError("executor_instances contains an unbound run")
        identities = tuple(HandoffIdentity(run_id, instances.get(run_id, "instance-1")) for run_id in normalized_runs)
        binding = EpisodeGoalBinding(
            binding_id=binding_id,
            episode_id=episode_id,
            primary_goal_id=goal.goal_id,
            secondary_goal_ids=tuple(secondary_goal_ids),
            objective_digest=goal.objective_digest(),
            run_ids=normalized_runs,
            episode_status="ACTIVE",
            goal_status_at_bind=goal.status,
            handoff_identity_digest=self._identity_digest(episode_id, goal.goal_id, normalized_runs),
            handoff_identities=identities,
            run_outcomes=(),
            created_at=created_at,
            updated_at=created_at,
        )
        self._bindings[binding_id] = binding
        self._events.append({"event": "GOAL_EPISODE_BOUND", "binding_id": binding_id, "goal_id": goal.goal_id, "episode_id": episode_id, "run_ids": list(normalized_runs), "goal_status_mutation": False})
        return binding

    def update_episode(self, binding_id: str, episode_status: str, *, updated_at: str) -> EpisodeGoalBinding:
        current = self.get(binding_id)
        _bounded_text(episode_status, "binding.episode_status")
        updated = replace(current, episode_status=episode_status, updated_at=updated_at)
        self._bindings[binding_id] = updated
        self._events.append({"event": "EPISODE_STATUS_UPDATED", "binding_id": binding_id, "episode_status": episode_status, "goal_status_mutation": False, "completion_inference": "INDEPENDENT_CONTRACT_REQUIRED"})
        return updated

    def record_run_outcome(self, binding_id: str, run_id: str, outcome: str, *, updated_at: str) -> EpisodeGoalBinding:
        current = self.get(binding_id)
        _safe_id(run_id, "binding.run_id")
        if run_id not in current.run_ids:
            raise SteeringValidationError("run outcome references a run outside the binding")
        _bounded_text(outcome, "binding.run_outcome")
        outcomes = dict(current.run_outcomes)
        outcomes[run_id] = outcome
        updated = replace(current, run_outcomes=tuple(outcomes.items()), updated_at=updated_at)
        self._bindings[binding_id] = updated
        self._events.append({"event": "RUN_OUTCOME_RECORDED", "binding_id": binding_id, "run_id": run_id, "outcome": outcome, "goal_status_mutation": False, "completion_inference": "INDEPENDENT_CONTRACT_REQUIRED"})
        return updated

    def handoff(self, binding_id: str, run_id: str, executor_instance_id: str, *, updated_at: str) -> EpisodeGoalBinding:
        current = self.get(binding_id)
        _safe_id(run_id, "handoff.run_id")
        if run_id not in current.run_ids:
            raise SteeringValidationError("handoff references a run outside the binding")
        identities = []
        for identity in current.handoff_identities:
            if identity.run_id == run_id:
                identities.append(replace(identity, executor_instance_id=executor_instance_id, sequence=identity.sequence + 1))
            else:
                identities.append(identity)
        updated = replace(current, handoff_identities=tuple(identities), updated_at=updated_at)
        self._bindings[binding_id] = updated
        self._events.append({"event": "EPISODE_HANDOFF_RECORDED", "binding_id": binding_id, "run_id": run_id, "executor_instance_id": executor_instance_id, "handoff_identity_digest_unchanged": True, "goal_status_mutation": False})
        return updated

    def reconcile_run_result(self, binding_id: str, run_id: str, outcome: str) -> dict[str, Any]:
        binding = self.get(binding_id)
        if run_id not in binding.run_ids:
            raise SteeringValidationError("run result references a run outside the binding")
        _bounded_text(outcome, "binding.run_outcome")
        return {"binding_id": binding_id, "run_id": run_id, "run_outcome": outcome, "goal_id": binding.primary_goal_id, "goal_status": binding.goal_status_at_bind, "goal_status_mutated": False, "completion_inference": binding.completion_inference}


DRIFT_OUTCOMES = frozenset({"CLEAR", "PAUSE_RECONCILE", "HUMAN_REVIEW"})


@dataclass(frozen=True)
class DriftReport:
    report_id: str
    goal_id: str
    outcome: str
    reasons: tuple[str, ...]
    expected_objective_digest: str
    observed_objective_digest: str
    missing_acceptance_criteria: tuple[str, ...]
    unexpected_acceptance_criteria: tuple[str, ...]
    authority_escalation: bool
    superseded_reference: str | None
    memory_conflict: bool
    handoff_identity_match: bool
    created_at: str

    def __post_init__(self) -> None:
        _safe_id(self.report_id, "drift.report_id")
        _safe_id(self.goal_id, "drift.goal_id")
        if self.outcome not in DRIFT_OUTCOMES:
            raise SteeringValidationError("drift outcome is invalid")
        object.__setattr__(self, "reasons", _refs(self.reasons, "drift.reasons"))
        for digest, field in ((self.expected_objective_digest, "drift.expected_objective_digest"), (self.observed_objective_digest, "drift.observed_objective_digest")):
            if not isinstance(digest, str) or not _HEX.fullmatch(digest):
                raise SteeringValidationError(f"{field} must be a SHA-256 digest")
        object.__setattr__(self, "missing_acceptance_criteria", _refs(self.missing_acceptance_criteria, "drift.missing_acceptance_criteria"))
        object.__setattr__(self, "unexpected_acceptance_criteria", _refs(self.unexpected_acceptance_criteria, "drift.unexpected_acceptance_criteria"))
        for field in ("authority_escalation", "memory_conflict", "handoff_identity_match"):
            if not isinstance(getattr(self, field), bool):
                raise SteeringValidationError(f"drift.{field} must be boolean")
        if self.superseded_reference is not None:
            _safe_id(self.superseded_reference, "drift.superseded_reference")
        _timestamp(self.created_at, "drift.created_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.drift-report",
            "report_id": self.report_id,
            "goal_id": self.goal_id,
            "outcome": self.outcome,
            "reasons": list(self.reasons),
            "expected_objective_digest": self.expected_objective_digest,
            "observed_objective_digest": self.observed_objective_digest,
            "missing_acceptance_criteria": list(self.missing_acceptance_criteria),
            "unexpected_acceptance_criteria": list(self.unexpected_acceptance_criteria),
            "authority_escalation": self.authority_escalation,
            "superseded_reference": self.superseded_reference,
            "memory_conflict": self.memory_conflict,
            "handoff_identity_match": self.handoff_identity_match,
            "created_at": self.created_at,
        }


class GoalDriftGuard:
    """Stop handoff or steering when objective, authority, or acceptance state drifts."""

    def inspect(self, report_id: str, goal: GoalRecord, observed_objective_digest: str, expected_acceptance_criteria: Sequence[str], observed_acceptance_criteria: Sequence[str], *, observed_provenance: AuthorityProvenance | None = None, superseded_reference: str | None = None, memory_conflict: bool = False, expected_handoff_identity_digest: str | None = None, observed_handoff_identity_digest: str | None = None, created_at: str) -> DriftReport:
        if not isinstance(goal, GoalRecord):
            raise SteeringValidationError("drift inspection requires a GoalRecord")
        _safe_id(report_id, "drift.report_id")
        expected_digest = goal.objective_digest()
        if not isinstance(observed_objective_digest, str) or not _HEX.fullmatch(observed_objective_digest):
            raise SteeringValidationError("observed objective must be a SHA-256 digest")
        expected_acceptance = set(_refs(expected_acceptance_criteria, "drift.expected_acceptance_criteria"))
        observed_acceptance = set(_refs(observed_acceptance_criteria, "drift.observed_acceptance_criteria"))
        missing = tuple(sorted(expected_acceptance - observed_acceptance))
        unexpected = tuple(sorted(observed_acceptance - expected_acceptance))
        authority_escalation = bool(observed_provenance and observed_provenance.is_owner_authority and not goal.provenance.is_owner_authority)
        handoff_match = True
        if expected_handoff_identity_digest is not None or observed_handoff_identity_digest is not None:
            if not expected_handoff_identity_digest or not observed_handoff_identity_digest or not _HEX.fullmatch(expected_handoff_identity_digest) or not _HEX.fullmatch(observed_handoff_identity_digest):
                raise SteeringValidationError("handoff identity digests must both be SHA-256 values when supplied")
            handoff_match = expected_handoff_identity_digest == observed_handoff_identity_digest
        reasons: list[str] = []
        if observed_objective_digest != expected_digest:
            reasons.append("objective_digest_mismatch")
        if missing:
            reasons.append("acceptance_criteria_lost")
        if unexpected:
            reasons.append("acceptance_criteria_changed")
        if authority_escalation:
            reasons.append("proposal_to_owner_escalation")
        if superseded_reference is not None:
            _safe_id(superseded_reference, "drift.superseded_reference")
            reasons.append("superseded_reference_present")
        if memory_conflict:
            reasons.append("memory_conflict_requires_review")
        if not handoff_match:
            reasons.append("handoff_identity_mismatch")
        if authority_escalation or memory_conflict:
            outcome = "HUMAN_REVIEW"
        elif reasons:
            outcome = "PAUSE_RECONCILE"
        else:
            outcome = "CLEAR"
        return DriftReport(report_id, goal.goal_id, outcome, tuple(reasons), expected_digest, observed_objective_digest, missing, unexpected, authority_escalation, superseded_reference, memory_conflict, handoff_match, created_at)


MEMORY_PROFILE_SOURCES = frozenset({"OPERATIONAL_MEMORY", "PROFILE_PROJECTION", "ESI_ADVISORY"})
MEMORY_PROFILE_DECISIONS = frozenset({"PROPOSAL_ONLY", "ADVISORY_ONLY", "CANONICAL_INTENT_WINS", "STALE_IGNORED"})


@dataclass(frozen=True)
class MemoryProfileObservation:
    observation_id: str
    source_kind: str
    summary: str
    preference_signal: str | None = None
    repeated_preference: bool = False
    stale: bool = False
    conflict_with_canonical: bool = False
    created_at: str = "1970-01-01T00:00:00+00:00"

    def __post_init__(self) -> None:
        _safe_id(self.observation_id, "memory_profile.observation_id")
        if self.source_kind not in MEMORY_PROFILE_SOURCES:
            raise SteeringValidationError("memory_profile source_kind is invalid")
        _bounded_text(self.summary, "memory_profile.summary")
        if self.preference_signal is not None:
            _bounded_text(self.preference_signal, "memory_profile.preference_signal")
        for field in ("repeated_preference", "stale", "conflict_with_canonical"):
            if not isinstance(getattr(self, field), bool):
                raise SteeringValidationError(f"memory_profile.{field} must be boolean")
        _timestamp(self.created_at, "memory_profile.created_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "source_kind": self.source_kind,
            "summary": self.summary,
            "preference_signal": self.preference_signal,
            "repeated_preference": self.repeated_preference,
            "stale": self.stale,
            "conflict_with_canonical": self.conflict_with_canonical,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ContextBoundaryDecision:
    observation_id: str
    decision: str
    priority_effect: str
    canonical_intent_id: str | None
    proposal: IntentRecord | None
    reasons: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        _safe_id(self.observation_id, "memory_profile.decision.observation_id")
        if self.decision not in MEMORY_PROFILE_DECISIONS:
            raise SteeringValidationError("memory_profile decision is invalid")
        if self.priority_effect not in {"NONE", "CANONICAL_INTENT_ONLY"}:
            raise SteeringValidationError("memory_profile priority_effect is invalid")
        if self.canonical_intent_id is not None:
            _safe_id(self.canonical_intent_id, "memory_profile.canonical_intent_id")
        if self.decision == "PROPOSAL_ONLY" and (self.proposal is None or self.proposal.status != "PROPOSED" or self.proposal.owner_authoritative):
            raise SteeringValidationError("proposal-only context must carry a non-authoritative proposal")
        if self.decision != "PROPOSAL_ONLY" and self.proposal is not None:
            raise SteeringValidationError("non-proposal context cannot carry a proposal")
        object.__setattr__(self, "reasons", _refs(self.reasons, "memory_profile.decision.reasons"))
        _timestamp(self.created_at, "memory_profile.decision.created_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": f"{STEERING_SCHEMA}.memory-profile-boundary",
            "observation_id": self.observation_id,
            "decision": self.decision,
            "priority_effect": self.priority_effect,
            "canonical_intent_id": self.canonical_intent_id,
            "proposal": self.proposal.to_dict() if self.proposal is not None else None,
            "reasons": list(self.reasons),
            "created_at": self.created_at,
        }


class MemoryProfileBoundary:
    """Keep operational context advisory and canonical Intent authoritative."""

    def evaluate(self, observation: MemoryProfileObservation, *, canonical_intent: IntentRecord | None = None) -> ContextBoundaryDecision:
        if not isinstance(observation, MemoryProfileObservation):
            raise SteeringValidationError("memory/profile boundary requires a MemoryProfileObservation")
        if canonical_intent is not None and not isinstance(canonical_intent, IntentRecord):
            raise SteeringValidationError("canonical_intent must be an IntentRecord")
        canonical_id = canonical_intent.intent_id if canonical_intent is not None else None
        if canonical_intent is not None and (observation.conflict_with_canonical or observation.stale):
            return ContextBoundaryDecision(observation.observation_id, "CANONICAL_INTENT_WINS", "CANONICAL_INTENT_ONLY", canonical_id, None, ("canonical_intent_remains_authoritative", "context_cannot_override_canonical"), observation.created_at)
        if observation.source_kind == "ESI_ADVISORY":
            return ContextBoundaryDecision(observation.observation_id, "ADVISORY_ONLY", "NONE", canonical_id, None, ("esi_is_advisory", "esi_cannot_change_priority"), observation.created_at)
        if observation.stale:
            return ContextBoundaryDecision(observation.observation_id, "STALE_IGNORED", "NONE", canonical_id, None, ("stale_context_not_reintroduced",), observation.created_at)
        if observation.repeated_preference and observation.preference_signal:
            provenance = AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "steering.boundary", f"proposal-{observation.observation_id}", "repeated preference is proposal only", evidence_refs=(observation.observation_id,))
            proposal = IntentRecord(f"proposal:{observation.observation_id}", observation.preference_signal, "steering.proposals", provenance, status="PROPOSED", scope={"priority_effect": "NONE", "source": observation.source_kind}, created_at=observation.created_at, updated_at=observation.created_at)
            return ContextBoundaryDecision(observation.observation_id, "PROPOSAL_ONLY", "NONE", canonical_id, proposal, ("repeated_preference_proposal_only", "no_priority_effect", "explicit_owner_promotion_required"), observation.created_at)
        return ContextBoundaryDecision(observation.observation_id, "ADVISORY_ONLY", "NONE", canonical_id, None, ("context_is_advisory", "no_intent_promotion"), observation.created_at)


STEERING_DURABILITY_SCHEMA = "os-steering-intent-obligation-r1.durable-state"
STEERING_DURABILITY_EVENT_TYPE = "STEERING_STATE_RECORDED"
STEERING_AGGREGATE_ID = "steering-state"


@dataclass(frozen=True)
class SteeringState:
    """Durable steering projection; event history remains the canonical source."""

    intents: tuple[Mapping[str, Any], ...] = ()
    goals: tuple[Mapping[str, Any], ...] = ()
    commitments: tuple[Mapping[str, Any], ...] = ()
    decision_traces: tuple[Mapping[str, Any], ...] = ()
    drift_reports: tuple[Mapping[str, Any], ...] = ()
    provenance_events: tuple[Mapping[str, Any], ...] = ()
    unresolved_refs: tuple[str, ...] = ()
    schema_epoch: str = "steering-r1"

    def __post_init__(self) -> None:
        for field in ("intents", "goals", "commitments", "decision_traces", "drift_reports", "provenance_events"):
            values = getattr(self, field)
            if isinstance(values, (str, bytes)) or any(not isinstance(item, Mapping) for item in values):
                raise SteeringValidationError(f"durable steering {field} must contain public objects")
            public = tuple(_public_value(dict(item), f"durable.{field}[]") for item in values)
            object.__setattr__(self, field, public)
        object.__setattr__(self, "unresolved_refs", _refs(self.unresolved_refs, "durable.unresolved_refs"))
        _safe_id(self.schema_epoch.replace(".", ":"), "durable.schema_epoch")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": STEERING_DURABILITY_SCHEMA,
            "schema_epoch": self.schema_epoch,
            "intents": [dict(item) for item in self.intents],
            "goals": [dict(item) for item in self.goals],
            "commitments": [dict(item) for item in self.commitments],
            "decision_traces": [dict(item) for item in self.decision_traces],
            "drift_reports": [dict(item) for item in self.drift_reports],
            "provenance_events": [dict(item) for item in self.provenance_events],
            "unresolved_refs": list(self.unresolved_refs),
            "claim_ceiling": "Durable repository-local steering projection only; event lineage remains canonical and no Owner or external truth is inferred.",
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SteeringState":
        if data.get("schema") != STEERING_DURABILITY_SCHEMA:
            raise SteeringValidationError("durable steering state schema mismatch")
        return cls(
            intents=tuple(data.get("intents", ())), goals=tuple(data.get("goals", ())), commitments=tuple(data.get("commitments", ())),
            decision_traces=tuple(data.get("decision_traces", ())), drift_reports=tuple(data.get("drift_reports", ())),
            provenance_events=tuple(data.get("provenance_events", ())), unresolved_refs=tuple(data.get("unresolved_refs", ())), schema_epoch=data.get("schema_epoch", "steering-r1"),
        )

    def digest(self) -> str:
        return sha256_json(self.to_dict())


def steering_migration_registry() -> MigrationRegistry:
    return MigrationRegistry(
        ("steering-r1", "steering-r1.1", "steering-r2"),
        (
            MigrationRule("steering-r1", "steering-r1.1", SAFE, "ADD_LIFECYCLE_METADATA", "add explicit steering lifecycle metadata without rewriting records"),
            MigrationRule("steering-r1.1", "steering-r2", SAFE, "ADD_NAMESPACE_SCOPE", "add namespace scope without rewriting event lineage"),
            MigrationRule("steering-r2", "steering-r1.1", "LOSSY_REQUIRES_APPROVAL", "REMOVE_ADVISORY_POINTER_LOSSY", "downgrade removes only advisory metadata and requires explicit approval"),
        ),
    )


class SteeringDurabilityAdapter:
    """Persist steering projections through the existing append-only ledger and snapshots."""

    def append_state(self, ledger: EventLedger, state: SteeringState, *, actor_ref: str = "os-steering", source_refs: Sequence[str] = (), expected_version: int | None = None, occurred_at: str | None = None):
        if not isinstance(ledger, EventLedger) or not isinstance(state, SteeringState):
            raise SteeringValidationError("steering durability append requires EventLedger and SteeringState")
        return ledger.append_event(
            aggregate_id=STEERING_AGGREGATE_ID,
            event_type=STEERING_DURABILITY_EVENT_TYPE,
            payload={"status": "STEERING_STATE_RECORDED", "state_patch": {"steering_state": state.to_dict(), "steering_state_sha256": state.digest()}},
            actor_ref=actor_ref,
            source_refs=source_refs,
            expected_version=expected_version,
            occurred_at=occurred_at,
            sensitivity="INTERNAL_OPERATIONAL",
            retention_class="LONG",
        )

    @staticmethod
    def _from_replayed(replayed: Mapping[str, Any]) -> SteeringState:
        aggregate = replayed.get("aggregates", {}).get(STEERING_AGGREGATE_ID, {})
        state = aggregate.get("steering_state") if isinstance(aggregate, Mapping) else None
        if not isinstance(state, Mapping):
            raise SteeringValidationError("steering ledger has no durable steering state")
        if aggregate.get("steering_state_sha256") != sha256_json(state):
            raise SteeringValidationError("steering state projection digest mismatch")
        return SteeringState.from_dict(state)

    def replay(self, ledger: EventLedger) -> SteeringState:
        return self._from_replayed(ledger.replay())

    def snapshot(self, ledger: EventLedger, snapshot_path: str, *, snapshot_id: str, provenance_refs: Sequence[str] = ()) -> CanonicalSnapshot:
        store = CanonicalSnapshotStore(snapshot_path)
        snapshot = store.create(ledger, snapshot_id=snapshot_id, namespace_scope="steering", provenance_refs=tuple(provenance_refs) + (STEERING_AGGREGATE_ID,), creation_tool="os-steering.durability-r1")
        return store.write(snapshot)

    def restore(self, ledger: EventLedger, snapshot: CanonicalSnapshot | None = None, *, snapshot_path: str | None = None) -> SteeringState:
        if snapshot is None:
            if snapshot_path is None:
                raise SteeringValidationError("steering restore requires snapshot or snapshot_path")
            snapshot = CanonicalSnapshotStore(snapshot_path).read()
        restored = CanonicalSnapshotStore(snapshot_path or "steering-snapshot.json").restore(ledger, snapshot, namespace_scope="steering")
        return self._from_replayed(restored)

    def migrate(self, state: SteeringState, *, migration_id: str, from_epoch: str, to_epoch: str, event_lineage: Sequence[str] = (), mode: str = DRY_RUN, approval: bool = False) -> MigrationResult:
        if not isinstance(state, SteeringState):
            raise SteeringValidationError("steering migration requires SteeringState")
        result = StateMigrator(steering_migration_registry()).migrate(state.to_dict(), migration_id=migration_id, from_epoch=from_epoch, to_epoch=to_epoch, event_lineage=event_lineage, mode=mode, approval=approval)
        if result.receipt.events_rewritten:
            raise SteeringValidationError("steering migration rewrote event lineage")
        return result


STEERING_RECORD_KINDS = frozenset({"intent", "goal", "commitment", "trace", "proposal"})
STEERING_NAMESPACE_ACTIONS = frozenset({"read", "propose", "canonical_write"})


@dataclass(frozen=True)
class SteeringScope:
    scope_id: str
    namespace_id: str
    intent_ids: tuple[str, ...] = ()
    goal_ids: tuple[str, ...] = ()
    commitment_ids: tuple[str, ...] = ()
    trace_ids: tuple[str, ...] = ()
    proposal_ids: tuple[str, ...] = ()
    shared_scope_ref: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.scope_id, "steering_scope.scope_id")
        _safe_id(self.namespace_id, "steering_scope.namespace_id")
        for field in ("intent_ids", "goal_ids", "commitment_ids", "trace_ids", "proposal_ids"):
            object.__setattr__(self, field, _refs(getattr(self, field), f"steering_scope.{field}"))
        if self.shared_scope_ref is not None:
            _safe_id(self.shared_scope_ref, "steering_scope.shared_scope_ref")

    def contains(self, record_kind: str, record_id: str) -> bool:
        if record_kind not in STEERING_RECORD_KINDS:
            raise SteeringValidationError("unknown steering record kind")
        _safe_id(record_id, "steering_scope.record_id")
        return record_id in getattr(self, f"{record_kind}_ids")

    def to_dict(self) -> dict[str, Any]:
        return {"scope_id": self.scope_id, "namespace_id": self.namespace_id, "intent_ids": list(self.intent_ids), "goal_ids": list(self.goal_ids), "commitment_ids": list(self.commitment_ids), "trace_ids": list(self.trace_ids), "proposal_ids": list(self.proposal_ids), "shared_scope_ref": self.shared_scope_ref}


class SteeringNamespaceGuard:
    """Apply namespace isolation to steering records without granting canonical authority."""

    def __init__(self, namespace_guard: NamespaceGuard | None = None) -> None:
        self.guard = namespace_guard or NamespaceGuard()

    def bind(self, binding: NamespaceBinding, principal: PrincipalIdentity) -> NamespaceBinding:
        return self.guard.bind(binding, principal)

    def authorize(
        self,
        source_binding: NamespaceBinding,
        source_scope: SteeringScope,
        target_binding: NamespaceBinding,
        target_scope: SteeringScope,
        *,
        record_kind: str,
        record_id: str,
        action: str,
        now: float,
        delegation: DelegationGrant | None = None,
    ) -> None:
        if record_kind not in STEERING_RECORD_KINDS:
            raise NamespaceIsolationError("unknown steering record kind")
        if action not in STEERING_NAMESPACE_ACTIONS:
            raise NamespaceIsolationError("unknown steering namespace action")
        _safe_id(record_id, "steering.record_id")
        if source_binding.namespace_id != source_scope.namespace_id or target_binding.namespace_id != target_scope.namespace_id:
            raise NamespaceIsolationError("steering scope does not match namespace binding")
        if action == "canonical_write":
            raise NamespaceIsolationError("namespace delegation cannot grant canonical steering authority")
        cross_namespace = source_binding.namespace_id != target_binding.namespace_id
        if cross_namespace:
            if not source_scope.shared_scope_ref or source_scope.shared_scope_ref != target_scope.shared_scope_ref:
                raise NamespaceIsolationError("cross-namespace steering requires an explicit shared scope")
            self.guard.authorize(source_binding, target_binding, action=f"steering.{record_kind}.{action}", now=now, delegation=delegation)
        else:
            self.guard.authorize(source_binding, target_binding, action=f"steering.{record_kind}.{action}", now=now)
        if not target_scope.contains(record_kind, record_id):
            raise NamespaceIsolationError("record is outside the target steering scope")

    def authorize_proposal(self, source_binding: NamespaceBinding, source_scope: SteeringScope, target_binding: NamespaceBinding, target_scope: SteeringScope, *, record_id: str, now: float, delegation: DelegationGrant | None = None) -> None:
        self.authorize(source_binding, source_scope, target_binding, target_scope, record_kind="proposal", record_id=record_id, action="propose", now=now, delegation=delegation)


__all__ = [
    "STEERING_SCHEMA", "INTENT_AUTHORITY_INVARIANT", "GOAL_COMPLETION_NON_INFERENCE_INVARIANT", "STEERING_EXPLAINABILITY_INVARIANT",
    "INTENT_SOURCE_TYPES", "INTENT_STATUSES", "ONTOLOGY_LAYERS", "SteeringValidationError", "AuthorityProvenance",
    "IntentRecord", "GoalRecord", "CompletionContract", "ontology_contract", "authority_digest",
    "IntentRegistry", "IntentRegistryError",
    "GOAL_STATUSES", "GoalRegistry", "GoalRegistryError", "COMPLETION_OUTCOMES", "CompletionDecision", "evaluate_completion",
    "COMMITMENT_STATUSES", "CommitmentRecord", "CommitmentLedger", "CommitmentLedgerError",
    "TEMPORAL_STATES", "TemporalWindow", "TemporalEvaluation", "evaluate_temporal",
    "DEPENDENCY_EDGE_TYPES", "GraphNode", "DependencyEdge", "GoalDependencyGraph", "GoalDependencyGraphError",
    "RISK_LEVELS", "OwnerOverride", "PriorityInputs", "PriorityDecision", "PriorityPolicy",
    "CONFLICT_TYPES", "ARBITRATION_OUTCOMES", "ConflictCandidate", "ArbitrationReceipt", "ConflictArbiter",
    "NextWorkCandidate", "SkippedGoal", "DecisionTrace", "SteeringEngine",
    "HandoffIdentity", "EpisodeGoalBinding", "GoalEpisodeBinder",
    "DRIFT_OUTCOMES", "DriftReport", "GoalDriftGuard",
    "MEMORY_PROFILE_SOURCES", "MEMORY_PROFILE_DECISIONS", "MemoryProfileObservation", "ContextBoundaryDecision", "MemoryProfileBoundary",
    "STEERING_DURABILITY_SCHEMA", "STEERING_DURABILITY_EVENT_TYPE", "STEERING_AGGREGATE_ID", "SteeringState", "steering_migration_registry", "SteeringDurabilityAdapter",
    "STEERING_RECORD_KINDS", "STEERING_NAMESPACE_ACTIONS", "SteeringScope", "SteeringNamespaceGuard",
]
