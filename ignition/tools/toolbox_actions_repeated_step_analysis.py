#!/usr/bin/env python3
"""Compare repeated named GitHub Actions steps across one PR's run history.

This offline adapter reports observed repetitions and intervals. It does not
decide whether repeated work was avoidable or calculate billing.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_RUNS = 20
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_IGNITION_ROOT = Path(__file__).resolve().parents[1]
if str(_IGNITION_ROOT) not in sys.path:
    sys.path.insert(0, str(_IGNITION_ROOT))

from tools.toolbox_actions_step_timeline import InputError, summarize_snapshot  # noqa: E402


class BatchInputError(ValueError):
    """Raised when snapshots cannot be compared as one run history."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise BatchInputError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise BatchInputError(f"non-standard JSON constant: {value}")


def _positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BatchInputError(f"{path} must be a positive integer")
    return value


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BatchInputError(f"{path} must be a nonblank string")
    return value


def _context(snapshot: Any, path: str) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise BatchInputError(f"{path} must be an object")
    run = snapshot.get("workflow_run")
    if not isinstance(run, dict):
        raise BatchInputError(f"{path}.workflow_run must be an object")
    workflow_id = _positive_int(run.get("workflow_id"), f"{path}.workflow_run.workflow_id")
    workflow_path = _nonblank(run.get("path"), f"{path}.workflow_run.path")
    event = _nonblank(run.get("event"), f"{path}.workflow_run.event")
    pull_requests = run.get("pull_requests")
    if not isinstance(pull_requests, list) or len(pull_requests) != 1 or not isinstance(pull_requests[0], dict):
        raise BatchInputError(f"{path}.workflow_run.pull_requests must contain exactly one PR binding")
    pull_request = pull_requests[0]
    pr_number = _positive_int(pull_request.get("number"), f"{path}.workflow_run.pull_requests[0].number")
    base = pull_request.get("base")
    if not isinstance(base, dict):
        raise BatchInputError(f"{path}.workflow_run.pull_requests[0].base must be an object")
    base_sha = _nonblank(base.get("sha"), f"{path}.workflow_run.pull_requests[0].base.sha")
    if not SHA_RE.fullmatch(base_sha):
        raise BatchInputError(f"{path}.workflow_run.pull_requests[0].base.sha must be a 40-character lowercase commit SHA")
    return {
        "workflow_id": workflow_id,
        "path": workflow_path,
        "event": event,
        "pull_request_number": pr_number,
        "base_sha": base_sha,
    }


def _drop_reversed_skipped_job_interval(snapshot: dict[str, Any], path: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Preserve a known GitHub skipped-job timestamp anomaly without timing it."""
    normalized = deepcopy(snapshot)
    jobs_response = normalized.get("jobs_response")
    jobs = jobs_response.get("jobs") if isinstance(jobs_response, dict) else None
    anomalies: list[dict[str, Any]] = []
    if not isinstance(jobs, list):
        return normalized, anomalies
    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            continue
        started_raw = job.get("started_at")
        completed_raw = job.get("completed_at")
        if not isinstance(started_raw, str) or not isinstance(completed_raw, str):
            continue
        try:
            started = datetime.fromisoformat(started_raw.replace("Z", "+00:00"))
            completed = datetime.fromisoformat(completed_raw.replace("Z", "+00:00"))
        except ValueError:
            continue  # The single-run validator reports malformed timestamps.
        if started.tzinfo is None or completed.tzinfo is None or completed >= started:
            continue
        if job.get("status") != "completed" or job.get("conclusion") != "skipped":
            continue  # Preserve the original parser's fail-closed behavior for real work.
        anomalies.append({
            "snapshot_path": f"{path}.jobs_response.jobs[{index}]",
            "job_id": job.get("id"),
            "job_name": job.get("name"),
            "original_started_at": started_raw,
            "original_completed_at": completed_raw,
            "analysis_started_at": None,
            "analysis_completed_at": None,
            "handling": "DROPPED_REVERSED_INTERVAL_FOR_COMPLETED_SKIPPED_JOB",
        })
        job["started_at"] = None
        job["completed_at"] = None
    return normalized, anomalies


def analyze_batch(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise BatchInputError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise BatchInputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise BatchInputError("input must be valid JSON") from exc
    if not isinstance(document, dict) or set(document) != {"snapshots"}:
        raise BatchInputError("root must contain exactly one key: snapshots")
    snapshots = document["snapshots"]
    if not isinstance(snapshots, list) or not 2 <= len(snapshots) <= MAX_RUNS:
        raise BatchInputError(f"snapshots must contain between 2 and {MAX_RUNS} runs")

    context: dict[str, Any] | None = None
    seen_attempts: set[tuple[int, int]] = set()
    run_receipts: list[dict[str, Any]] = []
    repeated_steps: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_step_count = 0
    all_job_count = 0
    all_time_coverage_complete = True
    all_job_lists_complete = True
    head_shas: set[str] = set()
    timestamp_anomalies: list[dict[str, Any]] = []

    for index, snapshot in enumerate(snapshots):
        path = f"snapshots[{index}]"
        observed_context = _context(snapshot, path)
        if context is None:
            context = observed_context
        elif observed_context != context:
            raise BatchInputError(f"{path} does not match the workflow, event, PR, and base context of snapshots[0]")

        run = snapshot["workflow_run"]
        run_id = _positive_int(run.get("id"), f"{path}.workflow_run.id")
        attempt = _positive_int(run.get("run_attempt"), f"{path}.workflow_run.run_attempt")
        attempt_key = (run_id, attempt)
        if attempt_key in seen_attempts:
            raise BatchInputError(f"duplicate workflow run/attempt pair: {run_id}/{attempt}")
        seen_attempts.add(attempt_key)

        analysis_snapshot, anomalies = _drop_reversed_skipped_job_interval(snapshot, path)
        timestamp_anomalies.extend(anomalies)
        single_bytes = json.dumps(analysis_snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        try:
            timeline = summarize_snapshot(single_bytes)
        except InputError as exc:
            raise BatchInputError(f"{path} rejected by the single-run timeline contract: {exc}") from exc

        head_sha = timeline["workflow_run"]["head_sha"]
        head_shas.add(head_sha)
        all_time_coverage_complete = all_time_coverage_complete and timeline["snapshot"]["time_coverage_complete"]
        all_job_lists_complete = all_job_lists_complete and timeline["snapshot"]["job_list_complete"]
        all_job_count += timeline["summary"]["job_count"]
        all_step_count += timeline["summary"]["step_count"]
        run_receipts.append({
            "input_ordinal": index + 1,
            "workflow_run": timeline["workflow_run"],
            "context": observed_context,
            "snapshot": timeline["snapshot"],
            "normalized_snapshot_sha256": timeline["input_sha256"],
            "timeline_tool_sha256": timeline["tool_sha256"],
            "summary": timeline["summary"],
            "jobs": timeline["jobs"],
        })

        for job in timeline["jobs"]:
            for step in job["steps"]:
                key = (job["name"], step["name"])
                repeated_steps[key].append({
                    "input_ordinal": index + 1,
                    "run_id": run_id,
                    "run_attempt": attempt,
                    "head_sha": head_sha,
                    "run_conclusion": timeline["workflow_run"]["conclusion"],
                    "job_id": job["id"],
                    "step_number": step["number"],
                    "status": step["status"],
                    "conclusion": step["conclusion"],
                    "observed_elapsed_seconds": step["observed_elapsed_seconds"],
                })

    repeated_groups = []
    for (job_name, step_name), occurrences in sorted(repeated_steps.items()):
        run_ordinals = sorted({item["input_ordinal"] for item in occurrences})
        if len(run_ordinals) < 2:
            continue
        repeated_groups.append({
            "job_name": job_name,
            "step_name": step_name,
            "run_presence_count": len(run_ordinals),
            "input_ordinals": run_ordinals,
            "occurrence_count": len(occurrences),
            "occurrences": occurrences,
        })

    if context is None:
        raise BatchInputError("no workflow context was supplied")
    source_sha = hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()
    return {
        "schema_version": "github-actions-repeated-step-analysis-r0",
        "receipt_status": (
            "COMPLETE_SNAPSHOT_SET"
            if all_time_coverage_complete and all_job_lists_complete
            else "PARTIAL_TIME_COVERAGE"
            if all_job_lists_complete
            else "PARTIAL_OR_UNVERIFIED_SNAPSHOT_SET"
        ),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": source_sha,
        "source_binding": "CALLER_SUPPLIED_UNAUTHENTICATED_SNAPSHOTS",
        "comparison_context": context,
        "summary": {
            "run_count": len(run_receipts),
            "distinct_head_sha_count": len(head_shas),
            "job_count_across_runs": all_job_count,
            "step_count_across_runs": all_step_count,
            "repeated_step_group_count": len(repeated_groups),
            "job_lists_complete_for_all_runs": all_job_lists_complete,
            "time_coverage_complete_for_all_runs": all_time_coverage_complete,
            "elapsed_time_aggregated_across_runs": False,
        },
        "runs": run_receipts,
        "repeated_step_groups": repeated_groups,
        "timestamp_anomalies": timestamp_anomalies,
        "non_claims": {
            "github_source_authenticated": False,
            "avoidable_work_attributed": False,
            "billable_minutes_calculated": False,
            "cash_cost_estimated": False,
            "required_check_satisfaction_interpreted": False,
            "release_authorized": False,
        },
        "claim_ceiling": (
            "Repeated job/step names and intervals observed in caller-supplied snapshots for one workflow, event, PR, and base SHA. "
            "Different head SHAs are distinct revisions, not proof of redundant or avoidable work; no GitHub source authentication, billing, causal attribution, CI sufficiency, or release authorization."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON batch from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = analyze_batch(raw)
    except BatchInputError as exc:
        print("ACTIONS_REPEATED_STEP_BATCH_INVALID", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
