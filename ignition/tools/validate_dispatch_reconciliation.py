#!/usr/bin/env python3
"""Offline durable external dispatch and reconciliation gate."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.dispatch_reconciliation import DispatchEnvelope, DispatchProgress, DispatchReceipt, DurableDispatchStore


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dispatch-gate-") as temp:
        store = DurableDispatchStore(Path(temp) / "dispatch.json")
        envelope = DispatchEnvelope("gate-dispatch", "gate-task", "external-fixture", "gate-idem", "a" * 64, "EXTERNAL_SIDE_EFFECT", 100.0, 5.0)
        record = store.create(envelope)
        store.mark_sent(record.dispatch_id)
        store.acknowledge(record.dispatch_id, accepted=True, ack_ref="gate-ack")
        store.append_progress(DispatchProgress(record.dispatch_id, record.task_id, record.executor_id, record.idempotency_key, 1, "RUNNING", "side effect dispatched"))
        timed_out = store.timeout(record.dispatch_id).state == "REQUIRES_RECONCILIATION"
        receipt = DispatchReceipt(record.dispatch_id, record.task_id, record.executor_id, record.idempotency_key, 2, "COMPLETED", "external completion claim", "b" * 64, 103.0)
        recorded = store.record_receipt(receipt, reconciliation=True).state == "RECEIPT_RECORDED"
        not_promoted = store.get(record.dispatch_id).state == "RECEIPT_RECORDED"
        validated = store.validate_receipt(record.dispatch_id, validation_ref="gate-validation", passed=True).state == "COMPLETED_VALIDATED"
        passed = timed_out and recorded and not_promoted and validated and store.audit()["status"] == "PASS"
        print(f"DURABLE_DISPATCH_R1={'PASS' if passed else 'FAIL'}")
        print(f"ACK_LOSS_SIDE_EFFECT={store.get(record.dispatch_id).state}")
        print(f"RECEIPT_BEFORE_VALIDATION={'PASS' if not_promoted else 'FAIL'}")
        print(f"VALIDATED_TERMINAL={'PASS' if validated else 'FAIL'}")
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
