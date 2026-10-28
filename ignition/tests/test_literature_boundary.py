import copy
import json
import unittest

from tools.validate_literature_boundary import DEFAULT_RECORD, DEFAULT_SCHEMA, validate


class LiteratureBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(DEFAULT_RECORD.read_text(encoding="utf-8"))
        cls.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_primary_review_is_bounded(self):
        self.assertEqual([], validate(self.record, self.schema))
        self.assertEqual("NOVELTY_NOT_ESTABLISHED", self.record["novelty_status"])
        self.assertEqual(4, len(self.record["sources"]))

    def test_novelty_claim_is_rejected(self):
        record = copy.deepcopy(self.record)
        record["novelty_status"] = "NOVEL"
        record["bounded_conclusions"].append("This is the first proven ESI mechanism.")
        self.assertTrue(validate(record, self.schema))

    def test_unreviewed_source_domain_is_rejected(self):
        record = copy.deepcopy(self.record)
        record["sources"][0]["url"] = "https://example.invalid/paper"
        self.assertTrue(validate(record, self.schema))


if __name__ == "__main__":
    unittest.main()
