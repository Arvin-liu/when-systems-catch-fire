import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/research/task163_mutable_basis_learning.py"
OUT = ROOT / "data/research/mutable-basis-learning-operator-2026-09-07"


class Task163MutableBasisLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(TOOL), "all"], cwd=ROOT.parent, check=True)

    def test_exact_provenance_and_stage_stop(self):
        protocol = json.loads((OUT / "experiment-protocol.json").read_text(encoding="utf-8"))
        ledger = json.loads((OUT / "freeze-ledger.json").read_text(encoding="utf-8"))
        qualification = json.loads((OUT / "historical-qualification-verdict.json").read_text(encoding="utf-8"))
        verdict = json.loads((OUT / "verdict.json").read_text(encoding="utf-8"))
        provenance = protocol["command_provenance"]
        self.assertEqual(provenance["commit"], "73cde2ab84d829bb0990f63d957e2152b1a330e4")
        self.assertEqual(provenance["git_blob_sha"], "521d468829425a210cc763df72456f2c28753d02")
        self.assertEqual(provenance["content_sha256"], "f4834b50cf26688e03e5655134d0d12019b8548093752f33b2454869b26a48a1")
        self.assertEqual(ledger["formal_base_sha"], "5c66ac502ca331d72c1362000ff5231503dde7ea")
        self.assertEqual(ledger["command_commit"], provenance["commit"])
        self.assertEqual(qualification["status"], "FAIL")
        self.assertFalse(qualification["stage_a_pass"])
        self.assertEqual(verdict["primary_verdict"], "BASIS_LEARNING_OPERATOR_NOT_VALIDATED")
        self.assertEqual(verdict["stage_b"]["status"], "NOT_RUN_STAGE_A_STOP")

    def test_pre_event_blindness_and_two_pass_determinism(self):
        one = (OUT / "historical-blind-run-1.jsonl").read_bytes()
        two = (OUT / "historical-blind-run-2.jsonl").read_bytes()
        self.assertEqual(one, two)
        rows = [json.loads(line) for line in one.decode("utf-8").splitlines()]
        self.assertEqual(len(rows), 18)
        forbidden = re.compile(
            r"(?ix)"
            r"(?:IGNITION[-_ ]?2026090[4-7][-_ ]?15[3-9]|TASK[-_ ]?15[3-9])"
            r"|(?:P0[1-4]|N0[1-9]|N1[0-2]|B0[1-2])[_-][A-Z0-9_-]+"
            r"|\b(?:TRUE_LEAP|NON_LEAP|BORDERLINE)\b"
            r"|\b(?:V\s*[×x]\s*S\s*[×x]\s*E|V/S/E|BF-X\*|EL-X\*|P_meta|Ψ_?0)\b"
            r"|\b64\b"
            r"|\b(?:transition\s+semantics|first[-_ ]class\s+transition|junction\s+invariant|binding\s+invariant)\b"
        )
        for row in rows:
            self.assertFalse(row["answer_key_read"])
            self.assertFalse(row["post_event_lookahead_used"])
            self.assertFalse(row["candidate_vocab_exposed"])
            self.assertFalse(forbidden.search(json.dumps(row, ensure_ascii=False)), row["packet_id"])

    def test_qualification_gate_and_stage_b_sentinels(self):
        qualification = json.loads((OUT / "historical-qualification-verdict.json").read_text(encoding="utf-8"))
        self.assertEqual(qualification["positive_true_leap_count"], 4)
        self.assertEqual(qualification["positive_capability_equivalent_hits"], 0)
        self.assertEqual(qualification["positive_holdout_capability_equivalent_hits"], 0)
        self.assertEqual(qualification["strong_negative_false_positive_count"], 0)
        self.assertIn("true_leap_signal_at_least_3_of_4", qualification["failed_gates"])
        self.assertIn("at_least_one_true_holdout_hit", qualification["failed_gates"])
        stop = json.loads((OUT / "stage-b-stop.json").read_text(encoding="utf-8"))
        self.assertEqual(stop["status"], "NOT_RUN_STAGE_A_STOP")
        self.assertTrue(stop["no_external_fulltext_acquired"])
        for name in [
            "discovery-source-manifest.jsonl",
            "fresh-holdout-source-manifest.jsonl",
            "causal-chain-extraction.jsonl",
            "cross-book-collisions.jsonl",
            "residual-ledger.jsonl",
            "competing-representation-results.jsonl",
            "coherence-ablation-O-S-B-R.jsonl",
            "fixed-vs-mutable-results.jsonl",
            "multi-pass-convergence.jsonl",
            "candidate-freeze.jsonl",
            "existing-basis-crosswalk.jsonl",
            "semantic-conservative-mappings.jsonl",
            "v2-candidate-scores.jsonl",
            "candidate-ablation-results.jsonl",
            "fake-mutation-controls.jsonl",
            "null-corpus-controls.jsonl",
            "fresh-holdout-results.jsonl",
        ]:
            rows = [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["status"], "NOT_RUN_STAGE_A_STOP", name)

    def test_all_mutation_operations_have_non_semantic_trials(self):
        spec = json.loads((OUT / "operator-spec-freeze.json").read_text(encoding="utf-8"))
        operations = spec["mutation_operations"]
        trials = spec["mutation_trials"]
        self.assertEqual(len(operations), 12)
        self.assertEqual({row["operation"] for row in trials}, set(operations))
        self.assertTrue(all(row["status"] == "TRIAL_APPLIED" for row in trials))
        self.assertTrue(all(row["semantic_claim"] == "NONE" for row in trials))

    def test_frozen_artifacts_are_self_consistent(self):
        ledger = json.loads((OUT / "freeze-ledger.json").read_text(encoding="utf-8"))
        for name, expected in ledger["frozen_file_hashes"].items():
            actual = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)
        self.assertTrue(ledger["answer_key_is_not_a_blind_input"])
        self.assertTrue(ledger["stage_b_not_started"])


if __name__ == "__main__":
    unittest.main()
