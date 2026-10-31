#!/usr/bin/env python3
"""Summarize observed wall-clock union and overlap across supplied Actions runs."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

_IGNITION_ROOT = Path(__file__).resolve().parents[1]
if str(_IGNITION_ROOT) not in sys.path:
    sys.path.insert(0, str(_IGNITION_ROOT))

from tools.toolbox_actions_repeated_step_analysis import BatchInputError, analyze_batch  # noqa: E402


def _instant(value: str, path: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # The batch parser normally rejects this first.
        raise BatchInputError(f"{path} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BatchInputError(f"{path} must include a timezone")
    return parsed


def _interval_metrics(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    intervals: list[tuple[datetime, datetime]] = []
    known_durations: list[float] = []
    for index, job in enumerate(jobs):
        started_raw = job.get("started_at")
        completed_raw = job.get("completed_at")
        if started_raw is None or completed_raw is None:
            continue
        started = _instant(started_raw, f"jobs[{index}].started_at")
        completed = _instant(completed_raw, f"jobs[{index}].completed_at")
        duration = (completed - started).total_seconds()
        if duration < 0:
            raise BatchInputError(f"jobs[{index}] completed before it started")
        known_durations.append(duration)
        if duration > 0:
            intervals.append((started, completed))

    if not known_durations:
        interval_sum = interval_union = overlap_excess = peak = None
    else:
        interval_sum = sum(known_durations)
        merged: list[list[datetime]] = []
        for started, completed in sorted(intervals):
            if not merged or started > merged[-1][1]:
                merged.append([started, completed])
            elif completed > merged[-1][1]:
                merged[-1][1] = completed
        interval_union = sum((end - start).total_seconds() for start, end in merged)

        events = [(start, 1) for start, _ in intervals] + [(end, -1) for _, end in intervals]
        active = peak_value = 0
        for _, delta in sorted(events, key=lambda event: (event[0], event[1])):
            active += delta  # End events sort before start events at a shared boundary.
            peak_value = max(peak_value, active)
        peak = peak_value
        overlap_excess = max(0.0, interval_sum - interval_union)

    job_count = len(jobs)
    timed_count = len(known_durations)
    return {
        "job_count": job_count,
        "jobs_with_observed_intervals": timed_count,
        "jobs_without_observed_intervals": job_count - timed_count,
        "job_interval_coverage_complete_for_supplied_rows": timed_count == job_count,
        "sum_observed_job_interval_seconds": None if interval_sum is None else round(interval_sum, 3),
        "union_observed_job_interval_seconds": None if interval_union is None else round(interval_union, 3),
        "excess_overlap_seconds": None if overlap_excess is None else round(overlap_excess, 3),
        "maximum_concurrent_observed_jobs": peak,
        "interval_semantics": "OBSERVED_JOB_WALL_INTERVALS_ONLY; UNION_AND_SUM_ARE_NOT_BILLABLE_MINUTES",
    }


def summarize_interval_union(raw: bytes) -> dict[str, Any]:
    """Validate a same-context run batch, then summarize only supplied job intervals."""
    batch = analyze_batch(raw)
    run_summaries: list[dict[str, Any]] = []
    all_jobs: list[dict[str, Any]] = []
    run_job_lists_complete = True

    for run in batch["runs"]:
        jobs = run["jobs"]
        run_metrics = _interval_metrics(jobs)
        job_list_complete = bool(run["snapshot"]["job_list_complete"])
        run_job_lists_complete = run_job_lists_complete and job_list_complete
        run_summaries.append({
            "run_id": run["workflow_run"]["id"],
            "run_attempt": run["workflow_run"]["run_attempt"],
            "head_sha": run["workflow_run"]["head_sha"],
            "run_conclusion": run["workflow_run"]["conclusion"],
            "job_list_complete": job_list_complete,
            **run_metrics,
            "job_interval_coverage_complete_for_declared_jobs": (
                job_list_complete and run_metrics["job_interval_coverage_complete_for_supplied_rows"]
            ),
        })
        all_jobs.extend(jobs)

    overall = _interval_metrics(all_jobs)
    job_list_complete = run_job_lists_complete and batch["summary"]["job_lists_complete_for_all_runs"]
    interval_coverage_complete = (
        job_list_complete and overall["job_interval_coverage_complete_for_supplied_rows"]
    )
    return {
        "schema_version": "github-actions-interval-union-r0",
        "receipt_status": "COMPLETE_OBSERVED_INTERVAL_SET" if interval_coverage_complete else "PARTIAL_OBSERVED_INTERVAL_SET",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        "source_binding": "CALLER_SUPPLIED_UNAUTHENTICATED_SNAPSHOTS",
        "comparison_context": batch["comparison_context"],
        "summary": {
            "run_count": len(run_summaries),
            "job_lists_complete_for_all_runs": job_list_complete,
            "job_interval_coverage_complete_for_declared_jobs": interval_coverage_complete,
            "timestamp_anomaly_count": len(batch["timestamp_anomalies"]),
            **overall,
        },
        "runs": run_summaries,
        "timestamp_anomalies": batch["timestamp_anomalies"],
        "non_claims": {
            "github_source_authenticated": False,
            "billable_minutes_calculated": False,
            "runner_capacity_or_resource_contention_inferred": False,
            "avoidable_work_attributed": False,
            "cash_cost_estimated": False,
            "required_check_satisfaction_interpreted": False,
            "release_authorized": False,
        },
        "claim_ceiling": (
            "Union, sum, and multiplicity overlap of timezone-aware job intervals present in the caller-supplied snapshots. "
            "Missing intervals and incomplete job lists remain explicit; no source authentication, billable usage, "
            "runner contention, avoidable-work attribution, CI sufficiency, or release authorization is established."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON run batch from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(2 * 1024 * 1024 + 1)
    try:
        result = summarize_interval_union(raw)
    except BatchInputError as exc:
        print("ACTIONS_INTERVAL_UNION_INVALID", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
