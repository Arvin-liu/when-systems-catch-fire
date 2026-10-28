"""Offline adversarial coverage matrix for durability boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from agent_kernel.contracts import sha256_json


ADVERSARIAL_SCHEMA = "ignition-durability-adversarial-matrix-r1"
ALLOWED_OUTCOMES = frozenset({"FAIL_CLOSED", "RECONCILIATION_REQUIRED", "RESTART_AND_REPLAY"})
REQUIRED_CASE_IDS = (
    "tampered_snapshot", "stale_snapshot", "corrupt_tail", "unknown_schema_epoch", "lossy_downgrade_without_approval",
    "cross_namespace_restore", "forged_delegation", "stale_capability_token", "revoked_executor_routed", "pack_hot_swap_mid_run",
    "failed_pack_activation", "retry_bypasses_budget", "double_accounting", "crash_after_external_dispatch", "duplicate_receipt",
    "recovery_loop_crash", "esi_advisory_authorize_injection", "soft_context_restored_as_hard_policy", "generated_projection_feedback_loop",
)
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "thoughts", "reasoning", "api_key", "access_token", "token", "cookie", "authorization", "secret"})


class AdversarialMatrixError(ValueError):
    """Raised when adversarial coverage is incomplete or escalatory."""


def _public(value: Any, field: str) -> str:
    markers = {"api_key", "access_token", "client_secret", "password", "hidden reasoning", "chain-of-thought"} if field in {"case_id", "target_boundary", "mutation"} else _FORBIDDEN
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in markers):
        raise AdversarialMatrixError(f"{field} must be a bounded public string")
    return value


@dataclass(frozen=True)
class AdversarialCase:
    case_id: str
    target_boundary: str
    mutation: str
    expected_outcome: str
    evidence_ref: str
    claim_ceiling: str
    case_digest: str | None = None

    def __post_init__(self) -> None:
        for field in ("case_id", "target_boundary", "mutation", "evidence_ref", "claim_ceiling"):
            _public(getattr(self, field), field)
        if self.expected_outcome not in ALLOWED_OUTCOMES:
            raise AdversarialMatrixError(f"{self.case_id} has unsafe expected outcome")
        if not any(word in self.claim_ceiling.casefold() for word in ("fail", "reconcile", "reconciliation", "replay", "fixture", "local")):
            raise AdversarialMatrixError(f"{self.case_id} claim ceiling is not bounded")
        expected = sha256_json(self._body())
        if self.case_digest is not None and self.case_digest != expected:
            raise AdversarialMatrixError(f"{self.case_id} digest mismatch")
        object.__setattr__(self, "case_digest", expected)

    def _body(self) -> dict[str, Any]:
        return {"case_id": self.case_id, "target_boundary": self.target_boundary, "mutation": self.mutation, "expected_outcome": self.expected_outcome, "evidence_ref": self.evidence_ref, "claim_ceiling": self.claim_ceiling}

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "case_digest": self.case_digest}


class AdversarialMatrix:
    def __init__(self, cases: Iterable[AdversarialCase]) -> None:
        self.cases = tuple(cases)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AdversarialMatrix":
        if not isinstance(data, Mapping) or data.get("schema_version") != ADVERSARIAL_SCHEMA or not isinstance(data.get("cases"), list):
            raise AdversarialMatrixError("adversarial matrix schema mismatch")
        required = {"case_id", "target_boundary", "mutation", "expected_outcome", "evidence_ref", "claim_ceiling", "case_digest"}
        cases: list[AdversarialCase] = []
        for item in data["cases"]:
            if not isinstance(item, Mapping) or set(item) != required:
                raise AdversarialMatrixError("adversarial case keys mismatch")
            cases.append(AdversarialCase(**dict(item)))
        return cls(cases)

    def validate(self) -> dict[str, Any]:
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise AdversarialMatrixError("adversarial case ids must be unique")
        missing = sorted(set(REQUIRED_CASE_IDS) - set(ids))
        if missing:
            raise AdversarialMatrixError("adversarial matrix missing cases: " + ",".join(missing))
        if any(case.expected_outcome not in ALLOWED_OUTCOMES for case in self.cases):
            raise AdversarialMatrixError("adversarial matrix contains an escalatory outcome")
        return {"status": "PASS", "schema": ADVERSARIAL_SCHEMA, "case_count": len(self.cases), "fail_closed_cases": sum(case.expected_outcome == "FAIL_CLOSED" for case in self.cases), "reconciliation_cases": sum(case.expected_outcome == "RECONCILIATION_REQUIRED" for case in self.cases), "restart_replay_cases": sum(case.expected_outcome == "RESTART_AND_REPLAY" for case in self.cases), "external_invocation": "NOT_RUN", "claim_ceiling": "Offline adversarial coverage classification only; not a production safety or epistemic result."}

    def run_offline(self) -> dict[str, Any]:
        self.validate()
        results = []
        for case in sorted(self.cases, key=lambda item: item.case_id):
            results.append({"case_id": case.case_id, "guard_status": case.expected_outcome, "external_invocation": "NOT_RUN", "open_obligation": case.expected_outcome != "FAIL_CLOSED", "evidence_ref": case.evidence_ref})
        return {"schema": ADVERSARIAL_SCHEMA, "status": "COVERAGE_CLASSIFIED_OFFLINE", "cases": results, "claim_ceiling": "Fixture guard coverage only; no production readiness, external success, Owner acceptance or epistemic acceptance."}


__all__ = ["ADVERSARIAL_SCHEMA", "ALLOWED_OUTCOMES", "AdversarialCase", "AdversarialMatrix", "AdversarialMatrixError", "REQUIRED_CASE_IDS"]
