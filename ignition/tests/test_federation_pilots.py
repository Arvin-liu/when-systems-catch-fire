from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_federation import (
    ReferenceExecutorAdapter,
    run_federation_pilots,
    validate_federation_pilot_report,
    write_federation_pilot_report,
)


class FederationPilotTests(unittest.TestCase):
    def test_reference_fixture_is_read_only_and_has_two_deterministic_issues(self) -> None:
        report = run_federation_pilots()
        self.assertEqual(report["fixture"]["os_validator_expected_issue_count"], 2)
        self.assertFalse(report["fixture"]["formal_repository_used_as_live_target"])
        self.assertEqual(report["live_invocation_policy"]["status"], "NOT_RUN_LIVE_EXTERNAL_INVOCATION")

    def test_pilot_a_uses_same_envelope_for_reference_and_available_adapters(self) -> None:
        report = run_federation_pilots()
        matrix = {row["executor_id"]: row for row in report["pilot_a_conformance_matrix"]}
        self.assertEqual(set(matrix), {"reference.executor", "external.openclaw", "external.hermes", "external.codex"})
        self.assertEqual(matrix["reference.executor"]["dispatch"], "PASS")
        self.assertEqual(matrix["external.openclaw"]["dispatch"], "DENIED_UNSUPPORTED_CAPABILITY")
        self.assertEqual(matrix["external.hermes"]["dispatch"], "PASS")
        self.assertEqual(matrix["external.codex"]["dispatch"], "PASS")
        self.assertEqual(matrix["external.hermes"]["structured_fidelity"], "TEXT_DEGRADED")
        self.assertEqual(matrix["external.codex"]["structured_fidelity"], "STRUCTURED_JSONL")
        for row in matrix.values():
            self.assertEqual(row["live_invocation"], "NOT_RUN_LIVE_EXTERNAL_INVOCATION")

    def test_pilot_b_reobserves_before_handoff_and_os_validates_target(self) -> None:
        report = run_federation_pilots()
        handoff = report["pilot_b_cross_executor_handoff"]
        self.assertEqual(handoff["status"], "PASS")
        self.assertEqual(handoff["takeover"]["status"], "ACCEPTED")
        self.assertEqual(handoff["target_executor_receipt_state"], "REQUIRES_RECONCILIATION")
        self.assertEqual(handoff["target_os_validation_receipt_state"], "COMPLETED_VALIDATED")
        self.assertEqual(handoff["validator"]["issue_count"], 2)

    def test_pilot_c_faults_fail_closed_without_repeated_irreversible_action(self) -> None:
        report = run_federation_pilots()
        faults = report["pilot_c_fault_injection"]
        self.assertEqual(faults["status"], "PASS")
        self.assertTrue(faults["no_irreversible_action_repeated"])
        self.assertEqual(faults["faults"]["malformed_vendor_output"], "MALFORMED_OUTPUT_REJECTED")
        self.assertEqual(faults["faults"]["forged_owner_approval"], "BLOCKED_WITH_EVIDENCE")
        self.assertEqual(faults["faults"]["unknown_side_effect"], "REQUIRES_RECONCILIATION")
        self.assertEqual(faults["faults"]["duplicate_dispatch"], "DUPLICATE_REJECTED")

    def test_report_writer_is_machine_readable_and_validated(self) -> None:
        with tempfile.TemporaryDirectory(prefix="federation-pilot-report-") as temporary:
            path = Path(temporary) / "federation-pilot-results-r1.json"
            written = write_federation_pilot_report(path)
            self.assertEqual(written["validation"]["status"], "PASS")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(validate_federation_pilot_report(loaded)["status"], "PASS")

    def test_reference_executor_is_a_bounded_protocol_view(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-executor-fixture-") as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# fixture\n", encoding="utf-8")
            (root / "manifest.json").write_text('{"files":[],"manifest_version":"fixture-r1"}\n', encoding="utf-8")
            adapter = ReferenceExecutorAdapter(root)
            self.assertEqual(adapter.describe().executor_id, "reference.executor")
            self.assertEqual(adapter.describe().capability_tokens, ("repo.read", "structured_progress"))
            self.assertNotIn("browser.act", adapter.describe().capability_tokens)


if __name__ == "__main__":
    unittest.main()
