import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/research/task165_cross_thread_collision.py"
OUT = ROOT / "data/research/cross-thread-creative-discontinuity-2026-09-08"


def read_json(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def read_jsonl(name):
    return [
        json.loads(line)
        for line in (OUT / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class Task165CrossThreadCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(TOOL), "verify"], cwd=ROOT.parent, check=True)
        spec = importlib.util.spec_from_file_location("task165_runner", TOOL)
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def test_exact_provenance_and_lifecycle_ceiling(self):
        command = read_json("command-freeze.json")
        verdict = read_json("verdict.json")
        self.assertEqual(command["commit"], "b3b128f46a625f728870ded1a975f3c2f0db53ce")
        self.assertEqual(command["git_blob_sha"], "065f02e04e3a0c8e55c398954a761c66901f74b5")
        self.assertEqual(
            command["content_sha256"],
            "dcd123b9ae487f54dd7afcc921f9f1fd691147c463634e33e8d3f1f136b2d22a",
        )
        self.assertEqual(command["formal_base"]["sha"], "ba6641d200000ad4ebaa764e4ed94d79f32fb2df")
        self.assertEqual(verdict["primary_verdict"], "NO_VALIDATED_CREATIVE_DISCONTINUITY_FOUND")
        self.assertEqual(verdict["stage_b"]["high_gate_candidate_count"], 0)
        self.assertFalse(verdict["canonical_mutation"]["current_pointer_changed"])
        self.assertFalse(verdict["canonical_mutation"]["state_changelog_changed"])

    def test_blind_replay_is_identical_and_answer_free(self):
        one = (OUT / "blind-run-1.jsonl").read_bytes()
        two = (OUT / "blind-run-2.jsonl").read_bytes()
        self.assertEqual(one, two)
        self.assertEqual(hashlib.sha256(one).hexdigest(), read_json("blind-run-digest.json")["blind_run_1_sha256"])
        for name in (
            "historical-blind-packets.jsonl",
            "blind-run-1.jsonl",
            "c0-single-thread-results.jsonl",
            "c1-nearest-results.jsonl",
            "c2-random-results.jsonl",
            "c3-cross-thread-results.jsonl",
            "c4-no-problem-rewrite-results.jsonl",
        ):
            self.assertIsNone(self.runner.FORBIDDEN_BLIND.search((OUT / name).read_text(encoding="utf-8")), name)
        rows = read_jsonl("blind-run-1.jsonl")
        self.assertEqual(len(rows), 195)
        self.assertTrue(all(not row["answer_key_read"] for row in rows))
        self.assertTrue(all(not row["post_event_lookahead_used"] for row in rows))

    def test_thread_pool_and_condition_invariants(self):
        self.assertGreaterEqual(len(read_jsonl("thread-field-manifest.jsonl")), 12)
        self.assertGreaterEqual(len(read_jsonl("dormant-question-pool.jsonl")), 50)
        rows = read_jsonl("blind-run-1.jsonl")
        c3 = {(row["packet_id"], row["round_seed"]): row["selection_digest"] for row in rows if row["condition"] == "C3"}
        c4 = {(row["packet_id"], row["round_seed"]): row["selection_digest"] for row in rows if row["condition"] == "C4"}
        self.assertEqual(c3, c4)
        stage = read_json("historical-qualification-verdict.json")
        self.assertFalse(stage["stage_a_pass"])
        self.assertIn("p00_boundary_scoreable", stage["failed_gates"])
        self.assertEqual(stage["strong_negative_l3_false_positives"], 3)

    def test_frozen_hashes_and_required_outputs(self):
        freeze = read_json("freeze-ledger.json")
        for name, expected in freeze["frozen_file_hashes"].items():
            self.assertEqual(hashlib.sha256((OUT / name).read_bytes()).hexdigest(), expected, name)
        required = [
            "dormant-pool-ablation.jsonl",
            "backward-influence-ablation.jsonl",
            "candidate-freeze.jsonl",
            "candidate-transfer-results.jsonl",
            "candidate-ablation-results.jsonl",
            "candidate-kill-conditions.jsonl",
            "existing-system-compile-away.jsonl",
            "v2-scores.jsonl",
            "precedent-search-protocol.json",
            "precedent-search-ledger.jsonl",
            "precedent-crosswalk.jsonl",
        ]
        for name in required:
            self.assertTrue((OUT / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
