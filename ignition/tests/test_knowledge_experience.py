import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("knowledge_validation", ROOT / "tools/governance/validate_knowledge_experience.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class KnowledgeExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "data/governance/knowledge-experience/config.json").read_text(encoding="utf-8"))
        cls.results = MODULE.BUILDER.knowledge_result_rows(cls.config)
        cls.cards = MODULE.read_jsonl(ROOT / "data/governance/knowledge-experience/asset-cards.jsonl")
        cls.layers = MODULE.read_jsonl(ROOT / "data/governance/knowledge-experience/layered-reading.jsonl")
        cls.aliases = MODULE.read_jsonl(ROOT / "data/governance/knowledge-experience/alias-index.jsonl")

    def test_current_experience_is_closed_and_two_click_reachable(self):
        result = MODULE.validate()
        self.assertGreaterEqual(result["cards"], len(self.results))
        self.assertEqual(result["layers"], len(self.results))
        function_count = len(MODULE.read_jsonl(ROOT / "data/foundation/function-assets/identity-cards.jsonl"))
        claim_count = len(MODULE.read_jsonl(ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"))
        self.assertEqual(result["search"], len(self.results) + function_count + claim_count)
        self.assertGreaterEqual(result["two_click_pages"], 8)

    def test_missing_reading_layer_fails_closed(self):
        broken = copy.deepcopy(self.layers[:-1])
        with self.assertRaisesRegex(AssertionError, "layered reading mismatch"):
            MODULE.assert_layer_coverage(self.results, broken, self.cards)

    def test_withdrawn_alias_cannot_disappear(self):
        broken = [row for row in self.aliases if row["alias"] != "大一统已被证明不可能"]
        with self.assertRaisesRegex(AssertionError, "missing or rebound"):
            MODULE.assert_required_aliases(broken, self.config)

    def test_stale_summary_hash_fails_closed(self):
        broken = copy.deepcopy(self.layers[:1])
        broken[0]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "stale source projection"):
            MODULE.assert_source_hashes(broken)

    def test_reading_layers_are_bounded_and_fully_sharded(self):
        manifest = json.loads((ROOT / "data/governance/knowledge-experience/manifest.json").read_text(encoding="utf-8"))
        shards = sorted((ROOT / "KNOWLEDGE/reading-layers").glob("part-*.md"))
        self.assertEqual(manifest["counts"]["layer_shards"], len(shards))
        self.assertTrue(shards)
        self.assertTrue(all(path.stat().st_size < 500_000 for path in shards))
        shard_anchors = set().union(*(MODULE.explicit_anchors(path) for path in shards))
        self.assertEqual({row["human_anchor"] for row in self.layers}, shard_anchors)

    def test_generated_experience_cannot_reenter_canonical_census(self):
        functions = MODULE.read_jsonl(ROOT / "data/foundation/function-assets/identity-cards.jsonl")
        claims = MODULE.read_jsonl(ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl")
        forbidden_prefixes = (
            "KNOWLEDGE/",
            "data/governance/",
            "data/foundation/nonfunction-claims/",
        )
        forbidden_exact = {
            "data/foundation/project-state.json",
            "data/foundation/registry-manifest.json",
            "data/foundation/migration-summary.json",
            "docs/foundation/nonfunction-claim-adjudication-index.md",
            "RESULTS/CHRONOLOGY.md",
            "RESULTS/CLAIM-DELTA.md",
            "RESULTS/IMPACT-ANALYSIS.md",
            "RESULTS/EVIDENCE-LINEAGE.md",
            "RESULTS/SELF-CORRECTION-AUDIT.md",
        }
        self.assertFalse(any(
            anchor.get("path", "").startswith(forbidden_prefixes) or anchor.get("path", "") in forbidden_exact
            for row in functions for anchor in row.get("source_anchors", [])
        ))
        self.assertFalse(any(
            anchor.get("path", "").startswith(forbidden_prefixes) or anchor.get("path", "") in forbidden_exact
            for row in claims for anchor in row.get("source_anchors", [])
        ))

    def test_generated_current_facts_result_is_not_reintroduced_into_knowledge(self):
        ledger = MODULE.read_jsonl(ROOT / "data/governance/human-results/result-ledger.jsonl")
        self.assertIn("docs/architecture/current-facts.md", {row["source"] for row in ledger})
        self.assertIn("docs/architecture/current-facts.md", self.config["excluded_generated_result_sources"])
        self.assertNotIn("docs/architecture/current-facts.md", {row["source"] for row in self.results})


if __name__ == "__main__":
    unittest.main()
