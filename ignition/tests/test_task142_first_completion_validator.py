from __future__ import annotations

import copy
import unittest

from agent_federation.task142_first_completion_validator import (
    FirstCompletionValidationError,
    VALIDATOR_VERSION,
    expected_result_digest,
    validate_exact_completion,
)


DIGEST = "a" * 64
RESULT = {"nonce": "0123456789abcdef01234567", "line_count": 3, "field_value": "task142-fixture", "checksum_prefix": "abcdef01"}


def record() -> dict[str, object]:
    return {
        "task_id": "IGNITION-20260827-142", "dispatch_id": "dispatch-142-a", "attempt_id": "attempt-142-a",
        "executor_id": "external.synthetic", "family": "AGENTIC_EXECUTOR", "executor_version": "fixture-agent-r1",
        "capability_lease_id": "lease-142-a", "capability_lease_status": "ACTIVE", "fixture_nonce": RESULT["nonce"],
        "workspace_digest_before": DIGEST, "workspace_digest_after": DIGEST,
        "capture_ref": "capture://attempt-142-a", "structured_result_ref": "capture://attempt-142-a/result", "validator_ref": "validator://task142-exact-validator-r1",
        "executor_state": "RETURNED_UNVALIDATED", "expected_result": RESULT, "returned_structured_result": copy.deepcopy(RESULT),
        "returned_result_digest": expected_result_digest(RESULT), "validator_version": VALIDATOR_VERSION, "validator_result": "PASS",
        "capture_completeness": "COMPLETE", "process_return_code": 0, "cleanup_status": "CONFIRMED_GONE",
        "workspace_mode": "DISPOSABLE_READ_ONLY_FIXTURE", "side_effect_observation": "READ_ONLY_UNCHANGED",
    }


class Task142FirstCompletionValidatorTests(unittest.TestCase):
    def test_exact_candidate_passes(self) -> None:
        result = validate_exact_completion(record())
        self.assertEqual(result["status"], "LIVE_READONLY_VALIDATED_COMPLETION")

    def test_executor_self_pass_is_not_authority(self) -> None:
        candidate = record()
        candidate["executor_state"] = "COMPLETED_VALIDATED"
        with self.assertRaisesRegex(FirstCompletionValidationError, "EXECUTOR_SELF_PASS_NOT_AUTHORITY"):
            validate_exact_completion(candidate)

    def test_missing_binding_fails(self) -> None:
        candidate = record()
        del candidate["dispatch_id"]
        with self.assertRaisesRegex(FirstCompletionValidationError, "MISSING_BINDING"):
            validate_exact_completion(candidate)

    def test_wrong_result_fails(self) -> None:
        candidate = record()
        candidate["returned_structured_result"] = {**RESULT, "line_count": 4}
        with self.assertRaisesRegex(FirstCompletionValidationError, "STRUCTURED_RESULT_SEMANTIC_MISMATCH"):
            validate_exact_completion(candidate)

    def test_non_agent_class_fails(self) -> None:
        candidate = record()
        candidate["family"] = "REASONER_RUNTIME"
        with self.assertRaisesRegex(FirstCompletionValidationError, "WRONG_EXECUTOR_CLASS"):
            validate_exact_completion(candidate)

    def test_workspace_capture_process_and_cleanup_fail_closed(self) -> None:
        for field, value, code in (
            ("workspace_digest_after", "b" * 64, "WORKSPACE_MUTATED"),
            ("capture_completeness", "INCOMPLETE", "CAPTURE_INCOMPLETE"),
            ("process_return_code", 1, "PROCESS_EXIT_NONZERO"),
            ("cleanup_status", "UNKNOWN", "CHILD_CLEANUP_NOT_CONFIRMED"),
        ):
            candidate = record()
            candidate[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(FirstCompletionValidationError, code):
                validate_exact_completion(candidate)


if __name__ == "__main__":
    unittest.main()
