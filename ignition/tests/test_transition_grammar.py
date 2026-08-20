import copy
import json
import unittest

from tools.validate_transition_grammar import DEFAULT_REGISTRY, DEFAULT_SCHEMA, validate


class TransitionGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
        cls.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_registry_is_source_bound(self):
        self.assertEqual([], validate(self.registry, self.schema))
        self.assertGreaterEqual(len(self.registry["rules"]), 12)

    def test_missing_provenance_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["source_refs"] = ["ignition/private/not-a-source.md"]
        self.assertTrue(any("missing canonical source" in error for error in validate(registry, self.schema)))

    def test_soft_current_rule_cannot_become_canonical(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["hard_or_soft"] = "SOFT_RESEARCH_PROJECTION"
        self.assertTrue(any("canonical hard rule" in error for error in validate(registry, self.schema)))


if __name__ == "__main__":
    unittest.main()
