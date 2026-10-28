from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.dispatch_reconciliation import DispatchConflict, DispatchEnvelope, DispatchProgress, DispatchReceipt, DurableDispatchStore


def envelope(dispatch_id: str, *, effect: str = "EXTERNAL_SIDE_EFFECT") -> DispatchEnvelope:
    return DispatchEnvelope(dispatch_id, f"task-{dispatch_id}", "external-fixture", f"idem-{dispatch_id}", "a" * 64, effect, 100.0, 5.0)


def receipt(record, *, sequence: int = 2, terminal: str = "COMPLETED") -> DispatchReceipt:
    return DispatchReceipt(record.dispatch_id, record.task_id, record.executor_id, record.idempotency_key, sequence, terminal, "public executor receipt", "b" * 64, 103.0)


class DispatchReconciliationTests(unittest.TestCase):
    def test_idempotency_progress_order_and_forged_binding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dispatch-") as temp:
            store = DurableDispatchStore(Path(temp) / "dispatch.json")
            record = store.create(envelope("dispatch-a"))
            self.assertEqual(store.create(envelope("dispatch-a")), record)
            with self.assertRaises(DispatchConflict):
                store.create(DispatchEnvelope("different-dispatch", record.task_id, record.executor_id, record.idempotency_key, "c" * 64, "EXTERNAL_SIDE_EFFECT", 100.0, 5.0))
            store.mark_sent(record.dispatch_id)
            store.acknowledge(record.dispatch_id, accepted=True, ack_ref="ack-a")
            store.append_progress(DispatchProgress(record.dispatch_id, record.task_id, record.executor_id, record.idempotency_key, 1, "RUNNING", "started"))
            with self.assertRaises(DispatchConflict):
                store.append_progress(DispatchProgress(record.dispatch_id, record.task_id, record.executor_id, record.idempotency_key, 1, "RUNNING", "duplicate"))
            with self.assertRaises(DispatchConflict):
                store.record_receipt(DispatchReceipt(record.dispatch_id, record.task_id, "forged", record.idempotency_key, 2, "COMPLETED", "forged", "b" * 64, 103.0))

    def test_external_receipt_requires_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dispatch-") as temp:
            store = DurableDispatchStore(Path(temp) / "dispatch.json")
            record = store.create(envelope("dispatch-b"))
            store.mark_sent(record.dispatch_id)
            store.acknowledge(record.dispatch_id, accepted=True, ack_ref="ack-b")
            recorded = store.record_receipt(receipt(record))
            self.assertEqual(recorded.state, "RECEIPT_RECORDED")
            self.assertEqual(store.validate_receipt(record.dispatch_id, validation_ref="validation-b", passed=True).state, "COMPLETED_VALIDATED")

    def test_timeout_policy_read_only_retry_and_side_effect_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dispatch-") as temp:
            store = DurableDispatchStore(Path(temp) / "dispatch.json")
            read = store.create(envelope("dispatch-read", effect="READ_ONLY"))
            store.mark_sent(read.dispatch_id)
            self.assertEqual(store.timeout(read.dispatch_id).state, "RETRY_ELIGIBLE_READ_ONLY")
            self.assertEqual(store.retry_read_only(read.dispatch_id).state, "SENT")
            side = store.create(envelope("dispatch-side", effect="EXTERNAL_SIDE_EFFECT"))
            store.mark_sent(side.dispatch_id)
            self.assertEqual(store.timeout(side.dispatch_id).state, "REQUIRES_RECONCILIATION")
            with self.assertRaises(DispatchConflict):
                store.mark_sent(side.dispatch_id)
            reconciled = store.record_receipt(receipt(store.get(side.dispatch_id), sequence=1, terminal="UNKNOWN"), reconciliation=True)
            self.assertEqual(reconciled.state, "RECEIPT_RECORDED")


if __name__ == "__main__":
    unittest.main()
