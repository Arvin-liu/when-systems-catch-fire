from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_failure_anchored_recovery as recovery  # noqa: E402


FIXTURE_PATH = IGNITION_ROOT / "tests/fixtures/toolbox-failure-anchored-recovery/pr264-current-state-sync-failure-r0.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-failure-anchored-recovery-output-r0.schema.json"


class FailureAnchoredRecoveryTests(unittest.TestCase):
    def payload(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def codes(self, result: dict) -> set[str]:
        return {finding["code"] for finding in result["findings"]}

    def test_real_failure_bundle_is_ready_only_for_human_review(self) -> None:
        result = recovery.evaluate(self.payload())
        self.assertEqual(result["status"], "READY_FOR_HUMAN_REVIEW")
        self.assertEqual(result["next_action"], "HUMAN_REVIEW")
        self.assertEqual(result["supported_diagnosis_ids"], [
            "stale-current-facts-observation", "projection-refresh-hypothesis"
        ])
        self.assertEqual(result["supporting_evidence_ids"], ["failed-current-state-sync-log"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["retry_authorized"])
        self.assertEqual(result["source_authentication"], "NOT_PERFORMED")

    def test_result_conforms_to_versioned_output_schema(self) -> None:
        result = recovery.evaluate(self.payload())
        schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)), [])

    def test_first_failure_must_be_preserved(self) -> None:
        payload = self.payload()
        payload["failure"]["preservation"]["first_failure_preserved"] = False
        result = recovery.evaluate(payload)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("FIRST_FAILURE_NOT_PRESERVED", self.codes(result))
        self.assertEqual(result["next_action"], "STOP_NO_RETRY")
        self.assertEqual(result["proposed_instructions"], [])

    def test_failure_evidence_must_be_append_only(self) -> None:
        payload = self.payload()
        payload["failure"]["preservation"]["evidence_append_only"] = False
        self.assertIn("FAILURE_EVIDENCE_NOT_APPEND_ONLY", self.codes(recovery.evaluate(payload)))

    def test_excerpt_digest_is_checked_against_exact_caller_text(self) -> None:
        payload = self.payload()
        payload["failure"]["evidence"][0]["excerpt"] += " changed"
        result = recovery.evaluate(payload)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("EVIDENCE_EXCERPT_DIGEST_MISMATCH", self.codes(result))

    def test_observation_must_be_present_in_cited_excerpt(self) -> None:
        payload = self.payload()
        payload["diagnoses"][0]["statement"] = "The network service was unavailable."
        result = recovery.evaluate(payload)
        self.assertIn("OBSERVATION_NOT_QUOTED_BY_EVIDENCE", self.codes(result))

    def test_missing_diagnosis_reference_blocks_recovery(self) -> None:
        payload = self.payload()
        payload["recovery"]["diagnosis_ids"] = ["missing-diagnosis"]
        result = recovery.evaluate(payload)
        self.assertIn("RECOVERY_DIAGNOSIS_REFERENCE_MISSING", self.codes(result))

    def test_recovery_must_retain_diagnosis_evidence(self) -> None:
        payload = self.payload()
        payload["recovery"]["evidence_ids"] = ["unrelated-evidence"]
        result = recovery.evaluate(payload)
        self.assertIn("RECOVERY_EVIDENCE_REFERENCE_MISSING", self.codes(result))
        self.assertIn("RECOVERY_DROPS_DIAGNOSIS_EVIDENCE", self.codes(result))

    def test_permission_expansion_is_blocked(self) -> None:
        payload = self.payload()
        payload["recovery"]["permission_delta"] = "EXPANSION"
        result = recovery.evaluate(payload)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("RECOVERY_PERMISSION_DELTA_NOT_NONE", self.codes(result))

    def test_unknown_or_expanded_budget_is_blocked(self) -> None:
        payload = self.payload()
        payload["recovery"]["budget_delta"] = "UNKNOWN"
        result = recovery.evaluate(payload)
        self.assertIn("RECOVERY_BUDGET_UNBOUNDED_OR_UNKNOWN", self.codes(result))

    def test_verification_must_recheck_the_exact_failure_signature(self) -> None:
        payload = self.payload()
        payload["recovery"]["verification"]["failure_signature_to_recheck"] = "different failure"
        result = recovery.evaluate(payload)
        self.assertIn("VERIFICATION_NOT_BOUND_TO_FAILURE_SIGNATURE", self.codes(result))

    def test_repeated_failed_identical_recovery_is_stopped(self) -> None:
        payload = self.payload()
        first = recovery.evaluate(payload)
        payload["prior_attempts"] = [{
            "failure_fingerprint_sha256": first["failure_fingerprint_sha256"],
            "action_fingerprint_sha256": first["action_fingerprint_sha256"],
            "outcome": "FAILED",
        }]
        result = recovery.evaluate(payload)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("UNCHANGED_ACTION_REPEATS_FAILED_SIGNATURE", self.codes(result))

    def test_same_successful_recovery_is_not_suggested_again(self) -> None:
        payload = self.payload()
        first = recovery.evaluate(payload)
        payload["prior_attempts"] = [{
            "failure_fingerprint_sha256": first["failure_fingerprint_sha256"],
            "action_fingerprint_sha256": first["action_fingerprint_sha256"],
            "outcome": "PASSED",
        }]
        result = recovery.evaluate(payload)
        self.assertIn("SAME_RECOVERY_ALREADY_PASSED", self.codes(result))

    def test_schema_rejects_undeclared_authority_flags(self) -> None:
        payload = self.payload()
        payload["recovery"]["execute"] = True
        with self.assertRaisesRegex(recovery.InputError, "INPUT_SCHEMA_INVALID"):
            recovery.evaluate(payload)

    def test_duplicate_json_keys_fail_closed(self) -> None:
        with self.assertRaisesRegex(recovery.InputError, "DUPLICATE_JSON_KEY"):
            json.loads('{"schema_version":"x","schema_version":"y"}', object_pairs_hook=recovery._unique_object)


if __name__ == "__main__":
    unittest.main()
