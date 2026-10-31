#!/usr/bin/env python3
"""Identify exact read-only validation invocations that may be reusable.

This tool only groups caller-supplied command records. It never executes a
command, reads a repository, changes CI, or authorizes sharing a result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any


MAX_INPUT_BYTES = 256 * 1024
MAX_PROFILES = 32
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class InvocationInputError(ValueError):
    """Raised when a command-profile comparison is malformed."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvocationInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InvocationInputError(f"non-standard JSON number is not allowed: {value}")


def _object(value: Any, path: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InvocationInputError(f"{path} must be an object")
    if set(value) != keys:
        missing = sorted(keys - set(value))
        extra = sorted(set(value) - keys)
        raise InvocationInputError(f"{path} keys mismatch (missing={missing}, extra={extra})")
    return value


def _nonblank(value: Any, path: str, maximum: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise InvocationInputError(f"{path} must be a nonblank string of at most {maximum} characters")
    if any(ord(char) < 32 for char in value):
        raise InvocationInputError(f"{path} must not contain control characters")
    return value


def _identifier(value: Any, path: str) -> str:
    result = _nonblank(value, path, maximum=96)
    if not ID_RE.fullmatch(result):
        raise InvocationInputError(f"{path} must be a bounded identifier")
    return result


def _digest(value: Any, path: str, pattern: re.Pattern[str]) -> str:
    result = _nonblank(value, path, maximum=64)
    if not pattern.fullmatch(result):
        raise InvocationInputError(f"{path} has an invalid digest")
    return result


def _working_directory(value: Any, path: str) -> str:
    result = _nonblank(value, path, maximum=256)
    if result.startswith("/") or "\\" in result:
        raise InvocationInputError(f"{path} must be a relative POSIX path")
    segments = result.split("/")
    if any(segment in {"", ".."} for segment in segments):
        raise InvocationInputError(f"{path} must not contain empty or parent segments")
    if result != "." and any(segment == "." for segment in segments):
        raise InvocationInputError(f"{path} must use canonical relative path segments")
    return result


def _parse(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise InvocationInputError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except InvocationInputError:
        raise
    except UnicodeDecodeError as exc:
        raise InvocationInputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise InvocationInputError("input must be valid JSON") from exc
    return _object(parsed, "root", {"schema_version", "evaluation_context", "profiles"})


def analyze(raw: bytes) -> dict[str, Any]:
    """Group exact invocation signatures and report non-authoritative candidates."""
    document = _parse(raw)
    if document["schema_version"] != "validation-invocation-dedup-input-r0":
        raise InvocationInputError("schema_version must be validation-invocation-dedup-input-r0")

    context = _object(
        document["evaluation_context"],
        "evaluation_context",
        {"evaluation_id", "source_ref", "analysis_purpose"},
    )
    evaluation_id = _identifier(context["evaluation_id"], "evaluation_context.evaluation_id")
    source_ref = _nonblank(context["source_ref"], "evaluation_context.source_ref")
    analysis_purpose = _nonblank(context["analysis_purpose"], "evaluation_context.analysis_purpose")

    profiles_raw = document["profiles"]
    if not isinstance(profiles_raw, list) or not 1 <= len(profiles_raw) <= MAX_PROFILES:
        raise InvocationInputError(f"profiles must contain 1 to {MAX_PROFILES} records")

    seen_ids: set[str] = set()
    grouped: dict[str, dict[str, Any]] = {}
    canonical_profiles: list[dict[str, Any]] = []
    profile_keys = {
        "profile_id",
        "argv",
        "working_directory",
        "source_tree_git_sha1",
        "runtime_fingerprint_sha256",
        "environment_fingerprint_sha256",
        "result_contract_id",
        "side_effect_class",
        "review_status",
        "evidence_ref",
    }

    for index, raw_profile in enumerate(profiles_raw):
        path = f"profiles[{index}]"
        profile = _object(raw_profile, path, profile_keys)
        profile_id = _identifier(profile["profile_id"], f"{path}.profile_id")
        if profile_id in seen_ids:
            raise InvocationInputError(f"duplicate profile_id: {profile_id}")
        seen_ids.add(profile_id)

        argv_raw = profile["argv"]
        if not isinstance(argv_raw, list) or not 1 <= len(argv_raw) <= 64:
            raise InvocationInputError(f"{path}.argv must contain 1 to 64 argument strings")
        argv = [_nonblank(arg, f"{path}.argv[{arg_index}]", maximum=2048) for arg_index, arg in enumerate(argv_raw)]
        if sum(len(arg) for arg in argv) > 8192:
            raise InvocationInputError(f"{path}.argv exceeds the aggregate argument limit")

        cwd = _working_directory(profile["working_directory"], f"{path}.working_directory")
        source_tree = _digest(profile["source_tree_git_sha1"], f"{path}.source_tree_git_sha1", SHA1_RE)
        runtime = _digest(profile["runtime_fingerprint_sha256"], f"{path}.runtime_fingerprint_sha256", SHA256_RE)
        environment = _digest(profile["environment_fingerprint_sha256"], f"{path}.environment_fingerprint_sha256", SHA256_RE)
        result_contract = _identifier(profile["result_contract_id"], f"{path}.result_contract_id")
        side_effect_class = profile["side_effect_class"]
        if side_effect_class not in {"READ_ONLY_VALIDATION", "EFFECTFUL_OR_UNKNOWN"}:
            raise InvocationInputError(f"{path}.side_effect_class has an unsupported value")
        review_status = profile["review_status"]
        if review_status not in {"SOURCE_REVIEWED_READ_ONLY", "NOT_REVIEWED"}:
            raise InvocationInputError(f"{path}.review_status has an unsupported value")
        evidence_ref = _nonblank(profile["evidence_ref"], f"{path}.evidence_ref")

        signature_fields = {
            "argv": argv,
            "working_directory": cwd,
            "source_tree_git_sha1": source_tree,
            "runtime_fingerprint_sha256": runtime,
            "environment_fingerprint_sha256": environment,
            "result_contract_id": result_contract,
        }
        signature_bytes = json.dumps(
            signature_fields,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        signature = hashlib.sha256(signature_bytes).hexdigest()
        group = grouped.setdefault(signature, {"signature_fields": signature_fields, "profiles": []})
        group["profiles"].append({
            "profile_id": profile_id,
            "side_effect_class": side_effect_class,
            "review_status": review_status,
            "evidence_ref": evidence_ref,
        })
        canonical_profiles.append({"profile_id": profile_id, **signature_fields})

    groups: list[dict[str, Any]] = []
    potential_duplicates = 0
    for signature, group in sorted(grouped.items(), key=lambda item: tuple(sorted(p["profile_id"] for p in item[1]["profiles"]))):
        profile_rows = sorted(group["profiles"], key=lambda row: row["profile_id"])
        is_duplicate = len(profile_rows) > 1
        all_read_only_reviewed = all(
            row["side_effect_class"] == "READ_ONLY_VALIDATION"
            and row["review_status"] == "SOURCE_REVIEWED_READ_ONLY"
            for row in profile_rows
        )
        reuse_status = (
            "POTENTIAL_READ_ONLY_REUSE"
            if is_duplicate and all_read_only_reviewed
            else "NOT_ESTABLISHED"
        )
        if is_duplicate and all_read_only_reviewed:
            potential_duplicates += len(profile_rows) - 1
        groups.append({
            "invocation_signature_sha256": signature,
            **group["signature_fields"],
            "profile_ids": [row["profile_id"] for row in profile_rows],
            "profile_count": len(profile_rows),
            "potential_duplicate_invocations": max(0, len(profile_rows) - 1),
            "reuse_candidate_status": reuse_status,
            "non_eligibility_reasons": (
                [] if reuse_status == "POTENTIAL_READ_ONLY_REUSE" else (
                    ["NO_DUPLICATE_SIGNATURE"] if not is_duplicate else ["SIDE_EFFECT_OR_REVIEW_NOT_ESTABLISHED"]
                )
            ),
            "review_evidence_refs": sorted({row["evidence_ref"] for row in profile_rows}),
        })

    input_sha256 = hashlib.sha256(raw).hexdigest()
    eligible_group_count = sum(group["reuse_candidate_status"] == "POTENTIAL_READ_ONLY_REUSE" for group in groups)
    return {
        "schema_version": "validation-invocation-dedup-output-r0",
        "evaluation_id": evaluation_id,
        "source_ref": source_ref,
        "analysis_purpose": analysis_purpose,
        "input_sha256": input_sha256,
        "profiles_analyzed": len(canonical_profiles),
        "invocation_group_count": len(groups),
        "potential_reuse_group_count": eligible_group_count,
        "potential_duplicate_invocations": potential_duplicates,
        "groups": groups,
        "non_claims": {
            "commands_executed": False,
            "execution_authorized": False,
            "results_authenticated": False,
            "semantic_equivalence_authenticated": False,
            "process_launches_saved": False,
            "runtime_or_cost_savings_established": False,
            "ci_or_required_checks_changed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded JSON document from stdin")
    args = parser.parse_args()
    if not args.stdin:
        parser.error("--stdin is required")
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        result = analyze(raw)
    except InvocationInputError as exc:
        sys.stderr.write(f"validation invocation deduplication rejected input: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
