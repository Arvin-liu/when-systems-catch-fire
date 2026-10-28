import copy
import json
import unittest

from tools.validate_synthetic_benchmark import DEFAULT_BENCHMARK, DEFAULT_SCHEMA, validate


class SyntheticBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = json.loads(DEFAULT_BENCHMARK.read_text(encoding="utf-8"))
        cls.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_benchmark_has_broad_domains_and_gold_boundaries(self):
        self.assertEqual([], validate(self.benchmark, self.schema))
        self.assertGreaterEqual(len(self.benchmark["cases"]), 12)

    def test_duplicate_case_id_fails(self):
        benchmark = copy.deepcopy(self.benchmark)
        benchmark["cases"][1]["case_id"] = benchmark["cases"][0]["case_id"]
        self.assertTrue(any("IDs must be unique" in error for error in validate(benchmark, self.schema)))

    def test_one_keyword_toy_case_is_not_accepted(self):
        benchmark = copy.deepcopy(self.benchmark)
        benchmark["cases"][0]["evidence_packet"] = ["green"]
        self.assertTrue(validate(benchmark, self.schema))


if __name__ == "__main__":
    unittest.main()
