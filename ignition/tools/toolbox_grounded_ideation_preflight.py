#!/usr/bin/env python3
"""Preflight one caller-supplied grounded research-ideation packet."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import re
import sys
from typing import Any


TOOL_ID = "research.preflight_grounded_ideation"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = "grounded-ideation-preflight-r0"
MAX_INPUT_BYTES = 262_144
MAX_SOURCES = 32
MAX_ANCHORS = 128
MAX_MAPPINGS = 32
MAX_TEXT_BYTES = 4_096
MAX_EXCERPT_BYTES = 16_384
MAX_QUOTE_BYTES = 2_048
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CLAIM_CEILING = (
    "Checks structure and exact quote-substring presence inside caller-supplied excerpts only. "
    "It does not authenticate sources, verify semantic support or novelty, establish a mechanism, "
    "perform independent review, run experiments, or accept a scientific claim."
)


class DuplicateJSONKey(ValueError):
    """Raised when a JSON object repeats a key."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(key)
        result[key] = value
    return result


def _utf8_size(value: str) -> int | None:
    try:
        return len(value.encode("utf-8"))
    except UnicodeEncodeError:
        return None


def _report(
    status: str,
    digest: str,
    findings: list[dict[str, str]],
    *,
    source_count: int = 0,
    used_source_count: int = 0,
    attached_source_count: int = 0,
    anchor_count: int = 0,
    mapping_count: int = 0,
) -> dict[str, Any]:
    ordered = sorted(findings, key=lambda item: (item["path"], item["code"], item["kind"]))
    return {
        "schema_version": "grounded-ideation-preflight-result-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "input_sha256": digest,
        "counts": {
            "sources": source_count,
            "used_sources": used_source_count,
            "attached_sources": attached_source_count,
            "anchors": anchor_count,
            "mechanism_mappings": mapping_count,
        },
        "source_authenticity": "NOT_ESTABLISHED",
        "quote_check": "SUBSTRING_IN_CALLER_SUPPLIED_EXCERPT_ONLY",
        "semantic_support": "NOT_VERIFIED",
        "independent_review": "NOT_PERFORMED",
        "scientific_acceptance": "NOT_ESTABLISHED",
        "network_requests": 0,
        "repository_writes": 0,
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
        "findings": ordered,
    }


def _finding(findings: list[dict[str, str]], kind: str, code: str, path: str) -> None:
    findings.append({"kind": kind, "code": code, "path": path})


def _record(
    value: Any,
    path: str,
    allowed: set[str],
    required: set[str],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        _finding(findings, "INVALID", "OBJECT_REQUIRED", path)
        return {}
    for key in sorted(set(value) - allowed):
        _finding(findings, "INVALID", "UNKNOWN_FIELD", f"{path}.{key}")
    for key in sorted(required - set(value)):
        _finding(findings, "INVALID", "MISSING_FIELD", f"{path}.{key}")
    return value


def _text(
    value: Any,
    path: str,
    findings: list[dict[str, str]],
    *,
    max_bytes: int = MAX_TEXT_BYTES,
    allow_empty: bool = False,
) -> str | None:
    if not isinstance(value, str):
        _finding(findings, "INVALID", "STRING_REQUIRED", path)
        return None
    if not allow_empty and not value.strip():
        _finding(findings, "INVALID", "NONBLANK_STRING_REQUIRED", path)
        return None
    size = _utf8_size(value)
    if size is None:
        _finding(findings, "INVALID", "INVALID_UNICODE", path)
        return None
    if size > max_bytes:
        _finding(findings, "INVALID", "TEXT_LIMIT_EXCEEDED", path)
        return None
    return value


def _identifier(value: Any, path: str, findings: list[dict[str, str]]) -> str | None:
    text = _text(value, path, findings, max_bytes=64)
    if text is not None and not ID_RE.fullmatch(text):
        _finding(findings, "INVALID", "IDENTIFIER_INVALID", path)
        return None
    return text


def _string_list(
    value: Any,
    path: str,
    findings: list[dict[str, str]],
    *,
    min_items: int = 0,
    max_items: int = 64,
    identifiers: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        _finding(findings, "INVALID", "ARRAY_REQUIRED", path)
        return []
    if len(value) > max_items:
        _finding(findings, "INVALID", "ITEM_LIMIT_EXCEEDED", path)
    if len(value) < min_items:
        _finding(findings, "INCOMPLETE", "REQUIRED_ITEMS_ABSENT", path)
    result: list[str] = []
    for index, item in enumerate(value[:max_items]):
        item_path = f"{path}[{index}]"
        text = _identifier(item, item_path, findings) if identifiers else _text(item, item_path, findings)
        if text is not None:
            result.append(text)
    if len(result) != len(set(result)):
        _finding(findings, "INVALID", "DUPLICATE_ITEMS", path)
    return result


def _date(value: Any, path: str, findings: list[dict[str, str]], *, nullable: bool) -> date | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        _finding(findings, "INVALID", "ISO_DATE_REQUIRED", path)
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        _finding(findings, "INVALID", "ISO_DATE_INVALID", path)
        return None


def validate_document(document: Any, raw_digest: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    root = _record(
        document,
        "$",
        {"schema_version", "task", "sources", "anchors", "gap", "mechanism_transfer", "proposal"},
        {"schema_version", "task", "sources", "anchors", "gap", "mechanism_transfer", "proposal"},
        findings,
    )
    if root.get("schema_version") != SCHEMA_VERSION:
        _finding(findings, "INVALID", "SCHEMA_VERSION_UNSUPPORTED", "$.schema_version")

    task = _record(root.get("task"), "$.task", {"question", "cutoff_date"}, {"question", "cutoff_date"}, findings)
    _text(task.get("question"), "$.task.question", findings)
    cutoff = _date(task.get("cutoff_date"), "$.task.cutoff_date", findings, nullable=True)

    source_rows = root.get("sources")
    if not isinstance(source_rows, list):
        _finding(findings, "INVALID", "ARRAY_REQUIRED", "$.sources")
        source_rows = []
    if len(source_rows) > MAX_SOURCES:
        _finding(findings, "INVALID", "SOURCE_LIMIT_EXCEEDED", "$.sources")
    sources: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(source_rows[:MAX_SOURCES]):
        path = f"$.sources[{index}]"
        row = _record(
            value,
            path,
            {"source_id", "citation", "revision", "usage", "publication_date", "excerpt"},
            {"source_id", "citation", "revision", "usage", "publication_date", "excerpt"},
            findings,
        )
        source_id = _identifier(row.get("source_id"), f"{path}.source_id", findings)
        citation = _text(row.get("citation"), f"{path}.citation", findings)
        revision = _text(row.get("revision"), f"{path}.revision", findings)
        usage = row.get("usage")
        if not isinstance(usage, str) or usage not in {"USED", "ATTACHED"}:
            _finding(findings, "INVALID", "SOURCE_USAGE_INVALID", f"{path}.usage")
        publication_date = _date(row.get("publication_date"), f"{path}.publication_date", findings, nullable=True)
        excerpt = _text(
            row.get("excerpt"),
            f"{path}.excerpt",
            findings,
            max_bytes=MAX_EXCERPT_BYTES,
            allow_empty=True,
        )
        if source_id:
            if source_id in sources:
                _finding(findings, "INVALID", "DUPLICATE_SOURCE_ID", f"{path}.source_id")
            else:
                sources[source_id] = {
                    "citation": citation,
                    "revision": revision,
                    "usage": usage,
                    "publication_date": publication_date,
                    "excerpt": excerpt,
                }
                if usage == "USED" and cutoff is not None:
                    if publication_date is None:
                        _finding(findings, "INCOMPLETE", "USED_SOURCE_DATE_UNKNOWN", f"{path}.publication_date")
                    elif publication_date > cutoff:
                        _finding(findings, "INCOMPLETE", "USED_SOURCE_AFTER_CUTOFF", f"{path}.publication_date")

    anchor_rows = root.get("anchors")
    if not isinstance(anchor_rows, list):
        _finding(findings, "INVALID", "ARRAY_REQUIRED", "$.anchors")
        anchor_rows = []
    if len(anchor_rows) > MAX_ANCHORS:
        _finding(findings, "INVALID", "ANCHOR_LIMIT_EXCEEDED", "$.anchors")
    anchors: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(anchor_rows[:MAX_ANCHORS]):
        path = f"$.anchors[{index}]"
        row = _record(
            value,
            path,
            {"anchor_id", "source_id", "locator", "quote", "interpretation", "role"},
            {"anchor_id", "source_id", "locator", "quote", "interpretation", "role"},
            findings,
        )
        anchor_id = _identifier(row.get("anchor_id"), f"{path}.anchor_id", findings)
        source_id = _identifier(row.get("source_id"), f"{path}.source_id", findings)
        locator = _text(row.get("locator"), f"{path}.locator", findings)
        quote = _text(row.get("quote"), f"{path}.quote", findings, max_bytes=MAX_QUOTE_BYTES)
        interpretation = _text(row.get("interpretation"), f"{path}.interpretation", findings)
        role = row.get("role")
        allowed_roles = {"gap_support", "counterevidence", "mechanism", "proposal_context"}
        if not isinstance(role, str) or role not in allowed_roles:
            _finding(findings, "INVALID", "ANCHOR_ROLE_INVALID", f"{path}.role")
        if source_id and source_id not in sources:
            _finding(findings, "INCOMPLETE", "ANCHOR_SOURCE_UNRESOLVED", f"{path}.source_id")
        elif source_id:
            source = sources[source_id]
            if source["usage"] != "USED":
                _finding(findings, "INCOMPLETE", "ATTACHED_SOURCE_USED_AS_EVIDENCE", f"{path}.source_id")
            if quote and source["excerpt"] is not None and quote not in source["excerpt"]:
                _finding(findings, "INCOMPLETE", "QUOTE_NOT_FOUND_IN_SUPPLIED_EXCERPT", f"{path}.quote")
        if anchor_id:
            if anchor_id in anchors:
                _finding(findings, "INVALID", "DUPLICATE_ANCHOR_ID", f"{path}.anchor_id")
            else:
                anchors[anchor_id] = {
                    "source_id": source_id,
                    "role": role,
                    "locator": locator,
                    "quote": quote,
                    "interpretation": interpretation,
                }

    referenced_source_ids = {anchor.get("source_id") for anchor in anchors.values() if anchor.get("source_id")}
    for source_id, source in sources.items():
        if source["usage"] == "USED" and source_id not in referenced_source_ids:
            _finding(findings, "INCOMPLETE", "USED_SOURCE_HAS_NO_ANCHOR", f"$.sources[{source_id}]")

    gap = _record(
        root.get("gap"),
        "$.gap",
        {"candidate", "support_anchor_ids", "contrary_anchor_ids", "limitations", "abstention_rule"},
        {"candidate", "support_anchor_ids", "contrary_anchor_ids", "limitations", "abstention_rule"},
        findings,
    )
    _text(gap.get("candidate"), "$.gap.candidate", findings)
    _text(gap.get("abstention_rule"), "$.gap.abstention_rule", findings)
    support_ids = _string_list(
        gap.get("support_anchor_ids"), "$.gap.support_anchor_ids", findings, min_items=1, max_items=128, identifiers=True,
    )
    contrary_ids = _string_list(
        gap.get("contrary_anchor_ids"), "$.gap.contrary_anchor_ids", findings, min_items=1, max_items=128, identifiers=True,
    )
    _string_list(gap.get("limitations"), "$.gap.limitations", findings, min_items=1)
    for anchor_id in support_ids:
        anchor = anchors.get(anchor_id)
        if anchor is None or anchor["role"] != "gap_support":
            _finding(findings, "INCOMPLETE", "GAP_SUPPORT_ANCHOR_UNRESOLVED", f"$.gap.support_anchor_ids[{anchor_id}]")
    for anchor_id in contrary_ids:
        anchor = anchors.get(anchor_id)
        if anchor is None or anchor["role"] != "counterevidence":
            _finding(findings, "INCOMPLETE", "CONTRARY_ANCHOR_UNRESOLVED", f"$.gap.contrary_anchor_ids[{anchor_id}]")

    transfer = _record(
        root.get("mechanism_transfer"),
        "$.mechanism_transfer",
        {"source_domain", "target_domain", "failure_structure", "mappings", "necessary_conditions", "boundaries", "closest_in_domain_alternative"},
        {"source_domain", "target_domain", "failure_structure", "mappings", "necessary_conditions", "boundaries", "closest_in_domain_alternative"},
        findings,
    )
    source_domain = _text(transfer.get("source_domain"), "$.mechanism_transfer.source_domain", findings)
    target_domain = _text(transfer.get("target_domain"), "$.mechanism_transfer.target_domain", findings)
    if source_domain and target_domain and source_domain.casefold() == target_domain.casefold():
        _finding(findings, "INCOMPLETE", "TRANSFER_DOMAINS_NOT_DISTINCT", "$.mechanism_transfer")
    _text(transfer.get("failure_structure"), "$.mechanism_transfer.failure_structure", findings)
    _text(transfer.get("closest_in_domain_alternative"), "$.mechanism_transfer.closest_in_domain_alternative", findings)
    _string_list(transfer.get("necessary_conditions"), "$.mechanism_transfer.necessary_conditions", findings, min_items=1)
    _string_list(transfer.get("boundaries"), "$.mechanism_transfer.boundaries", findings, min_items=1)
    mappings = transfer.get("mappings")
    if not isinstance(mappings, list):
        _finding(findings, "INVALID", "ARRAY_REQUIRED", "$.mechanism_transfer.mappings")
        mappings = []
    if len(mappings) > MAX_MAPPINGS:
        _finding(findings, "INVALID", "MAPPING_LIMIT_EXCEEDED", "$.mechanism_transfer.mappings")
    if not mappings:
        _finding(findings, "INCOMPLETE", "MECHANISM_MAPPING_ABSENT", "$.mechanism_transfer.mappings")
    for index, value in enumerate(mappings[:MAX_MAPPINGS]):
        path = f"$.mechanism_transfer.mappings[{index}]"
        row = _record(value, path, {"source_relation", "target_relation_candidate", "anchor_ids", "assumptions"}, {"source_relation", "target_relation_candidate", "anchor_ids", "assumptions"}, findings)
        _text(row.get("source_relation"), f"{path}.source_relation", findings)
        _text(row.get("target_relation_candidate"), f"{path}.target_relation_candidate", findings)
        anchor_ids = _string_list(
            row.get("anchor_ids"), f"{path}.anchor_ids", findings, min_items=1, max_items=128, identifiers=True,
        )
        _string_list(row.get("assumptions"), f"{path}.assumptions", findings, min_items=1)
        for anchor_id in anchor_ids:
            anchor = anchors.get(anchor_id)
            if anchor is None or anchor["role"] != "mechanism":
                _finding(findings, "INCOMPLETE", "MECHANISM_ANCHOR_UNRESOLVED", f"{path}.anchor_ids[{anchor_id}]")

    proposal = _record(
        root.get("proposal"),
        "$.proposal",
        {"hypothesis", "minimum_experiment", "controls", "falsifiers", "uncertainties", "evidence_anchor_ids"},
        {"hypothesis", "minimum_experiment", "controls", "falsifiers", "uncertainties", "evidence_anchor_ids"},
        findings,
    )
    _text(proposal.get("hypothesis"), "$.proposal.hypothesis", findings)
    _text(proposal.get("minimum_experiment"), "$.proposal.minimum_experiment", findings)
    _string_list(proposal.get("controls"), "$.proposal.controls", findings, min_items=1)
    _string_list(proposal.get("falsifiers"), "$.proposal.falsifiers", findings, min_items=1)
    _string_list(proposal.get("uncertainties"), "$.proposal.uncertainties", findings, min_items=1)
    proposal_anchor_ids = _string_list(
        proposal.get("evidence_anchor_ids"), "$.proposal.evidence_anchor_ids", findings,
        min_items=1, max_items=128, identifiers=True,
    )
    for anchor_id in proposal_anchor_ids:
        if anchor_id not in anchors:
            _finding(findings, "INCOMPLETE", "PROPOSAL_ANCHOR_UNRESOLVED", f"$.proposal.evidence_anchor_ids[{anchor_id}]")

    invalid = any(item["kind"] == "INVALID" for item in findings)
    incomplete = any(item["kind"] == "INCOMPLETE" for item in findings)
    status = "INPUT_INVALID" if invalid else "INCOMPLETE" if incomplete else "PREFLIGHT_READY_FOR_HUMAN_REVIEW"
    used_count = sum(source.get("usage") == "USED" for source in sources.values())
    attached_count = sum(source.get("usage") == "ATTACHED" for source in sources.values())
    return _report(
        status,
        raw_digest,
        findings,
        source_count=len(sources),
        used_source_count=used_count,
        attached_source_count=attached_count,
        anchor_count=len(anchors),
        mapping_count=len(mappings),
    )


def analyze_bytes(payload: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) > MAX_INPUT_BYTES:
        return _report("INPUT_INVALID", digest, [{"kind": "INVALID", "code": "INPUT_LIMIT_EXCEEDED", "path": "$"}])
    try:
        decoded = payload.decode("utf-8")
        document = json.loads(decoded, object_pairs_hook=_unique_object)
    except DuplicateJSONKey:
        return _report("INPUT_INVALID", digest, [{"kind": "INVALID", "code": "DUPLICATE_JSON_KEY", "path": "$"}])
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return _report("INPUT_INVALID", digest, [{"kind": "INVALID", "code": "JSON_INVALID", "path": "$"}])
    return validate_document(document, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded UTF-8 JSON packet from stdin")
    args = parser.parse_args(argv)
    if not args.stdin:
        parser.error("--stdin is required; no file, network, or output-path option is supported")
    payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    result = analyze_bytes(payload)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0 if result["status"] == "PREFLIGHT_READY_FOR_HUMAN_REVIEW" else 2 if result["status"] == "INPUT_INVALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
