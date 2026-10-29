#!/usr/bin/env python3
"""Compare two matched ContextPacket outputs without evaluating their meaning.

The tool measures excerpt text bytes and reports caller-declared structural
coverage deltas. It does not authenticate either packet, judge semantic
relevance or sufficiency, or estimate provider token and billing costs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any


TOOL_ID = "maintenance.compare_context_packet_variants"
TOOL_VERSION = "0.1.0"
MAX_REQUEST_BYTES = 256_000
MAX_CONTEXT_ITEMS = 16
MAX_EXCERPT_LINES = 200
MAX_EXCERPT_TEXT_BYTES = 2_000_000
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContextVariantError(ValueError):
    """Raised when two packets cannot be safely compared as a matched task."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContextVariantError("duplicate JSON input key: " + key)
        result[key] = value
    return result


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ContextVariantError(f"{field} must be a bounded stable identifier")
    return value


def _id_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ContextVariantError(f"{field} must be a string array")
    result = [_identifier(item, field) for item in value]
    if len(result) != len(set(result)):
        raise ContextVariantError(f"{field} must not contain duplicates")
    return result


def _nonnegative_int(value: Any, field: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ContextVariantError(f"{field} must be an integer from 0 to {maximum}")
    return value


def _packet_summary(packet: Any, role: str) -> dict[str, Any]:
    if not isinstance(packet, dict):
        raise ContextVariantError(f"{role}_packet must be a ContextPacket object")
    if packet.get("schema_version") != "toolbox-context-packet-r0":
        raise ContextVariantError(f"{role}_packet has an unsupported ContextPacket schema_version")
    if packet.get("tool_id") != "knowledge.assemble_context_packet":
        raise ContextVariantError(f"{role}_packet was not emitted by knowledge.assemble_context_packet")
    if packet.get("execution_authorized") is not False:
        raise ContextVariantError(f"{role}_packet must explicitly keep execution_authorized=false")
    if not isinstance(packet.get("current_ref"), str) or not packet["current_ref"]:
        raise ContextVariantError(f"{role}_packet current_ref must be caller-declared text")
    operation_id = _identifier(packet.get("operation_or_question_id"), f"{role}_packet operation_or_question_id")
    packet_id = _identifier(packet.get("packet_id"), f"{role}_packet packet_id")
    if not isinstance(packet.get("packet_status"), str):
        raise ContextVariantError(f"{role}_packet packet_status must be text")

    items = packet.get("context_items")
    if not isinstance(items, list) or len(items) > MAX_CONTEXT_ITEMS:
        raise ContextVariantError(f"{role}_packet context_items must contain at most {MAX_CONTEXT_ITEMS} items")
    item_ids: set[str] = set()
    excerpt_bytes = 0
    excerpt_characters = 0
    excerpt_lines = 0
    current_digest_items: list[str] = []
    source_identities: set[tuple[str, str]] = set()
    item_source_bytes_reported = 0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ContextVariantError(f"{role}_packet context item {index} must be an object")
        item_id = _identifier(item.get("context_item_id"), f"{role}_packet context_item_id")
        if item_id in item_ids:
            raise ContextVariantError(f"{role}_packet context_item_id values must be unique")
        item_ids.add(item_id)
        source_ref = item.get("canonical_source_ref")
        if not isinstance(source_ref, str) or not source_ref.startswith("ignition/"):
            raise ContextVariantError(f"{role}_packet source refs must remain under ignition/")
        expected_digest = item.get("source_version_or_digest")
        if not isinstance(expected_digest, str) or not _SHA256_RE.fullmatch(expected_digest):
            raise ContextVariantError(f"{role}_packet source_version_or_digest must be a lowercase SHA-256")
        source_identities.add((source_ref, expected_digest))
        materialization = item.get("materialization_status")
        if not isinstance(materialization, str):
            raise ContextVariantError(f"{role}_packet materialization_status must be text")
        current_digest = item.get("current_source_sha256")
        if current_digest is not None and (not isinstance(current_digest, str) or not _SHA256_RE.fullmatch(current_digest)):
            raise ContextVariantError(f"{role}_packet current_source_sha256 must be null or a lowercase SHA-256")
        if materialization == "CURRENT_BYTES_MATCH_EXPECTED_DIGEST":
            if current_digest != expected_digest:
                raise ContextVariantError(f"{role}_packet current digest does not match its declared source digest")
            current_digest_items.append(item_id)
        source_bytes = _nonnegative_int(item.get("source_bytes_read"), f"{role}_packet source_bytes_read", 1_000_000)
        item_source_bytes_reported += source_bytes

        excerpt = item.get("context_excerpt")
        if excerpt is None:
            continue
        if not isinstance(excerpt, list) or len(excerpt) > MAX_EXCERPT_LINES:
            raise ContextVariantError(f"{role}_packet context_excerpt must be null or a bounded line array")
        for line in excerpt:
            if not isinstance(line, dict) or set(line) not in (
                {"line", "text"},
                {"line", "text", "truncated"},
            ):
                raise ContextVariantError(
                    f"{role}_packet excerpt lines must contain line and text, with optional truncated"
                )
            line_number = _nonnegative_int(line.get("line"), f"{role}_packet excerpt line", 1_000_000)
            if line_number < 1:
                raise ContextVariantError(f"{role}_packet excerpt line numbers must be positive")
            text = line.get("text")
            if not isinstance(text, str):
                raise ContextVariantError(f"{role}_packet excerpt text must be a string")
            if "truncated" in line and type(line["truncated"]) is not bool:
                raise ContextVariantError(f"{role}_packet excerpt truncated flag must be a boolean")
            excerpt_characters += len(text)
            excerpt_bytes += len(text.encode("utf-8"))
            excerpt_lines += 1
            if excerpt_bytes > MAX_EXCERPT_TEXT_BYTES:
                raise ContextVariantError("combined excerpt text exceeds the 2000000-byte limit")

    coverage = packet.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("semantic_coverage") != "NOT_EVALUATED":
        raise ContextVariantError(f"{role}_packet must keep semantic_coverage=NOT_EVALUATED")
    if coverage.get("sufficiency_decision") != "NOT_EVALUATED":
        raise ContextVariantError(f"{role}_packet must keep sufficiency_decision=NOT_EVALUATED")
    required = _id_list(coverage.get("required"), f"{role}_packet required obligations")
    declared = _id_list(coverage.get("declared_present"), f"{role}_packet declared_present obligations")
    source_required = _id_list(coverage.get("source_required_present"), f"{role}_packet source_required_present obligations")
    missing = _id_list(coverage.get("missing"), f"{role}_packet missing obligations")
    stale_or_invalid = _id_list(coverage.get("stale_or_invalid"), f"{role}_packet stale_or_invalid obligations")
    generated_only = _id_list(coverage.get("generated_only"), f"{role}_packet generated_only obligations")
    all_required = set(required)
    for label, values in (
        ("declared_present", declared),
        ("source_required_present", source_required),
        ("missing", missing),
        ("stale_or_invalid", stale_or_invalid),
        ("generated_only", generated_only),
    ):
        if not set(values) <= all_required:
            raise ContextVariantError(f"{role}_packet {label} references an unknown obligation")
    if not set(source_required) <= set(declared):
        raise ContextVariantError(f"{role}_packet source_required_present must be included in declared_present")
    if set(declared) & (set(missing) | set(stale_or_invalid) | set(generated_only)):
        raise ContextVariantError(f"{role}_packet coverage declares one obligation in conflicting states")
    if not isinstance(packet.get("budgets"), dict):
        raise ContextVariantError(f"{role}_packet budgets must be an object")
    source_bytes_read_reported = _nonnegative_int(
        packet["budgets"].get("source_bytes_read"),
        f"{role}_packet budgets.source_bytes_read",
        1_000_000,
    )
    if item_source_bytes_reported != source_bytes_read_reported:
        raise ContextVariantError(f"{role}_packet item source-byte counts do not sum to the packet budget")
    return {
        "packet_id": packet_id,
        "operation_or_question_id": operation_id,
        "current_ref": packet["current_ref"],
        "packet_status": packet["packet_status"],
        "required_obligation_ids": required,
        "declared_present_obligation_ids": declared,
        "source_required_present_obligation_ids": source_required,
        "missing_obligation_ids": missing,
        "stale_or_invalid_obligation_ids": stale_or_invalid,
        "generated_only_obligation_ids": generated_only,
        "context_item_count": len(items),
        "current_digest_item_ids_caller_packet_declared": current_digest_items,
        "unique_source_digest_count": len(source_identities),
        "excerpt_line_count": excerpt_lines,
        "excerpt_text_characters": excerpt_characters,
        "excerpt_text_utf8_bytes": excerpt_bytes,
        "source_bytes_read_reported_by_packet": source_bytes_read_reported,
        "item_source_bytes_reported_sum": item_source_bytes_reported,
    }


def compare_context_packets(request: Any, *, raw_input_sha256: str) -> dict[str, Any]:
    if not isinstance(request, dict) or set(request) != {
        "comparison_id",
        "baseline_packet",
        "candidate_packet",
    }:
        raise ContextVariantError("request must contain exactly comparison_id, baseline_packet, candidate_packet")
    comparison_id = _identifier(request["comparison_id"], "comparison_id")
    baseline = _packet_summary(request["baseline_packet"], "baseline")
    candidate = _packet_summary(request["candidate_packet"], "candidate")
    if baseline["packet_id"] == candidate["packet_id"]:
        raise ContextVariantError("baseline and candidate packet_id values must differ")
    if baseline["operation_or_question_id"] != candidate["operation_or_question_id"]:
        raise ContextVariantError("baseline and candidate must declare the same operation_or_question_id")
    if baseline["current_ref"] != candidate["current_ref"]:
        raise ContextVariantError("baseline and candidate must declare the same current_ref")
    if baseline["required_obligation_ids"] != candidate["required_obligation_ids"]:
        raise ContextVariantError("baseline and candidate must declare the same ordered required obligations")
    baseline_source = set(baseline["source_required_present_obligation_ids"])
    candidate_source = set(candidate["source_required_present_obligation_ids"])
    baseline_declared = set(baseline["declared_present_obligation_ids"])
    candidate_declared = set(candidate["declared_present_obligation_ids"])
    byte_delta = candidate["excerpt_text_utf8_bytes"] - baseline["excerpt_text_utf8_bytes"]
    baseline_bytes = baseline["excerpt_text_utf8_bytes"]
    return {
        "schema_version": "toolbox-context-packet-variant-comparison-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "comparison_id": comparison_id,
        "input_sha256": raw_input_sha256,
        "comparison_status": "MATCHED_STRUCTURAL_COMPARISON",
        "matched_task_binding": {
            "operation_or_question_id": baseline["operation_or_question_id"],
            "current_ref": baseline["current_ref"],
            "required_obligation_ids": baseline["required_obligation_ids"],
            "binding_basis": "CALLER_DECLARED_PACKET_FIELDS_NOT_INDEPENDENTLY_AUTHENTICATED",
        },
        "baseline": baseline,
        "candidate": candidate,
        "deltas": {
            "candidate_minus_baseline_excerpt_text_utf8_bytes": byte_delta,
            "candidate_excerpt_byte_reduction_fraction": (
                round(-byte_delta / baseline_bytes, 6) if baseline_bytes else None
            ),
            "dropped_declared_obligation_ids": sorted(baseline_declared - candidate_declared),
            "added_declared_obligation_ids": sorted(candidate_declared - baseline_declared),
            "dropped_source_required_obligation_ids": sorted(baseline_source - candidate_source),
            "added_source_required_obligation_ids": sorted(candidate_source - baseline_source),
        },
        "interpretation": {
            "semantic_relevance": "NOT_EVALUATED",
            "semantic_coverage": "NOT_EVALUATED",
            "task_outcome_comparison": "NOT_PERFORMED",
            "provider_token_usage": "NOT_MEASURED",
            "provider_billing_cost": "NOT_MEASURED",
            "caller_packet_authenticity": "NOT_VERIFIED",
            "sufficiency_decision": "NOT_EVALUATED",
            "execution_authorized": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded two-packet comparison")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        print("CONTEXT_VARIANTS_NOT_AVAILABLE: request exceeds the 256000-byte limit", file=sys.stderr)
        return 2
    try:
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        result = compare_context_packets(request, raw_input_sha256=hashlib.sha256(raw).hexdigest())
    except (UnicodeDecodeError, json.JSONDecodeError, ContextVariantError, RecursionError) as exc:
        print("CONTEXT_VARIANTS_NOT_AVAILABLE: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
