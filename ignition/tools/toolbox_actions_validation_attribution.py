#!/usr/bin/env python3
"""Bind a supplied component-validation plan, Actions timeline and target receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from toolbox_actions_step_timeline import InputError as TimelineInputError
from toolbox_actions_step_timeline import summarize_snapshot


TOOL_ID = "maintenance.attribute_actions_validation_evidence"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_SELECTED_TARGETS = 500
MAX_ARTIFACT_FILES = 100
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
TARGET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
PLAN_FILE = "component-validation-plan.json"
RECEIPT_FILE = "component-validation-receipt.json"


class InputError(ValueError):
    """Raised when caller-supplied snapshots cannot be safely associated."""


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


def _sha(value: Any, pattern: re.Pattern[str], path: str) -> str:
    result = _nonblank(value, path)
    if not pattern.fullmatch(result):
        raise InputError(path + " must be a lowercase hexadecimal digest of the required length")
    return result


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _validate_plan(plan: Any) -> dict[str, Any]:
    value = _object(plan, "validation_plan")
    if value.get("schema_version") != "1.0.0":
        raise InputError("validation_plan.schema_version must be 1.0.0")
    mode = value.get("mode")
    if mode not in {"TARGETED", "FULL"}:
        raise InputError("validation_plan.mode must be TARGETED or FULL")
    plan_hash = _sha(value.get("plan_sha256"), SHA64_RE, "validation_plan.plan_sha256")
    unsigned_plan = dict(value)
    unsigned_plan.pop("plan_sha256", None)
    if digest_json(unsigned_plan) != plan_hash:
        raise InputError("validation_plan.plan_sha256 does not match its canonical content")

    source = _object(value.get("source"), "validation_plan.source")
    base_sha = _sha(source.get("base_sha"), SHA40_RE, "validation_plan.source.base_sha")
    head_sha = _sha(source.get("head_sha"), SHA40_RE, "validation_plan.source.head_sha")
    validation_sha = _sha(source.get("validation_sha"), SHA40_RE, "validation_plan.source.validation_sha")
    map_hash = _sha(value.get("validation_map_sha256"), SHA64_RE, "validation_plan.validation_map_sha256")
    target_ids = value.get("selected_target_ids")
    if (
        not isinstance(target_ids, list)
        or not target_ids
        or len(target_ids) > MAX_SELECTED_TARGETS
        or any(not isinstance(item, str) or not TARGET_ID_RE.fullmatch(item) for item in target_ids)
        or len(target_ids) != len(set(target_ids))
    ):
        raise InputError("validation_plan.selected_target_ids must be a nonempty unique list of bounded IDs")
    return {
        "mode": mode,
        "plan_sha256": plan_hash,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "validation_sha": validation_sha,
        "validation_map_sha256": map_hash,
        "selected_target_ids": list(target_ids),
    }


def _validate_artifact_inventory(inventory: Any) -> dict[str, Any]:
    value = _object(inventory, "artifact_inventory")
    run_id = _positive_int(value.get("run_id"), "artifact_inventory.run_id")
    attempt = _positive_int(value.get("run_attempt"), "artifact_inventory.run_attempt")
    artifact_id = _positive_int(value.get("artifact_id"), "artifact_inventory.artifact_id")
    name = _nonblank(value.get("name"), "artifact_inventory.name")
    digest = _sha(value.get("artifact_sha256"), SHA64_RE, "artifact_inventory.artifact_sha256")
    files_complete = value.get("files_complete")
    if not isinstance(files_complete, bool):
        raise InputError("artifact_inventory.files_complete must be a boolean")
    files = value.get("files")
    if (
        not isinstance(files, list)
        or len(files) > MAX_ARTIFACT_FILES
        or any(not isinstance(item, str) or item != Path(item).name or item in {"", ".", ".."} for item in files)
        or len(files) != len(set(files))
    ):
        raise InputError("artifact_inventory.files must be a bounded unique list of file basenames")
    if PLAN_FILE not in files:
        raise InputError("artifact_inventory.files must include " + PLAN_FILE)
    if not files_complete and RECEIPT_FILE not in files and value.get("validation_receipt") is not None:
        raise InputError("a supplied receipt must be listed in artifact_inventory.files")
    return {
        "run_id": run_id,
        "run_attempt": attempt,
        "artifact_id": artifact_id,
        "name": name,
        "artifact_sha256": digest,
        "files_complete": files_complete,
        "files": list(files),
    }


def _validate_receipt(receipt: Any, plan: dict[str, Any]) -> dict[str, Any]:
    value = _object(receipt, "validation_receipt")
    if value.get("schema_version") != "1.0.0":
        raise InputError("validation_receipt.schema_version must be 1.0.0")
    receipt_hash = _sha(value.get("receipt_sha256"), SHA64_RE, "validation_receipt.receipt_sha256")
    unsigned_receipt = dict(value)
    unsigned_receipt.pop("receipt_sha256", None)
    if digest_json(unsigned_receipt) != receipt_hash:
        raise InputError("validation_receipt.receipt_sha256 does not match its canonical content")
    for field in ("base_sha", "head_sha", "validation_sha", "plan_sha256", "validation_map_sha256"):
        if value.get(field) != plan[field]:
            raise InputError("validation_receipt." + field + " does not match the supplied plan")
    results = value.get("target_results")
    if not isinstance(results, list):
        raise InputError("validation_receipt.target_results must be an array")
    result_ids = [row.get("target_id") if isinstance(row, dict) else None for row in results]
    if result_ids != plan["selected_target_ids"]:
        raise InputError("validation_receipt target IDs do not exactly match the supplied plan")
    return {
        "binding_status": "DIGEST_AND_PLAN_BINDING_MATCH",
        "receipt_sha256": receipt_hash,
        "declared_target_results": [
            {
                "target_id": row["target_id"],
                "caller_declared_successful": row.get("successful") if isinstance(row.get("successful"), bool) else None,
            }
            for row in results
        ],
        "target_result_trust": "CALLER_SUPPLIED_DECLARATIONS_NOT_OFFICIAL_CI_VALIDATION",
    }


def attribute_validation_evidence(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input exceeds " + str(MAX_INPUT_BYTES) + " bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise InputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise InputError("input must be valid JSON") from exc

    root = _object(payload, "root")
    unknown_root_keys = set(root) - {
        "schema_version", "validation_plan", "actions_snapshot", "artifact_inventory", "validation_receipt",
    }
    if unknown_root_keys:
        raise InputError("root contains unsupported fields: " + ", ".join(sorted(unknown_root_keys)))
    if root.get("schema_version") != "toolbox-actions-validation-attribution-input-r0":
        raise InputError("unsupported input schema_version")
    plan = _validate_plan(root.get("validation_plan"))
    inventory = _validate_artifact_inventory(root.get("artifact_inventory"))
    snapshot = _object(root.get("actions_snapshot"), "actions_snapshot")
    try:
        timeline = summarize_snapshot(canonical_json(snapshot).encode("utf-8"))
    except TimelineInputError as exc:
        raise InputError("actions_snapshot: " + str(exc)) from exc

    run = timeline["workflow_run"]
    if run["id"] != inventory["run_id"]:
        raise InputError("workflow_run.id does not match artifact_inventory.run_id")
    if run["run_attempt"] != inventory["run_attempt"]:
        raise InputError("workflow_run.run_attempt does not match artifact_inventory.run_attempt")
    if run["head_sha"] != plan["head_sha"]:
        raise InputError("workflow_run.head_sha does not match validation_plan.source.head_sha")

    raw_run = snapshot["workflow_run"]
    pull_requests = raw_run.get("pull_requests")
    base_binding = "NOT_SUPPLIED_IN_WORKFLOW_RUN_SNAPSHOT"
    if pull_requests is not None:
        if not isinstance(pull_requests, list):
            raise InputError("actions_snapshot.workflow_run.pull_requests must be an array when present")
        supplied_bases = []
        for index, pull_request in enumerate(pull_requests):
            pr = _object(pull_request, "actions_snapshot.workflow_run.pull_requests[{}]".format(index))
            base = pr.get("base")
            if base is not None:
                base_object = _object(base, "actions_snapshot.workflow_run.pull_requests[{}].base".format(index))
                if base_object.get("sha") is not None:
                    supplied_bases.append(_sha(
                        base_object["sha"], SHA40_RE,
                        "actions_snapshot.workflow_run.pull_requests[{}].base.sha".format(index),
                    ))
        if supplied_bases:
            if any(item != plan["base_sha"] for item in supplied_bases):
                raise InputError("workflow pull request base SHA does not match validation_plan.source.base_sha")
            base_binding = "SUPPLIED_PULL_REQUEST_BASE_MATCHES_PLAN"

    receipt_input = root.get("validation_receipt")
    receipt_filename_listed = RECEIPT_FILE in inventory["files"]
    if receipt_input is not None and not receipt_filename_listed:
        raise InputError("validation_receipt was supplied but is absent from artifact_inventory.files")
    if receipt_input is not None:
        receipt_summary = _validate_receipt(receipt_input, plan)
        receipt_presence = "CONTENT_SUPPLIED_AND_BOUND"
    elif receipt_filename_listed:
        receipt_summary = {
            "binding_status": "CONTENT_NOT_SUPPLIED",
            "receipt_sha256": None,
            "declared_target_results": [],
            "target_result_trust": "NO_TARGET_RESULT_CLAIM",
        }
        receipt_presence = "LISTED_BUT_CONTENT_NOT_SUPPLIED"
    elif inventory["files_complete"]:
        receipt_summary = {
            "binding_status": "NO_RECEIPT_CONTENT",
            "receipt_sha256": None,
            "declared_target_results": [],
            "target_result_trust": "NO_TARGET_RESULT_CLAIM",
        }
        receipt_presence = "ABSENT_FROM_SUPPLIED_COMPLETE_FILE_LIST"
    else:
        receipt_summary = {
            "binding_status": "PRESENCE_UNKNOWN",
            "receipt_sha256": None,
            "declared_target_results": [],
            "target_result_trust": "NO_TARGET_RESULT_CLAIM",
        }
        receipt_presence = "UNKNOWN_IN_INCOMPLETE_FILE_LIST"

    timeline_tool_path = Path(__file__).with_name("toolbox_actions_step_timeline.py")
    return {
        "schema_version": "toolbox-actions-validation-attribution-output-r0",
        "tool_id": TOOL_ID,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "timeline_helper_sha256": hashlib.sha256(timeline_tool_path.read_bytes()).hexdigest(),
        "source_binding": "CALLER_SUPPLIED_UNAUTHENTICATED_JSON",
        "plan_binding": {
            "digest_valid": True,
            "mode": plan["mode"],
            "plan_sha256": plan["plan_sha256"],
            "base_sha": plan["base_sha"],
            "head_sha": plan["head_sha"],
            "validation_sha": plan["validation_sha"],
            "validation_sha_scope": "PLAN_ONLY_NOT_COMPARED_TO_WORKFLOW_RUN_HEAD",
            "validation_map_sha256": plan["validation_map_sha256"],
            "selected_target_ids": plan["selected_target_ids"],
        },
        "workflow_binding": {
            "run_id": run["id"],
            "run_attempt": run["run_attempt"],
            "head_sha": run["head_sha"],
            "head_sha_matches_plan": True,
            "base_sha_binding": base_binding,
            "event": run["event"],
            "status": run["status"],
            "conclusion": run["conclusion"],
        },
        "artifact_inventory": {
            "artifact_id": inventory["artifact_id"],
            "name": inventory["name"],
            "artifact_sha256": inventory["artifact_sha256"],
            "files_complete_as_supplied": inventory["files_complete"],
            "files": inventory["files"],
            "validation_receipt_presence": receipt_presence,
        },
        "validation_receipt": receipt_summary,
        "observed_jobs": [
            {
                "id": row["id"],
                "name": row["name"],
                "status": row["status"],
                "conclusion": row["conclusion"],
                "observed_elapsed_seconds": row["observed_elapsed_seconds"],
            }
            for row in timeline["jobs"]
        ],
        "timeline_summary": timeline["summary"],
        "snapshot_completeness": timeline["snapshot"],
        "non_claims": {
            "github_source_authenticated": False,
            "component_validation_receipt_officially_verified": False,
            "selected_target_success_inferred_without_receipt": False,
            "required_check_satisfaction_interpreted": False,
            "billable_minutes_cost_or_savings_estimated": False,
            "merge_or_release_authorized": False,
        },
        "claim_ceiling": "Digest and identity alignment of caller-supplied plan, Actions snapshot, artifact file list and optional receipt only; job intervals remain source observations, target receipt claims are not official CI validation, and no billing, gate, merge or release conclusion is made.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON envelope from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = attribute_validation_evidence(raw)
    except InputError as exc:
        print("ACTIONS_VALIDATION_ATTRIBUTION_INVALID", file=sys.stderr)
        print("- " + str(exc), file=sys.stderr)
        return 2
    sys.stdout.write(canonical_json(result) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
