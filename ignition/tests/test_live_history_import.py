from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from tools.import_historical_live_attempts import build_historical_records, import_history


class HistoricalAttemptImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]

    def test_build_preserves_four_historical_states_and_second_context_loss(self) -> None:
        records = build_historical_records(self.repo_root)
        self.assertEqual(len(records), 4)
        self.assertEqual(
            [record["process"]["state"] for record in records],
            ["TIMED_OUT_EFFECT_UNKNOWN", "FAILED_VALIDATION", "STARTUP_FAILURE", "OBSERVATION_INCOMPLETE"],
        )
        second = records[-1]
        self.assertEqual(second["task_id"], "IGNITION-20260824-138")
        self.assertEqual(second["dispatch_id"], "dispatch-138-live-02")
        self.assertEqual(second["attempt_id"], "attempt-138-live-02")
        self.assertEqual(second["evidence_completeness"], "INCOMPLETE")
        self.assertIsNone(second["process"]["return_code"])
        self.assertEqual(second["structured_result"]["digest"], "UNRECOVERED")
        self.assertEqual(second["validator"]["status"], "UNKNOWN")
        self.assertEqual(second["reconciliation_status"], "REQUIRES_RECONCILIATION")

    def test_import_is_append_only_and_auditable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger_path = root / "attempts.jsonl"
            artifact_path = root / "step05.json"
            report_path = root / "step05.md"
            artifact = import_history(
                self.repo_root,
                ledger_path=ledger_path,
                artifact_path=artifact_path,
                report_path=report_path,
            )
            audit = LiveAttemptLedger(ledger_path).audit()
            self.assertEqual(audit["record_count"], 4)
            self.assertEqual(artifact["canonical_task138_second_fact"], "ATTEMPT_HAPPENED_OBSERVATION_INCOMPLETE")
            self.assertTrue(artifact_path.exists())
            self.assertTrue(report_path.exists())
            with self.assertRaises(RuntimeError):
                import_history(
                    self.repo_root,
                    ledger_path=ledger_path,
                    artifact_path=root / "second.json",
                    report_path=root / "second.md",
                )


if __name__ == "__main__":
    unittest.main()
