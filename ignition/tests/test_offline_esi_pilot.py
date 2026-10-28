import copy
import json
import unittest

from tools.run_offline_esi_pilot import DEFAULT_FIXTURE, DEFAULT_SCHEMA, load, run_pilot
from tools.run_esi_experiment import ANNOTATION_SCHEMA


class OfflineEsiPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(DEFAULT_FIXTURE)
        cls.schema = load(DEFAULT_SCHEMA)
        cls.annotation_schema = load(ANNOTATION_SCHEMA)

    def test_synthetic_pilot_completes_without_live_provider(self):
        result = run_pilot(self.fixture, self.schema, self.annotation_schema)
        self.assertEqual("COMPLETED_OFFLINE", result["execution_status"])
        self.assertEqual("NOT_RUN_LIVE_EXTERNAL", result["live_model_status"])
        self.assertEqual(7, result["response_count"])
        self.assertEqual(1, result["summary"]["unauthorized_transition_count"])

    def test_fixture_cannot_be_relabelled_as_live(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["provider_status"] = "LIVE_COMPLETED"
        with self.assertRaises(ValueError):
            run_pilot(fixture, self.schema, self.annotation_schema)

    def test_terminology_mimicry_is_not_boundary_evidence(self):
        result = run_pilot(self.fixture, self.schema, self.annotation_schema)
        checks = result["checks"]
        self.assertTrue(checks["terminology_mimicry_has_leakage"])
        self.assertTrue(checks["terminology_does_not_authorize"])
        self.assertTrue(checks["over_caution_is_separate"])


if __name__ == "__main__":
    unittest.main()
