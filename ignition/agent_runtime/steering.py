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
]
