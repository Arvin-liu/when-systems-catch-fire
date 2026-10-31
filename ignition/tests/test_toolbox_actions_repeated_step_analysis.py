from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.toolbox_actions_repeated_step_analysis import BatchInputError, analyze_batch


FIXTURE = Path(__file__).parent / "fixtures/toolbox-actions-repeated-step-analysis/pr264-four-runs-r0.json"


class ActionsRepeatedStepAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = FIXTURE.read_bytes()
        self.document = json.loads(self.raw)

    def test_real_pr264_run_sequence_preserves_head_changes_and_repeated_steps(self) -> None:
        result = analyze_batch(self.raw)
        self.assertEqual(result["receipt_status"], "PARTIAL_TIME_COVERAGE")
        self.assertEqual(result["comparison_context"], {
            "workflow_id": 311987523,
            "path": ".github/workflows/foundation-validation.yml",
            "event": "pull_request",
            "pull_request_number": 264,
            "base_sha": "483658e2ff57ad553c3fda762ed855a8bd93ebbe",
        })
        self.assertEqual(result["summary"]["run_count"], 4)
        self.assertEqual(result["summary"]["distinct_head_sha_count"], 4)
        self.assertEqual(result["summary"]["job_count_across_runs"], 14)
        self.assertEqual(result["summary"]["step_count_across_runs"], 275)
        self.assertTrue(result["summary"]["job_lists_complete_for_all_runs"])
        self.assertFalse(result["summary"]["elapsed_time_aggregated_across_runs"])
        self.assertFalse(result["non_claims"]["avoidable_work_attributed"])
        self.assertFalse(result["non_claims"]["billable_minutes_calculated"])

        foundation_job = next(group for group in result["repeated_step_groups"] if group["job_name"] == "Full Foundation regression" and group["step_name"] == "Run python3 tools/foundation/validate_foundation.py")
        self.assertEqual(foundation_job["run_presence_count"], 4)
        self.assertEqual(
            [row["observed_elapsed_seconds"] for row in foundation_job["occurrences"]],
            [1234.0, 1205.0, 701.0, 0.0],
        )
        self.assertEqual(
            [run["workflow_run"]["conclusion"] for run in result["runs"]],
            ["failure", "failure", "success", "cancelled"],
        )
        self.assertEqual(foundation_job["occurrences"][3]["conclusion"], "skipped")
        self.assertEqual(foundation_job["occurrences"][3]["run_conclusion"], "cancelled")
        self.assertEqual(len(result["timestamp_anomalies"]), 2)
        self.assertTrue(all(row["analysis_started_at"] is None and row["analysis_completed_at"] is None for row in result["timestamp_anomalies"]))

    def test_rejects_mixed_pr_or_base_context(self) -> None:
        document = copy.deepcopy(self.document)
        document["snapshots"][1]["workflow_run"]["pull_requests"][0]["number"] = 999
        with self.assertRaisesRegex(BatchInputError, "does not match the workflow, event, PR, and base context"):
            analyze_batch(json.dumps(document).encode())

    def test_rejects_duplicate_run_attempt_even_if_head_is_same(self) -> None:
        document = copy.deepcopy(self.document)
        document["snapshots"][1] = copy.deepcopy(document["snapshots"][0])
        with self.assertRaisesRegex(BatchInputError, "duplicate workflow run/attempt pair"):
            analyze_batch(json.dumps(document).encode())

    def test_rejects_reversed_timestamps_on_non_skipped_job(self) -> None:
        document = copy.deepcopy(self.document)
        job = document["snapshots"][0]["jobs_response"]["jobs"][0]
        job["started_at"], job["completed_at"] = job["completed_at"], job["started_at"]
        with self.assertRaisesRegex(BatchInputError, "completed before it started"):
            analyze_batch(json.dumps(document).encode())

    def test_rejects_duplicate_json_keys_and_batch_overflow(self) -> None:
        with self.assertRaisesRegex(BatchInputError, "duplicate JSON key"):
            analyze_batch(b'{"snapshots":[],"snapshots":[] }')
        with self.assertRaisesRegex(BatchInputError, "input exceeds"):
            analyze_batch(b" " * (2 * 1024 * 1024 + 1))

    def test_does_not_claim_time_completeness_when_a_timestamp_is_missing(self) -> None:
        document = copy.deepcopy(self.document)
        document["snapshots"][0]["jobs_response"]["jobs"][0]["steps"][0]["started_at"] = None
        result = analyze_batch(json.dumps(document).encode())
        self.assertEqual(result["receipt_status"], "PARTIAL_TIME_COVERAGE")
        self.assertFalse(result["summary"]["time_coverage_complete_for_all_runs"])

    def test_marks_a_truncated_job_list_as_unverified(self) -> None:
        document = copy.deepcopy(self.document)
        document["snapshots"][0]["jobs_response"]["total_count"] += 1
        result = analyze_batch(json.dumps(document).encode())
        self.assertEqual(result["receipt_status"], "PARTIAL_OR_UNVERIFIED_SNAPSHOT_SET")
        self.assertFalse(result["summary"]["job_lists_complete_for_all_runs"])


if __name__ == "__main__":
    unittest.main()
