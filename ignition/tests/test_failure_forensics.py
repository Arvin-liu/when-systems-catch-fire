from __future__ import annotations

import copy
import unittest

from agent_federation.failure_forensics import (
    FailureForensicsError,
    build_failure_forensics_capsule,
    classify_failure,
    public_argv_shape,
    update_spool_disposition,
    validate_failure_forensics_capsule,
)


class FailureForensicsTests(unittest.TestCase):
    def capsule(self) -> dict:
        return build_failure_forensics_capsule(
            task_id="IGNITION-20260826-141",
            dispatch_id="dispatch-141-test-01",
            attempt_id="attempt-141-test-01",
            executor_id="external.synthetic",
            adapter_id="synthetic-r1",
            executor_version="synthetic 1",
            interface_digest="a" * 64,
            argv=("/usr/bin/synthetic", "exec", "--json", "/private/path/omitted"),
            process_return_code=1,
            duration_ms=58.0,
            timed_out=False,
            process_group_status="CONFIRMED_GONE",
            cleanup_status="CLEANED",
            stdout_byte_count=0,
            stdout_digest="b" * 64,
            stderr_byte_count=271,
            stderr_digest="c" * 64,
            parser_status="NOT_RUN",
            parser_error_class="NO_PUBLIC_EVENTS",
            schema_status="NOT_RUN",
            schema_error_class="NO_STRUCTURED_RESULT",
            structured_output_status="ABSENT",
            structured_output_present=False,
            runtime_scratch_status="CLEANED",
            auth_source_status="UNCHANGED_REFERENCE",
            workspace_status="UNCHANGED",
            inference_observation_status="NOT_OBSERVED",
            raw_spool_initialized=True,
            raw_spool_retention_status="RETAINED_UNTIL_DURABLE_RECEIPT",
            raw_spool_disposal_status="PENDING",
            known=("process started", "process returned nonzero"),
            unknown=("provider-private diagnostic text",),
            not_inferable=("private inference execution",),
        )

    def test_capsule_is_sanitized_and_machine_validated(self) -> None:
        capsule = self.capsule()
        self.assertEqual(capsule["diagnostic_class"], "PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT")
        self.assertNotIn("argv", capsule)
        self.assertNotIn("stdout", capsule)
        self.assertNotIn("stderr", capsule)
        self.assertNotIn("private/path", str(capsule))
        self.assertEqual(validate_failure_forensics_capsule(capsule)["redaction"]["status"], "PASS")

    def test_cleanup_disposition_is_updated_without_raw_output(self) -> None:
        updated = update_spool_disposition(self.capsule(), retention_status="CLEANED_AFTER_DURABLE_RECEIPT", disposal_status="CLEANED")
        self.assertEqual(updated["raw_spool"]["disposal_status"], "CLEANED")
        self.assertEqual(updated["capsule_digest"], validate_failure_forensics_capsule(updated)["capsule_digest"])

    def test_classification_is_stable_and_specific(self) -> None:
        self.assertEqual(classify_failure(process_return_code=1, timed_out=False, parser_status="NOT_RUN", schema_status="NOT_RUN", structured_output_status="ABSENT"), "PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT")
        self.assertEqual(classify_failure(process_return_code=0, timed_out=False, parser_status="FAIL", schema_status="NOT_RUN", structured_output_status="MALFORMED"), "STRUCTURED_RESULT_PARSE_FAILURE")
        self.assertEqual(classify_failure(process_return_code=None, timed_out=False, parser_status="NOT_RUN", schema_status="NOT_RUN", structured_output_status="UNKNOWN", permission_error=True), "STARTUP_PERMISSION_FAILURE")

    def test_private_and_tampered_capsules_fail_closed(self) -> None:
        private = copy.deepcopy(self.capsule())
        private["knowledge"]["known"] = ["api_key=must-not-persist"]
        with self.assertRaises(FailureForensicsError):
            validate_failure_forensics_capsule(private, check_digest=False)
        tampered = copy.deepcopy(self.capsule())
        tampered["process"]["return_code"] = 0
        with self.assertRaises(FailureForensicsError):
            validate_failure_forensics_capsule(tampered)

    def test_argv_shape_contains_only_public_option_shape(self) -> None:
        shape = public_argv_shape(("/usr/bin/agent", "exec", "--auth", "/private/secret", "prompt"))
        self.assertEqual(shape["status"], "SHAPE_ONLY")
        self.assertIn("--auth", shape["option_names"])
        self.assertNotIn("/private/secret", str(shape))


if __name__ == "__main__":
    unittest.main()
