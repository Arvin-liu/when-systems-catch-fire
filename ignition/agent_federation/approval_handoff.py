"""Approval intersection, handoff and failover boundaries for Federation R1.

This module is OS policy machinery.  It records what an external executor
observed, but never lets an executor approve itself, migrate hidden state, or
turn an unverified side effect into a safe automatic retry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contracts import (
    ArtifactRef,
    ApprovalPolicy,
    ExternalSessionRef,
    FederatedHandoffBundle,
    FederatedResultReceipt,
    FederationContractError,
    HandoffEligibility,
    TERMINAL_STATES,
    canonical_digest,
)
from .sdk import map_capabilities


APPROVAL_OBSERVATION_STATES = frozenset({"NOT_REQUESTED", "WAITING", "APPROVED", "DENIED"})
APPROVAL_DECISION_STATES = frozenset({"APPROVED", "WAITING_FOR_APPROVAL", "WAITING_EXTERNAL_APPROVAL", "BLOCKED_WITH_EVIDENCE", "CAPABILITY_MISMATCH"})
FAILOVER_REASONS = frozenset({
    "EXECUTOR_UNAVAILABLE",
    "EXECUTOR_TIMEOUT",
    "EXECUTOR_CRASH",
    "EXECUTOR_OUTPUT_INVALID",
    "EXTERNAL_APPROVAL_BLOCKED",
    "CAPABILITY_MISMATCH",
    "RECEIPT_UNVERIFIED",
})
FAILOVER_STATES = frozenset({"AUTO_FAILOVER_ELIGIBLE", "WAITING_FOR_APPROVAL", "REQUIRES_RECONCILIATION", "BLOCKED_WITH_EVIDENCE", "CAPABILITY_MISMATCH"})
_PRIVATE_MARKERS = ("prompt", "chain_of_thought", "cot", "reasoning", "token", "secret", "cookie", "authorization", "api_key", "password")


class ApprovalHandoffError(FederationContractError):
    """Raised when an approval, handoff or failover boundary is unsafe."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ApprovalHandoffError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ApprovalHandoffError(f"{field} must be an array")
    result = tuple(_text(item, f"{field}[]") for item in value)
    if nonempty and not result:
        raise ApprovalHandoffError(f"{field} must not be empty")
    if len(result) != len(set(result)):
        raise ApprovalHandoffError(f"{field} must not contain duplicates")
    return result


def _public_text(value: str, field: str) -> str:
    value = _text(value, field)
    normalized = value.casefold().replace("-", "_")
    if any(marker in normalized for marker in _PRIVATE_MARKERS):
        raise ApprovalHandoffError(f"{field} contains hidden or secret state")
    return value


@dataclass(frozen=True)
class ExternalApprovalObservation:
    status: str
    observation_ref: str | None = None
    summary: str = "external approval state observed at adapter boundary"

    def __post_init__(self) -> None:
        if self.status not in APPROVAL_OBSERVATION_STATES:
            raise ApprovalHandoffError("external approval observation status is unsupported")
        if self.observation_ref is not None:
            _public_text(self.observation_ref, "external_approval.observation_ref")
        _public_text(self.summary, "external_approval.summary")

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "observation_ref": self.observation_ref, "summary": self.summary}


@dataclass(frozen=True)
class ApprovalBridgeDecision:
    status: str
    reason: str
    effective_capabilities: tuple[str, ...]
    owner_decision: str | None
    external_observation: ExternalApprovalObservation
    external_authority_effect: str = "EXTERNAL_SELF_APPROVAL_NEVER_REPLACES_OS_AUTHORITY"

    def __post_init__(self) -> None:
        if self.status not in APPROVAL_DECISION_STATES:
            raise ApprovalHandoffError("approval bridge decision status is unsupported")
        _public_text(self.reason, "approval_decision.reason")
        object.__setattr__(self, "effective_capabilities", map_capabilities(self.effective_capabilities))
        if self.owner_decision not in {None, "ALLOW", "DENY"}:
            raise ApprovalHandoffError("owner_decision must be null, ALLOW or DENY")
        if not isinstance(self.external_observation, ExternalApprovalObservation):
            raise ApprovalHandoffError("external_observation must be typed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "effective_capabilities": list(self.effective_capabilities),
            "owner_decision": self.owner_decision,
            "external_observation": self.external_observation.to_dict(),
            "external_authority_effect": self.external_authority_effect,
        }


class ApprovalBridge:
    """Evaluate OS and external approval as a strict intersection."""

    def evaluate(
        self,
        policy: ApprovalPolicy,
        requested_capabilities: Sequence[str],
        *,
        owner_decision: str | None = None,
        external_observation: ExternalApprovalObservation | None = None,
        external_capability_ceiling: Sequence[str] = (),
        external_approval_required: bool = False,
    ) -> ApprovalBridgeDecision:
        if not isinstance(policy, ApprovalPolicy):
            raise ApprovalHandoffError("ApprovalBridge requires ApprovalPolicy")
        requested = map_capabilities(requested_capabilities)
        if not requested:
            raise ApprovalHandoffError("requested_capabilities must not be empty")
        external = external_observation or ExternalApprovalObservation("NOT_REQUESTED")
        os_missing = sorted(set(requested) - set(map_capabilities(policy.capability_ceiling)))
        external_ceiling = map_capabilities(external_capability_ceiling) if external_capability_ceiling else requested
        external_missing = sorted(set(requested) - set(external_ceiling))
        if os_missing or external_missing:
            missing = sorted(set(os_missing + external_missing))
            return ApprovalBridgeDecision("CAPABILITY_MISMATCH", f"approval capability intersection is missing: {missing}", requested, owner_decision, external)
        if policy.mode == "DENY":
            return ApprovalBridgeDecision("BLOCKED_WITH_EVIDENCE", "OS approval policy is DENY; external approval cannot override it", requested, owner_decision, external)
        if owner_decision == "DENY":
            return ApprovalBridgeDecision("BLOCKED_WITH_EVIDENCE", "Owner decision is DENY", requested, owner_decision, external)
        if policy.mode in {"REQUIRE_OWNER", "DELEGATED"} and owner_decision != "ALLOW":
            return ApprovalBridgeDecision("WAITING_FOR_APPROVAL", "Owner decision is required before any external approval can take effect", requested, owner_decision, external)
        if external.status == "DENIED":
            return ApprovalBridgeDecision("BLOCKED_WITH_EVIDENCE", "external executor approval gate denied the request", requested, owner_decision, external)
        if external.status == "WAITING" or (external_approval_required and external.status == "NOT_REQUESTED"):
            return ApprovalBridgeDecision("WAITING_EXTERNAL_APPROVAL", "external executor approval is pending; it is not an OS authority grant", requested, owner_decision, external)
        if external.status == "APPROVED" and not policy.external_approval_allowed and external_approval_required:
            return ApprovalBridgeDecision("BLOCKED_WITH_EVIDENCE", "OS policy does not allow the required external approval gate", requested, owner_decision, external)
        return ApprovalBridgeDecision("APPROVED", "OS approval and any required external gate intersect without widening capability", requested, owner_decision, external)


def build_handoff_bundle(
    *,
    handoff_id: str,
    source_receipt: FederatedResultReceipt,
    goal: str,
    pending_work: Sequence[str],
    allowed_capabilities: Sequence[str],
    workspace_refs: Sequence[str],
    acceptance_criteria: Sequence[str],
    operational_memory_capsule_refs: Sequence[str] = (),
    unresolveds: Sequence[str] = (),
) -> FederatedHandoffBundle:
    """Build a canonical handoff from a public receipt, never private history."""

    if not isinstance(source_receipt, FederatedResultReceipt):
        raise ApprovalHandoffError("source_receipt must be FederatedResultReceipt")
    _public_text(handoff_id, "handoff_id")
    _public_text(goal, "handoff.goal")
    for field, values in (("pending_work", pending_work), ("allowed_capabilities", allowed_capabilities), ("workspace_refs", workspace_refs), ("acceptance_criteria", acceptance_criteria), ("operational_memory_capsule_refs", operational_memory_capsule_refs), ("unresolveds", unresolveds)):
        for value in values:
            _public_text(value, f"handoff.{field}[]")
    validated_work = tuple(source_receipt.claimed_actions) if source_receipt.terminal_state == "COMPLETED_VALIDATED" else ()
    if source_receipt.terminal_state != "COMPLETED_VALIDATED" and source_receipt.claimed_actions:
        raise ApprovalHandoffError("unvalidated executor actions cannot be copied into validated_completed_work")
    source_session_refs = (source_receipt.external_session_ref,) if source_receipt.external_session_ref is not None else ()
    return FederatedHandoffBundle(
        handoff_id=handoff_id,
        federation_task_id=source_receipt.federation_task_id,
        source_executor_id=source_receipt.executor_id,
        goal=goal,
        validated_completed_work=validated_work,
        pending_work=tuple(pending_work),
        allowed_capabilities=map_capabilities(allowed_capabilities),
        workspace_refs=tuple(workspace_refs),
        artifact_refs=source_receipt.artifact_refs,
        acceptance_criteria=tuple(acceptance_criteria),
        operational_memory_capsule_refs=tuple(operational_memory_capsule_refs),
        external_session_refs=source_session_refs,
        unresolveds=tuple(dict.fromkeys((*source_receipt.unresolveds, *unresolveds))),
    )


@dataclass(frozen=True)
class HandoffTakeoverDecision:
    status: str
    source_executor_id: str
    target_executor_id: str
    reason: str
    effective_capabilities: tuple[str, ...]
    observed_artifact_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"ACCEPTED", "REQUIRES_RECONCILIATION", "CAPABILITY_MISMATCH"}:
            raise ApprovalHandoffError("handoff takeover status is unsupported")
        _public_text(self.source_executor_id, "takeover.source_executor_id")
        _public_text(self.target_executor_id, "takeover.target_executor_id")
        _public_text(self.reason, "takeover.reason")
        object.__setattr__(self, "effective_capabilities", map_capabilities(self.effective_capabilities))
        object.__setattr__(self, "observed_artifact_refs", _strings(self.observed_artifact_refs, "takeover.observed_artifact_refs"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source_executor_id": self.source_executor_id,
            "target_executor_id": self.target_executor_id,
            "reason": self.reason,
            "effective_capabilities": list(self.effective_capabilities),
            "observed_artifact_refs": list(self.observed_artifact_refs),
        }


def accept_handoff(
    bundle: FederatedHandoffBundle,
    target_executor_id: str,
    target_capabilities: Sequence[str],
    *,
    workspace_reobserved: bool,
    source_receipt_verified: bool,
    observed_artifact_refs: Sequence[str] = (),
) -> HandoffTakeoverDecision:
    if not isinstance(bundle, FederatedHandoffBundle):
        raise ApprovalHandoffError("accept_handoff requires FederatedHandoffBundle")
    _public_text(target_executor_id, "takeover.target_executor_id")
    if target_executor_id == bundle.source_executor_id:
        raise ApprovalHandoffError("handoff target must be a different executor")
    allowed = map_capabilities(bundle.allowed_capabilities)
    target = set(map_capabilities(target_capabilities))
    missing = sorted(set(allowed) - target)
    observed = tuple(_strings(observed_artifact_refs, "observed_artifact_refs"))
    if missing:
        return HandoffTakeoverDecision("CAPABILITY_MISMATCH", bundle.source_executor_id, target_executor_id, f"target lacks handoff capabilities: {missing}", tuple(allowed), observed)
    expected_artifacts = {item.ref for item in bundle.artifact_refs}
    if not workspace_reobserved or not source_receipt_verified or not expected_artifacts.issubset(set(observed)):
        return HandoffTakeoverDecision("REQUIRES_RECONCILIATION", bundle.source_executor_id, target_executor_id, "target must re-observe workspace and verify the source receipt/artifact refs before takeover", tuple(allowed), observed)
    return HandoffTakeoverDecision("ACCEPTED", bundle.source_executor_id, target_executor_id, "target re-observed the workspace and verified the public source receipt before takeover", tuple(allowed), observed)


@dataclass(frozen=True)
class FailoverContext:
    source_executor_id: str
    target_executor_id: str
    reason: str
    task_capabilities: tuple[str, ...]
    task_read_only: bool
    side_effects_validated: bool
    side_effects_replayable: bool
    receipt_verified: bool
    external_approval_allowed: bool = False

    def __post_init__(self) -> None:
        _public_text(self.source_executor_id, "failover.source_executor_id")
        _public_text(self.target_executor_id, "failover.target_executor_id")
        if self.reason not in FAILOVER_REASONS:
            raise ApprovalHandoffError("failover reason is unsupported")
        object.__setattr__(self, "task_capabilities", map_capabilities(self.task_capabilities))
        if self.source_executor_id == self.target_executor_id:
            raise ApprovalHandoffError("failover target must differ from source")
        for field in ("task_read_only", "side_effects_validated", "side_effects_replayable", "receipt_verified", "external_approval_allowed"):
            if not isinstance(getattr(self, field), bool):
                raise ApprovalHandoffError(f"failover.{field} must be boolean")


@dataclass(frozen=True)
class FailoverDecision:
    status: str
    reason: str
    source_executor_id: str
    target_executor_id: str
    failover_reason: str
    effective_capabilities: tuple[str, ...]
    automatic: bool

    def __post_init__(self) -> None:
        if self.status not in FAILOVER_STATES:
            raise ApprovalHandoffError("failover decision status is unsupported")
        _public_text(self.reason, "failover_decision.reason")
        _public_text(self.source_executor_id, "failover_decision.source_executor_id")
        _public_text(self.target_executor_id, "failover_decision.target_executor_id")
        if self.failover_reason not in FAILOVER_REASONS:
            raise ApprovalHandoffError("failover_decision.failover_reason is unsupported")
        object.__setattr__(self, "effective_capabilities", map_capabilities(self.effective_capabilities))
        if not isinstance(self.automatic, bool):
            raise ApprovalHandoffError("failover_decision.automatic must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "source_executor_id": self.source_executor_id,
            "target_executor_id": self.target_executor_id,
            "failover_reason": self.failover_reason,
            "effective_capabilities": list(self.effective_capabilities),
            "automatic": self.automatic,
        }


def decide_failover(context: FailoverContext, *, target_capabilities: Sequence[str]) -> FailoverDecision:
    if not isinstance(context, FailoverContext):
        raise ApprovalHandoffError("decide_failover requires FailoverContext")
    target = set(map_capabilities(target_capabilities))
    missing = sorted(set(context.task_capabilities) - target)
    if missing:
        return FailoverDecision("CAPABILITY_MISMATCH", f"target lacks required capabilities: {missing}", context.source_executor_id, context.target_executor_id, context.reason, context.task_capabilities, False)
    if context.reason == "EXTERNAL_APPROVAL_BLOCKED":
        return FailoverDecision("WAITING_FOR_APPROVAL" if context.external_approval_allowed else "BLOCKED_WITH_EVIDENCE", "external approval is a gate, not a reason to silently switch executor", context.source_executor_id, context.target_executor_id, context.reason, context.task_capabilities, False)
    safe_to_retry = context.task_read_only or context.side_effects_validated or context.side_effects_replayable
    if not context.receipt_verified or not safe_to_retry or context.reason == "RECEIPT_UNVERIFIED":
        return FailoverDecision("REQUIRES_RECONCILIATION", "unknown or unverified side effects prevent automatic failover", context.source_executor_id, context.target_executor_id, context.reason, context.task_capabilities, False)
    return FailoverDecision("AUTO_FAILOVER_ELIGIBLE", "task is read-only or its side effects are validated/replayable and the target has the same capability ceiling", context.source_executor_id, context.target_executor_id, context.reason, context.task_capabilities, True)


__all__ = [
    "APPROVAL_DECISION_STATES",
    "APPROVAL_OBSERVATION_STATES",
    "FAILOVER_REASONS",
    "FAILOVER_STATES",
    "ApprovalBridge",
    "ApprovalBridgeDecision",
    "ApprovalHandoffError",
    "ExternalApprovalObservation",
    "FailoverContext",
    "FailoverDecision",
    "HandoffTakeoverDecision",
    "accept_handoff",
    "build_handoff_bundle",
    "decide_failover",
]
