from __future__ import annotations

import copy
import unittest

from agent_federation.executor_conformance import EXPECTED_RESULT, evaluate_case, fixture_cases, run_matrix, validate_matrix


class ExecutorConformanceTests(unittest.TestCase):
    def test_exact_case_is_the_only_accepted_case(self) -> None:
        matrix = run_matrix()
        self.assertEqual(validate_matrix(matrix), [])
        self.assertEqual(matrix["summary"]["accepted_count"], 1)
        self.assertEqual(matrix["summary"]["rejected_count"], 10)

    def test_result_shape_and_semantics_are_not_repaired(self) -> None:
        case = next(item for item in fixture_cases() if item["case_id"] == "extra_field")
        result = evaluate_case(case)
        self.assertIn("EXTRA_FIELDS", result["reasons"])
        wrong = next(item for item in fixture_cases() if item["case_id"] == "wrong_result")
        self.assertIn("STRUCTURED_RESULT_SEMANTIC_MISMATCH", evaluate_case(wrong)["reasons"])
        self.assertEqual(EXPECTED_RESULT["line_count"], 3)

    def test_safety_and_capture_failures_reject_completion(self) -> None:
        for case_id in ("nonzero_exit", "timeout", "child_cleanup_failure", "workspace_mutation", "runtime_scratch_leak", "capture_incomplete", "redaction_failure"):
            case = next(item for item in fixture_cases() if item["case_id"] == case_id)
            result = evaluate_case(case)
            self.assertFalse(result["validated_completion"], case_id)
            self.assertTrue(result["reasons"], case_id)

    def test_matrix_mutation_is_detected(self) -> None:
        matrix = run_matrix()
        mutated = copy.deepcopy(matrix)
        mutated["summary"]["live_process_started"] = True
        self.assertTrue(validate_matrix(mutated))


if __name__ == "__main__":
    unittest.main()
