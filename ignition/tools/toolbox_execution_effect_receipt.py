#!/usr/bin/env python3
"""Check caller-declared bindings between one tool run and later outcome observations."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator


TOOL_ID = "maintenance.preflight_execution_effect_receipt"
TOOL_VERSION = "0.1.0"
MAX_INPUT_BYTES = 131_072
MAX_FINDINGS = 64
MAX_REPOSITORY_PATHS = 32
MAX_FILE_BYTES = 1_048_576
MAX_TOTAL_REPOSITORY_BYTES = 4_194_304
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/operations/toolbox-execution-effect-receipt-input-r0.schema.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
CLAIM_CEILING = (
    "Checks schema, chronology, and equality among caller-supplied run, tool/version/source, input/output, environment, "
    "observer, and failure-record references. It does not read or authenticate the referenced bytes, source, actor, "
    "environment, run, or observation; independently establish an effect; execute a tool; authorize an action; "
    "or establish scientific, production, or release truth."
)


class InputError(ValueError):
    """Raised when bounded JSON cannot be safely parsed or validated."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InputError("NONFINITE_JSON_NUMBER:" + value)


def _parse_time(value: Any, path: str, findings: list[dict[str, str]]) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not RFC3339_RE.fullmatch(value):
        findings.append({"code": "TIMESTAMP_INVALID", "path": path})
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        findings.append({"code": "TIMESTAMP_INVALID", "path": path})
        return None
    if parsed.tzinfo is None:
        findings.append({"code": "TIMESTAMP_INVALID", "path": path})
        return None
    return parsed


def _schema_findings(payload: Any) -> list[dict[str, str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""),
    )
    return [
        {
            "code": "INPUT_SCHEMA_INVALID",
            "path": "$" + ("/" + "/".join(map(str, error.absolute_path)) if error.absolute_path else ""),
        }
        for error in errors[:MAX_FINDINGS]
    ]


def _safe_repo_parts(relative_path: str) -> tuple[str, ...] | None:
    if not isinstance(relative_path, str) or "\\" in relative_path or relative_path.startswith("/"):
        return None
    parts = tuple(relative_path.split("/"))
    if len(parts) < 2 or parts[0] != "ignition" or any(part in {"", ".", ".."} for part in parts):
        return None
    if any(not re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in parts):
        return None
    return parts


def _observe_repo_file(relative_path: str, *, remaining_budget: int) -> dict[str, Any]:
    """Hash one regular file below ignition/ using no-follow directory-relative opens."""
    parts = _safe_repo_parts(relative_path)
    if parts is None:
        return {"path": relative_path, "state": "PATH_REJECTED", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptors: list[int] = []
    try:
        directory_fd = os.open(str(REPO_ROOT), flags)
        descriptors.append(directory_fd)
        for component in parts[:-1]:
            try:
                info = os.stat(component, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                return {"path": relative_path, "state": "MISSING", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
            if stat.S_ISLNK(info.st_mode):
                return {"path": relative_path, "state": "SYMLINK", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
            if not stat.S_ISDIR(info.st_mode):
                return {"path": relative_path, "state": "NOT_REGULAR_FILE", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
            directory_fd = os.open(component, flags, dir_fd=directory_fd)
            descriptors.append(directory_fd)
        leaf = parts[-1]
        try:
            info = os.stat(leaf, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return {"path": relative_path, "state": "MISSING", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
        if stat.S_ISLNK(info.st_mode):
            return {"path": relative_path, "state": "SYMLINK", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
        if not stat.S_ISREG(info.st_mode):
            return {"path": relative_path, "state": "NOT_REGULAR_FILE", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
        if info.st_size > MAX_FILE_BYTES or info.st_size > remaining_budget:
            return {"path": relative_path, "state": "TOO_LARGE", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
        file_fd = os.open(leaf, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
        descriptors.append(file_fd)
        opened = os.fstat(file_fd)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            return {"path": relative_path, "state": "READ_ERROR", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
        digest = hashlib.sha256()
        count = 0
        while True:
            chunk = os.read(file_fd, min(65_536, MAX_FILE_BYTES + 1 - count))
            if not chunk:
                break
            digest.update(chunk)
            count += len(chunk)
            if count > MAX_FILE_BYTES or count > remaining_budget:
                return {"path": relative_path, "state": "TOO_LARGE", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
        return {"path": relative_path, "state": "PRESENT", "sha256": digest.hexdigest(), "matches_baseline": None, "change": "UNKNOWN", "bytes_read": count}
    except FileNotFoundError:
        return {"path": relative_path, "state": "MISSING", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
    except OSError:
        return {"path": relative_path, "state": "READ_ERROR", "sha256": None, "matches_baseline": None, "change": "UNKNOWN", "bytes_read": 0}
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def evaluate(payload: Any) -> dict[str, Any]:
    """Evaluate caller-declared receipt relations without accessing referenced evidence."""
    if not isinstance(payload, dict):
        raise InputError("INPUT_MUST_BE_OBJECT")
    if _schema_findings(payload):
        raise InputError("INPUT_SCHEMA_INVALID")

    execution = payload["execution"]
    observations = payload["observations"]
    findings: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    repository_observations: list[dict[str, Any]] = []
    total_bytes_read = 0

    def add(target: list[dict[str, str]], code: str, path: str) -> None:
        row = {"code": code, "path": path}
        if row not in target and len(target) < MAX_FINDINGS:
            target.append(row)

    status = execution["status"]
    is_completed = status == "COMPLETED"
    if status == "NOT_RUN":
        if any(execution[key] is not None for key in (
            "run_id", "tool_id", "tool_version", "source_sha256", "input_sha256", "output_sha256",
            "environment_ref", "executor_actor_ref", "started_at_utc", "completed_at_utc", "exit_code",
        )):
            add(findings, "NONRUN_STATUS_HAS_RUN_FIELDS", "$/execution")
        if observations:
            add(findings, "OBSERVATION_WITHOUT_RECORDED_RUN", "$/observations")
    elif status == "UNKNOWN" and observations:
        add(findings, "OBSERVATION_WITHOUT_CONFIRMED_COMPLETED_RUN", "$/observations")
    elif status == "STARTED":
        required = (
            "run_id", "tool_id", "tool_version", "source_sha256", "input_sha256",
            "environment_ref", "executor_actor_ref", "started_at_utc",
        )
        for key in required:
            if execution[key] is None:
                add(findings, "STARTED_RUN_FIELD_MISSING", "$/execution/" + key)
        if observations:
            add(findings, "OBSERVATION_WITHOUT_COMPLETED_RUN", "$/observations")

    if payload["repository_paths"] and not is_completed:
        add(findings, "REPOSITORY_OBSERVATION_WITHOUT_COMPLETED_RUN", "$/repository_paths")
    elif is_completed:
        seen_paths: set[str] = set()
        for index, expected in enumerate(payload["repository_paths"]):
            path = expected["path"]
            if path in seen_paths:
                add(findings, "DUPLICATE_REPOSITORY_PATH", f"$/repository_paths/{index}/path")
                continue
            seen_paths.add(path)
            observed = _observe_repo_file(path, remaining_budget=MAX_TOTAL_REPOSITORY_BYTES - total_bytes_read)
            observed["baseline_state"] = expected["baseline_state"]
            observed["baseline_sha256"] = expected["baseline_sha256"]
            if observed["state"] == "PRESENT":
                if expected["baseline_state"] == "PRESENT":
                    observed["matches_baseline"] = observed["sha256"] == expected["baseline_sha256"]
                    observed["change"] = "UNCHANGED" if observed["matches_baseline"] else "CHANGED"
                else:
                    observed["matches_baseline"] = False
                    observed["change"] = "ADDED"
                total_bytes_read += observed["bytes_read"]
            elif observed["state"] == "MISSING":
                if expected["baseline_state"] == "MISSING":
                    observed["matches_baseline"] = True
                    observed["change"] = "UNCHANGED"
                else:
                    observed["matches_baseline"] = False
                    observed["change"] = "REMOVED"
            else:
                add(findings, "REPOSITORY_PATH_OBSERVATION_INCOMPLETE", f"$/repository_paths/{index}/path")
            repository_observations.append(observed)

    repository_changes = [row for row in repository_observations if row["matches_baseline"] is False]
    repository_complete = all(row["matches_baseline"] is not None for row in repository_observations)
    if not repository_observations:
        repository_effect_status = "NOT_REQUESTED"
    elif not repository_complete:
        repository_effect_status = "INCOMPLETE"
    elif repository_changes:
        repository_effect_status = "DIFFERENCE_FROM_DECLARED_BASELINE_OBSERVED"
    else:
        repository_effect_status = "NO_DIFFERENCE_FROM_DECLARED_BASELINE_OBSERVED"

    started = _parse_time(execution["started_at_utc"], "$/execution/started_at_utc", findings)
    completed = _parse_time(execution["completed_at_utc"], "$/execution/completed_at_utc", findings)
    if status == "COMPLETED":
        required = (
            "run_id", "tool_id", "tool_version", "source_sha256", "input_sha256", "environment_ref",
            "executor_actor_ref", "started_at_utc", "completed_at_utc", "exit_code",
        )
        for key in required:
            if execution[key] is None:
                add(findings, "COMPLETED_RUN_FIELD_MISSING", "$/execution/" + key)
        if started is not None and completed is not None and started > completed:
            add(findings, "RUN_COMPLETION_PRECEDES_START", "$/execution/completed_at_utc")

    observation_ids: set[str] = set()
    effect_states: set[str] = set()
    matched_effect_observations: list[dict[str, Any]] = []
    matched_failure_observations: list[dict[str, Any]] = []
    expected_fields = (
        ("run_id", "run_id", "OBSERVATION_RUN_ID_MISMATCH"),
        ("tool_id", "tool_id", "OBSERVATION_TOOL_ID_MISMATCH"),
        ("tool_version", "tool_version", "OBSERVATION_TOOL_VERSION_MISMATCH"),
        ("source_sha256", "source_sha256", "OBSERVATION_SOURCE_DIGEST_MISMATCH"),
        ("input_sha256", "input_sha256", "OBSERVATION_INPUT_DIGEST_MISMATCH"),
        ("output_sha256", "output_sha256", "OBSERVATION_OUTPUT_DIGEST_MISMATCH"),
        ("environment_ref", "environment_ref", "OBSERVATION_ENVIRONMENT_MISMATCH"),
    )
    for index, observation in enumerate(observations):
        base = f"$/observations/{index}"
        observation_id = observation["observation_id"]
        if observation_id in observation_ids:
            add(findings, "DUPLICATE_OBSERVATION_ID", base + "/observation_id")
        observation_ids.add(observation_id)
        if not is_completed:
            continue
        matched = True
        for observation_key, execution_key, code in expected_fields:
            if observation[observation_key] != execution[execution_key]:
                matched = False
                add(findings, code, base + "/" + observation_key)
        observed_at = _parse_time(observation["observed_at_utc"], base + "/observed_at_utc", findings)
        if completed is not None and observed_at is not None and observed_at < completed:
            matched = False
            add(findings, "OBSERVATION_PRECEDES_COMPLETION", base + "/observed_at_utc")
        if observation["observer_actor_ref"] == execution["executor_actor_ref"]:
            add(warnings, "OBSERVER_IS_EXECUTOR_SELF_REPORT", base + "/observer_actor_ref")
        if matched and observation["kind"] == "EFFECT":
            matched_effect_observations.append(observation)
            if observation["effect_state"] is not None:
                effect_states.add(observation["effect_state"])
        if matched and observation["kind"] == "FAILURE_RECORD":
            matched_failure_observations.append(observation)

    if len(effect_states - {"UNKNOWN"}) > 1:
        add(findings, "CONTRADICTORY_EFFECT_OBSERVATIONS", "$/observations")

    failure_evidence_missing = (
        status == "COMPLETED"
        and execution["exit_code"] not in (None, 0)
        and not any(row["first_failure_preserved"] is True for row in matched_failure_observations)
    )
    if failure_evidence_missing:
        add(findings, "FAILURE_EVIDENCE_NOT_PRESERVED", "$/observations")

    if findings:
        outcome_status = "BINDING_OR_COMPLETENESS_FINDINGS"
    elif status == "NOT_RUN":
        outcome_status = "NO_RUN_RECORDED"
    elif status == "UNKNOWN":
        outcome_status = "EXECUTION_UNKNOWN"
    elif status == "STARTED":
        outcome_status = "RUN_STARTED_OUTCOME_NOT_AVAILABLE"
    elif matched_effect_observations and effect_states - {"UNKNOWN"}:
        outcome_status = (
            "OUTCOME_WITH_UNRESOLVED_OBSERVATION"
            if "UNKNOWN" in effect_states
            else "OUTCOME_RECORDED_CALLER_DECLARATION"
        )
    else:
        outcome_status = "OUTCOME_UNKNOWN"

    return {
        "schema_version": "toolbox-execution-effect-receipt-output-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "task_ref": payload["task_ref"],
        "outcome_status": outcome_status,
        "execution_status": status,
        "run_id": execution["run_id"],
        "bound_observation_ids": [row["observation_id"] for row in matched_effect_observations + matched_failure_observations],
        "effect_states": sorted(effect_states),
        "failure_preservation_declared": bool(
            matched_failure_observations
            and any(row["first_failure_preserved"] is True for row in matched_failure_observations)
        ),
        "repository_effect_status": repository_effect_status,
        "repository_state_observations": repository_observations,
        "repository_bytes_read": total_bytes_read,
        "findings": findings,
        "warnings": warnings,
        "source_authentication": "NOT_PERFORMED",
        "referenced_bytes_read": False,
        "observer_independence": "ACTOR_REF_COMPARISON_ONLY",
        "repository_state_observer": "LOCAL_READ_ONLY_RECHECK_OF_IGNITION_PATHS",
        "causal_attribution": "NOT_ESTABLISHED",
        "outcome_truth": "NOT_ESTABLISHED",
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded UTF-8 JSON object from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        print(json.dumps({"error": "INPUT_TOO_LARGE"}), file=sys.stderr)
        return 2
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        result = evaluate(payload)
        result["input_sha256"] = hashlib.sha256(raw).hexdigest()
        result["tool_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except (UnicodeDecodeError, json.JSONDecodeError, InputError, OSError) as exc:
        error = exc.args[0] if isinstance(exc, InputError) and exc.args else "INPUT_INVALID"
        print(json.dumps({"error": error}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
