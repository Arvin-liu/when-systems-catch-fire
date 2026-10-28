import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/research/task160_basis_escape_v2.py"
OUT = ROOT / "data/research/basis-escape-v2-2026-09-07"


class Task160BasisEscapeV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(TOOL), "all"], cwd=ROOT.parent, check=True)

    def test_frozen_inputs_and_required_outputs(self):
        subprocess.run(["python3", str(TOOL), "verify"], cwd=ROOT.parent, check=True)
        required = [
            "experiment-protocol.json", "hypothesis-freeze.json", "corpus-universe.jsonl",
            "corpus-split-manifest.json", "exclusion-ledger.jsonl", "sanitization-ledger.jsonl",
            "c8-mixed-holdout-manifest.json",
            "freeze-ledger.json", "v2-replay-results.jsonl", "historical-64-absorption.jsonl",
            "basis-free-induction-results.jsonl", "basis-free-candidate-freeze.jsonl",
            "axis-knockout-results.jsonl", "axis-rediscovery-results.jsonl",
            "fake-axis-controls.jsonl", "representation-residuals.jsonl",
            "residual-family-summary.json", "competing-basis-results.jsonl",
            "shadow-mutator-manifest.json", "shadow-mutator-results.jsonl",
            "candidate-v2-scores.jsonl", "candidate-ablation-results.jsonl",
            "holdout-transfer-results.jsonl", "verdict.json",
        ]
        for name in required:
            self.assertTrue((OUT / name).is_file(), name)
        c8 = json.loads((OUT / "c8-mixed-holdout-manifest.json").read_text())
        self.assertEqual(c8["stratum"], "C8_MIXED_HOLDOUT")
        self.assertEqual(c8["status"], "DERIVED_FROM_FROZEN_SPLIT")
        self.assertFalse(c8["contains_task160_outputs"])

    def test_v2_and_verdict_gates(self):
        replay = json.loads((OUT / "v2-replay-summary.json").read_text())
        self.assertEqual(replay["status"], "V2_REPLAY_STABLE")
        self.assertTrue(replay["clean_clone"]["run1_run2_byte_identical"])
        self.assertTrue(replay["n02_n03_preserved_non_leap"])
        scores = [json.loads(line) for line in (OUT / "candidate-v2-scores.jsonl").read_text().splitlines()]
        self.assertEqual(len(scores), 6)
        self.assertTrue(all(row["verdict"] == "NON_LEAP" for row in scores))
        verdict = json.loads((OUT / "verdict.json").read_text())
        self.assertEqual(verdict["candidate_v2_pass_count"], 0)
        self.assertEqual(verdict["new_supported_candidate_count"], 0)
        self.assertIn(verdict["primary_verdict"], verdict["allowed_primary_verdict_set"])

    def test_blinding_and_fake_controls(self):
        forbidden = re.compile(r"(?ix)(?<![a-z0-9])(?:v[1-4]|s[1-4]|e[1-4])(?=[^a-z0-9]|$)|v\s*[x×]\s*s\s*[x×]\s*e|\b64\b|ignition[-_ ]?2026090[4-7][-_ ]?15[3-9]|\btask[-_ ]?15[3-9]\b|meta[-_ ]?protocols?|junction\s+invariant|binding\s+challenger|\bp/o/n/a\b")
        for line in (OUT / "basis-free-packets/all.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            self.assertFalse(forbidden.search(row["text"]), row["item_id"])
            self.assertEqual(row["input_labels"], [])
        fake = [json.loads(line) for line in (OUT / "fake-axis-controls.jsonl").read_text().splitlines()]
        self.assertTrue(fake)
        self.assertTrue(all(not row["selected_as_basis"] for row in fake))

    def test_deterministic_artifact_bytes(self):
        names = ["corpus-universe.jsonl", "basis-free-packets/all.jsonl", "basis-free-candidate-freeze.jsonl", "candidate-v2-scores.jsonl", "verdict.json"]
        before = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
        subprocess.run(["python3", str(TOOL), "analyze"], cwd=ROOT.parent, check=True)
        after = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
