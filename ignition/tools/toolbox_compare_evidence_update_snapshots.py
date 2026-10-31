#!/usr/bin/env python3
"""Compare two caller-supplied evidence-update snapshots without adjudication."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import re
import sys
from typing import Any


TOOL_ID = "research.compare_evidence_update_snapshots"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "ignition.toolbox-evidence-update-snapshot-comparison-input-r0"
OUTPUT_SCHEMA_VERSION = "ignition.toolbox-evidence-update-snapshot-comparison-output-r0"
MAX_INPUT_BYTES = 262_144
MAX_OUTPUT_BYTES = 262_144
MAX_EVIDENCE_ITEMS = 200
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@_+#-]{0,159}$")
FAMILY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
DEPENDENCE_MODES = {
    "INDEPENDENT",
    "PRIOR_SYNTHESIS_VISIBLE",
    "MIXED",
    "UNKNOWN",
}
RECORD_STATES = {
    "LINKED",
    "WITHDRAWN",
    "RETRACTED",
    "SUPERSEDED",
    "UNAVAILABLE",
    "UNKNOWN",
}
CLAIM_CEILING = (
    "Exact caller-declared snapshot and record deltas only. The tool does not read or authenticate sources, "
    "judge evidence quality, decide claim truth, infer a downgrade, identify causal reasons, establish scientific "
    "acceptance, or authorize an action."
)


class InputError(ValueError):
    """A bounded, non-echoing input contract error."""

    def __init__(self, code: str, path: str) -> None:
        super().__init__(code)
        self.code = code
        self.path = path


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("DUPLICATE_JSON_KEY", "$" )
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise InputError("NONSTANDARD_JSON_NUMBER", "$")


def _object(value: Any, path: str, required: set[str], optional: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError("OBJECT_REQUIRED", path)
    allowed = required | (optional or set())
    if set(value) - allowed:
        raise InputError("UNKNOWN_FIELD", path)
    if required - set(value):
        raise InputError("MISSING_FIELD", path)
    return value


def _string(
    value: Any,
    path: str,
    *,
    max_bytes: int,
    pattern: re.Pattern[str] | None = None,
    nullable: bool = False,
) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise InputError("NONBLANK_STRING_REQUIRED", path)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        raise InputError("INVALID_UNICODE", path) from None
    if len(encoded) > max_bytes:
        raise InputError("TEXT_LIMIT_EXCEEDED", path)
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise InputError("CONTROL_CHARACTER_FORBIDDEN", path)
    if pattern and not pattern.fullmatch(value):
        raise InputError("IDENTIFIER_INVALID", path)
    return value


def _digest(value: Any, path: str) -> str | None:
    parsed = _string(value, path, max_bytes=64, nullable=True)
    if parsed is not None and not SHA256_RE.fullmatch(parsed):
        raise InputError("SHA256_INVALID", path)
    return parsed


def _time(value: Any, path: str) -> str:
    parsed = _string(value, path, max_bytes=20)
    if parsed is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", parsed):
        raise InputError("UTC_TIMESTAMP_INVALID", path)
    try:
        datetime.strptime(parsed, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise InputError("UTC_TIMESTAMP_INVALID", path) from None
    return parsed


def _policy(value: Any, path: str) -> dict[str, Any]:
    row = _object(value, path, {"identity", "revision_digest"})
    identity = _string(row["identity"], f"{path}.identity", max_bytes=160, pattern=IDENTIFIER_RE)
    digest = _digest(row["revision_digest"], f"{path}.revision_digest")
    return {"identity": identity, "revision_digest": digest}


def _snapshot(value: Any, path: str) -> dict[str, Any]:
    fields = {
        "snapshot_id",
        "task_ref",
        "claim_id",
        "as_of",
        "scope_digest",
        "applicability_digest",
        "declared_claim_state",
        "change_reason",
        "evaluation_instrument",
        "update_policy",
        "stopping_policy",
        "acquisition_dependence",
        "evidence_items",
    }
    row = _object(value, path, fields)
    snapshot_id = _string(row["snapshot_id"], f"{path}.snapshot_id", max_bytes=160, pattern=IDENTIFIER_RE)
    task = _object(row["task_ref"], f"{path}.task_ref", {"task_id", "revision_digest"})
    task_id = _string(task["task_id"], f"{path}.task_ref.task_id", max_bytes=160, pattern=IDENTIFIER_RE)
    task_revision = _digest(task["revision_digest"], f"{path}.task_ref.revision_digest")
    claim_id = _string(row["claim_id"], f"{path}.claim_id", max_bytes=160, pattern=IDENTIFIER_RE)
    as_of = _object(row["as_of"], f"{path}.as_of", {"reference", "observed_at_utc"})
    as_of_ref = _string(as_of["reference"], f"{path}.as_of.reference", max_bytes=240)
    observed_at = _time(as_of["observed_at_utc"], f"{path}.as_of.observed_at_utc")
    scope_digest = _digest(row["scope_digest"], f"{path}.scope_digest")
    applicability_digest = _digest(row["applicability_digest"], f"{path}.applicability_digest")
    claim_state = _string(row["declared_claim_state"], f"{path}.declared_claim_state", max_bytes=96, pattern=IDENTIFIER_RE)

    reason = _object(row["change_reason"], f"{path}.change_reason", {"code", "reference"})
    reason_code = _string(reason["code"], f"{path}.change_reason.code", max_bytes=96, pattern=IDENTIFIER_RE)
    reason_ref = _string(reason["reference"], f"{path}.change_reason.reference", max_bytes=240, nullable=True)
    evaluation = _policy(row["evaluation_instrument"], f"{path}.evaluation_instrument")
    update_policy = _policy(row["update_policy"], f"{path}.update_policy")
    stopping_policy = _policy(row["stopping_policy"], f"{path}.stopping_policy")

    dependence = _string(row["acquisition_dependence"], f"{path}.acquisition_dependence", max_bytes=40)
    if dependence not in DEPENDENCE_MODES:
        raise InputError("ACQUISITION_DEPENDENCE_UNSUPPORTED", f"{path}.acquisition_dependence")

    item_rows = row["evidence_items"]
    if not isinstance(item_rows, list):
        raise InputError("ARRAY_REQUIRED", f"{path}.evidence_items")
    if len(item_rows) > MAX_EVIDENCE_ITEMS:
        raise InputError("EVIDENCE_ITEM_LIMIT_EXCEEDED", f"{path}.evidence_items")
    items: dict[str, dict[str, str | None]] = {}
    for index, item_value in enumerate(item_rows):
        item_path = f"{path}.evidence_items[{index}]"
        item = _object(item_value, item_path, {"evidence_id", "source_family", "record_state", "record_sha256"})
        evidence_id = _string(item["evidence_id"], f"{item_path}.evidence_id", max_bytes=160, pattern=IDENTIFIER_RE)
        source_family = _string(item["source_family"], f"{item_path}.source_family", max_bytes=64, pattern=FAMILY_RE)
        record_state = _string(item["record_state"], f"{item_path}.record_state", max_bytes=32, pattern=FAMILY_RE)
        if record_state not in RECORD_STATES:
            raise InputError("RECORD_STATE_UNSUPPORTED", f"{item_path}.record_state")
        record_digest = _digest(item["record_sha256"], f"{item_path}.record_sha256")
        if evidence_id in items:
            raise InputError("DUPLICATE_EVIDENCE_ID", item_path)
        items[evidence_id] = {
            "source_family": source_family,
            "record_state": record_state,
            "record_sha256": record_digest,
        }

    return {
        "snapshot_id": snapshot_id,
        "task_ref": {"task_id": task_id, "revision_digest": task_revision},
        "claim_id": claim_id,
        "as_of": {"reference": as_of_ref, "observed_at_utc": observed_at},
        "scope_digest": scope_digest,
        "applicability_digest": applicability_digest,
        "declared_claim_state": claim_state,
        "change_reason": {"code": reason_code, "reference": reason_ref},
        "evaluation_instrument": evaluation,
        "update_policy": update_policy,
        "stopping_policy": stopping_policy,
        "acquisition_dependence": dependence,
        "evidence_items": items,
    }


def _field_delta(before: Any, after: Any, *, known_when: Any = None) -> dict[str, Any]:
    known = before is not None and after is not None
    if known_when is not None:
        known = known and before != known_when and after != known_when
    return {"before": before, "after": after, "changed": before != after, "known": known}


def _policy_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "identity": _field_delta(before["identity"], after["identity"], known_when="UNKNOWN"),
        "revision_digest": _field_delta(before["revision_digest"], after["revision_digest"]),
    }


def _compare(request: dict[str, Any], input_sha256: str) -> dict[str, Any]:
    if request.get("schema_version") != INPUT_SCHEMA_VERSION:
        raise InputError("SCHEMA_VERSION_UNSUPPORTED", "$.schema_version")
    comparison_id = _string(request.get("comparison_id"), "$.comparison_id", max_bytes=160, pattern=IDENTIFIER_RE)
    before = _snapshot(request.get("baseline_snapshot"), "$.baseline_snapshot")
    after = _snapshot(request.get("candidate_snapshot"), "$.candidate_snapshot")
    if before["task_ref"]["task_id"] != after["task_ref"]["task_id"]:
        raise InputError("TASK_BINDING_MISMATCH", "$.candidate_snapshot.task_ref.task_id")
    if before["claim_id"] != after["claim_id"]:
        raise InputError("CLAIM_BINDING_MISMATCH", "$.candidate_snapshot.claim_id")
    if after["as_of"]["observed_at_utc"] <= before["as_of"]["observed_at_utc"]:
        raise InputError("CANDIDATE_AS_OF_NOT_LATER", "$.candidate_snapshot.as_of.observed_at_utc")

    evidence_before: dict[str, dict[str, str | None]] = before["evidence_items"]
    evidence_after: dict[str, dict[str, str | None]] = after["evidence_items"]
    before_ids, after_ids = set(evidence_before), set(evidence_after)
    added_ids = sorted(after_ids - before_ids)
    removed_ids = sorted(before_ids - after_ids)
    retained_ids: list[str] = []
    changed_records: list[dict[str, Any]] = []
    unresolved_records: list[dict[str, Any]] = []
    withdrawal_transitions: list[dict[str, str]] = []

    for evidence_id in sorted(before_ids & after_ids):
        old = evidence_before[evidence_id]
        new = evidence_after[evidence_id]
        changed_fields: list[dict[str, Any]] = []
        unknown_fields: list[str] = []
        for field in ("source_family", "record_state", "record_sha256"):
            old_value, new_value = old[field], new[field]
            unknown = old_value is None or new_value is None or old_value == "UNKNOWN" or new_value == "UNKNOWN"
            if unknown:
                unknown_fields.append(field)
            if old_value != new_value and not unknown:
                changed_fields.append({"field": field, "before": old_value, "after": new_value})
        if changed_fields:
            changed_records.append({"evidence_id": evidence_id, "changed_fields": changed_fields})
        if unknown_fields:
            unresolved_records.append({"evidence_id": evidence_id, "unknown_fields": unknown_fields})
        if not changed_fields and not unknown_fields:
            retained_ids.append(evidence_id)
        if old["record_state"] not in {"WITHDRAWN", "RETRACTED"} and new["record_state"] in {"WITHDRAWN", "RETRACTED"}:
            withdrawal_transitions.append({
                "evidence_id": evidence_id,
                "before_state": str(old["record_state"]),
                "after_state": str(new["record_state"]),
            })

    before_family_counts = Counter(row["source_family"] for row in evidence_before.values())
    after_family_counts = Counter(row["source_family"] for row in evidence_after.values())
    families = sorted(set(before_family_counts) | set(after_family_counts))
    family_delta = [
        {
            "source_family": family,
            "baseline_count": before_family_counts[family],
            "candidate_count": after_family_counts[family],
            "delta": after_family_counts[family] - before_family_counts[family],
        }
        for family in families
    ]

    scope_delta = _field_delta(before["scope_digest"], after["scope_digest"])
    applicability_delta = _field_delta(before["applicability_digest"], after["applicability_digest"])
    state_delta = _field_delta(before["declared_claim_state"], after["declared_claim_state"], known_when="UNKNOWN")
    task_revision_delta = _field_delta(before["task_ref"]["revision_digest"], after["task_ref"]["revision_digest"])
    evaluation_delta = _policy_delta(before["evaluation_instrument"], after["evaluation_instrument"])
    update_policy_delta = _policy_delta(before["update_policy"], after["update_policy"])
    stopping_policy_delta = _policy_delta(before["stopping_policy"], after["stopping_policy"])
    dependence_delta = _field_delta(before["acquisition_dependence"], after["acquisition_dependence"], known_when="UNKNOWN")

    unknown_reasons: set[str] = set()
    if not task_revision_delta["known"] or task_revision_delta["changed"]:
        unknown_reasons.add("TASK_REVISION_CHANGED_OR_UNKNOWN")
    for name, delta in (
        ("SCOPE", scope_delta),
        ("APPLICABILITY", applicability_delta),
    ):
        if not delta["known"] or delta["changed"]:
            unknown_reasons.add(f"{name}_CHANGED_OR_UNKNOWN")
    for name, delta in (
        ("EVALUATION_INSTRUMENT", evaluation_delta),
        ("UPDATE_POLICY", update_policy_delta),
        ("STOPPING_POLICY", stopping_policy_delta),
    ):
        if any(not part["known"] or part["changed"] for part in delta.values()):
            unknown_reasons.add(f"{name}_CHANGED_OR_UNKNOWN")
    if not dependence_delta["known"] or dependence_delta["changed"]:
        unknown_reasons.add("ACQUISITION_DEPENDENCE_CHANGED_OR_UNKNOWN")
    if unresolved_records:
        unknown_reasons.add("EVIDENCE_RECORD_METADATA_UNKNOWN")
    if any(row["source_family"] == "UNKNOWN" or row["record_state"] == "UNKNOWN" or row["record_sha256"] is None for row in evidence_before.values()):
        unknown_reasons.add("BASELINE_EVIDENCE_METADATA_UNKNOWN")
    if any(row["source_family"] == "UNKNOWN" or row["record_state"] == "UNKNOWN" or row["record_sha256"] is None for row in evidence_after.values()):
        unknown_reasons.add("CANDIDATE_EVIDENCE_METADATA_UNKNOWN")

    review_triggers: set[str] = set()
    if removed_ids:
        review_triggers.add("EVIDENCE_ABSENT_FROM_CANDIDATE_SNAPSHOT")
    if changed_records:
        review_triggers.add("EVIDENCE_RECORD_FIELDS_CHANGED")
    if withdrawal_transitions:
        review_triggers.add("DECLARED_WITHDRAWAL_OR_RETRACTION")
    if state_delta["changed"]:
        review_triggers.add("CALLER_DECLARED_CLAIM_STATE_CHANGED")
    if scope_delta["changed"] or applicability_delta["changed"]:
        review_triggers.add("SCOPE_OR_APPLICABILITY_CHANGED")
    if unknown_reasons:
        review_triggers.add("COMPARABILITY_REVIEW_REQUIRED")
    if before["change_reason"]["code"] in {"UNKNOWN", "UNSPECIFIED"} or after["change_reason"]["code"] in {"UNKNOWN", "UNSPECIFIED"}:
        review_triggers.add("CHANGE_REASON_UNSPECIFIED")
    if after["acquisition_dependence"] in {"PRIOR_SYNTHESIS_VISIBLE", "MIXED"}:
        review_triggers.add("ACCUMULATION_BIAS_REVIEW_NOT_EVALUATED")

    known_delta = bool(
        added_ids
        or removed_ids
        or changed_records
        or scope_delta["changed"]
        or applicability_delta["changed"]
        or state_delta["changed"]
        or task_revision_delta["changed"]
        or any(part["changed"] for delta in (evaluation_delta, update_policy_delta, stopping_policy_delta) for part in delta.values())
        or dependence_delta["changed"]
    )
    if known_delta:
        update_status = "UPDATE_DELTA_REPORTED"
    elif unknown_reasons:
        update_status = "NO_CHANGE_NOT_ESTABLISHED"
    else:
        update_status = "EXPLICIT_NO_CHANGE"

    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": update_status,
        "comparison_status": "COMPARISON_UNKNOWN" if unknown_reasons else "COMPARABLE_AS_DECLARED",
        "comparison_id": comparison_id,
        "input_sha256": input_sha256,
        "predecessor": {"snapshot_id": before["snapshot_id"], **before["as_of"]},
        "candidate": {"snapshot_id": after["snapshot_id"], **after["as_of"]},
        "task_revision_delta": task_revision_delta,
        "scope_delta": scope_delta,
        "applicability_delta": applicability_delta,
        "declared_claim_state_delta": {
            **state_delta,
            "authority": "CALLER_DECLARED_ONLY",
        },
        "change_reason": {"baseline": before["change_reason"], "candidate": after["change_reason"]},
        "evaluation_instrument_delta": evaluation_delta,
        "update_policy_delta": update_policy_delta,
        "stopping_policy_delta": stopping_policy_delta,
        "acquisition_dependence": {
            **dependence_delta,
            "accumulation_bias_assessment": "NOT_EVALUATED",
        },
        "evidence_delta": {
            "added_ids": added_ids,
            "absent_from_candidate_ids": removed_ids,
            "retained_exact_ids": retained_ids,
            "changed_records": changed_records,
            "unresolved_records": unresolved_records,
            "declared_withdrawal_or_retraction_transitions": withdrawal_transitions,
            "source_family_counts": family_delta,
        },
        "review_triggers": sorted(review_triggers),
        "comparison_unknown_reasons": sorted(unknown_reasons),
        "source_authenticity": "NOT_VERIFIED",
        "evidence_quality": "NOT_ASSESSED",
        "claim_truth": "NOT_ADJUDICATED",
        "scientific_acceptance": "NOT_GRANTED",
        "filesystem_access": "NONE",
        "network_requests": 0,
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def analyze_bytes(raw: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(raw).hexdigest()
    try:
        if len(raw) > MAX_INPUT_BYTES:
            raise InputError("INPUT_LIMIT_EXCEEDED", "$")
        text = raw.decode("utf-8", errors="strict")
        request = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        if not isinstance(request, dict):
            raise InputError("OBJECT_REQUIRED", "$")
        _object(request, "$", {"schema_version", "comparison_id", "baseline_snapshot", "candidate_snapshot"})
        result = _compare(request, digest)
        encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_OUTPUT_BYTES:
            raise InputError("OUTPUT_LIMIT_EXCEEDED", "$")
        return result
    except InputError as exc:
        return {
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "status": "INPUT_INVALID",
            "input_sha256": digest,
            "errors": [{"code": exc.code, "path": exc.path}],
            "execution_authorized": False,
        }
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "status": "INPUT_INVALID",
            "input_sha256": digest,
            "errors": [{"code": "JSON_INVALID", "path": "$"}],
            "execution_authorized": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON request from stdin")
    parser.parse_args(argv)
    report = analyze_bytes(sys.stdin.buffer.read(MAX_INPUT_BYTES + 1))
    rendered = json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n"
    sys.stdout.write(rendered)
    return 0 if report["status"] != "INPUT_INVALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
