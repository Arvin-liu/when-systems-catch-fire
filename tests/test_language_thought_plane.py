import copy
import json
import unittest
from pathlib import Path

from tools.language_thought.validate_language_thought import (
    DATA,
    REQUIRED_DIMENSIONS,
    REQUIRED_LAYERS,
    evaluate_fixtures,
    load_json,
    load_jsonl,
    validate_fixture_references,
    validate_repository,
    validate_transformation,
)


ROOT = Path(__file__).resolve().parents[1]


class LanguageThoughtPlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json(DATA / "manifest.json")
        cls.dimensions = load_json(DATA / "dimensions.json")
        cls.transformations = load_jsonl(DATA / "transformations.jsonl")
        cls.fixtures = load_jsonl(DATA / "fixtures.jsonl")

    def test_repository_contract_passes(self):
        report = validate_repository(ROOT)
        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertEqual(report["dimensions"], 12)
        self.assertEqual(report["profiles"], 4)
        self.assertEqual(report["fixture_layers"], REQUIRED_LAYERS)

    def test_architecture_is_plane_not_l7(self):
        self.assertEqual(
            self.manifest["architecture_decision"],
            "ORTHOGONAL_PLANE_ACROSS_L0_L6_NOT_L7",
        )
        self.assertEqual(self.manifest["cross_layer_coverage"], REQUIRED_LAYERS)
        self.assertNotIn("L7", self.manifest["cross_layer_coverage"])

    def test_basis_is_finite_exact_and_non_exhaustive(self):
        ids = [item["dimension_id"] for item in self.dimensions["dimensions"]]
        self.assertEqual(ids, REQUIRED_DIMENSIONS)
        self.assertIn("not an exhaustive", self.dimensions["claim_ceiling"])
        for item in self.dimensions["dimensions"]:
            self.assertGreaterEqual(len(item["counterexamples_and_variation"]), 2)
            self.assertTrue(item["validation_fixture_ids"])

    def test_profile_set_has_two_full_and_two_preliminary(self):
        profile_entries = {entry["profile_id"]: entry for entry in self.manifest["profiles"]}
        self.assertEqual(profile_entries["zh-hans-modern-written-r1"]["coverage"], "FULL")
        self.assertEqual(profile_entries["en-contemporary-written-r1"]["coverage"], "FULL")
        for profile_id in ("ja-modern-standard-pilot-r1", "tr-modern-standard-pilot-r1"):
            entry = profile_entries[profile_id]
            self.assertEqual(entry["coverage"], "BOUNDED_PRELIMINARY")
            self.assertEqual(entry["publication_authority"], "NO_INDEPENDENT_PUBLICATION_AUTHORITY")

    def test_production_records_fail_if_delta_is_removed(self):
        record = copy.deepcopy(self.transformations[1])
        record["framing_deltas"] = record["framing_deltas"][1:]
        errors = validate_transformation(record, production=True)
        self.assertTrue(any("silent or spurious frame changes" in error for error in errors), errors)

    def test_production_records_fail_on_unresolved_epistemic_change(self):
        record = copy.deepcopy(self.transformations[1])
        record["framing_deltas"][0]["disposition"] = "unresolved"
        errors = validate_transformation(record, production=True)
        self.assertTrue(any("forbidden silent/unresolved" in error for error in errors), errors)

    def test_fixture_metrics_report_permissions_rejections_and_unsupported(self):
        metrics, errors, phenomena, layers = evaluate_fixtures(self.fixtures)
        self.assertFalse(errors, errors)
        self.assertEqual(metrics.false_positive, 0)
        self.assertEqual(metrics.false_negative, 0)
        self.assertGreater(metrics.true_positive, 0)
        self.assertGreater(metrics.true_negative, 0)
        self.assertGreater(metrics.unsupported, 0)
        self.assertEqual(metrics.precision, 1.0)
        self.assertEqual(metrics.recall, 1.0)
        self.assertEqual(layers, set(REQUIRED_LAYERS))
        self.assertIn("purposeful_marked_syntax", phenomena)

    def test_dimension_fixture_reference_fails_closed(self):
        dimensions = copy.deepcopy(self.dimensions)
        dimensions["dimensions"][0]["validation_fixture_ids"][0] = "fixture-does-not-exist"
        errors = []
        validate_fixture_references(dimensions, self.fixtures, errors)
        self.assertTrue(any("unknown validation fixtures" in error for error in errors), errors)

    def test_schema_assets_are_valid_json_and_declared(self):
        for relative_path in self.manifest["schemas"]:
            value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
            self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
