import json
import unittest

from tools.generate_challenge_fixtures import (
    BENCHMARK,
    MATRIX,
    OUT,
    SCHEMA,
    build_fixtures,
    load,
    validate_fixtures,
    validate_matrix,
)


class ChallengeMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = load(MATRIX)
        cls.benchmark = load(BENCHMARK)
        cls.schema = load(SCHEMA)

    def test_matrix_and_fixtures_cover_all_arms(self):
        self.assertEqual([], validate_matrix(self.matrix, self.schema))
        fixtures = build_fixtures(self.matrix, self.benchmark)
        self.assertEqual([], validate_fixtures(fixtures, self.matrix))
        self.assertEqual(49, fixtures["fixture_count"])

    def test_fixture_generation_is_deterministic_and_no_outputs_are_fabricated(self):
        fixtures = build_fixtures(self.matrix, self.benchmark)
        expected = (json.dumps(fixtures, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.assertEqual(expected, OUT.read_bytes())
        self.assertTrue(all(item["live_output_status"] == "NOT_SUPPLIED" for item in fixtures["fixtures"]))

    def test_delayed_transfer_and_withdrawn_rebound_are_present(self):
        fixtures = build_fixtures(self.matrix, self.benchmark)["fixtures"]
        self.assertTrue(any(item["challenge_arm"] == "C6_DELAYED_TRANSFER" for item in fixtures))
        self.assertTrue(any(item["challenge_arm"] == "C5_WITHDRAWN_REBOUND" for item in fixtures))


if __name__ == "__main__":
    unittest.main()
