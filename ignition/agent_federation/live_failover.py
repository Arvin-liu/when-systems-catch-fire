"""Bounded cross-executor failover semantics without replaying unknown effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .live_bridge import LiveExecutorReceipt


LIVE_FAILOVER_SCHEMA = "ignition-136-live-failover-r1"


@dataclass(frozen=True)
class LiveFailoverDecision:
    status: str
    source_executor_id: str
    target_executor_id: str
    new_attempt_id: str | None
    reason: str
    handoff_capsule: Mapping[str, Any]
    private_session_propagated: bool = False
    policy_rechecked: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": LIVE_FAILOVER_SCHEMA, "status": self.status, "source_executor_id": self.source_executor_id,
            "target_executor_id": self.target_executor_id, "new_attempt_id": self.new_attempt_id, "reason": self.reason,
            "handoff_capsule": dict(self.handoff_capsule), "private_session_propagated": self.private_session_propagated,
            "policy_rechecked": self.policy_rechecked,
        }


def decide_bounded_failover(
    receipt: LiveExecutorReceipt,
    *,
    target_executor_id: str,
    target_admission_status: str,
    target_capabilities: Sequence[str],
    no_effect_proven: bool,
) -> LiveFailoverDecision:
    if not isinstance(receipt, LiveExecutorReceipt):
        raise ValueError("failover requires a typed live receipt")
    if not isinstance(target_executor_id, str) or not target_executor_id.strip() or target_executor_id == receipt.executor_id:
        raise ValueError("failover target must be a distinct executor")
    if receipt.state in {"COMPLETED_VALIDATED", "REQUIRES_RECONCILIATION", "TIMED_OUT_EFFECT_UNKNOWN", "CANCEL_REQUESTED"} or not no_effect_proven:
        return LiveFailoverDecision(
            "REQUIRES_RECONCILIATION", receipt.executor_id, target_executor_id, None,
            "captured receipt does not prove absence of external effect; no replay or completion bypass",
            {"task_id": receipt.task_id, "dispatch_id": receipt.dispatch_id, "receipt_digest": receipt.receipt_digest, "permission_ceiling": ["repo.read"]},
        )
    if target_admission_status != "ADMITTED":
        return LiveFailoverDecision(
            "REJECTED_CAPABILITY", receipt.executor_id, target_executor_id, None,
            "target executor must pass a fresh OS capability admission",
            {"task_id": receipt.task_id, "dispatch_id": receipt.dispatch_id, "receipt_digest": receipt.receipt_digest, "permission_ceiling": ["repo.read"]},
        )
    if "repo.read" not in set(target_capabilities):
        return LiveFailoverDecision(
            "REJECTED_CAPABILITY", receipt.executor_id, target_executor_id, None,
            "target executor lacks the bounded read capability",
            {"task_id": receipt.task_id, "dispatch_id": receipt.dispatch_id, "receipt_digest": receipt.receipt_digest, "permission_ceiling": ["repo.read"]},
        )
    new_attempt = f"{receipt.attempt_id}:failover:{target_executor_id}"
    return LiveFailoverDecision(
        "FAILOVER_ELIGIBLE_NEW_LINEAGE", receipt.executor_id, target_executor_id, new_attempt,
        "no-effect proof permits one fresh lineage after target policy and capability re-admission",
        {"task_id": receipt.task_id, "dispatch_id": receipt.dispatch_id, "receipt_digest": receipt.receipt_digest, "permission_ceiling": ["repo.read"], "source_attempt_id": receipt.attempt_id},
    )


__all__ = ["LIVE_FAILOVER_SCHEMA", "LiveFailoverDecision", "decide_bounded_failover"]
