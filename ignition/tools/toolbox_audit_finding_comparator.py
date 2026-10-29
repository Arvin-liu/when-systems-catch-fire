#!/usr/bin/env python3
"""Compare caller-declared audit findings without adjudicating them."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any


TOOL_ID = "maintenance.compare_audit_findings"
TOOL_VERSION = "0.1.0"
REQUEST_SCHEMA_VERSION = "toolbox-audit-finding-comparison-request-r0"
OUTPUT_SCHEMA_VERSION = "toolbox-audit-finding-comparison-r0"
MAX_REQUEST_BYTES = 256_000
MAX_FINDINGS = 100
MAX_EVIDENCE_REFS = 20
MAX_TEXT_CHARS = 512
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DISPOSITIONS = {"CONFIRMED", "NEEDS_VALIDATION", "REJECTED", "OUT_OF_SCOPE"}


class AuditFindingComparisonError(ValueError):
    """Raised when an audit-comparison request is malformed or incomparable."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditFindingComparisonError(f"duplicate JSON input key: {key}")
        result[key] = value
    return result


def _text(value: Any, field: str, *, identifier: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT_CHARS:
        raise AuditFindingComparisonError(f"{field} must be nonblank text of at most {MAX_TEXT_CHARS} characters")
    if any(ord(char) < 32 for char in value):
        raise AuditFindingComparisonError(f"{field} must not contain control characters")
    if identifier and ID_RE.fullmatch(value) is None:
        raise AuditFindingComparisonError(f"{field} must use the bounded identifier format")
    return value


def _exact_object(value: Any, keys: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise AuditFindingComparisonError(f"{field} must contain exactly {sorted(keys)}")
    return value


def _evidence_refs(value: Any, field: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > MAX_EVIDENCE_REFS:
        raise AuditFindingComparisonError(f"{field} must contain at most {MAX_EVIDENCE_REFS} references")
    refs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(value):
        item = _exact_object(row, {"ref", "sha256"}, f"{field}[{index}]")
        ref = _text(item["ref"], f"{field}[{index}].ref")
        digest = item["sha256"]
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            raise AuditFindingComparisonError(f"{field}[{index}].sha256 must be a lowercase SHA-256")
        identity = (ref, digest)
        if identity in seen:
            raise AuditFindingComparisonError(f"{field} must not contain duplicate reference identities")
        seen.add(identity)
        refs.append({"ref": ref, "sha256": digest})
    return sorted(refs, key=lambda item: (item["ref"], item["sha256"]))


def _review(value: Any, role: str) -> dict[str, Any]:
    keys = {"audit_id", "reviewer_ref", "scope_ref", "target_ref", "target_revision", "findings"}
    review = _exact_object(value, keys, role)
    normalized = {
        "audit_id": _text(review["audit_id"], f"{role}.audit_id", identifier=True),
        "reviewer_ref": _text(review["reviewer_ref"], f"{role}.reviewer_ref", identifier=True),
        "scope_ref": _text(review["scope_ref"], f"{role}.scope_ref"),
        "target_ref": _text(review["target_ref"], f"{role}.target_ref"),
        "target_revision": _text(review["target_revision"], f"{role}.target_revision"),
        "findings": {},
    }
    findings = review["findings"]
    if not isinstance(findings, list) or len(findings) > MAX_FINDINGS:
        raise AuditFindingComparisonError(f"{role}.findings must contain at most {MAX_FINDINGS} findings")
    for index, raw_finding in enumerate(findings):
        finding = _exact_object(raw_finding, {"finding_id", "disposition", "evidence_refs"}, f"{role}.findings[{index}]")
        finding_id = _text(finding["finding_id"], f"{role}.findings[{index}].finding_id", identifier=True)
        if finding_id in normalized["findings"]:
            raise AuditFindingComparisonError(f"{role}.finding_id values must be unique")
        disposition = finding["disposition"]
        if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
            raise AuditFindingComparisonError(f"{role}.findings[{index}].disposition is unsupported")
        normalized["findings"][finding_id] = {
            "disposition": disposition,
            "evidence_refs": _evidence_refs(finding["evidence_refs"], f"{role}.findings[{index}].evidence_refs"),
        }
    return normalized


def compare_audit_findings(request: Any, *, raw_input_sha256: str) -> dict[str, Any]:
    """Return record-level coverage and disagreement; never decide audit truth."""
    expected = {"schema_version", "comparison_id", "primary_audit", "second_review"}
    request_obj = _exact_object(request, expected, "request")
    if request_obj["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise AuditFindingComparisonError("request.schema_version is unsupported")
    comparison_id = _text(request_obj["comparison_id"], "comparison_id", identifier=True)
    primary = _review(request_obj["primary_audit"], "primary_audit")
    second = _review(request_obj["second_review"], "second_review")
    if primary["audit_id"] == second["audit_id"]:
        raise AuditFindingComparisonError("audit_id values must differ to compare two records")
    for field in ("scope_ref", "target_ref", "target_revision"):
        if primary[field] != second[field]:
            raise AuditFindingComparisonError(f"primary_audit and second_review must have identical {field}")

    rows: list[dict[str, Any]] = []
    counts = {
        "primary_only": 0,
        "second_review_only": 0,
        "shared": 0,
        "disposition_agreements": 0,
        "disposition_disagreements": 0,
        "evidence_reference_sets_equal": 0,
        "evidence_reference_sets_different": 0,
    }
    for finding_id in sorted(set(primary["findings"]) | set(second["findings"])):
        left = primary["findings"].get(finding_id)
        right = second["findings"].get(finding_id)
        if left is None:
            relation = "ONLY_IN_SECOND_REVIEW"
            counts["second_review_only"] += 1
        elif right is None:
            relation = "ONLY_IN_PRIMARY_AUDIT"
            counts["primary_only"] += 1
        else:
            counts["shared"] += 1
            relation = "DISPOSITION_AGREES" if left["disposition"] == right["disposition"] else "DISPOSITION_DIFFERS"
            if relation == "DISPOSITION_AGREES":
                counts["disposition_agreements"] += 1
            else:
                counts["disposition_disagreements"] += 1
            if left["evidence_refs"] == right["evidence_refs"]:
                counts["evidence_reference_sets_equal"] += 1
            else:
                counts["evidence_reference_sets_different"] += 1
        rows.append({
            "finding_id": finding_id,
            "record_relation": relation,
            "primary_disposition_as_declared": left["disposition"] if left else None,
            "second_review_disposition_as_declared": right["disposition"] if right else None,
            "primary_evidence_refs_as_declared": left["evidence_refs"] if left else [],
            "second_review_evidence_refs_as_declared": right["evidence_refs"] if right else [],
        })

    reviewer_relation = (
        "SAME_CALLER_DECLARED_REVIEWER_REFERENCE"
        if primary["reviewer_ref"] == second["reviewer_ref"]
        else "DISTINCT_CALLER_DECLARED_REVIEWER_REFERENCES_IDENTITY_UNVERIFIED"
    )
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "comparison_id": comparison_id,
        "input_sha256": raw_input_sha256,
        "comparison_status": "CALLER_DECLARED_AUDIT_RECORDS_COMPARED",
        "target_binding": {
            "scope_ref": primary["scope_ref"],
            "target_ref": primary["target_ref"],
            "target_revision": primary["target_revision"],
            "basis": "CALLER_DECLARED_MATCHING_FIELDS_NOT_AUTHENTICATED",
        },
        "reviewer_binding": {
            "primary_reviewer_ref": primary["reviewer_ref"],
            "second_review_reviewer_ref": second["reviewer_ref"],
            "relation": reviewer_relation,
            "reviewer_identity_authenticated": False,
            "reviewer_independence_established": False,
        },
        "audit_ids": {
            "primary_audit_id": primary["audit_id"],
            "second_review_audit_id": second["audit_id"],
        },
        "summary": counts,
        "findings": rows,
        "interpretation": {
            "dispositions": "CALLER_DECLARED_NOT_ADJUDICATED",
            "evidence_authenticity": "NOT_VERIFIED",
            "claim_truth": "NOT_EVALUATED",
            "reviewer_independence": "NOT_ESTABLISHED",
            "decision_authority": "NONE",
            "execution_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded JSON request from stdin")
    args = parser.parse_args()
    if not args.stdin:
        parser.error("--stdin is required")
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        print(f"AUDIT_FINDING_COMPARISON_REJECTED: request exceeds {MAX_REQUEST_BYTES}-byte limit", file=sys.stderr)
        return 2
    try:
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        result = compare_audit_findings(request, raw_input_sha256=hashlib.sha256(raw).hexdigest())
    except (UnicodeDecodeError, json.JSONDecodeError, AuditFindingComparisonError) as exc:
        print(f"AUDIT_FINDING_COMPARISON_REJECTED: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
