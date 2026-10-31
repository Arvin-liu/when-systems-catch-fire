#!/usr/bin/env python3
"""Classify caller-supplied GitHub check-run observations for exact SHA/context/App matches."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


TOOL_ID = "maintenance.inspect_exact_head_check_observations"
TOOL_VERSION = "0.1.0"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_CHECK_RUNS = 2000
MAX_REQUESTED_CONTEXTS = 100
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
CHECK_STATUSES = {"requested", "queued", "waiting", "pending", "in_progress", "completed"}
CHECK_CONCLUSIONS = {
    "action_required", "cancelled", "failure", "neutral", "skipped", "stale",
    "startup_failure", "success", "timed_out",
}
OUTCOMES = {
    "OBSERVED_SUCCESS",
    "OBSERVED_NON_SUCCESS",
    "PENDING",
    "UNKNOWN_PROVIDER_STATE",
    "SNAPSHOT_INCOMPLETE",
    "CONTEXT_NOT_OBSERVED",
    "STALE_SHA_ONLY",
    "WRONG_APP_ONLY",
    "DUPLICATE_AMBIGUOUS",
}


class InputError(ValueError):
    """Raised when a supplied check-run snapshot is malformed or ambiguous."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise InputError("duplicate JSON key: " + key)
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise InputError("non-finite JSON constant is not permitted: " + value)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: Any, path: str) -> str:
    if not isinstance(value, str) or not SHA40_RE.fullmatch(value):
        raise InputError(path + " must be a lowercase 40-character commit SHA")
    return value


def _positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InputError(path + " must be a positive integer")
    return value


def _nonnegative_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InputError(path + " must be a nonnegative integer")
    return value


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(path + " must be a nonblank string")
    return value


def _exact_object(value: Any, path: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(path + " must be an object")
    missing = keys - set(value)
    extra = set(value) - keys
    if missing:
        raise InputError(path + " is missing keys: " + ", ".join(sorted(missing)))
    if extra:
        raise InputError(path + " has unsupported keys: " + ", ".join(sorted(extra)))
    return value


def _validate_payload(payload: Any) -> dict[str, Any]:
    payload = _exact_object(payload, "input", {
        "schema_version", "expected_head_sha", "check_runs_complete", "requested_contexts", "check_runs_snapshot",
    })
    if payload.get("schema_version") != "toolbox-actions-check-observations-input-r0":
        raise InputError("unsupported schema_version")
    expected_sha = _sha(payload.get("expected_head_sha"), "expected_head_sha")
    complete = payload.get("check_runs_complete")
    if not isinstance(complete, bool):
        raise InputError("check_runs_complete must be a boolean caller assertion")

    contexts = payload.get("requested_contexts")
    if (
        not isinstance(contexts, list)
        or not contexts
        or len(contexts) > MAX_REQUESTED_CONTEXTS
    ):
        raise InputError("requested_contexts must contain 1 to " + str(MAX_REQUESTED_CONTEXTS) + " rows")
    normalized_contexts: list[dict[str, Any]] = []
    seen_contexts: set[tuple[str, int]] = set()
    for index, raw in enumerate(contexts):
        path = f"requested_contexts[{index}]"
        raw = _exact_object(raw, path, {"name", "app_id"})
        name = _nonblank(raw.get("name"), path + ".name")
        app_id = _positive_int(raw.get("app_id"), path + ".app_id")
        key = (name, app_id)
        if key in seen_contexts:
            raise InputError(path + " duplicates a requested name/app_id pair")
        seen_contexts.add(key)
        normalized_contexts.append({"name": name, "app_id": app_id})

    snapshot = payload.get("check_runs_snapshot")
    snapshot = _exact_object(snapshot, "check_runs_snapshot", {"total_count", "check_runs"})
    total_count = _nonnegative_int(snapshot.get("total_count"), "check_runs_snapshot.total_count")
    rows = snapshot.get("check_runs")
    if not isinstance(rows, list) or len(rows) > MAX_CHECK_RUNS:
        raise InputError("check_runs_snapshot.check_runs must be a bounded array")
    if total_count < len(rows):
        raise InputError("check_runs_snapshot.total_count cannot be below the supplied row count")
    if complete and total_count != len(rows):
        raise InputError("a complete snapshot must supply exactly total_count check runs")

    normalized_runs: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for index, raw in enumerate(rows):
        path = f"check_runs_snapshot.check_runs[{index}]"
        raw = _exact_object(raw, path, {"id", "name", "head_sha", "status", "conclusion", "app"})
        run_id = _positive_int(raw.get("id"), path + ".id")
        if run_id in seen_ids:
            raise InputError(path + " duplicates a check-run id")
        seen_ids.add(run_id)
        name = _nonblank(raw.get("name"), path + ".name")
        head_sha = _sha(raw.get("head_sha"), path + ".head_sha")
        status = _nonblank(raw.get("status"), path + ".status")
        if status not in CHECK_STATUSES:
            raise InputError(path + ".status is not a recognized GitHub check-run status")
        conclusion = raw.get("conclusion")
        if conclusion is not None and (not isinstance(conclusion, str) or conclusion not in CHECK_CONCLUSIONS):
            raise InputError(path + ".conclusion is not a recognized GitHub check-run conclusion or null")
        app = raw.get("app")
        app_id: int | None = None
        app_slug: str | None = None
        if app is not None:
            app = _exact_object(app, path + ".app", {"id", "slug"})
            raw_app_id = app.get("id")
            if raw_app_id is not None:
                app_id = _positive_int(raw_app_id, path + ".app.id")
            raw_slug = app.get("slug")
            if raw_slug is not None:
                app_slug = _nonblank(raw_slug, path + ".app.slug")
        normalized_runs.append({
            "id": run_id,
            "name": name,
            "head_sha": head_sha,
            "status": status,
            "conclusion": conclusion,
            "app_id": app_id,
            "app_slug": app_slug,
        })

    return {
        "expected_head_sha": expected_sha,
        "check_runs_complete": complete,
        "requested_contexts": normalized_contexts,
        "total_count": total_count,
        "check_runs": normalized_runs,
    }


def _single_run_outcome(run: dict[str, Any]) -> str:
    if run["status"] != "completed":
        return "PENDING"
    conclusion = run["conclusion"]
    if conclusion == "success":
        return "OBSERVED_SUCCESS"
    if conclusion in CHECK_CONCLUSIONS:
        return "OBSERVED_NON_SUCCESS"
    return "UNKNOWN_PROVIDER_STATE"


def classify_check_observations(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input exceeds " + str(MAX_INPUT_BYTES) + " bytes")
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except UnicodeDecodeError as exc:
        raise InputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise InputError("input is malformed JSON") from exc

    request = _validate_payload(payload)
    requested: list[dict[str, Any]] = []
    counts = {outcome: 0 for outcome in sorted(OUTCOMES)}
    for context in request["requested_contexts"]:
        by_name = [run for run in request["check_runs"] if run["name"] == context["name"]]
        exact_sha = [run for run in by_name if run["head_sha"] == request["expected_head_sha"]]
        exact_app = [run for run in exact_sha if run["app_id"] == context["app_id"]]
        if not request["check_runs_complete"]:
            outcome = "SNAPSHOT_INCOMPLETE"
        elif not by_name:
            outcome = "CONTEXT_NOT_OBSERVED"
        elif not exact_sha:
            outcome = "STALE_SHA_ONLY"
        elif any(run["app_id"] is None for run in exact_sha):
            outcome = "UNKNOWN_PROVIDER_STATE"
        elif not exact_app:
            outcome = "WRONG_APP_ONLY"
        elif len(exact_app) > 1:
            outcome = "DUPLICATE_AMBIGUOUS"
        else:
            outcome = _single_run_outcome(exact_app[0])
        counts[outcome] += 1
        single = exact_app[0] if len(exact_app) == 1 and request["check_runs_complete"] else None
        requested.append({
            "name": context["name"],
            "expected_app_id": context["app_id"],
            "observation": outcome,
            "same_name_observation_count": len(by_name),
            "exact_head_sha_observation_count": len(exact_sha),
            "exact_name_sha_app_match_count": len(exact_app),
            "matching_check_run_ids": [run["id"] for run in exact_app],
            "stale_head_shas": sorted({run["head_sha"] for run in by_name if run["head_sha"] != request["expected_head_sha"]}),
            "app_ids_observed_on_exact_head": sorted({run["app_id"] for run in exact_sha if run["app_id"] is not None}),
            "observed_status": single["status"] if single is not None else None,
            "observed_conclusion": single["conclusion"] if single is not None else None,
        })

    return {
        "schema_version": "toolbox-actions-check-observations-output-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "expected_head_sha": request["expected_head_sha"],
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "check_runs_snapshot": {
            "total_count": request["total_count"],
            "supplied_count": len(request["check_runs"]),
            "complete_caller_assertion": request["check_runs_complete"],
        },
        "outcome_counts": counts,
        "requested_contexts": requested,
        "non_claims": {
            "snapshot_source_authenticated": False,
            "requested_contexts_authenticated": False,
            "branch_protection_binding": "NOT_ESTABLISHED",
            "required_check_satisfaction_interpreted": False,
            "merge_or_release_authorized": False,
            "ci_or_scientific_validity_established": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON request from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        receipt = classify_check_observations(raw)
    except (InputError, OSError) as exc:
        print("ACTIONS_CHECK_OBSERVATIONS_INVALID: " + str(exc), file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
