from __future__ import annotations

import json
import sys
from pathlib import Path
import unittest

from agent_federation import (
    ApprovalBridge,
    ApprovalPolicy,
    ExternalApprovalObservation,
    ExternalSessionRef,
    FederatedProgressEvent,
    FederationContractError,
    ProgressLedger,
)
from agent_federation.adapters.codex import CodexAdapter
from agent_federation.adapters.hermes import HermesAdapter
from agent_federation.adapters.openclaw import OpenClawAdapter
from agent_federation.sdk import (
    AdapterSDKError,
    MalformedOutput,
    discover_executable,
    match_version,
    parse_jsonl_events,
    python_fixture_argv,
    redact_public_mapping,
    run_safe_subprocess,
)
from tools.propagation.impact_contract import derive_blast_radius, load_blast_radius_contract


ROOT = Path(__file__).resolve().parents[1]


class FederationStep12AdversarialTests(unittest.TestCase):
    def test_sdk_rejects_shell_values_bad_patterns_and_output_overflow(self) -> None:
        self.assertIsNone(discover_executable("ignition-executor-that-does-not-exist"))
        with self.assertRaises(AdapterSDKError):
            discover_executable("/definitely/not-a-bare-executable")
        self.assertTrue(match_version("codex 0.144.4", r"^codex 0\."))
        with self.assertRaises(AdapterSDKError):
            match_version("codex 0.144.4", "[")
        with self.assertRaises(AdapterSDKError):
            run_safe_subprocess((sys.executable, "-c", "print('ok')", ";"))
        with self.assertRaises(MalformedOutput):
            run_safe_subprocess(
                python_fixture_argv("print('x' * 64)"),
                output_cap_bytes=8,
                executable_allowlist=(sys.executable,),
            )

    def test_missing_external_clis_fail_closed_as_unavailable(self) -> None:
        adapters = (
            OpenClawAdapter(executable="/definitely/missing/openclaw"),
            HermesAdapter(executable="/definitely/missing/hermes"),
            CodexAdapter(executable="/definitely/missing/codex"),
        )
        for adapter in adapters:
            with self.subTest(executor=adapter.executor_id):
                self.assertEqual(adapter.probe().status, "UNAVAILABLE")
                self.assertEqual(adapter.describe().availability, "UNAVAILABLE")

    def test_public_boundary_redacts_hidden_state_and_approval_is_an_intersection(self) -> None:
        public = redact_public_mapping(
            {
                "prompt": "hidden",
                "nested": {"reasoning": "hidden"},
                "message": "authorization: Bearer private-value",
            }
        )
        self.assertNotIn("prompt", public)
        self.assertNotIn("reasoning", public["nested"])
        self.assertIn("[REDACTED]", public["message"])
        with self.assertRaises(FederationContractError):
            ExternalSessionRef("external.fixture", "session-1", "cli", "2026-08-16T00:00:00Z", False)

        decision = ApprovalBridge().evaluate(
            ApprovalPolicy("DENY", False, ("repo.read",)),
            ("repo.read",),
            external_observation=ExternalApprovalObservation("APPROVED", "external-allow"),
            external_capability_ceiling=("repo.read",),
            external_approval_required=True,
        )
        self.assertEqual(decision.status, "BLOCKED_WITH_EVIDENCE")
        self.assertIn("OS approval policy is DENY", decision.reason)

    def test_streaming_progress_duplicates_late_events_and_terminal_order_are_explicit(self) -> None:
        self.assertEqual(len(parse_jsonl_events('{"type":"started"}\n')), 1)
        with self.assertRaises(MalformedOutput):
            parse_jsonl_events('{"type":"started"}\n{"type":')

        def event(sequence: int, state: str) -> FederatedProgressEvent:
            return FederatedProgressEvent("step12-task", "fixture.executor", sequence, state, "public fixture status", ())

        ledger = ProgressLedger()
        self.assertEqual(ledger.ingest(event(0, "RUNNING"), event_key="progress-0").status, "NEW")
        terminal = event(2, "COMPLETED_UNVALIDATED")
        self.assertEqual(ledger.ingest(terminal, event_key="progress-2").status, "NEW")
        self.assertEqual(ledger.ingest(terminal, event_key="progress-2").status, "DUPLICATE")
        self.assertEqual(ledger.ingest(event(1, "FAILED"), event_key="progress-1").status, "LATE_TERMINAL")
        self.assertEqual(ledger.ingest(event(3, "RUNNING"), event_key="progress-3").status, "POST_TERMINAL_EVENT")

    def test_federation_source_change_stays_outside_knowledge_and_writing(self) -> None:
        contract = load_blast_radius_contract(str(ROOT))
        result = derive_blast_radius(
            ["agent_federation/contracts.py", "tests/test_federation_step12_adversarial.py"],
            contract,
        )
        self.assertEqual(
            result["source_domains"],
            {"agent_federation": ["agent_federation/contracts.py", "tests/test_federation_step12_adversarial.py"]},
        )
        self.assertEqual(result["affected_projections"], ["agent_platform.federation"])
        self.assertTrue(
            set(result["affected_projections"]).isdisjoint(
                contract["source_domains"]["agent_federation"]["forbidden_projections"]
            )
        )

    def test_pilot_is_disposable_and_reference_executor_remains_frozen(self) -> None:
        pilot = json.loads((ROOT / "data/agent-federation/federation-pilot-results-r1.json").read_text(encoding="utf-8"))
        self.assertFalse(pilot["fixture"]["formal_repository_used_as_live_target"])
        self.assertEqual(pilot["live_invocation_policy"]["status"], "NOT_RUN_LIVE_EXTERNAL_INVOCATION")

        def keys(value: object) -> set[str]:
            found: set[str] = set()
            if isinstance(value, dict):
                found.update(str(key).casefold() for key in value)
                for item in value.values():
                    found.update(keys(item))
            elif isinstance(value, list):
                for item in value:
                    found.update(keys(item))
            return found

        self.assertTrue(
            keys(pilot).isdisjoint(
                {"prompt", "system_prompt", "chain_of_thought", "cot", "reasoning", "token", "secret", "cookie", "authorization"}
            )
        )
        ownership = json.loads((ROOT / "data/agent-federation/executor-component-ownership-r1.json").read_text(encoding="utf-8"))
        roles = {component["component_id"]: component["role"] for component in ownership["components"]}
        self.assertEqual(roles["reference-executor"], "REFERENCE_ONLY")
        self.assertIn("agent_platform.federation", load_blast_radius_contract(str(ROOT))["projection_classes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
