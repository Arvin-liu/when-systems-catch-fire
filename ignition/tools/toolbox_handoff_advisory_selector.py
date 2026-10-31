#!/usr/bin/env python3
"""Suggest exact-duplicate advisory omissions for a caller-reviewed handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from typing import Any


TOOL_ID = "collaboration.select_handoff_advisories"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "handoff-advisory-selection-r0"
OUTPUT_SCHEMA_VERSION = "handoff-advisory-selection-result-r0"
MAX_INPUT_BYTES = 262_144
MAX_MESSAGES = 64
MAX_CONTEXT_DIGESTS = 128
MAX_MESSAGE_CHARS = 8_192
MAX_SOURCE_REFS = 16
MAX_SOURCE_REF_CHARS = 500
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MESSAGE_KINDS = {"ADVISORY", "ACTION", "AUTHORITY", "OUTCOME", "WITNESS", "SOURCE", "UNKNOWN"}
REQUEST_KEYS = {
    "schema_version",
    "task_scope_id",
    "receiver_state_ref",
    "receiver_context_message_digests",
    "messages",
}
MESSAGE_KEYS = {"message_id", "kind", "must_forward", "text", "source_refs"}
CLAIM_CEILING = (
    "Suggests omission only for one explicitly optional ADVISORY message whose exact UTF-8 text, "
    "ordered source references, task scope, and receiver-state revision hash match caller-declared receiver context. "
    "It does not authenticate receiver state, determine semantic necessity, transform or send a "
    "handoff, authorize actions, or establish task completion."
)


class AdvisorySelectionError(ValueError):
    """Raised when input is malformed or exceeds a fixed resource bound."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdvisorySelectionError("duplicate JSON input key")
        result[key] = value
    return result


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise AdvisorySelectionError(f"{label} must contain exactly the declared keys")
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        raise AdvisorySelectionError(f"{label} must be a bounded stable identifier")
    return value


def _nonblank_text(value: Any, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise AdvisorySelectionError(f"{label} must be nonblank text of at most {maximum} characters")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise AdvisorySelectionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def message_digest(task_scope_id: str, receiver_state_ref: str, text: str, source_refs: list[str]) -> str:
    """Hash exact text, ordered refs, task scope, and the caller's receiver-state revision."""
    canonical = json.dumps(
        {
            "task_scope_id": task_scope_id,
            "receiver_state_ref": receiver_state_ref,
            "text": text,
            "source_refs": source_refs,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _result_base(status: str, finding: str | None = None) -> dict[str, Any]:
    result = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "selection_status": status,
        "task_scope_id": None,
        "receiver_state_ref": None,
        "receiver_context_attestation": "NOT_AUTHENTICATED_CALLER_DECLARATION",
        "retained_message_ids": [],
        "suggested_omissions": [],
        "metrics": {
            "input_message_count": 0,
            "suggested_omission_count": 0,
            "suggested_omission_content_utf8_bytes": 0,
        },
        "semantic_necessity": "NOT_EVALUATED",
        "handoff_transformed": False,
        "send_authorized": False,
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    if finding is not None:
        result["finding"] = finding
    return result


def _input_error(reason: str) -> tuple[dict[str, Any], int]:
    return _result_base("INPUT_INVALID", reason), 2


def evaluate(request: Any) -> tuple[dict[str, Any], int]:
    """Return a review-only selection proposal; never edit or transmit messages."""
    try:
        clean = _exact_keys(request, REQUEST_KEYS, "request")
        if clean["schema_version"] != INPUT_SCHEMA_VERSION:
            raise AdvisorySelectionError("unsupported schema_version")
        task_scope_id = _identifier(clean["task_scope_id"], "task_scope_id")
        receiver_state_ref = _nonblank_text(clean["receiver_state_ref"], "receiver_state_ref", 200)

        context_digests = clean["receiver_context_message_digests"]
        if not isinstance(context_digests, list) or len(context_digests) > MAX_CONTEXT_DIGESTS:
            raise AdvisorySelectionError("receiver_context_message_digests exceeds its bounded list")
        normalized_context = [_sha256(value, "receiver context digest") for value in context_digests]
        if len(normalized_context) != len(set(normalized_context)):
            raise AdvisorySelectionError("receiver context digests must be unique")

        raw_messages = clean["messages"]
        if not isinstance(raw_messages, list) or len(raw_messages) > MAX_MESSAGES:
            raise AdvisorySelectionError(f"messages must contain at most {MAX_MESSAGES} entries")
        messages: list[dict[str, Any]] = []
        ids: set[str] = set()
        for index, raw in enumerate(raw_messages):
            message = _exact_keys(raw, MESSAGE_KEYS, f"messages[{index}]")
            message_id = _identifier(message["message_id"], "message_id")
            if message_id in ids:
                raise AdvisorySelectionError("message_id values must be unique")
            ids.add(message_id)
            kind = message["kind"]
            if not isinstance(kind, str) or kind not in MESSAGE_KINDS:
                raise AdvisorySelectionError("message kind is not declared")
            if type(message["must_forward"]) is not bool:
                raise AdvisorySelectionError("must_forward must be a boolean")
            text = _nonblank_text(message["text"], "message text", MAX_MESSAGE_CHARS)
            refs = message["source_refs"]
            if not isinstance(refs, list) or len(refs) > MAX_SOURCE_REFS:
                raise AdvisorySelectionError(f"source_refs must contain at most {MAX_SOURCE_REFS} entries")
            clean_refs = [_nonblank_text(ref, "source_ref", MAX_SOURCE_REF_CHARS) for ref in refs]
            if len(clean_refs) != len(set(clean_refs)):
                raise AdvisorySelectionError("source_refs must be unique and retain their declared order")
            messages.append({
                "message_id": message_id,
                "kind": kind,
                "must_forward": message["must_forward"],
                "text": text,
                "source_refs": clean_refs,
                "digest": message_digest(task_scope_id, receiver_state_ref, text, clean_refs),
            })

        pending_counts = Counter(message["digest"] for message in messages)
        context_set = set(normalized_context)
        retained: list[str] = []
        omissions: list[dict[str, Any]] = []
        omission_bytes = 0
        for message in messages:
            digest = message["digest"]
            if (
                message["kind"] == "ADVISORY"
                and not message["must_forward"]
                and digest in context_set
                and pending_counts[digest] == 1
            ):
                content_bytes = len(message["text"].encode("utf-8"))
                omission_bytes += content_bytes
                omissions.append({
                    "message_id": message["message_id"],
                    "basis": "EXACT_TEXT_AND_ORDERED_SOURCE_REFS_MATCH_CALLER_DECLARED_CONTEXT",
                    "message_sha256": digest,
                    "content_utf8_bytes": content_bytes,
                })
            else:
                if message["must_forward"]:
                    reason = "CALLER_MARKED_MUST_FORWARD"
                elif message["kind"] != "ADVISORY":
                    reason = "NON_ADVISORY_KIND_ALWAYS_RETAINED"
                elif digest in context_set and pending_counts[digest] > 1:
                    reason = "REPEATED_WITHIN_PENDING_BUNDLE_RETAINED"
                else:
                    reason = "NO_EXACT_CALLER_CONTEXT_MATCH"
                retained.append(message["message_id"])

        result = _result_base("REVIEW_ONLY_CANDIDATE")
        result.update({
            "task_scope_id": task_scope_id,
            "receiver_state_ref": receiver_state_ref,
            "retained_message_ids": retained,
            "suggested_omissions": omissions,
            "metrics": {
                "input_message_count": len(messages),
                "suggested_omission_count": len(omissions),
                "suggested_omission_content_utf8_bytes": omission_bytes,
            },
        })
        return result, 0
    except AdvisorySelectionError as exc:
        return _input_error(str(exc))


def _read_stdin() -> Any:
    data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise AdvisorySelectionError("input exceeds the 262144-byte limit")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded UTF-8 JSON request")
    parser.parse_args(argv)
    try:
        request = _read_stdin()
    except (AdvisorySelectionError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        result, code = _input_error("INPUT_UNAVAILABLE_OR_INVALID")
    else:
        result, code = evaluate(request)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
