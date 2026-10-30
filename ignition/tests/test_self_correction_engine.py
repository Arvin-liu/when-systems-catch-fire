import hashlib
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

    def test_extra_canonical_outputs_have_no_source_or_authority_impact(self):
        products, summary = MODULE.build()
        expected = {
            MODULE.MACHINE_OUTPUTS["plan"]: "065806e7e11ff3a22a7dd387ad0c9b1176976bbeb4e9504f25e669611d026c69",
            MODULE.HUMAN_OUTPUTS["audit"]: "d50bac8e4bd00f741e3ba809a1b8f1ed57f064b509ea733aa8455ad3671ad94b",
        }
        self.assertEqual(len(products), 11)
        for path, expected_sha256 in expected.items():
            actual = hashlib.sha256(products[path].encode("utf-8")).hexdigest()
            self.assertEqual(actual, expected_sha256, str(path.relative_to(ROOT)))
        self.assertEqual(summary["blocking_rules"], 0)
        self.assertEqual(summary["claim_ceiling"], "Automated repository governance only; no external truth adjudication.")


if __name__ == "__main__":
    unittest.main()
