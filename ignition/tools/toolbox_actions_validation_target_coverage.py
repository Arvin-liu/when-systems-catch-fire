#!/usr/bin/env python3
"""Compare planned validation-target coverage across supplied Actions runs.

This offline adapter reuses the single-run attribution contract for each row,
then compares plans and caller-declared target results. Missing receipt content
stays unknown and is never projected as target failure.
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

from toolbox_actions_validation_attribution import (
    InputError as AttributionInputError,
    attribute_validation_evidence,
    canonical_json,
    digest_json,
)


TOOL_ID = "maintenance.compare_actions_validation_target_coverage"
INPUT_SCHEMA_VERSION = "toolbox-actions-validation-target-coverage-input-r0"
OUTPUT_SCHEMA_VERSION = "toolbox-actions-validation-target-coverage-output-r0"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MIN_RUNS = 2
MAX_RUNS = 20
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class InputError(ValueError):
    """Raised when inputs are malformed or do not describe one PR history."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise InputError("duplicate JSON key: " + key)
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise InputError("non-finite JSON constant is not permitted: " + value)


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(path + " must be an object")
    return value


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(path + " must be a nonblank string")
    return value


def _positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InputError(path + " must be a positive integer")
    return value


def _context(snapshot: Any, path: str) -> dict[str, Any]:
    """Bind every row to one caller-supplied workflow/event/PR/base context."""
    root = _object(snapshot, path)
    run = _object(root.get("workflow_run"), path + ".workflow_run")
    workflow_id = _positive_int(run.get("workflow_id"), path + ".workflow_run.workflow_id")
    workflow_path = _nonblank(run.get("path"), path + ".workflow_run.path")
    event = _nonblank(run.get("event"), path + ".workflow_run.event")
    pull_requests = run.get("pull_requests")
    if not isinstance(pull_requests, list) or len(pull_requests) != 1:
        raise InputError(path + ".workflow_run.pull_requests must contain exactly one PR binding")
    pull_request = _object(pull_requests[0], path + ".workflow_run.pull_requests[0]")
    pr_number = _positive_int(pull_request.get("number"), path + ".workflow_run.pull_requests[0].number")
    base = _object(pull_request.get("base"), path + ".workflow_run.pull_requests[0].base")
    base_sha = _nonblank(base.get("sha"), path + ".workflow_run.pull_requests[0].base.sha")
    if not SHA40_RE.fullmatch(base_sha):
        raise InputError(path + ".workflow_run.pull_requests[0].base.sha must be a 40-character lowercase commit SHA")
    return {
        "workflow_id": workflow_id,
        "workflow_path": workflow_path,
        "event": event,
        "pull_request_number": pr_number,
        "base_sha": base_sha,
    }


def _attribution_input(row: Any, path: str) -> dict[str, Any]:
    value = _object(row, path)
    allowed = {"schema_version", "validation_plan", "actions_snapshot", "artifact_inventory", "validation_receipt"}
    unknown = set(value) - allowed
    if unknown:
        raise InputError(path + " contains unsupported fields: " + ", ".join(sorted(unknown)))
    if value.get("schema_version") != "toolbox-actions-validation-attribution-input-r0":
        raise InputError(path + ".schema_version must identify the existing single-run attribution contract")
    for key in ("validation_plan", "actions_snapshot", "artifact_inventory"):
        if key not in value:
            raise InputError(path + " is missing " + key)
    return value


def _normalize_reversed_skipped_job_intervals(
    snapshot: dict[str, Any], path: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Drop only the known non-executed skipped-job interval anomaly."""
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
            continue  # The reused attribution contract reports malformed timestamps.
        if started.tzinfo is None or completed.tzinfo is None or completed >= started:
            continue
        if job.get("status") != "completed" or job.get("conclusion") != "skipped":
            continue  # Executed work remains fail-closed under the attribution contract.
        anomalies.append({
            "snapshot_path": "{}.jobs_response.jobs[{}]".format(path, index),
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


def _result_values(attributed: dict[str, Any]) -> dict[str, bool | None]:
    receipt = attributed["validation_receipt"]
    return {
        row["target_id"]: row["caller_declared_successful"]
        for row in receipt["declared_target_results"]
    }


def analyze_validation_target_coverage(raw: bytes) -> dict[str, Any]:
    """Validate and compare two to twenty same-context run attribution inputs."""
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input exceeds " + str(MAX_INPUT_BYTES) + " bytes")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise InputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise InputError("input must be valid JSON") from exc

    root = _object(document, "root")
    if set(root) != {"schema_version", "runs"}:
        raise InputError("root must contain exactly schema_version and runs")
    if root.get("schema_version") != INPUT_SCHEMA_VERSION:
        raise InputError("unsupported input schema_version")
    runs = root.get("runs")
    if not isinstance(runs, list) or not MIN_RUNS <= len(runs) <= MAX_RUNS:
        raise InputError("runs must contain between 2 and " + str(MAX_RUNS) + " attribution inputs")

    observed_context: dict[str, Any] | None = None
    seen_run_attempts: set[tuple[int, int]] = set()
    normalized_runs: list[dict[str, Any]] = []
    timestamp_anomalies: list[dict[str, Any]] = []
    for ordinal, raw_row in enumerate(runs, start=1):
        path = "runs[{}]".format(ordinal - 1)
        row = _attribution_input(raw_row, path)
        context = _context(row["actions_snapshot"], path + ".actions_snapshot")
        if observed_context is None:
            observed_context = context
        elif context != observed_context:
            raise InputError(path + " does not match the workflow, event, PR, and base context of runs[0]")

        analysis_snapshot, anomalies = _normalize_reversed_skipped_job_intervals(
            row["actions_snapshot"], path + ".actions_snapshot",
        )
        timestamp_anomalies.extend(anomalies)
        attribution_row = dict(row)
        attribution_row["actions_snapshot"] = analysis_snapshot
        try:
            attributed = attribute_validation_evidence(canonical_json(attribution_row).encode("utf-8"))
        except AttributionInputError as exc:
            raise InputError(path + " rejected by the single-run attribution contract: " + str(exc)) from exc
        workflow = attributed["workflow_binding"]
        plan = attributed["plan_binding"]
        if plan["base_sha"] != context["base_sha"]:
            raise InputError(path + " validation plan base does not match the shared PR base")
        attempt_key = (workflow["run_id"], workflow["run_attempt"])
        if attempt_key in seen_run_attempts:
            raise InputError("duplicate workflow run/attempt pair: {}/{}".format(*attempt_key))
        seen_run_attempts.add(attempt_key)

        targets = plan["selected_target_ids"]
        results = _result_values(attributed)
        target_set_sha256 = digest_json({"selected_target_ids": sorted(targets)})
        normalized_runs.append({
            "input_ordinal": ordinal,
            "context": context,
            "attribution": attributed,
            "source_input_sha256": hashlib.sha256(canonical_json(row).encode("utf-8")).hexdigest(),
            "normalized_actions_snapshot_sha256": hashlib.sha256(canonical_json(analysis_snapshot).encode("utf-8")).hexdigest(),
            "timestamp_anomalies": anomalies,
            "target_set_sha256": target_set_sha256,
            "result_values": results,
        })

    if observed_context is None:
        raise InputError("no workflow context supplied")

    target_ids = sorted({
        target_id
        for row in normalized_runs
        for target_id in row["attribution"]["plan_binding"]["selected_target_ids"]
    })
    target_statistics: dict[str, dict[str, Any]] = {
        target_id: {
            "target_id": target_id,
            "plan_presence_count": 0,
            "caller_declared_success_count": 0,
            "caller_declared_failure_count": 0,
            "caller_declared_unknown_value_count": 0,
            "no_target_result_claim_count": 0,
            "claims_by_run": [],
        }
        for target_id in target_ids
    }
    signature_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    per_run: list[dict[str, Any]] = []
    adjacent_deltas: list[dict[str, Any]] = []

    for row in normalized_runs:
        attributed = row["attribution"]
        workflow = attributed["workflow_binding"]
        plan = attributed["plan_binding"]
        inventory = attributed["artifact_inventory"]
        receipt = attributed["validation_receipt"]
        selected = list(plan["selected_target_ids"])
        result_values = row["result_values"]
        for target_id in selected:
            stats = target_statistics[target_id]
            stats["plan_presence_count"] += 1
            if target_id in result_values:
                value = result_values[target_id]
                if value is True:
                    stats["caller_declared_success_count"] += 1
                    outcome = "CALLER_DECLARED_SUCCESS"
                elif value is False:
                    stats["caller_declared_failure_count"] += 1
                    outcome = "CALLER_DECLARED_FAILURE"
                else:
                    stats["caller_declared_unknown_value_count"] += 1
                    outcome = "CALLER_DECLARED_VALUE_UNKNOWN"
                stats["claims_by_run"].append({
                    "input_ordinal": row["input_ordinal"],
                    "run_id": workflow["run_id"],
                    "head_sha": workflow["head_sha"],
                    "outcome": outcome,
                })
            else:
                stats["no_target_result_claim_count"] += 1
                stats["claims_by_run"].append({
                    "input_ordinal": row["input_ordinal"],
                    "run_id": workflow["run_id"],
                    "head_sha": workflow["head_sha"],
                    "outcome": "NO_TARGET_RESULT_CLAIM",
                })

        signature_groups[row["target_set_sha256"]].append({
            "input_ordinal": row["input_ordinal"],
            "run_id": workflow["run_id"],
            "head_sha": workflow["head_sha"],
            "plan_sha256": plan["plan_sha256"],
            "selected_target_ids": sorted(selected),
        })

        per_run.append({
            "input_ordinal": row["input_ordinal"],
            "source_attribution_input_sha256": row["source_input_sha256"],
            "normalized_actions_snapshot_sha256": row["normalized_actions_snapshot_sha256"],
            "timestamp_anomalies": row["timestamp_anomalies"],
            "workflow_run": {
                "run_id": workflow["run_id"],
                "run_attempt": workflow["run_attempt"],
                "head_sha": workflow["head_sha"],
                "status": workflow["status"],
                "conclusion": workflow["conclusion"],
            },
            "plan": {
                "digest_valid_under_single_run_contract": plan["digest_valid"],
                "mode": plan["mode"],
                "plan_sha256": plan["plan_sha256"],
                "validation_map_sha256": plan["validation_map_sha256"],
                "selected_target_ids": selected,
                "target_set_sha256": row["target_set_sha256"],
            },
            "artifact_inventory": {
                "run_attempt_bound_to_actions_snapshot": True,
                "artifact_id": inventory["artifact_id"],
                "name": inventory["name"],
                "archive_sha256_as_supplied_unverified": inventory["artifact_sha256"],
                "files_complete_as_supplied": inventory["files_complete_as_supplied"],
                "files": inventory["files"],
            },
            "validation_receipt": {
                "presence": inventory["validation_receipt_presence"],
                "binding_status": receipt["binding_status"],
                "target_result_trust": receipt["target_result_trust"],
                "declared_target_results": receipt["declared_target_results"],
            },
        })

    for previous, current in zip(normalized_runs, normalized_runs[1:]):
        previous_attribution = previous["attribution"]
        current_attribution = current["attribution"]
        previous_targets = set(previous_attribution["plan_binding"]["selected_target_ids"])
        current_targets = set(current_attribution["plan_binding"]["selected_target_ids"])
        previous_results = previous["result_values"]
        current_results = current["result_values"]
        compared = sorted(previous_targets & current_targets)
        outcome_deltas = []
        for target_id in compared:
            old_value = previous_results.get(target_id)
            new_value = current_results.get(target_id)
            if old_value is None or new_value is None:
                change = "NO_COMPARABLE_RESULT_CLAIM"
            elif old_value is new_value:
                change = "CALLER_DECLARED_RESULT_UNCHANGED"
            else:
                change = "CALLER_DECLARED_RESULT_CHANGED"
            outcome_deltas.append({
                "target_id": target_id,
                "previous_caller_declared_successful": old_value,
                "current_caller_declared_successful": new_value,
                "change": change,
            })
        previous_run = previous_attribution["workflow_binding"]
        current_run = current_attribution["workflow_binding"]
        adjacent_deltas.append({
            "from_input_ordinal": previous["input_ordinal"],
            "to_input_ordinal": current["input_ordinal"],
            "from_run_id": previous_run["run_id"],
            "to_run_id": current_run["run_id"],
            "from_head_sha": previous_run["head_sha"],
            "to_head_sha": current_run["head_sha"],
            "added_target_ids": sorted(current_targets - previous_targets),
            "removed_target_ids": sorted(previous_targets - current_targets),
            "retained_target_ids": compared,
            "target_result_deltas": outcome_deltas,
        })

    repeated_coverage_signatures = []
    for signature, members in sorted(signature_groups.items()):
        if len(members) < 2:
            continue
        repeated_coverage_signatures.append({
            "target_set_sha256": signature,
            "classification": "REPEATED_COVERAGE_SET_NOT_EVIDENCE_OF_REDUNDANCY_OR_WASTE",
            "runs": members,
        })

    coverage_intersection = sorted(set(target_ids).intersection(*(
        set(row["attribution"]["plan_binding"]["selected_target_ids"])
        for row in normalized_runs
    )))
    attribution_tool_path = Path(__file__).with_name("toolbox_actions_validation_attribution.py")
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "single_run_attribution_helper_sha256": hashlib.sha256(attribution_tool_path.read_bytes()).hexdigest(),
        "source_binding": "CALLER_SUPPLIED_UNAUTHENTICATED_JSON",
        "shared_context": observed_context,
        "summary": {
            "run_count": len(per_run),
            "distinct_head_sha_count": len({row["workflow_run"]["head_sha"] for row in per_run}),
            "coverage_union_target_ids": target_ids,
            "coverage_intersection_target_ids": coverage_intersection,
            "repeated_coverage_signature_count": len(repeated_coverage_signatures),
            "target_result_claims_are_official_ci_evidence": False,
        },
        "runs": per_run,
        "adjacent_run_deltas": adjacent_deltas,
        "per_target": [target_statistics[target_id] for target_id in target_ids],
        "repeated_coverage_signatures": repeated_coverage_signatures,
        "timestamp_anomalies": timestamp_anomalies,
        "non_claims": {
            "github_source_authenticated": False,
            "artifact_archive_bytes_verified_by_this_tool": False,
            "component_validation_receipt_officially_verified": False,
            "missing_receipt_means_target_failure": False,
            "required_check_sufficiency_or_satisfaction_interpreted": False,
            "repeated_coverage_means_wasted_or_redundant_work": False,
            "billable_minutes_cost_or_savings_estimated": False,
            "merge_or_release_authorized": False,
        },
        "claim_ceiling": (
            "The tool validates caller-supplied plan, run, artifact-inventory, and optional receipt shapes and bindings "
            "using the existing single-run attribution contract, then compares selected target sets and caller-declared "
            "receipt values. It does not authenticate GitHub sources, verify official CI, infer target results without "
            "receipt content, evaluate required checks, attribute waste or billing, or authorize merge or release."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON envelope from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = analyze_validation_target_coverage(raw)
    except InputError as exc:
        print("ACTIONS_VALIDATION_TARGET_COVERAGE_INVALID", file=sys.stderr)
        print("- " + str(exc), file=sys.stderr)
        return 2
    sys.stdout.write(canonical_json(result) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
