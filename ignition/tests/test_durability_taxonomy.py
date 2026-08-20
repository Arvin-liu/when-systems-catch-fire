from __future__ import annotations

import copy
import json
import unittest

from tools.validate_durability_taxonomy import DEFAULT_DATA, DEFAULT_SCHEMA, EXPECTED, validate


class DurabilityTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(DEFAULT_DATA.read_text(encoding="utf-8"))
        cls.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_taxonomy_has_six_non_authoritative_classes(self) -> None:
        self.assertEqual(validate(self.data, self.schema), [])
        self.assertEqual({item["class_id"] for item in self.data["classes"]}, EXPECTED)
        self.assertTrue(all(item["can_be_authority"] is False for item in self.data["classes"]))

    def test_advisory_context_cannot_become_authority(self) -> None:
        candidate = copy.deepcopy(self.data)
        next(item for item in candidate["classes"] if item["class_id"] == "ADVISORY_SOFT_CONTEXT")["can_be_authority"] = True
        self.assertTrue(validate(candidate, self.schema))

    def test_missing_historical_sealed_class_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["classes"] = [item for item in candidate["classes"] if item["class_id"] != "HISTORICAL_SEALED"]
        self.assertTrue(validate(candidate, self.schema))

    def test_external_pointer_is_not_secret_storage(self) -> None:
        candidate = copy.deepcopy(self.data)
        pointer = next(item for item in candidate["classes"] if item["class_id"] == "EXTERNAL_POINTER_ONLY")
        pointer["examples"].append("secret token contents")
        self.assertTrue(validate(candidate, self.schema))


if __name__ == "__main__":
    unittest.main()
