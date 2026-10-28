import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/research/task164_historical_basis_pressure.py"
OUT = ROOT / "data/research/historical-basis-pressure-sensor-2026-09-07"


class Task164HistoricalBasisPressureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(TOOL), "all"], cwd=ROOT.parent, check=True)

    def test_exact_provenance_and_stage_a_stop(self):
        command = json.loads((OUT / "command-freeze.json").read_text(encoding="utf-8"))
        verdict = json.loads((OUT / "verdict.json").read_text(encoding="utf-8"))
        self.assertEqual(command["commit"], "ef5ac179529bb0dc44c7d1111ca1ea63ef4c89e5")
        self.assertEqual(command["git_blob_sha"], "18ba43e3a7d6aab3a8bdc794b2767db2e861b78a")
        self.assertEqual(command["content_sha256"], "e25ac0171db94709d0a0c65fa51c8f425b935c191a17e8210336e6ed943db1f3")
        self.assertEqual(command["formal_base"]["sha"], "644c93cd5cd0c7d4ed490f95795897df3bcd8826")
        self.assertEqual(verdict["primary_verdict"], "BASIS_PRESSURE_SENSOR_NOT_VALIDATED")
        self.assertEqual(verdict["stage_b"]["status"], "NOT_RUN_STAGE_A_STOP")

    def test_blind_runs_are_byte_identical_and_not_answer_like(self):
        one = (OUT / "blind-run-1.jsonl").read_bytes()
        two = (OUT / "blind-run-2.jsonl").read_bytes()
        self.assertEqual(one, two)
        forbidden = re.compile(
            r"(?ix)IGNITION[-_ ]?2026090[4-7][- _]?(?:15[3-9]|16[0-4])"
            r"|TASK[-_ ]?16[0-4]"
            r"|\b(?:P0[1-4]|N0[2-9])(?:[_-][A-Z0-9_-]+)?\b"
            r"|\b(?:TRUE_LEAP|NON_LEAP|BORDERLINE)\b"
            r"|\b(?:OBJECT_LANGUAGE_CHANGE|SELF_REFERENCE|INDEPENDENT_COUNTERCHECK|COMPOSITIONAL_GENERATION)\b"
            r"|\b(?:meta[-_ ]protocol|basis[-_ ]escape|semantic[-_ ]leap|junction[-_ ]invariant)\b"
        )
        rows = [json.loads(line) for line in one.decode("utf-8").splitlines()]
        self.assertGreaterEqual(len(rows), 60)
        for row in rows:
            self.assertFalse(row["answer_key_read"])
            self.assertFalse(row["post_event_lookahead_used"])
            self.assertFalse(row["future_capability_vocab_exposed"])
            self.assertFalse(forbidden.search(json.dumps(row, ensure_ascii=False)))

    def test_qualification_gates_and_stage_b_sentinels(self):
        stage_a = json.loads((OUT / "stage-a-verdict.json").read_text(encoding="utf-8"))
        self.assertEqual(stage_a["status"], "FAIL")
        self.assertFalse(stage_a["stage_a_pass"])
        self.assertEqual(stage_a["strong_negative_false_positive_count"], 0)
        self.assertIn("every_positive_boundary_reconstructed", stage_a["failed_gates"])
        self.assertIn("null_proxy_not_equivalent", stage_a["failed_gates"])
        for name in ["r1-trigger-coupling.jsonl", "mutation-proposals.jsonl", "capability-equivalence.jsonl"]:
            rows = [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["status"], "NOT_RUN_STAGE_A_STOP", name)
        stop = json.loads((OUT / "stage-b-stop.json").read_text(encoding="utf-8"))
        self.assertEqual(stop["status"], "NOT_RUN_STAGE_A_STOP")

    def test_checkpoint_chronology_is_monotone(self):
        rows = [json.loads(line) for line in (OUT / "checkpoint-manifest.jsonl").read_text(encoding="utf-8").splitlines()]
        grouped = {}
        for row in rows:
            grouped.setdefault(row["blind_epoch_id"], []).append(row)
        for epoch_rows in grouped.values():
            epoch_rows.sort(key=lambda row: row["checkpoint_index"])
            positions = [row["chronology_position_in_full_history"] for row in epoch_rows]
            self.assertEqual(positions, sorted(positions))
            self.assertEqual([row["checkpoint_index"] for row in epoch_rows], list(range(len(epoch_rows))))

    def test_frozen_artifacts_are_self_consistent(self):
        ledger = json.loads((OUT / "freeze-ledger.json").read_text(encoding="utf-8"))
        for name, expected in ledger["frozen_file_hashes"].items():
            self.assertEqual(hashlib.sha256((OUT / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(
            hashlib.sha256((OUT / "blind-run-1.jsonl").read_bytes()).hexdigest(),
            hashlib.sha256((OUT / "blind-run-2.jsonl").read_bytes()).hexdigest(),
        )
        self.assertTrue((OUT / "artifact-sha256.json").is_file())


if __name__ == "__main__":
    unittest.main()
