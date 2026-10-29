#!/usr/bin/env python3
"""Assemble a bounded, digest-checked context packet from caller-selected files.

This tool verifies local bytes and declared obligation links only. It does not
judge semantic relevance, source authority, truth, or whether the packet is
sufficient for a task.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
TOOL_ID = "knowledge.assemble_context_packet"
TOOL_VERSION = "0.1.0"
MAX_REQUEST_BYTES = 32_000
MAX_OBLIGATIONS = 8
MAX_CONTEXT_ITEMS = 16
MAX_TOTAL_SOURCE_BYTES = 1_000_000
MAX_LINES_PER_ITEM = 200
MAX_LINE_CHARS = 2_000
MAX_EXCERPT_CHARS = 2_000
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_KINDS = {"CANONICAL_SOURCE", "DERIVED_PROJECTION", "GENERATED_SUMMARY"}

CLAIM_CEILING = (
    "A bounded packet of caller-selected local excerpts with current byte-digest checks and "
    "structural obligation linkage only. Current-ref resolution, source-kind declarations, "
    "authority, freshness meaning, semantic relevance, evidential support, sufficiency, truth, "
    "proof, scientific acceptance, and publication readiness are not evaluated."
)


class ContextPacketError(ValueError):
    """Raised when a request is malformed or attempts unsafe file access."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContextPacketError("duplicate JSON input key: " + key)
        result[key] = value
    return result


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ContextPacketError(f"{field} must be a bounded stable identifier")
    return value


def _text(value: Any, field: str, *, max_chars: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_chars:
        raise ContextPacketError(f"{field} must be nonblank text of at most {max_chars} characters")
    return value


def _safe_repo_file(repo_root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        raise ContextPacketError("source paths must remain under ignition/")
    if "\\" in relative_path or Path(relative_path).is_absolute():
        raise ContextPacketError("source path must be repository-relative POSIX text")
    root = Path(repo_root)
    if root.is_symlink():
        raise ContextPacketError("repository root must not be a symlink")
    root = root.resolve()
    candidate = root
    for part in Path(relative_path).parts:
        if part in {"", ".", ".."}:
            raise ContextPacketError("source path contains traversal")
        candidate = candidate / part
        if candidate.is_symlink():
            raise ContextPacketError("source path contains a symlink")
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise ContextPacketError("source path escapes the repository") from exc
    return candidate


def _validate_request(request: Any) -> dict[str, Any]:
    required_keys = {
        "packet_id",
        "current_ref",
        "operation_or_question_id",
        "obligations",
        "context_items",
        "max_total_source_bytes",
        "max_excerpt_chars",
    }
    if not isinstance(request, dict) or set(request) != required_keys:
        raise ContextPacketError("request must contain exactly " + ", ".join(sorted(required_keys)))
    packet_id = _identifier(request["packet_id"], "packet_id")
    operation_id = _identifier(request["operation_or_question_id"], "operation_or_question_id")
    current_ref = _text(request["current_ref"], "current_ref", max_chars=200)

    obligations = request["obligations"]
    if not isinstance(obligations, list) or not obligations or len(obligations) > MAX_OBLIGATIONS:
        raise ContextPacketError("obligations must contain 1 to 8 entries")
    clean_obligations: list[dict[str, Any]] = []
    obligation_ids: set[str] = set()
    for item in obligations:
        if not isinstance(item, dict) or set(item) != {"obligation_id", "description", "source_required"}:
            raise ContextPacketError("each obligation must contain exactly obligation_id, description, and source_required")
        obligation_id = _identifier(item["obligation_id"], "obligation_id")
        if obligation_id in obligation_ids:
            raise ContextPacketError("obligation_id values must be unique")
        if type(item["source_required"]) is not bool:
            raise ContextPacketError("source_required must be a boolean")
        obligation_ids.add(obligation_id)
        clean_obligations.append({
            "obligation_id": obligation_id,
            "description": _text(item["description"], "obligation description"),
            "source_required": item["source_required"],
        })

    context_items = request["context_items"]
    if not isinstance(context_items, list) or len(context_items) > MAX_CONTEXT_ITEMS:
        raise ContextPacketError("context_items must contain 0 to 16 entries")
    clean_items: list[dict[str, Any]] = []
    item_ids: set[str] = set()
    required_item_keys = {
        "context_item_id",
        "canonical_source_ref",
        "source_version_or_digest",
        "source_kind",
        "line_start",
        "line_end",
        "evidence_role",
        "epistemic_status",
        "freshness_or_as_of",
        "inclusion_reason",
        "obligation_ids",
    }
    for item in context_items:
        if not isinstance(item, dict) or set(item) != required_item_keys:
            raise ContextPacketError("each context item must contain exactly the declared ContextPacket fields")
        item_id = _identifier(item["context_item_id"], "context_item_id")
        if item_id in item_ids:
            raise ContextPacketError("context_item_id values must be unique")
        item_ids.add(item_id)
        path = item["canonical_source_ref"]
        if not isinstance(path, str) or not path.startswith("ignition/"):
            raise ContextPacketError("canonical_source_ref must remain under ignition/")
        digest = item["source_version_or_digest"]
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise ContextPacketError("source_version_or_digest must be a lowercase SHA-256")
        if not isinstance(item["source_kind"], str) or item["source_kind"] not in _SOURCE_KINDS:
            raise ContextPacketError("source_kind is not a declared ContextPacket kind")
        line_start, line_end = item["line_start"], item["line_end"]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (line_start, line_end)):
            raise ContextPacketError("line_start and line_end must be integers")
        if line_start < 1 or line_end < line_start or line_end - line_start + 1 > MAX_LINES_PER_ITEM:
            raise ContextPacketError("context line range must contain 1 to 200 positive lines")
        linked = item["obligation_ids"]
        if not isinstance(linked, list) or any(not isinstance(value, str) for value in linked):
            raise ContextPacketError("obligation_ids must be a string array")
        if len(linked) != len(set(linked)):
            raise ContextPacketError("obligation_ids must be a duplicate-free array")
        if any(not isinstance(value, str) or value not in obligation_ids for value in linked):
            raise ContextPacketError("context item references an unknown obligation_id")
        freshness = item["freshness_or_as_of"]
        if freshness is not None and (not isinstance(freshness, str) or len(freshness) > 200):
            raise ContextPacketError("freshness_or_as_of must be null or text of at most 200 characters")
        clean_items.append({
            "context_item_id": item_id,
            "canonical_source_ref": path,
            "source_version_or_digest": digest,
            "source_kind": item["source_kind"],
            "line_start": line_start,
            "line_end": line_end,
            "evidence_role": _text(item["evidence_role"], "evidence_role"),
            "epistemic_status_caller_declared": _text(item["epistemic_status"], "epistemic_status"),
            "freshness_or_as_of_caller_declared": freshness,
            "inclusion_reason": _text(item["inclusion_reason"], "inclusion_reason"),
            "obligation_ids": list(linked),
        })

    total_bytes = request["max_total_source_bytes"]
    max_excerpt = request["max_excerpt_chars"]
    if isinstance(total_bytes, bool) or not isinstance(total_bytes, int) or not 1 <= total_bytes <= MAX_TOTAL_SOURCE_BYTES:
        raise ContextPacketError("max_total_source_bytes must be an integer from 1 to 1000000")
    if isinstance(max_excerpt, bool) or not isinstance(max_excerpt, int) or not 80 <= max_excerpt <= MAX_EXCERPT_CHARS:
        raise ContextPacketError("max_excerpt_chars must be an integer from 80 to 2000")
    return {
        "packet_id": packet_id,
        "current_ref": current_ref,
        "operation_or_question_id": operation_id,
        "obligations": clean_obligations,
        "context_items": clean_items,
        "max_total_source_bytes": total_bytes,
        "max_excerpt_chars": max_excerpt,
    }


def _materialize_item(
    item: dict[str, Any],
    repo_root: Path,
    bytes_left: int,
    max_excerpt_chars: int,
) -> tuple[dict[str, Any], int]:
    path = _safe_repo_file(repo_root, item["canonical_source_ref"])
    base = {
        **item,
        "source_kind_provenance": "CALLER_DECLARED_NOT_AUTHORITY_VERIFIED",
        "semantic_support": "NOT_EVALUATED",
        "current_source_sha256": None,
        "source_bytes_read": 0,
        "line_count": 0,
        "context_excerpt": None,
        "excerpt_truncated": False,
    }
    if not path.exists():
        return {**base, "materialization_status": "SOURCE_MISSING"}, 0
    if not path.is_file():
        return {**base, "materialization_status": "SOURCE_NOT_REGULAR_FILE"}, 0
    size = path.stat().st_size
    if size > bytes_left:
        return {
            **base,
            "materialization_status": "SOURCE_NOT_OPENED_BUDGET",
            "source_bytes_estimate": size,
        }, 0
    raw = path.read_bytes()
    current_digest = hashlib.sha256(raw).hexdigest()
    if current_digest != item["source_version_or_digest"]:
        return {
            **base,
            "materialization_status": "SOURCE_STALE_DIGEST_MISMATCH",
            "current_source_sha256": current_digest,
            "source_bytes_read": len(raw),
        }, len(raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return {
            **base,
            "materialization_status": "SOURCE_NOT_UTF8",
            "current_source_sha256": current_digest,
            "source_bytes_read": len(raw),
        }, len(raw)
    lines = text.splitlines()
    selected = lines[item["line_start"] - 1:item["line_end"]]
    complete_range = len(selected) == item["line_end"] - item["line_start"] + 1
    rendered = []
    any_truncated = False
    for line_number, line in enumerate(selected, start=item["line_start"]):
        bounded = line[:min(MAX_LINE_CHARS, max_excerpt_chars)]
        truncated = len(line) > len(bounded)
        any_truncated = any_truncated or truncated
        rendered.append({"line": line_number, "text": bounded, "truncated": truncated})
    return {
        **base,
        "materialization_status": "CURRENT_BYTES_MATCH_EXPECTED_DIGEST" if complete_range else "LINE_RANGE_PARTIAL",
        "current_source_sha256": current_digest,
        "source_bytes_read": len(raw),
        "line_count": len(selected),
        "context_excerpt": rendered,
        "excerpt_truncated": any_truncated,
    }, len(raw)


def build_context_packet(request: Any, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Build one bounded packet; coverage is declared structure, not semantic support."""
    clean = _validate_request(request)
    bytes_used = 0
    materialized: list[dict[str, Any]] = []
    for item in clean["context_items"]:
        result, consumed = _materialize_item(
            item,
            Path(repo_root),
            clean["max_total_source_bytes"] - bytes_used,
            clean["max_excerpt_chars"],
        )
        bytes_used += consumed
        materialized.append(result)

    obligation_rows: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for obligation in clean["obligations"]:
        linked = [item for item in materialized if obligation["obligation_id"] in item["obligation_ids"]]
        current = [item for item in linked if item["materialization_status"] == "CURRENT_BYTES_MATCH_EXPECTED_DIGEST"]
        canonical = [item for item in current if item["source_kind"] == "CANONICAL_SOURCE"]
        acceptable = canonical if obligation["source_required"] else current
        if acceptable:
            status = "SOURCE_PRESENT_BY_CALLER_DECLARATION" if obligation["source_required"] else "CONTEXT_PRESENT_BY_CALLER_DECLARATION"
            gap_class = None
        elif any(item["materialization_status"] == "SOURCE_STALE_DIGEST_MISMATCH" for item in linked):
            status, gap_class = "STALE_ONLY", "STALE"
        elif (
            linked
            and all(item["source_kind"] == "GENERATED_SUMMARY" for item in linked)
            and any(item["materialization_status"] == "CURRENT_BYTES_MATCH_EXPECTED_DIGEST" for item in linked)
        ):
            status, gap_class = "GENERATED_ONLY", "GENERATED_CONTEXT_NOT_SOURCE"
        elif any(item["materialization_status"] == "SOURCE_NOT_OPENED_BUDGET" for item in linked):
            status, gap_class = "BUDGET_NOT_OPENED", "BUDGET"
        elif any(item["materialization_status"] in {"SOURCE_MISSING", "SOURCE_NOT_REGULAR_FILE", "SOURCE_NOT_UTF8", "LINE_RANGE_PARTIAL"} for item in linked):
            status, gap_class = "UNREADABLE_OR_PARTIAL", "UNREADABLE"
        else:
            status, gap_class = "MISSING", "MISSING"
        obligation_rows.append({
            "obligation_id": obligation["obligation_id"],
            "description": obligation["description"],
            "source_required": obligation["source_required"],
            "linked_context_item_ids": [item["context_item_id"] for item in linked],
            "current_context_item_ids": [item["context_item_id"] for item in current],
            "current_canonical_source_item_ids": [item["context_item_id"] for item in canonical],
            "declared_status": status,
            "semantic_support": "NOT_EVALUATED",
        })
        if gap_class is not None:
            gaps.append({
                "gap_id": "gap:" + obligation["obligation_id"],
                "obligation_id": obligation["obligation_id"],
                "gap_class": gap_class,
                "detail": "Required context is absent, stale, generated-only, partial, unreadable, or outside the byte budget; no sufficiency decision was made.",
                "retrieval_authorized": False,
            })

    missing = [row["obligation_id"] for row in obligation_rows if row["declared_status"] == "MISSING"]
    stale = [row["obligation_id"] for row in obligation_rows if row["declared_status"] == "STALE_ONLY"]
    generated_only = [row["obligation_id"] for row in obligation_rows if row["declared_status"] == "GENERATED_ONLY"]
    stale_or_invalid = [
        row["obligation_id"] for row in obligation_rows
        if row["declared_status"] in {"STALE_ONLY", "UNREADABLE_OR_PARTIAL", "BUDGET_NOT_OPENED"}
    ]
    packet_status = "ASSEMBLED_STRUCTURAL_CONTEXT_WITH_OPEN_GAPS" if gaps else "ASSEMBLED_STRUCTURAL_CONTEXT_NO_DECLARED_GAPS"
    return {
        "schema_version": "toolbox-context-packet-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "packet_id": clean["packet_id"],
        "packet_version": "r0",
        "packet_status": packet_status,
        "current_ref": clean["current_ref"],
        "current_ref_binding": "CALLER_SUPPLIED_NOT_RESOLVED_BY_THIS_TOOL",
        "operation_or_question_id": clean["operation_or_question_id"],
        "context_items": materialized,
        "coverage": {
            "required": [row["obligation_id"] for row in obligation_rows],
            "declared_present": [row["obligation_id"] for row in obligation_rows if row["declared_status"] in {"SOURCE_PRESENT_BY_CALLER_DECLARATION", "CONTEXT_PRESENT_BY_CALLER_DECLARATION"}],
            "source_required_present": [row["obligation_id"] for row in obligation_rows if row["declared_status"] == "SOURCE_PRESENT_BY_CALLER_DECLARATION"],
            "missing": missing,
            "stale_or_invalid": stale_or_invalid,
            "generated_only": generated_only,
            "obligations": obligation_rows,
            "semantic_coverage": "NOT_EVALUATED",
            "sufficiency_decision": "NOT_EVALUATED",
        },
        "gaps": gaps,
        "budgets": {
            "max_total_source_bytes": clean["max_total_source_bytes"],
            "source_bytes_read": bytes_used,
            "max_context_items": MAX_CONTEXT_ITEMS,
            "max_lines_per_item": MAX_LINES_PER_ITEM,
            "max_excerpt_chars": clean["max_excerpt_chars"],
        },
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON ContextPacket request")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        print("CONTEXT_PACKET_NOT_AVAILABLE: request exceeds the 32000-byte limit", file=sys.stderr)
        return 2
    try:
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        packet = build_context_packet(request)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ContextPacketError, RecursionError) as exc:
        print("CONTEXT_PACKET_NOT_AVAILABLE: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
