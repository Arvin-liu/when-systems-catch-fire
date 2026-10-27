import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("self_correction", ROOT / "tools/governance/run_self_correction.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class SelfCorrectionEngineTests(unittest.TestCase):
    def finding(self, name: str, fixture: str) -> dict:
        text = (ROOT / "tests/fixtures/self-correction" / fixture).read_text(encoding="utf-8")
        return {row["rule_id"]: row for row in MODULE.analyze_text(fixture, text)}[name]

    def test_bounded_correction_does_not_rebound(self):
        self.assertEqual(self.finding("conclusion_rebound", "safe-correction.md")["status"], "PASS")
        self.assertEqual(self.finding("analogy_as_isomorphism", "safe-correction.md")["status"], "PASS")

    def test_model_failure_universal_inference_is_reviewed(self):
        self.assertEqual(self.finding("model_failure_to_universal_impossibility", "rebound.md")["status"], "REVIEW")

    def test_hidden_essential_content_blocks(self):
        self.assertEqual(self.finding("hidden_essential_content", "hidden.md")["status"], "BLOCK")

    def test_products_are_deterministic_and_paired(self):
        first, summary_first = MODULE.build()
        second, summary_second = MODULE.build()
        self.assertEqual(first, second)
        self.assertEqual(summary_first, summary_second)
        config = json.loads((ROOT / "data/governance/human-results/config.json").read_text(encoding="utf-8"))
        for pair in config["machine_human_pairs"]:
            self.assertTrue((ROOT / pair["machine"]).is_file(), pair["machine"])
            self.assertTrue((ROOT / pair["human"]).is_file(), pair["human"])


if __name__ == "__main__":
    unittest.main()
