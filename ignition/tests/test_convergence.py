from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_federation import (
    ApprovalBridge,
    ApprovalPolicy,
    ArtifactRef,
    ExternalApprovalObservation,
    ExternalSessionRef,
    FailoverContext,
    FederatedProgressEvent,
    FederatedResultReceipt,
    FederationConvergence,
    HandoffEligibility,
    ProgressLedger,
    ReceiptRegistry,
    project_approval,
    project_recovery,
)
from agent_federation.convergence import ConvergenceError, FederationMemoryAbsorber, project_progress, project_receipt
from agent_runtime.memory import OperationalMemoryStore
from agent_federation.approval_handoff import decide_failover
from agent_federation.sdk import MalformedOutput, parse_jsonl_events


FIXTURES = Path(__file__).parent / "fixtures" / "federation"


def validated_receipt() -> FederatedResultReceipt:
    return FederatedResultReceipt.build(
        federation_task_id="convergence-task-001", executor_id="external.codex", terminal_state="COMPLETED_VALIDATED",
        claimed_actions=("read manifest",), artifact_refs=(ArtifactRef("fixture/manifest.json", "b" * 64, "manifest"),),
        validation_refs=("validator/manifest-v1",), external_session_ref=ExternalSessionRef("external.codex", "thread-001", "codex-thread-id", "2026-08-16T00:00:00Z"),
        executor_telemetry={"transport": "fixture", "vendor_event_count": 4}, unresolveds=(),
        handoff_eligibility=HandoffEligibility(True, "validated"),
    )


class ConvergenceTests(unittest.TestCase):
    def event(self, sequence: int, state: str, summary: str) -> FederatedProgressEvent:
        return FederatedProgressEvent("convergence-task-001", "external.codex", sequence, state, summary, ())

    def test_progress_is_sortable_deduplicated_and_late_terminal_is_not_regression(self) -> None:
        ledger = ProgressLedger()
        first = ledger.ingest(self.event(1, "RUNNING", "started"), event_key="event-1")
        self.assertEqual(first.status, "NEW")
        terminal = ledger.ingest(self.event(3, "COMPLETED_UNVALIDATED", "done claim"), event_key="event-3")
        self.assertEqual(terminal.status, "NEW")
        duplicate = ledger.ingest(self.event(3, "COMPLETED_UNVALIDATED", "done claim"), event_key="event-3")
        self.assertEqual(duplicate.status, "DUPLICATE")
        late = ledger.ingest(self.event(2, "FAILED", "late failure"), event_key="event-2")
        self.assertEqual(late.status, "LATE_TERMINAL")
        self.assertEqual(ledger.canonical("convergence-task-001").sequence, 3)
        self.assertEqual([event.sequence for event in ledger.ordered("convergence-task-001")], [1, 2, 3])

    def test_streaming_partial_and_malformed_parser_fixtures_are_typed(self) -> None:
        events = parse_jsonl_events((FIXTURES / "streaming-progress-events.jsonl").read_text(encoding="utf-8"))
        self.assertEqual([item["sequence"] for item in events], [1, 2, 3])
        with self.assertRaises(MalformedOutput):
            parse_jsonl_events((FIXTURES / "malformed-event.txt").read_text(encoding="utf-8"))

    def test_receipt_registry_accepts_validated_and_keeps_unverified_separate(self) -> None:
        registry = ReceiptRegistry()
        receipt = validated_receipt()
        self.assertEqual(registry.register(receipt).status, "VERIFIED")
        self.assertEqual(registry.register(receipt).status, "DUPLICATE")
        unverified = FederatedResultReceipt.build(
            federation_task_id="convergence-task-002", executor_id="external.hermes", terminal_state="REQUIRES_RECONCILIATION",
            claimed_actions=(), artifact_refs=(), validation_refs=(), external_session_ref=None,
            executor_telemetry={"transport": "fixture"}, unresolveds=("OS_VALIDATION_NOT_PERFORMED",),
            handoff_eligibility=HandoffEligibility(False, "unverified"),
        )
        self.assertEqual(registry.register(unverified).status, "UNVERIFIED")

    def test_memory_absorption_is_public_and_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory(prefix="federation-memory-") as temp:
            store = OperationalMemoryStore(Path(temp) / "memory.json")
            absorber = FederationMemoryAbsorber(store)
            event = self.event(1, "RUNNING", "public inspection started")
            projection = project_progress(event, memory_id="memory-progress-1", source_run_id="convergence-task-001", event_key="event-1")
            self.assertEqual(absorber.absorb("progress:event-1", projection).status, "ABSORBED")
            self.assertEqual(absorber.absorb("progress:event-1", projection).status, "DUPLICATE")
            self.assertEqual(len(store.query()), 1)
            raw = (Path(temp) / "memory.json").read_text(encoding="utf-8")
            self.assertNotIn("vendor_event_count", raw)

    def test_receipt_approval_recovery_projects_are_typed_memory(self) -> None:
        receipt = validated_receipt()
        receipt_registry = ReceiptRegistry()
        ingest = receipt_registry.register(receipt)
        receipt_projection = project_receipt(receipt, memory_id="memory-receipt-1", source_run_id="convergence-task-001", ingest=ingest)
        self.assertEqual(receipt_projection.memory_type, "EPISODIC")
        approval = ApprovalBridge().evaluate(ApprovalPolicy("AUTO", True, ("repo.read",)), ("repo.read",), external_observation=ExternalApprovalObservation("APPROVED", "approval-ref-1"))
        self.assertEqual(project_approval(approval, memory_id="memory-approval-1", source_run_id="convergence-task-001").memory_type, "APPROVAL")
        recovery = decide_failover(FailoverContext("external.codex", "external.hermes", "EXECUTOR_TIMEOUT", ("repo.read",), True, False, False, True), target_capabilities=("repo.read",))
        self.assertEqual(project_recovery(recovery, memory_id="memory-recovery-1", source_run_id="convergence-task-001").memory_type, "ROLLBACK")

    def test_hidden_or_raw_prompt_projection_is_rejected(self) -> None:
        event = self.event(1, "RUNNING", "raw prompt should not cross")
        with self.assertRaises(ConvergenceError):
            project_progress(event, memory_id="memory-bad", source_run_id="convergence-task-001", event_key="event-bad")

    def test_convergence_coordinator_deduplicates_progress_and_receipts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="federation-convergence-") as temp:
            convergence = FederationConvergence(OperationalMemoryStore(Path(temp) / "memory.json"))
            event = self.event(1, "RUNNING", "one public event")
            self.assertEqual(convergence.ingest_progress(event, source_run_id="convergence-task-001", memory_id="memory-progress-2", event_key="event-2").status, "NEW")
            self.assertEqual(convergence.ingest_progress(event, source_run_id="convergence-task-001", memory_id="memory-progress-2", event_key="event-2").status, "DUPLICATE")
            receipt = validated_receipt()
            self.assertEqual(convergence.ingest_receipt(receipt, source_run_id="convergence-task-001", memory_id="memory-receipt-2").status, "VERIFIED")
            self.assertEqual(convergence.ingest_receipt(receipt, source_run_id="convergence-task-001", memory_id="memory-receipt-2").status, "DUPLICATE")
            self.assertEqual(len(convergence.audit()["progress"]["event_count"] and convergence.memory.store.query()), 2)


if __name__ == "__main__":
    unittest.main()
