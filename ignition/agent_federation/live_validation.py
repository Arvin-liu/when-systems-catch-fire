"""Independent OS-owned validation for Task137 live completion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json

from .contracts import FederationContractError, canonical_digest
from .live_bridge import LiveCapabilityLease, LiveDispatchEnvelope, LiveExecutorReceipt
from .live_pilot import DisposableLiveCompletionFixture, LiveCompletionValidator, LiveValidationReport


LIVE_VALIDATION_SCHEMA = "ignition-137-independent-validation-receipt-r2"
_SURFACE_KEYS = ("channel", "browser", "remote_git", "user_data", "formal_repo_mutation", "billing_authority")


def _iso(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be non-empty text")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class IndependentValidationReceipt:
    schema_version: str
    task_id: str
    dispatch_id: str
    attempt_id: str
    executor_id: str
    adapter_id: str
    capability_lease_digest: str
    workspace_ref: str
    workspace_digest_before: str
    workspace_digest_after: str
    result_digest: str
    executor_receipt_digest: str
    status: str
    checks: Mapping[str, bool]
    failure_codes: tuple[str, ...]
    effective_capabilities: tuple[str, ...]
    child_depth: int
    reconciliation_status: str
    claim_ceiling: str
    validator_receipt_digest: str

    def __post_init__(self) -> None:
        if self.schema_version != LIVE_VALIDATION_SCHEMA:
            raise FederationContractError("independent validation schema mismatch")
        for value, field in (
            (self.task_id, "task_id"), (self.dispatch_id, "dispatch_id"), (self.attempt_id, "attempt_id"),
            (self.executor_id, "executor_id"), (self.adapter_id, "adapter_id"), (self.workspace_ref, "workspace_ref"),
            (self.claim_ceiling, "claim_ceiling"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise FederationContractError(f"validation receipt {field} must be non-empty text")
        for value, field in (
            (self.capability_lease_digest, "capability_lease_digest"),
            (self.workspace_digest_before, "workspace_digest_before"),
            (self.workspace_digest_after, "workspace_digest_after"),
            (self.result_digest, "result_digest"),
            (self.executor_receipt_digest, "executor_receipt_digest"),
        ):
            if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise FederationContractError(f"validation receipt {field} must be a lowercase SHA-256 digest")
        if self.status not in {"PASS", "FAIL"}:
            raise FederationContractError("validation receipt status is unsupported")
        if not isinstance(self.checks, Mapping) or any(not isinstance(value, bool) for value in self.checks.values()):
            raise FederationContractError("validation receipt checks must be boolean fields")
        if self.status == "PASS" and (self.failure_codes or not all(self.checks.values())):
            raise FederationContractError("PASS validation receipt contains failed checks")
        if any(not isinstance(value, str) or not value.strip() for value in self.failure_codes):
            raise FederationContractError("validation receipt failure codes must be non-empty text")
        if any(not isinstance(value, str) or not value.strip() for value in self.effective_capabilities):
            raise FederationContractError("validation receipt capabilities must be non-empty text")
        if self.child_depth != 1:
            raise FederationContractError("validated live completion requires child depth one")
        if self.reconciliation_status not in {"NOT_REQUIRED", "CLOSED", "OPEN"}:
            raise FederationContractError("validation receipt reconciliation status is unsupported")
        expected = canonical_digest(self._unsigned_dict())
        if self.validator_receipt_digest != expected:
            raise FederationContractError("validator receipt digest does not match unsigned content")

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "task_id": self.task_id, "dispatch_id": self.dispatch_id,
            "attempt_id": self.attempt_id, "executor_id": self.executor_id, "adapter_id": self.adapter_id,
            "capability_lease_digest": self.capability_lease_digest, "workspace_ref": self.workspace_ref,
            "workspace_digest_before": self.workspace_digest_before, "workspace_digest_after": self.workspace_digest_after,
            "result_digest": self.result_digest, "executor_receipt_digest": self.executor_receipt_digest,
            "status": self.status, "checks": dict(self.checks), "failure_codes": list(self.failure_codes),
            "effective_capabilities": list(self.effective_capabilities), "child_depth": self.child_depth,
            "reconciliation_status": self.reconciliation_status, "claim_ceiling": self.claim_ceiling,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self._unsigned_dict()
        result["validator_receipt_digest"] = self.validator_receipt_digest
        return result

    @classmethod
    def build(cls, **kwargs: Any) -> "IndependentValidationReceipt":
        values = dict(kwargs)
        values.setdefault("schema_version", LIVE_VALIDATION_SCHEMA)
        values["validator_receipt_digest"] = canonical_digest({key: value for key, value in values.items() if key != "validator_receipt_digest"})
        return cls(**values)


class LiveIndependentValidator:
    """Validate the external result independently of executor claims."""

    def __init__(self, fixture: DisposableLiveCompletionFixture) -> None:
        self.fixture = fixture

    def validate(
        self,
        *,
        envelope: LiveDispatchEnvelope,
        lease: LiveCapabilityLease,
        executor_receipt: LiveExecutorReceipt,
        result: Mapping[str, Any],
        before_digest: str,
        after_digest: str,
        observed_at: str,
        child_depth: int,
        external_surface_evidence: Mapping[str, bool],
        side_effect_observation: str = "READ_ONLY_UNCHANGED",
    ) -> tuple[IndependentValidationReceipt, LiveValidationReport]:
        checks: dict[str, bool] = {}
        failures: list[str] = []
        try:
            fixture_report = LiveCompletionValidator(self.fixture).validate(
                result, before_digest=before_digest, after_digest=after_digest, side_effect_observation=side_effect_observation,
            )
        except Exception:
            fixture_report = LiveValidationReport("FAIL", {}, ("VALIDATOR_EXCEPTION",), sha256_json(result))

        checks["task_binding"] = executor_receipt.task_id == envelope.task_id
        checks["dispatch_binding"] = executor_receipt.dispatch_id == envelope.dispatch_id
        checks["attempt_binding"] = executor_receipt.attempt_id == envelope.attempt_id
        checks["executor_binding"] = executor_receipt.executor_id == envelope.executor_id == lease.executor_id
        checks["adapter_binding"] = executor_receipt.adapter_id == envelope.adapter_id
        checks["lease_reference_binding"] = envelope.capability_lease_ref == lease.lease_id
        checks["lease_digest_binding"] = executor_receipt.capability_lease_digest == lease.lease_digest
        try:
            checks["lease_integrity"] = LiveCapabilityLease.from_dict(lease.to_dict()) == lease
        except Exception:
            checks["lease_integrity"] = False
        try:
            checks["receipt_integrity"] = LiveExecutorReceipt.from_dict(executor_receipt.to_dict()) == executor_receipt
        except Exception:
            checks["receipt_integrity"] = False
        try:
            observed = _iso(observed_at)
            checks["lease_fresh"] = _iso(lease.observed_at) <= observed <= _iso(lease.expires_at)
        except (TypeError, ValueError):
            checks["lease_fresh"] = False
        checks["lease_eligibility"] = lease.live_eligibility == "ELIGIBLE_FOR_LIVE_READONLY"
        effective = tuple(sorted(set(envelope.permission_ceiling) & set(lease.observed_capabilities)))
        checks["permission_intersection"] = tuple(sorted(envelope.permission_ceiling)) == effective and not (set(envelope.permission_ceiling) & set(lease.forbidden_capabilities))
        checks["workspace_binding"] = executor_receipt.workspace_ref == envelope.workspace_ref
        checks["workspace_digest_binding"] = executor_receipt.workspace_before_digest == before_digest and executor_receipt.workspace_after_digest == after_digest
        checks["result_digest_binding"] = executor_receipt.result_digest == sha256_json(result)
        checks["executor_return_unvalidated"] = executor_receipt.state == "RETURNED_UNVALIDATED" and executor_receipt.os_validation_status == "NOT_RUN"
        checks["fixture_validator"] = fixture_report.status == "PASS"
        checks["workspace_unchanged"] = before_digest == after_digest == self.fixture.before_digest == self.fixture.current_digest()
        checks["child_depth"] = child_depth == 1 and executor_receipt.child_depth == 1 and envelope.provenance.get("child_depth") == 1
        checks["side_effect_free"] = side_effect_observation == "READ_ONLY_UNCHANGED" and executor_receipt.side_effect_observation == "READ_ONLY_UNCHANGED"
        checks["external_surface_clear"] = set(external_surface_evidence) == set(_SURFACE_KEYS) and all(value is False for value in external_surface_evidence.values())
        for name, passed in checks.items():
            if not passed:
                failures.append(name.upper())
        failures = sorted(set(failures))
        status = "PASS" if not failures else "FAIL"
        validation_receipt = IndependentValidationReceipt.build(
            task_id=envelope.task_id, dispatch_id=envelope.dispatch_id, attempt_id=envelope.attempt_id,
            executor_id=envelope.executor_id, adapter_id=envelope.adapter_id, capability_lease_digest=lease.lease_digest,
            workspace_ref=envelope.workspace_ref, workspace_digest_before=before_digest, workspace_digest_after=after_digest,
            result_digest=sha256_json(result), executor_receipt_digest=executor_receipt.receipt_digest, status=status,
            checks=checks, failure_codes=tuple(failures), effective_capabilities=effective, child_depth=child_depth,
            reconciliation_status="CLOSED" if status == "PASS" else executor_receipt.reconciliation_status,
            claim_ceiling="Independent OS validation of one bounded synthetic read-only result only; no Goal completion, production readiness or external truth is inferred.",
        )
        return validation_receipt, fixture_report


__all__ = ["IndependentValidationReceipt", "LIVE_VALIDATION_SCHEMA", "LiveIndependentValidator"]
