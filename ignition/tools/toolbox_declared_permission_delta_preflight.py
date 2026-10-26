#!/usr/bin/env python3
"""Report exact set differences between two caller-supplied permission snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any


TOOL_ID = "governance.preflight_declared_permission_delta"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = "declared-permission-delta-r0"
MAX_INPUT_BYTES = 131_072
MAX_GRANTS = 256
MAX_IDENTIFIER_BYTES = 64
MAX_SCOPE_BYTES = 512
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
ALLOWED_CAPABILITIES = {
    "filesystem.read",
    "filesystem.write",
    "network.connect",
    "process.execute",
    "secrets.read",
    "billing.use",
    "external_action.invoke",
    "syscalls.use",
}
CLAIM_CEILING = (
    "Exact string-set differences between two caller-supplied grant lists only. "
    "The tool does not resolve inheritance, wildcard or path containment semantics, "
    "authenticate snapshots, inspect an effective sandbox, enforce policy, or grant authority."
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
    max_bytes: int,
    identifier: bool = False,
) -> str | None:
    if not isinstance(value, str):
        _finding(findings, "INVALID", "STRING_REQUIRED", path)
        return None
    if not value.strip():
        _finding(findings, "INVALID", "NONBLANK_STRING_REQUIRED", path)
        return None
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        _finding(findings, "INVALID", "INVALID_UNICODE", path)
        return None
    if size > max_bytes:
        _finding(findings, "INVALID", "TEXT_LIMIT_EXCEEDED", path)
        return None
    if any(ord(char) < 32 for char in value):
        _finding(findings, "INVALID", "CONTROL_CHARACTER_FORBIDDEN", path)
        return None
    if identifier and not IDENTIFIER_RE.fullmatch(value):
        _finding(findings, "INVALID", "IDENTIFIER_INVALID", path)
        return None
    return value


def _snapshot(
    value: Any,
    path: str,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    row = _record(
        value,
        path,
        {"snapshot_id", "policy_id", "policy_revision", "subject_id", "grants"},
        {"snapshot_id", "policy_id", "policy_revision", "subject_id", "grants"},
        findings,
    )
    parsed: dict[str, Any] = {}
    for field in ("snapshot_id", "policy_id", "policy_revision", "subject_id"):
        parsed[field] = _text(
            row.get(field),
            f"{path}.{field}",
            findings,
            max_bytes=MAX_IDENTIFIER_BYTES,
            identifier=True,
        )

    grant_rows = row.get("grants")
    if not isinstance(grant_rows, list):
        _finding(findings, "INVALID", "ARRAY_REQUIRED", f"{path}.grants")
        grant_rows = []
    if len(grant_rows) > MAX_GRANTS:
        _finding(findings, "INVALID", "GRANT_LIMIT_EXCEEDED", f"{path}.grants")

    grants: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, value in enumerate(grant_rows[:MAX_GRANTS]):
        grant_path = f"{path}.grants[{index}]"
        grant = _record(
            value,
            grant_path,
            {"capability", "scope"},
            {"capability", "scope"},
            findings,
        )
        capability = _text(
            grant.get("capability"),
            f"{grant_path}.capability",
            findings,
            max_bytes=64,
            identifier=True,
        )
        scope = _text(
            grant.get("scope"),
            f"{grant_path}.scope",
            findings,
            max_bytes=MAX_SCOPE_BYTES,
        )
        if capability is not None and capability not in ALLOWED_CAPABILITIES:
            _finding(findings, "INVALID", "CAPABILITY_UNSUPPORTED", f"{grant_path}.capability")
        if capability is not None and scope is not None:
            key = (capability, scope)
            if key in seen:
                _finding(findings, "INVALID", "DUPLICATE_GRANT", grant_path)
            else:
                seen.add(key)
                grants.append({"capability": capability, "scope": scope})

    parsed["grants"] = grants
    return parsed


def _report(
    status: str,
    digest: str,
    findings: list[dict[str, str]],
    *,
    baseline: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
    added: list[dict[str, str]] | None = None,
    removed: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "declared-permission-delta-result-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "input_sha256": digest,
        "baseline_binding": {
            field: baseline.get(field) if baseline else None
            for field in ("snapshot_id", "policy_id", "policy_revision", "subject_id")
        },
        "candidate_binding": {
            field: candidate.get(field) if candidate else None
            for field in ("snapshot_id", "policy_id", "policy_revision", "subject_id")
        },
        "counts": {
            "baseline_grants": len(baseline["grants"]) if baseline else 0,
            "candidate_grants": len(candidate["grants"]) if candidate else 0,
            "declared_additions": len(added or []),
            "declared_removals": len(removed or []),
        },
        "declared_additions": added or [],
        "declared_removals": removed or [],
        "effective_policy_resolved": False,
        "snapshot_authenticity": "NOT_ESTABLISHED",
        "sandbox_enforced": False,
        "permission_granted": False,
        "owner_authorization_granted": False,
        "network_requests": 0,
        "repository_writes": 0,
        "claim_ceiling": CLAIM_CEILING,
        "findings": sorted(findings, key=lambda item: (item["path"], item["code"], item["kind"])),
    }


def validate_document(document: Any, raw_digest: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    root = _record(
        document,
        "$",
        {"schema_version", "baseline", "candidate"},
        {"schema_version", "baseline", "candidate"},
        findings,
    )
    if root.get("schema_version") != SCHEMA_VERSION:
        _finding(findings, "INVALID", "SCHEMA_VERSION_UNSUPPORTED", "$.schema_version")

    baseline = _snapshot(root.get("baseline"), "$.baseline", findings)
    candidate = _snapshot(root.get("candidate"), "$.candidate", findings)
    for field in ("policy_id", "subject_id"):
        if baseline.get(field) is not None and candidate.get(field) is not None and baseline[field] != candidate[field]:
            _finding(findings, "INVALID", "COMPARISON_BINDING_MISMATCH", f"$.{field}")

    if any(item["kind"] == "INVALID" for item in findings):
        return _report("INPUT_INVALID", raw_digest, findings)

    baseline_set = {(row["capability"], row["scope"]) for row in baseline["grants"]}
    candidate_set = {(row["capability"], row["scope"]) for row in candidate["grants"]}
    added_pairs = sorted(candidate_set - baseline_set)
    removed_pairs = sorted(baseline_set - candidate_set)
    added = [{"capability": capability, "scope": scope} for capability, scope in added_pairs]
    removed = [{"capability": capability, "scope": scope} for capability, scope in removed_pairs]
    if added and removed:
        status = "MIXED_DECLARED_DIFF_REVIEW_REQUIRED"
    elif added:
        status = "DECLARED_ADDITIONS_REVIEW_REQUIRED"
    elif removed:
        status = "DECLARED_REMOVALS_REVIEW_REQUIRED"
    else:
        status = "NO_EXACT_DECLARED_DIFF"
    return _report(status, raw_digest, findings, baseline=baseline, candidate=candidate, added=added, removed=removed)


def analyze_bytes(payload: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) > MAX_INPUT_BYTES:
        return _report(
            "INPUT_INVALID",
            digest,
            [{"kind": "INVALID", "code": "INPUT_LIMIT_EXCEEDED", "path": "$"}],
        )
    try:
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except DuplicateJSONKey:
        return _report("INPUT_INVALID", digest, [{"kind": "INVALID", "code": "DUPLICATE_JSON_KEY", "path": "$"}])
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return _report("INPUT_INVALID", digest, [{"kind": "INVALID", "code": "JSON_INVALID", "path": "$"}])
    return validate_document(document, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded UTF-8 JSON request from stdin")
    args = parser.parse_args(argv)
    if not args.stdin:
        parser.error("--stdin is required; no file, network, policy-apply, or output-path option is supported")
    payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    result = analyze_bytes(payload)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 2 if result["status"] == "INPUT_INVALID" else 0


if __name__ == "__main__":
    raise SystemExit(main())
