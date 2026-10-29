#!/usr/bin/env python3
"""Summarize observed GitHub Actions job and step intervals from a supplied snapshot."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_JOBS = 500
MAX_STEPS_PER_JOB = 1000
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class InputError(ValueError):
    """Raised when a supplied workflow/job snapshot cannot be bound safely."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise InputError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{path} must be an object")
    return value


def _positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InputError(f"{path} must be a positive integer")
    return value


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{path} must be a nonblank string")
    return value


def _nullable_text(value: Any, path: str) -> str | None:
    if value is None:
        return None
    return _nonblank(value, path)


def _timestamp(value: Any, path: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    raw = _nonblank(value, path)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InputError(f"{path} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InputError(f"{path} must include a timezone")
    return raw, parsed


def _elapsed(start: datetime | None, finish: datetime | None, path: str) -> float | None:
    if start is None or finish is None:
        return None
    seconds = (finish - start).total_seconds()
    if seconds < 0:
        raise InputError(f"{path} completed before it started")
    return round(seconds, 3)


def _snapshot(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except UnicodeDecodeError as exc:
        raise InputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise InputError("input must be valid JSON") from exc

    root = _object(payload, "root")
    run = _object(root.get("workflow_run"), "workflow_run")
    run_id = _positive_int(run.get("id"), "workflow_run.id")
    run_attempt = _positive_int(run.get("run_attempt"), "workflow_run.run_attempt")
    head_sha = _nonblank(run.get("head_sha"), "workflow_run.head_sha")
    if not SHA_RE.fullmatch(head_sha):
        raise InputError("workflow_run.head_sha must be a 40-character lowercase commit SHA")
    event = _nonblank(run.get("event"), "workflow_run.event")
    run_status = _nonblank(run.get("status"), "workflow_run.status")
    run_conclusion = _nullable_text(run.get("conclusion"), "workflow_run.conclusion")
    run_started, _ = _timestamp(run.get("run_started_at"), "workflow_run.run_started_at")

    jobs_response = _object(root.get("jobs_response"), "jobs_response")
    jobs = jobs_response.get("jobs")
    if not isinstance(jobs, list):
        raise InputError("jobs_response.jobs must be an array")
    if len(jobs) > MAX_JOBS:
        raise InputError(f"jobs_response.jobs exceeds {MAX_JOBS} entries")
    total_count = jobs_response.get("total_count")
    if total_count is not None and (isinstance(total_count, bool) or not isinstance(total_count, int) or total_count < len(jobs)):
        raise InputError("jobs_response.total_count must be an integer at least as large as the supplied jobs array")
    snapshot_complete = total_count == len(jobs) if total_count is not None else False

    seen_job_ids: set[int] = set()
    normalized_jobs: list[dict[str, Any]] = []
    job_elapsed_values: list[float] = []
    step_elapsed_values: list[float] = []
    step_count = 0
    timed_step_count = 0
    time_coverage_complete = True

    for job_index, raw_job in enumerate(jobs):
        path = f"jobs_response.jobs[{job_index}]"
        job = _object(raw_job, path)
        job_id = _positive_int(job.get("id"), f"{path}.id")
        if job_id in seen_job_ids:
            raise InputError(f"duplicate job id: {job_id}")
        seen_job_ids.add(job_id)
        if _positive_int(job.get("run_id"), f"{path}.run_id") != run_id:
            raise InputError(f"{path}.run_id does not match workflow_run.id")
        if _positive_int(job.get("run_attempt"), f"{path}.run_attempt") != run_attempt:
            raise InputError(f"{path}.run_attempt does not match workflow_run.run_attempt")
        job_head = _nonblank(job.get("head_sha"), f"{path}.head_sha")
        if job_head != head_sha:
            raise InputError(f"{path}.head_sha does not match workflow_run.head_sha")
        name = _nonblank(job.get("name"), f"{path}.name")
        status = _nonblank(job.get("status"), f"{path}.status")
        conclusion = _nullable_text(job.get("conclusion"), f"{path}.conclusion")
        started_raw, started = _timestamp(job.get("started_at"), f"{path}.started_at")
        completed_raw, completed = _timestamp(job.get("completed_at"), f"{path}.completed_at")
        duration = _elapsed(started, completed, path)
        if duration is not None:
            job_elapsed_values.append(duration)
        else:
            time_coverage_complete = False

        raw_steps = job.get("steps")
        if not isinstance(raw_steps, list):
            raise InputError(f"{path}.steps must be an array")
        if len(raw_steps) > MAX_STEPS_PER_JOB:
            raise InputError(f"{path}.steps exceeds {MAX_STEPS_PER_JOB} entries")
        seen_step_numbers: set[int] = set()
        normalized_steps: list[dict[str, Any]] = []
        for step_index, raw_step in enumerate(raw_steps):
            step_path = f"{path}.steps[{step_index}]"
            step = _object(raw_step, step_path)
            number = _positive_int(step.get("number"), f"{step_path}.number")
            if number in seen_step_numbers:
                raise InputError(f"duplicate step number {number} in job {job_id}")
            seen_step_numbers.add(number)
            step_name = _nonblank(step.get("name"), f"{step_path}.name")
            step_status = _nonblank(step.get("status"), f"{step_path}.status")
            step_conclusion = _nullable_text(step.get("conclusion"), f"{step_path}.conclusion")
            step_started_raw, step_started = _timestamp(step.get("started_at"), f"{step_path}.started_at")
            step_completed_raw, step_completed = _timestamp(step.get("completed_at"), f"{step_path}.completed_at")
            step_duration = _elapsed(step_started, step_completed, step_path)
            step_count += 1
            if step_duration is not None:
                timed_step_count += 1
                step_elapsed_values.append(step_duration)
            else:
                time_coverage_complete = False
            normalized_steps.append({
                "number": number,
                "name": step_name,
                "status": step_status,
                "conclusion": step_conclusion,
                "started_at": step_started_raw,
                "completed_at": step_completed_raw,
                "observed_elapsed_seconds": step_duration,
            })

        normalized_jobs.append({
            "id": job_id,
            "name": name,
            "run_attempt": run_attempt,
            "head_sha": head_sha,
            "status": status,
            "conclusion": conclusion,
            "started_at": started_raw,
            "completed_at": completed_raw,
            "observed_elapsed_seconds": duration,
            "steps": sorted(normalized_steps, key=lambda row: row["number"]),
        })

    normalized_jobs.sort(key=lambda row: (row["started_at"] is None, row["started_at"] or "", row["id"]))
    tool_path = Path(__file__).resolve()
    return {
        "schema_version": "github-actions-step-timeline-r0",
        "receipt_status": "COMPLETE_SNAPSHOT" if snapshot_complete and time_coverage_complete else "PARTIAL_OR_UNVERIFIED_SNAPSHOT",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": hashlib.sha256(tool_path.read_bytes()).hexdigest(),
        "source_binding": "CALLER_SUPPLIED_UNAUTHENTICATED_SNAPSHOT",
        "workflow_run": {
            "id": run_id,
            "run_attempt": run_attempt,
            "head_sha": head_sha,
            "event": event,
            "status": run_status,
            "conclusion": run_conclusion,
            "run_started_at": run_started,
        },
        "snapshot": {
            "supplied_job_count": len(normalized_jobs),
            "declared_total_job_count": total_count,
            "job_list_complete": snapshot_complete,
            "time_coverage_complete": time_coverage_complete,
            "complete": snapshot_complete and time_coverage_complete,
        },
        "summary": {
            "job_count": len(normalized_jobs),
            "jobs_with_observed_elapsed": len(job_elapsed_values),
            "sum_observed_job_intervals_seconds": round(sum(job_elapsed_values), 3),
            "step_count": step_count,
            "steps_with_observed_elapsed": timed_step_count,
            "sum_observed_step_intervals_seconds": round(sum(step_elapsed_values), 3),
            "interval_sum_semantics": "SUM_OF_RECORDED_INTERVALS; PARALLEL_JOBS_MAY_OVERLAP; NOT_BILLABLE_MINUTES",
        },
        "non_claims": {
            "github_source_authenticated": False,
            "billable_minutes_calculated": False,
            "cash_cost_estimated": False,
            "required_check_satisfaction_interpreted": False,
            "release_authorized": False,
        },
        "jobs": normalized_jobs,
        "claim_ceiling": "Observed intervals from caller-supplied JSON only; no live GitHub query, source authentication, billing, test equivalence, required-check decision, or release authorization.",
    }


def summarize_snapshot(raw: bytes) -> dict[str, Any]:
    """Return the validated single-run receipt for reuse by batch analyzers."""
    return _snapshot(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON envelope from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = summarize_snapshot(raw)
    except InputError as exc:
        print("ACTIONS_STEP_TIMELINE_INVALID", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
