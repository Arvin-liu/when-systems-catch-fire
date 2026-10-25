from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_actions_step_timeline.py"
FIXTURE_PATH = IGNITION_ROOT / "tests/fixtures/toolbox-actions-step-timeline/actions-run-40064357026.json"
SPEC = importlib.util.spec_from_file_location("toolbox_actions_step_timeline", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ActionsStepTimelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_fixture = FIXTURE_PATH.read_bytes()
        self.payload = json.loads(self.raw_fixture)

    def invoke(self, raw: bytes, *, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(TOOL_PATH), "--stdin"],
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            check=False,
        )

    def test_exact_api_snapshot_smoke_is_bounded_partial_and_deterministic(self) -> None:
        first = self.invoke(self.raw_fixture)
        second = self.invoke(self.raw_fixture)
        self.assertEqual(first.returncode, 0, first.stderr.decode())
        self.assertEqual(first.stdout, second.stdout)
        receipt = json.loads(first.stdout)
        self.assertEqual(receipt["workflow_run"]["id"], 40064357026)
        self.assertEqual(receipt["workflow_run"]["run_attempt"], 1)
        self.assertEqual(receipt["workflow_run"]["head_sha"], "8230dc6c13ec12c57f9c81f81994ee775ebb2ce8")
        self.assertEqual(receipt["workflow_run"]["conclusion"], "cancelled")
        self.assertEqual(receipt["receipt_status"], "COMPLETE_SNAPSHOT")
        self.assertTrue(receipt["snapshot"]["job_list_complete"])
        self.assertTrue(receipt["snapshot"]["time_coverage_complete"])
        self.assertEqual(receipt["summary"]["job_count"], 2)
        self.assertEqual(receipt["summary"]["step_count"], 65)
        jobs = {job["name"]: job for job in receipt["jobs"]}
        self.assertEqual(jobs["foundation-validation-route"]["observed_elapsed_seconds"], 1949.0)
        self.assertEqual(jobs["Full Foundation regression"]["observed_elapsed_seconds"], 49.0)
        timed_step = next(
            step for step in jobs["foundation-validation-route"]["steps"]
            if step["name"] == "Run selected component and consumer tests"
        )
        self.assertEqual(timed_step["observed_elapsed_seconds"], 1894.0)
        self.assertEqual(
            receipt["summary"]["interval_sum_semantics"],
            "SUM_OF_RECORDED_INTERVALS; PARALLEL_JOBS_MAY_OVERLAP; NOT_BILLABLE_MINUTES",
        )
        self.assertFalse(receipt["non_claims"]["github_source_authenticated"])
        self.assertFalse(receipt["non_claims"]["billable_minutes_calculated"])
        self.assertFalse(receipt["non_claims"]["required_check_satisfaction_interpreted"])
        self.assertFalse(receipt["non_claims"]["release_authorized"])

    def assert_rejected_without_partial_stdout(self, raw: bytes) -> None:
        result = self.invoke(raw)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"ACTIONS_STEP_TIMELINE_INVALID", result.stderr)

    def test_mismatched_run_bindings_fail_closed(self) -> None:
        cases = []
        changed = copy.deepcopy(self.payload)
        changed["jobs_response"]["jobs"][0]["head_sha"] = "0" * 40
        cases.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["jobs_response"]["jobs"][0]["run_id"] += 1
        cases.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["jobs_response"]["jobs"][0]["run_attempt"] += 1
        cases.append(changed)
        for payload in cases:
            with self.subTest(job=payload["jobs_response"]["jobs"][0]):
                self.assert_rejected_without_partial_stdout(json.dumps(payload).encode())

    def test_invalid_intervals_duplicate_steps_and_duplicate_keys_fail_closed(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["jobs_response"]["jobs"][0]["started_at"] = "2026-10-24T06:00:00Z"
        self.assert_rejected_without_partial_stdout(json.dumps(changed).encode())

        changed = copy.deepcopy(self.payload)
        steps = changed["jobs_response"]["jobs"][0]["steps"]
        steps[1]["number"] = steps[0]["number"]
        self.assert_rejected_without_partial_stdout(json.dumps(changed).encode())

        self.assert_rejected_without_partial_stdout(b'{"workflow_run":{},"workflow_run":{}}')

    def test_missing_timestamps_are_preserved_as_partial_not_zero(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["jobs_response"]["jobs"][0]["started_at"] = None
        result = self.invoke(json.dumps(changed).encode())
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["receipt_status"], "PARTIAL_OR_UNVERIFIED_SNAPSHOT")
        route_job = next(job for job in receipt["jobs"] if job["id"] == self.payload["jobs_response"]["jobs"][0]["id"])
        self.assertIsNone(route_job["observed_elapsed_seconds"])
        self.assertFalse(receipt["snapshot"]["time_coverage_complete"])

    def test_oversized_input_has_no_partial_stdout(self) -> None:
        self.assert_rejected_without_partial_stdout(b" " * (TOOL.MAX_INPUT_BYTES + 1))

    def test_stdin_cli_writes_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            result = self.invoke(self.raw_fixture, cwd=cwd)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual(list(cwd.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
