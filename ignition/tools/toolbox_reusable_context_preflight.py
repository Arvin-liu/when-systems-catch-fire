#!/usr/bin/env python3
"""Preflight caller-selected derived context cards for bounded local reuse.

The tool checks declared access state, source identity/version/scope and exact
local source bytes. It does not discover, create, persist, or semantically
validate context cards, and it never treats derived context as raw evidence.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
TOOL_ID = "knowledge.preflight_reusable_context"
TOOL_VERSION = "0.2.0"
MAX_REQUEST_BYTES = 128_000
MAX_SOURCE_BYTES_PER_FILE = 1_000_000
MAX_TOTAL_SOURCE_BYTES = 5_000_000
MAX_CONTEXT_BYTES = 16_384
MAX_CARDS = 16
MAX_SOURCES = 32
MAX_BINDINGS_PER_CARD = 8
MAX_CONTEXT_CHARS = 4_000
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReusableContextError(ValueError):
    """Raised when a request is malformed or exceeds a declared boundary."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReusableContextError(f"duplicate JSON input key: {key}")
        result[key] = value
    return result


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ReusableContextError(f"{label} must contain exactly {', '.join(sorted(expected))}")
    return value


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        raise ReusableContextError(f"{field} must be a bounded stable identifier")
    return value


def _text(value: Any, field: str, *, max_chars: int = 200) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_chars:
        raise ReusableContextError(f"{field} must be nonblank text of at most {max_chars} characters")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ReusableContextError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _bounded_integer(value: Any, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ReusableContextError(f"{field} must be an integer from {minimum} to {maximum}")
    return value


def _repo_file(relative_path: str) -> Path:
    if not relative_path.startswith("ignition/") or "\\" in relative_path or Path(relative_path).is_absolute():
        raise ReusableContextError("source paths must be repository-relative POSIX paths under ignition/")
    if REPO_ROOT.is_symlink():
        raise ReusableContextError("repository root must not be a symlink")
    root = REPO_ROOT.resolve()
    candidate = root
    for part in Path(relative_path).parts:
        if part in {"", ".", ".."}:
            raise ReusableContextError("source path contains traversal")
        candidate = candidate / part
        if candidate.is_symlink():
            raise ReusableContextError("source path contains a symlink")
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise ReusableContextError("source path escapes the repository") from exc
    return candidate


def _parse_utc_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ):
        raise ReusableContextError(f"{field} must be a UTC timestamp in YYYY-MM-DDTHH:MM:SSZ form")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ReusableContextError(f"{field} must be a valid UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ReusableContextError(f"{field} must be a canonical UTC timestamp")
    return parsed


def _validate_request(request: Any) -> dict[str, Any]:
    request = _exact_keys(request, {"schema_version", "task", "current_sources", "cached_cards"}, "request")
    schema_version = request["schema_version"]
    if schema_version not in {
        "toolbox-reusable-context-preflight-r0",
        "toolbox-reusable-context-preflight-r1",
    }:
        raise ReusableContextError("unsupported schema_version")
    expiry_enabled = schema_version == "toolbox-reusable-context-preflight-r1"

    task = _exact_keys(request["task"], {"task_id", "raw_source_required", "max_context_bytes", "max_source_bytes"}, "task")
    clean_task = {
        "task_id": _identifier(task["task_id"], "task.task_id"),
        "raw_source_required": task["raw_source_required"],
        "max_context_bytes": _bounded_integer(task["max_context_bytes"], "task.max_context_bytes", 1, MAX_CONTEXT_BYTES),
        "max_source_bytes": _bounded_integer(task["max_source_bytes"], "task.max_source_bytes", 1, MAX_TOTAL_SOURCE_BYTES),
    }
    if type(clean_task["raw_source_required"]) is not bool:
        raise ReusableContextError("task.raw_source_required must be a boolean")

    current_sources = request["current_sources"]
    if not isinstance(current_sources, list) or len(current_sources) > MAX_SOURCES:
        raise ReusableContextError(f"current_sources must be an array of at most {MAX_SOURCES} entries")
    clean_sources: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    source_keys = {"source_id", "path", "version", "sha256", "access_scope_id", "access_state", "authorized"}
    for index, raw in enumerate(current_sources):
        item = _exact_keys(raw, source_keys, f"current_sources[{index}]")
        source_id = _identifier(item["source_id"], "source_id")
        if source_id in source_ids:
            raise ReusableContextError("current source IDs must be unique")
        source_ids.add(source_id)
        path = _text(item["path"], "source path", max_chars=500)
        _repo_file(path)
        access_state = item["access_state"]
        if not isinstance(access_state, str) or access_state not in {"ACTIVE", "REVOKED", "UNREADABLE", "MISSING"}:
            raise ReusableContextError("access_state must be ACTIVE, REVOKED, UNREADABLE, or MISSING")
        if type(item["authorized"]) is not bool:
            raise ReusableContextError("authorized must be a boolean")
        clean_sources.append({
            "source_id": source_id,
            "path": path,
            "version": _text(item["version"], "source version", max_chars=128),
            "sha256": _sha256(item["sha256"], "current source sha256"),
            "access_scope_id": _identifier(item["access_scope_id"], "access_scope_id"),
            "access_state": access_state,
            "authorized": item["authorized"],
        })

    cached_cards = request["cached_cards"]
    if not isinstance(cached_cards, list) or len(cached_cards) > MAX_CARDS:
        raise ReusableContextError(f"cached_cards must be an array of at most {MAX_CARDS} entries")
    clean_cards: list[dict[str, Any]] = []
    card_ids: set[str] = set()
    base_card_keys = {"card_id", "source_bindings", "derived_context"}
    binding_keys = {"source_id", "path", "version", "sha256", "access_scope_id"}
    for index, raw in enumerate(cached_cards):
        card_keys = base_card_keys | ({"expires_at_utc"} if expiry_enabled else set())
        card = _exact_keys(raw, card_keys, f"cached_cards[{index}]")
        card_id = _identifier(card["card_id"], "card_id")
        if card_id in card_ids:
            raise ReusableContextError("cached card IDs must be unique")
        card_ids.add(card_id)
        bindings = card["source_bindings"]
        if not isinstance(bindings, list) or not 1 <= len(bindings) <= MAX_BINDINGS_PER_CARD:
            raise ReusableContextError(f"{card_id}.source_bindings must contain 1 to {MAX_BINDINGS_PER_CARD} entries")
        clean_bindings: list[dict[str, str]] = []
        binding_ids: set[str] = set()
        for binding_index, raw_binding in enumerate(bindings):
            binding = _exact_keys(raw_binding, binding_keys, f"{card_id}.source_bindings[{binding_index}]")
            source_id = _identifier(binding["source_id"], "binding source_id")
            if source_id in binding_ids:
                raise ReusableContextError(f"{card_id} repeats a source binding")
            binding_ids.add(source_id)
            path = _text(binding["path"], "binding path", max_chars=500)
            _repo_file(path)
            clean_bindings.append({
                "source_id": source_id,
                "path": path,
                "version": _text(binding["version"], "binding version", max_chars=128),
                "sha256": _sha256(binding["sha256"], "binding sha256"),
                "access_scope_id": _identifier(binding["access_scope_id"], "binding access_scope_id"),
            })
        clean_card = {
            "card_id": card_id,
            "source_bindings": clean_bindings,
            "derived_context": _text(card["derived_context"], "derived_context", max_chars=MAX_CONTEXT_CHARS),
        }
        if expiry_enabled:
            clean_card["expires_at_utc"] = card["expires_at_utc"]
            clean_card["expires_at"] = _parse_utc_timestamp(card["expires_at_utc"], f"{card_id}.expires_at_utc")
        clean_cards.append(clean_card)

    return {"schema_version": schema_version, "task": clean_task, "current_sources": clean_sources, "cached_cards": clean_cards}


def _source_check(source: dict[str, Any], binding: dict[str, str], byte_budget_left: int) -> tuple[str, str | None, int, str | None]:
    """Return (status, observed digest, bytes read, refresh reason)."""
    if source["access_state"] != "ACTIVE":
        return f"ACCESS_{source['access_state']}", None, 0, None
    if not source["authorized"]:
        return "CALLER_NOT_AUTHORIZED", None, 0, None
    if source["path"] != binding["path"]:
        return "SOURCE_PATH_CHANGED", None, 0, "SOURCE_PATH_CHANGED"
    if source["access_scope_id"] != binding["access_scope_id"]:
        return "ACCESS_SCOPE_CHANGED", None, 0, "ACCESS_SCOPE_CHANGED"
    if source["version"] != binding["version"] or source["sha256"] != binding["sha256"]:
        return "SOURCE_VERSION_OR_DIGEST_CHANGED", None, 0, "SOURCE_VERSION_OR_DIGEST_CHANGED"
    path = _repo_file(source["path"])
    if not path.exists():
        return "LOCAL_SOURCE_MISSING", None, 0, "LOCAL_SOURCE_MISSING"
    if not path.is_file():
        return "LOCAL_SOURCE_NOT_REGULAR_FILE", None, 0, "LOCAL_SOURCE_NOT_REGULAR_FILE"
    size = path.stat().st_size
    if size > MAX_SOURCE_BYTES_PER_FILE:
        return "LOCAL_SOURCE_OVER_SIZE", None, 0, "LOCAL_SOURCE_OVER_SIZE"
    if size > byte_budget_left:
        return "SOURCE_READ_BUDGET_EXCEEDED", None, 0, None
    content = path.read_bytes()
    observed = hashlib.sha256(content).hexdigest()
    if observed != source["sha256"]:
        return "CURRENT_SOURCE_DECLARATION_STALE", observed, size, "CURRENT_SOURCE_DECLARATION_STALE"
    return "MATCH", observed, size, None


def _current_utc(now_utc: datetime | None) -> datetime:
    if now_utc is None:
        return datetime.now(timezone.utc)
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
        raise ReusableContextError("now_utc must be a timezone-aware datetime")
    return now_utc.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def preflight(request: Any, now_utc: datetime | None = None) -> dict[str, Any]:
    clean = _validate_request(request)
    task = clean["task"]
    sources = {item["source_id"]: item for item in clean["current_sources"]}
    expiry_enabled = clean["schema_version"] == "toolbox-reusable-context-preflight-r1"
    evaluated_at = _current_utc(now_utc) if expiry_enabled else None
    evaluated_at_utc = _format_utc(evaluated_at) if evaluated_at is not None else None
    result_schema_version = (
        "toolbox-reusable-context-preflight-result-r1"
        if expiry_enabled else "toolbox-reusable-context-preflight-result-r0"
    )
    decisions: list[dict[str, Any]] = []
    returned: list[dict[str, Any]] = []
    refresh_required: dict[str, dict[str, Any]] = {}
    raw_reopen: dict[str, dict[str, str]] = {}
    source_bytes_read = 0
    source_checks: dict[tuple[str, str, str, str, str], tuple[str, str | None, int, str | None]] = {}
    hashed_source_keys: set[tuple[str, str]] = set()
    context_bytes_returned = 0

    if task["raw_source_required"]:
        for card in clean["cached_cards"]:
            source_ids = [binding["source_id"] for binding in card["source_bindings"]]
            for source_id in source_ids:
                source = sources.get(source_id)
                if source and source["access_state"] == "ACTIVE" and source["authorized"]:
                    raw_reopen[source_id] = {"source_id": source_id, "path": source["path"], "reason": "RAW_SOURCE_REQUIRED"}
            decisions.append({"card_id": card["card_id"], "decision": "SKIP", "reason": "RAW_SOURCE_REQUIRED", "source_ids": source_ids})
        return _result(
            task["task_id"], decisions, returned, refresh_required, raw_reopen,
            source_bytes_read, context_bytes_returned,
            result_schema_version=result_schema_version,
            evaluated_at_utc=evaluated_at_utc,
        )

    for card in clean["cached_cards"]:
        context_bytes = len(card["derived_context"].encode("utf-8"))
        if expiry_enabled and card["expires_at"] <= evaluated_at:
            source_ids = [binding["source_id"] for binding in card["source_bindings"]]
            for binding in card["source_bindings"]:
                source = sources.get(binding["source_id"])
                if source and source["access_state"] == "ACTIVE" and source["authorized"]:
                    refresh_required[binding["source_id"]] = {
                        "source_id": binding["source_id"],
                        "path": source["path"],
                        "reason": "MEMORY_CARD_EXPIRED",
                        "current_version": source["version"],
                        "declared_current_sha256": source["sha256"],
                        "expires_at_utc": card["expires_at_utc"],
                    }
            decisions.append({
                "card_id": card["card_id"],
                "decision": "INVALIDATE",
                "reason": "MEMORY_CARD_EXPIRED",
                "source_ids": source_ids,
                "expires_at_utc": card["expires_at_utc"],
                "evaluated_at_utc": evaluated_at_utc,
                "context_bytes": context_bytes,
            })
            continue
        if context_bytes_returned + context_bytes > task["max_context_bytes"]:
            decisions.append({"card_id": card["card_id"], "decision": "SKIP", "reason": "CONTEXT_BUDGET_EXCEEDED", "context_bytes": context_bytes})
            continue
        failures: list[tuple[dict[str, str], str, str | None]] = []
        for binding in card["source_bindings"]:
            source_id = binding["source_id"]
            source = sources.get(source_id)
            if source is None:
                failures.append((binding, "CURRENT_SOURCE_NOT_DECLARED", None))
                continue
            key = (source_id, binding["path"], binding["version"], binding["sha256"], binding["access_scope_id"])
            checked = source_checks.get(key)
            if checked is None:
                checked = _source_check(source, binding, min(task["max_source_bytes"], MAX_TOTAL_SOURCE_BYTES) - source_bytes_read)
                source_checks[key] = checked
                source_bytes_read += checked[2]
                if checked[0] in {"MATCH", "CURRENT_SOURCE_DECLARATION_STALE"}:
                    hashed_source_keys.add((source_id, binding["path"]))
            status, observed, _, refresh_reason = checked
            if status != "MATCH":
                failures.append((binding, status, refresh_reason))
                if refresh_reason and source["access_state"] == "ACTIVE" and source["authorized"]:
                    entry = {"source_id": source_id, "path": source["path"], "reason": refresh_reason, "current_version": source["version"], "declared_current_sha256": source["sha256"]}
                    if observed is not None:
                        entry["observed_local_sha256"] = observed
                    refresh_required[source_id] = entry

        if failures:
            reason = failures[0][1] if len(failures) == 1 else "ONE_OR_MORE_SOURCE_BINDINGS_INVALID"
            decisions.append({
                "card_id": card["card_id"],
                "decision": "INVALIDATE",
                "reason": reason,
                "invalid_bindings": [{"source_id": binding["source_id"], "reason": status} for binding, status, _ in failures],
            })
            continue

        context_bytes_returned += context_bytes
        decisions.append({"card_id": card["card_id"], "decision": "REUSE", "reason": "SOURCE_BYTES_AND_CALLER_DECLARED_ACCESS_SCOPE_MATCH", "context_bytes": context_bytes})
        returned_card = {
            "card_id": card["card_id"],
            "derived_context": card["derived_context"],
            "context_kind": "DERIVED_CONTEXT_ONLY",
            "source_bindings": card["source_bindings"],
        }
        if expiry_enabled:
            returned_card["expires_at_utc"] = card["expires_at_utc"]
        returned.append(returned_card)

    return _result(
        task["task_id"], decisions, returned, refresh_required, raw_reopen,
        source_bytes_read, context_bytes_returned, len(hashed_source_keys),
        result_schema_version=result_schema_version,
        evaluated_at_utc=evaluated_at_utc,
    )


def _result(
    task_id: str,
    decisions: list[dict[str, Any]],
    returned: list[dict[str, Any]],
    refresh_required: dict[str, dict[str, Any]],
    raw_reopen: dict[str, dict[str, str]],
    source_bytes_read: int,
    context_bytes_returned: int,
    source_files_hashed: int = 0,
    *,
    result_schema_version: str = "toolbox-reusable-context-preflight-result-r0",
    evaluated_at_utc: str | None = None,
) -> dict[str, Any]:
    result = {
        "schema_version": result_schema_version,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "task_id": task_id,
        "decision": "CONTEXT_REUSED" if returned else "NO_ELIGIBLE_CONTEXT",
        "decisions": decisions,
        "reused_context_cards": returned,
        "refresh_required": [refresh_required[key] for key in sorted(refresh_required)],
        "raw_reopen_required": [raw_reopen[key] for key in sorted(raw_reopen)],
        "resource_observation": {
            "source_files_hashed": source_files_hashed,
            "source_bytes_read": source_bytes_read,
            "context_bytes_returned": context_bytes_returned,
            "latency_ms": "UNKNOWN",
            "cost_equivalent": "NOT_MEASURED",
        },
        "execution_authorized": False,
        "authority_effect": "NONE",
        "semantic_relevance": "NOT_EVALUATED",
        "evidential_sufficiency": "NOT_EVALUATED",
        "claim_ceiling": (
            "Caller-selected derived context may be reused only after exact local byte-digest and caller-declared access-scope checks. No source authority, permission grant, semantic relevance, raw-evidence support, sufficiency, truth, or task completion is established."
            if evaluated_at_utc is None else
            "R1 checks required caller-declared expiry timestamps against the observed local system clock before reuse, then applies the same local byte-digest and caller-declared access-scope checks. Clock accuracy, source authority, current external truth, permission grant, semantic relevance, raw-evidence support, sufficiency, truth, and task completion are not established."
        ),
    }
    if evaluated_at_utc is not None:
        result["evaluated_at_utc"] = evaluated_at_utc
    return result


def run(stdin: Any, stdout: Any, stderr: Any) -> int:
    raw = stdin.read(MAX_REQUEST_BYTES + 1)
    if len(raw.encode("utf-8")) > MAX_REQUEST_BYTES:
        stderr.write("request exceeds byte limit\n")
        return 2
    try:
        request = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
        result = preflight(request)
    except (json.JSONDecodeError, ReusableContextError, OSError) as exc:
        stderr.write(str(exc) + "\n")
        return 2
    stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read exactly one JSON request from stdin")
    args = parser.parse_args(argv)
    if not args.stdin:
        parser.error("--stdin is required")
    return run(sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
