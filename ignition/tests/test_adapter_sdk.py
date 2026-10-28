from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
import unittest

from agent_federation.conformance import FederationConformanceSuite, IdempotencyLedger
from agent_federation.contracts import (
    ExecutorDescriptor,
    ExecutorHealth,
    FederatedProgressEvent,
    FederatedTaskEnvelope,
    FederationContractError,
)
from agent_federation.sdk import (
    AdapterSDKError,
    CapabilityMismatch,
    MalformedOutput,
    ProcessTimeout,
    build_receipt,
    map_capabilities,
    parse_jsonl_events,
    python_fixture_argv,
    redact_public_mapping,
    run_safe_subprocess,
)
from tests.test_federation_core import descriptor, envelope


@dataclass
class FixtureAdapter:
    descriptor_value: ExecutorDescriptor
    last: FederatedProgressEvent | None = None

    def probe(self) -> ExecutorHealth:
        return self.descriptor_value.health

    def describe(self) -> ExecutorDescriptor:
        return self.descriptor_value

    def dispatch(self, task: FederatedTaskEnvelope) -> FederatedProgressEvent:
        self.last = FederatedProgressEvent(task.federation_task_id, self.descriptor_value.executor_id, 1, "RUNNING", "fixture dispatch", ())
        return self.last

    def status(self, federation_task_id: str) -> FederatedProgressEvent:
        return FederatedProgressEvent(federation_task_id, self.descriptor_value.executor_id, 2, "COMPLETED_VALIDATED", "fixture status", ())

    def cancel(self, federation_task_id: str) -> FederatedProgressEvent:
        return FederatedProgressEvent(federation_task_id, self.descriptor_value.executor_id, 3, "CANCELLED", "fixture cancelled", ())

    def resume(self, bundle):
        raise NotImplementedError


class AdapterSDKTests(unittest.TestCase):
    def test_safe_subprocess_uses_literal_argv_and_caps_timeout(self) -> None:
        result = run_safe_subprocess(python_fixture_argv("print('ok')"), timeout_seconds=2, executable_allowlist=(python_fixture_argv("x")[0],))
        self.assertEqual(result.stdout.strip(), "ok")
        with self.assertRaises(ProcessTimeout):
            run_safe_subprocess(python_fixture_argv("import time; time.sleep(2)"), timeout_seconds=0.05, executable_allowlist=(python_fixture_argv("x")[0],))
        with self.assertRaises(MalformedOutput):
            run_safe_subprocess(python_fixture_argv("print('x' * 100)"), timeout_seconds=2, output_cap_bytes=10, executable_allowlist=(python_fixture_argv("x")[0],))

    def test_parser_redaction_and_capability_mapping(self) -> None:
        events = parse_jsonl_events('{"sequence": 1}\n{"sequence": 2}\n')
        self.assertEqual(len(events), 2)
        with self.assertRaises(MalformedOutput):
            parse_jsonl_events("not-json\n")
        redacted = redact_public_mapping({"message": "Authorization: Bearer abc123", "api_key": "secret"})
        self.assertNotIn("api_key", redacted)
        self.assertEqual(redacted["redacted_fields"], 1)
        self.assertNotIn("abc123", redacted["message"])
        self.assertEqual(map_capabilities(["read", "test"], {"read": "repo.read", "test": "repo.test"}), ("repo.read", "repo.test"))
        with self.assertRaises(AdapterSDKError):
            map_capabilities(["unknown"], {})

    def test_conformance_and_idempotency(self) -> None:
        adapter = FixtureAdapter(descriptor())
        report = FederationConformanceSuite().run(adapter, envelope())
        self.assertTrue(report.passed)
        self.assertEqual(len(report.cases), 6)
        ledger = IdempotencyLedger()
        self.assertTrue(ledger.claim("key-1"))
        self.assertFalse(ledger.claim("key-1"))

    def test_unsupported_capability_short_circuits_as_typed_case(self) -> None:
        limited = descriptor()
        limited = ExecutorDescriptor(**{**limited.__dict__, "capability_tokens": ("repo.read",)})
        report = FederationConformanceSuite().run(FixtureAdapter(limited), envelope())
        self.assertTrue(report.passed)
        self.assertEqual(report.cases[-1].name, "deny_unsupported_capability")

    def test_receipt_builder_redacts_telemetry(self) -> None:
        receipt = build_receipt(
            federation_task_id="fed-task-1", executor_id="fixture.executor.a", terminal_state="FAILED",
            claimed_actions=(), artifacts=(), validation_refs=(), external_session_ref=None,
            telemetry={"api_key": "hidden", "duration_ms": 2}, unresolveds=("timeout",),
            handoff_eligible=False, handoff_reason="timeout",
        )
        self.assertNotIn("api_key", receipt.executor_telemetry)
        self.assertEqual(receipt.executor_telemetry["redacted_fields"], 1)


if __name__ == "__main__":
    unittest.main()
