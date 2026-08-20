import json
import unittest

from tools.generate_structural_projections import (
    PROJECTION_TYPES,
    SCHEMA,
    SOURCE,
    build_projection,
    load,
    validate,
)


class StructuralProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.surface = load(SOURCE)
        cls.schema = load(SCHEMA)

    def test_all_required_projection_arms_are_schema_valid(self):
        self.assertEqual(5, len(PROJECTION_TYPES))
        for projection_type in PROJECTION_TYPES:
            projection = build_projection(self.surface, projection_type)
            self.assertEqual([], validate(projection, self.schema), projection_type)
            self.assertEqual(12, projection["control_properties"]["item_count"])

    def test_delexicalized_preserves_relational_content_without_named_terms(self):
        projection = build_projection(self.surface, "DELEXICALIZED_STRUCTURE")
        body = "\n".join(item["body"] for item in projection["items"])
        self.assertNotIn("K13", body)
        self.assertNotIn("Claim Ceiling", body)
        self.assertTrue(projection["control_properties"]["relation_preserved"])

    def test_terminology_only_does_not_offer_transition_relations(self):
        projection = build_projection(self.surface, "TERMINOLOGY_ONLY")
        body = "\n".join(item["body"] for item in projection["items"])
        self.assertIn("K13", body)
        self.assertIn("Claim Ceiling", body)
        self.assertFalse(projection["control_properties"]["relation_preserved"])

    def test_broken_structure_is_not_the_original_projection(self):
        original = build_projection(self.surface, "DELEXICALIZED_STRUCTURE")
        broken = build_projection(self.surface, "STRUCTURE_BROKEN_CONTROL")
        self.assertNotEqual(original["items"], broken["items"])
        self.assertFalse(broken["control_properties"]["relation_preserved"])


if __name__ == "__main__":
    unittest.main()
