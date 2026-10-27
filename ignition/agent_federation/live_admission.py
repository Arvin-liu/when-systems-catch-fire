"""Bridge live capability leases into the existing durability admission stores."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any, Iterable, Sequence

from agent_runtime.executor_admission import ExecutorAdmission, ExecutorAdmissionError, ExecutorAdmissionStore, ExecutorRouteDenied

from .contracts import FederationContractError
from .live_bridge import LiveCapabilityLease, LiveDispatchEnvelope
from .sdk import map_capabilities


class LiveAdmissionError(FederationContractError):
    """Raised when a live lease cannot be admitted through the OS stores."""


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise LiveAdmissionError("live observation time must be non-empty text")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise LiveAdmissionError("live observation time must be ISO-8601") from exc
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


@dataclass(frozen=True)
class LiveAdmissionDecision:
    executor_id: str
    lease_id: str
    status: str
    effective_capabilities: tuple[str, ...]
    reason: str
    admission_ref: str | None = None


class LiveCapabilityAdmission:
    """Use existing executor admission/revocation as the durable authority."""

    def __init__(self, *, admission_store: ExecutorAdmissionStore | None = None, expected_conformance_epoch: int = 1) -> None:
        self.admission_store = admission_store
        if not isinstance(expected_conformance_epoch, int) or expected_conformance_epoch < 1:
            raise LiveAdmissionError("expected_conformance_epoch must be positive")
        self.expected_conformance_epoch = expected_conformance_epoch

    @staticmethod
    def _effective(envelope: LiveDispatchEnvelope, lease: LiveCapabilityLease, os_granted: Iterable[str], executor_declared: Iterable[str]) -> tuple[str, ...]:
        try:
            requested = set(map_capabilities(envelope.permission_ceiling))
            granted = set(map_capabilities(tuple(os_granted)))
            declared = set(map_capabilities(tuple(executor_declared)))
        except Exception as exc:
            raise LiveAdmissionError("capability intersection contains an unsupported token") from exc
        observed = set(lease.observed_capabilities)
        forbidden = set(lease.forbidden_capabilities)
        effective = requested & granted & declared & observed
        if effective & forbidden:
            raise LiveAdmissionError("lease observed and forbidden capability sets overlap")
        if effective != requested:
            missing = sorted(requested - effective)
            raise LiveAdmissionError(f"OS/executor/runtime capability intersection is missing: {missing}")
        return tuple(sorted(effective))

    def admit(
        self,
        envelope: LiveDispatchEnvelope,
        lease: LiveCapabilityLease,
        *,
        os_granted: Iterable[str],
        executor_declared: Iterable[str],
        now_observed: str,
        now_epoch: float | None = None,
        current_binary_digest: str | None = None,
        current_interface_digest: str | None = None,
        capability_grant_ids: Sequence[str] = (),
    ) -> LiveAdmissionDecision:
        if not isinstance(envelope, LiveDispatchEnvelope) or not isinstance(lease, LiveCapabilityLease):
            raise LiveAdmissionError("live admission requires envelope and capability lease contracts")
        if envelope.executor_id != lease.executor_id or envelope.capability_lease_ref != lease.lease_id:
            return LiveAdmissionDecision(envelope.executor_id, lease.lease_id, "REJECTED_CAPABILITY", (), "executor or capability lease binding mismatch")
        observed = _time(now_observed)
        if observed >= _time(lease.expires_at):
            return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "REJECTED_CAPABILITY", (), "capability lease is stale")
        if lease.live_eligibility != "ELIGIBLE_FOR_LIVE_READONLY":
            return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "REJECTED_CAPABILITY", (), "live eligibility is not admitted: " + lease.live_eligibility)
        if current_binary_digest is not None and current_binary_digest != lease.binary_digest:
            return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "REJECTED_CAPABILITY", (), "binary digest drift invalidated the capability lease")
        if current_interface_digest is not None and current_interface_digest != lease.interface_digest:
            return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "REJECTED_CAPABILITY", (), "interface digest drift invalidated the capability lease")
        try:
            effective = self._effective(envelope, lease, os_granted, executor_declared)
        except LiveAdmissionError as exc:
            return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "REJECTED_CAPABILITY", (), str(exc))
        if self.admission_store is None:
            return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "ADMITTED", effective, "fresh lease and strict capability intersection admitted")
        current_epoch = float(time.time() if now_epoch is None else now_epoch)
        record = ExecutorAdmission(
            executor_id=lease.executor_id,
            adapter_family=lease.executor_id,
            observed_version=lease.executor_version,
            conformance_epoch=self.expected_conformance_epoch,
            declared_capabilities=effective,
            permission_ceiling=effective,
            workspace_support=(envelope.workspace_mode,),
            handoff_semantics="OS_LIVE_CAPSULE_ONLY",
            recovery_semantics="IDEMPOTENCY_RECONCILIATION",
            health_lease_id=lease.lease_id,
            health_status="HEALTHY",
            observed_at=current_epoch,
            health_expires_at=current_epoch + float(lease.ttl_seconds),
            privacy_boundary="LOCAL_FIXTURE_ONLY",
            conformance_receipt_ref="live-lease:" + lease.lease_id,
            capability_grant_ids=tuple(capability_grant_ids),
        )
        try:
            self.admission_store.admit(record, expected_conformance_epoch=self.expected_conformance_epoch, now=current_epoch)
            self.admission_store.route(
                lease.executor_id, required_capabilities=effective, workspace=envelope.workspace_mode,
                observed_version=lease.executor_version, conformance_epoch=self.expected_conformance_epoch, now=current_epoch,
            )
        except (ExecutorAdmissionError, ExecutorRouteDenied) as exc:
            return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "REJECTED_CAPABILITY", (), f"existing OS admission store denied route: {exc}")
        return LiveAdmissionDecision(lease.executor_id, lease.lease_id, "ADMITTED", effective, "fresh lease admitted through existing ExecutorAdmissionStore", admission_ref=lease.executor_id)

    def route(self, executor_id: str, *, required_capabilities: Iterable[str], workspace_mode: str, observed_version: str, now_epoch: float, revocation_store: Any = None) -> LiveAdmissionDecision:
        if self.admission_store is None:
            raise LiveAdmissionError("route requires the existing ExecutorAdmissionStore")
        try:
            record = self.admission_store.route(
                executor_id, required_capabilities=tuple(required_capabilities), workspace=workspace_mode,
                observed_version=observed_version, conformance_epoch=self.expected_conformance_epoch,
                revocation_store=revocation_store, now=now_epoch,
            )
        except (ExecutorAdmissionError, ExecutorRouteDenied) as exc:
            return LiveAdmissionDecision(executor_id, "unknown", "REJECTED_CAPABILITY", (), f"existing OS admission/revocation store denied route: {exc}")
        return LiveAdmissionDecision(record.executor_id, record.health_lease_id, "ADMITTED", tuple(sorted(record.permission_ceiling)), "existing OS admission/revocation store admitted route", admission_ref=record.executor_id)

    def revoke_in_flight(self, executor_id: str, *, started: bool, effect_class: str) -> LiveAdmissionDecision:
        if self.admission_store is None:
            raise LiveAdmissionError("revoke_in_flight requires the existing ExecutorAdmissionStore")
        record = self.admission_store.revoke(executor_id, reason="live capability revoked; future dispatch denied")
        if not started:
            status = "CANCEL_CONFIRMED"
            reason = "future dispatch revoked before start"
        elif effect_class == "READ_ONLY":
            status = "CANCEL_REQUESTED"
            reason = "in-flight read-only dispatch drained through OS revocation"
        else:
            status = "REQUIRES_RECONCILIATION"
            reason = "in-flight effect is not proven absent after revocation"
        return LiveAdmissionDecision(record.executor_id, record.health_lease_id, status, (), reason, admission_ref=record.executor_id)


__all__ = ["LiveAdmissionDecision", "LiveAdmissionError", "LiveCapabilityAdmission"]
