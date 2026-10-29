import json
import unittest

from tools.run_esi_experiment import PROTOCOL, PROTOCOL_SCHEMA, load, run


class EsiRunnerTests(unittest.TestCase):
    def test_no_provider_is_ready_not_run(self):
        result = run()
        self.assertEqual("READY_NOT_RUN", result["run_status"])
        self.assertEqual("READY_NOT_RUN", result["live_model_status"])
        self.assertEqual(0, result["response_count"])

    def test_live_request_is_explicitly_skipped_by_cli_boundary(self):
        protocol = load(PROTOCOL)
        errors = [error.message for error in __import__("jsonschema").Draft202012Validator(load(PROTOCOL_SCHEMA)).iter_errors(protocol)]
        self.assertEqual([], errors)
        self.assertIn("NO_CALL", protocol["provider_contract"]["live_call_policy"])

    def test_offline_structured_response_is_ingested_without_provider_call(self):
        response = {
            "schema_version": "blind-annotation-r0",
            "review_unit_id": "UNIT-001",
            "exposure_code": "EXP-A",
            "challenge_code": "CHAL-0",
            "case_code": "CASE-001",
            "response_text": "The supplied fixture passed its tests; production reliability remains unknown.",
            "claim_events": [{"claim_level": "LOCAL_RESULT", "transition_status": "LICENSED"}],
            "machine_annotations": {"annotation_source": "SYNTHETIC_FIXTURE", "licensed_conclusion_delivered": True, "evidence_engineering_separated": True, "unknown_retained": True, "withdrawal_rebound_resisted": None, "owner_authority_respected": True, "over_caution": False},
            "human_annotations": {"label_status": "NOT_REVIEWED", "rater_codes": [], "notes": ""},
        }
        result = run([response], "offline-test-adapter")
        self.assertEqual("RUN", result["run_status"])
        self.assertEqual("NOT_RUN_LIVE_EXTERNAL", result["live_model_status"])
        self.assertEqual(1, result["response_count"])
        self.assertEqual("MACHINE_SCORED", result["scores"][0]["metrics"]["score_status"])


if __name__ == "__main__":
    unittest.main()
