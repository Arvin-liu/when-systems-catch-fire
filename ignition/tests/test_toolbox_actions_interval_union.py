from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from tools.toolbox_actions_interval_union import BatchInputError, summarize_interval_union


FIXTURE = Path(__file__).parent / "fixtures/toolbox-actions-repeated-step-analysis/pr264-four-runs-r0.json"
OUTPUT_SCHEMA = Path(__file__).parents[1] / "schemas/operations/toolbox-actions-interval-union-output-r0.schema.json"


class ActionsIntervalUnionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = FIXTURE.read_bytes()
        self.document = json.loads(self.raw)

    def test_real_pr264_batch_reports_observed_union_and_incomplete_jobs(self) -> None:
        result = summarize_interval_union(self.raw)
        self.assertEqual(result["receipt_status"], "PARTIAL_OBSERVED_INTERVAL_SET")
        self.assertEqual(result["comparison_context"]["pull_request_number"], 264)
        self.assertEqual(result["summary"]["run_count"], 4)
        self.assertEqual(result["summary"]["job_count"], 14)
        self.assertEqual(result["summary"]["jobs_with_observed_intervals"], 12)
        self.assertEqual(result["summary"]["jobs_without_observed_intervals"], 2)
        self.assertEqual(result["summary"]["sum_observed_job_interval_seconds"], 26972.0)
        self.assertEqual(result["summary"]["union_observed_job_interval_seconds"], 26972.0)
        self.assertEqual(result["summary"]["excess_overlap_seconds"], 0.0)
        self.assertEqual(result["summary"]["maximum_concurrent_observed_jobs"], 1)
        self.assertFalse(result["summary"]["job_interval_coverage_complete_for_declared_jobs"])
        self.assertEqual(result["summary"]["timestamp_anomaly_count"], 2)
        self.assertFalse(result["non_claims"]["billable_minutes_calculated"])
        schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)), [])

    def test_overlapping_jobs_report_union_excess_and_peak_concurrency(self) -> None:
        document = copy.deepcopy(self.document)
        for snapshot in document["snapshots"]:
            for job in snapshot["jobs_response"]["jobs"]:
                job["started_at"] = None
                job["completed_at"] = None
        jobs = document["snapshots"][0]["jobs_response"]["jobs"]
        jobs[0]["started_at"], jobs[0]["completed_at"] = "2026-10-01T00:00:00Z", "2026-10-01T00:10:00Z"
        jobs[1]["started_at"], jobs[1]["completed_at"] = "2026-10-01T00:05:00Z", "2026-10-01T00:15:00Z"

        result = summarize_interval_union(json.dumps(document).encode())
        self.assertEqual(result["summary"]["sum_observed_job_interval_seconds"], 1200.0)
        self.assertEqual(result["summary"]["union_observed_job_interval_seconds"], 900.0)
        self.assertEqual(result["summary"]["excess_overlap_seconds"], 300.0)
        self.assertEqual(result["summary"]["maximum_concurrent_observed_jobs"], 2)
        self.assertEqual(result["receipt_status"], "PARTIAL_OBSERVED_INTERVAL_SET")

    def test_touching_intervals_are_not_counted_as_overlapping(self) -> None:
        document = copy.deepcopy(self.document)
        for snapshot in document["snapshots"]:
            for job in snapshot["jobs_response"]["jobs"]:
                job["started_at"] = None
                job["completed_at"] = None
        jobs = document["snapshots"][0]["jobs_response"]["jobs"]
        jobs[0]["started_at"], jobs[0]["completed_at"] = "2026-10-01T00:00:00Z", "2026-10-01T00:10:00Z"
        jobs[1]["started_at"], jobs[1]["completed_at"] = "2026-10-01T00:10:00Z", "2026-10-01T00:20:00Z"

        result = summarize_interval_union(json.dumps(document).encode())
        self.assertEqual(result["summary"]["sum_observed_job_interval_seconds"], 1200.0)
        self.assertEqual(result["summary"]["union_observed_job_interval_seconds"], 1200.0)
        self.assertEqual(result["summary"]["excess_overlap_seconds"], 0.0)
        self.assertEqual(result["summary"]["maximum_concurrent_observed_jobs"], 1)

    def test_rejects_mixed_pull_request_context(self) -> None:
        document = copy.deepcopy(self.document)
        document["snapshots"][1]["workflow_run"]["pull_requests"][0]["number"] = 999
        with self.assertRaisesRegex(BatchInputError, "does not match the workflow, event, PR, and base context"):
            summarize_interval_union(json.dumps(document).encode())


if __name__ == "__main__":
    unittest.main()
