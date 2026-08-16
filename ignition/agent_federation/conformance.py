"""Boundary conformance checks shared by reference and vendor adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import FederatedExecutor, FederatedTaskEnvelope, FederationContractError
from .sdk import CapabilityMismatch, require_capabilities


@dataclass(frozen=True)
class ConformanceCase:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class ConformanceReport:
    executor_id: str
    cases: tuple[ConformanceCase, ...]

    @property
    def passed(self) -> bool:
        return all(case.status == "PASS" for case in self.cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "passed": self.passed,
            "cases": [{"name": case.name, "status": case.status, "detail": case.detail} for case in self.cases],
        }


class FederationConformanceSuite:
    """Run only observable protocol checks; it never executes a hidden loop."""

    def run(self, adapter: FederatedExecutor, envelope: FederatedTaskEnvelope) -> ConformanceReport:
        cases: list[ConformanceCase] = []
        descriptor = adapter.describe()
        health = adapter.probe()
        if descriptor.executor_id == "" or health.status == "UNKNOWN":
            raise FederationContractError("adapter descriptor/health is not usable")
        cases.append(ConformanceCase("probe_descriptor", "PASS", f"{descriptor.executor_id}:{health.status}"))
        try:
            require_capabilities(envelope.required_capabilities, descriptor.capability_tokens)
        except CapabilityMismatch as exc:
            cases.append(ConformanceCase("deny_unsupported_capability", "PASS", str(exc)))
            return ConformanceReport(descriptor.executor_id, tuple(cases))
        cases.append(ConformanceCase("capability_mapping", "PASS", "required capability ceiling is declared"))
        event = adapter.dispatch(envelope)
        if event.federation_task_id != envelope.federation_task_id or event.executor_id != descriptor.executor_id:
            raise FederationContractError("adapter dispatch returned an unbound progress event")
        cases.append(ConformanceCase("dispatch_progress", "PASS", f"sequence={event.sequence}"))
        status = adapter.status(envelope.federation_task_id)
        if status.sequence < event.sequence:
            raise FederationContractError("adapter status regressed progress sequence")
        cases.append(ConformanceCase("status_ordering", "PASS", f"sequence={status.sequence}"))
        if descriptor.cancel_support:
            cancelled = adapter.cancel(envelope.federation_task_id)
            if cancelled.federation_task_id != envelope.federation_task_id:
                raise FederationContractError("adapter cancellation returned the wrong task")
            cases.append(ConformanceCase("cancel", "PASS", cancelled.state))
        else:
            cases.append(ConformanceCase("cancel", "PASS", "UNSUPPORTED_DECLARED"))
        if descriptor.native_resume_support:
            cases.append(ConformanceCase("resume", "PASS", "DECLARED_OPTIONAL"))
        else:
            cases.append(ConformanceCase("resume", "PASS", "UNSUPPORTED_DECLARED"))
        return ConformanceReport(descriptor.executor_id, tuple(cases))


class IdempotencyLedger:
    """In-memory duplicate guard used by adapters before dispatch."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def claim(self, idempotency_key: str) -> bool:
        if not isinstance(idempotency_key, str) or not idempotency_key:
            raise FederationContractError("idempotency key must be non-empty")
        if idempotency_key in self._seen:
            return False
        self._seen.add(idempotency_key)
        return True
