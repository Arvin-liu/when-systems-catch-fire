#!/usr/bin/env python3
"""Gate one proposed recovery plan against preserved failure evidence.

This offline preflight checks caller-supplied references and retry controls. It
does not authenticate sources, diagnose a root cause, execute a recovery, or
authorize a retry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator


MAX_INPUT_BYTES = 131_072
MAX_FINDINGS = 64
TOOL_ID = "maintenance.preflight_failure_anchored_recovery"
TOOL_VERSION = "0.1.0"
IGNITION_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-failure-anchored-recovery-input-r0.schema.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
CLAIM_CEILING = (
    "Checks only the internal consistency of one caller-supplied failure receipt, evidence excerpts, diagnosis references, "
    "and proposed recovery plan. It does not authenticate sources or callers, establish a root cause, verify that a command "
    "is safe or effective, execute or authorize a retry, change permissions or budgets, or establish scientific or production truth."
)


class InputError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise InputError("NONFINITE_JSON_NUMBER")


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _failure_fingerprint(failure: dict[str, Any]) -> str:
    signature = " ".join(failure["failure_signature"].split()).casefold()
    return _canonical_sha256({"failed_step": failure["failed_step"].casefold(), "failure_signature": signature})


def _action_fingerprint(recovery: dict[str, Any]) -> str:
    return _canonical_sha256({
        "instructions": recovery["instructions"],
        "permission_delta": recovery["permission_delta"],
        "budget_delta": recovery["budget_delta"],
        "verification": recovery["verification"],
        "stop_conditions": recovery["stop_conditions"],
    })


def validate_schema(payload: Any) -> list[dict[str, str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""))
    return [
        {"code": "INPUT_SCHEMA_INVALID", "path": "$" + ("/" + "/".join(map(str, error.absolute_path)) if error.absolute_path else "")}
        for error in errors[:MAX_FINDINGS]
    ]


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    schema_findings = validate_schema(payload)
    if schema_findings:
        raise InputError("INPUT_SCHEMA_INVALID")

    failure = payload["failure"]
    recovery = payload["recovery"]
    evidence_by_id = {row["evidence_id"]: row for row in failure["evidence"]}
    diagnosis_by_id = {row["diagnosis_id"]: row for row in payload["diagnoses"]}
    findings: list[dict[str, str]] = []

    def add(code: str, path: str) -> None:
        record = {"code": code, "path": path}
        if record not in findings and len(findings) < MAX_FINDINGS:
            findings.append(record)

    for index, evidence in enumerate(failure["evidence"]):
        digest = hashlib.sha256(evidence["excerpt"].encode("utf-8")).hexdigest()
        if digest != evidence["excerpt_sha256"]:
            add("EVIDENCE_EXCERPT_DIGEST_MISMATCH", f"$/failure/evidence/{index}/excerpt_sha256")
    if failure["preservation"]["first_failure_preserved"] is not True:
        add("FIRST_FAILURE_NOT_PRESERVED", "$/failure/preservation/first_failure_preserved")
    if failure["preservation"]["evidence_append_only"] is not True:
        add("FAILURE_EVIDENCE_NOT_APPEND_ONLY", "$/failure/preservation/evidence_append_only")

    for index, diagnosis in enumerate(payload["diagnoses"]):
        supported = [evidence_by_id[item] for item in diagnosis["supporting_evidence_ids"] if item in evidence_by_id]
        if len(supported) != len(diagnosis["supporting_evidence_ids"]) or not supported:
            add("DIAGNOSIS_EVIDENCE_REFERENCE_MISSING", f"$/diagnoses/{index}/supporting_evidence_ids")
        if diagnosis["classification"] == "OBSERVATION" and supported:
            joined = "\n".join(item["excerpt"] for item in supported)
            if diagnosis["statement"] not in joined:
                add("OBSERVATION_NOT_QUOTED_BY_EVIDENCE", f"$/diagnoses/{index}/statement")

    selected_diagnoses = [diagnosis_by_id[item] for item in recovery["diagnosis_ids"] if item in diagnosis_by_id]
    if len(selected_diagnoses) != len(recovery["diagnosis_ids"]) or not selected_diagnoses:
        add("RECOVERY_DIAGNOSIS_REFERENCE_MISSING", "$/recovery/diagnosis_ids")
    selected_evidence = [item for item in recovery["evidence_ids"] if item in evidence_by_id]
    if len(selected_evidence) != len(recovery["evidence_ids"]) or not selected_evidence:
        add("RECOVERY_EVIDENCE_REFERENCE_MISSING", "$/recovery/evidence_ids")
    required_evidence = {
        evidence_id
        for diagnosis in selected_diagnoses
        for evidence_id in diagnosis["supporting_evidence_ids"]
    }
    if not required_evidence.issubset(set(recovery["evidence_ids"])):
        add("RECOVERY_DROPS_DIAGNOSIS_EVIDENCE", "$/recovery/evidence_ids")

    if recovery["permission_delta"] != "NONE":
        add("RECOVERY_PERMISSION_DELTA_NOT_NONE", "$/recovery/permission_delta")
    if recovery["budget_delta"] not in {"NONE", "WITHIN_DECLARED_BOUND"}:
        add("RECOVERY_BUDGET_UNBOUNDED_OR_UNKNOWN", "$/recovery/budget_delta")
    if recovery["verification"]["failure_signature_to_recheck"] != failure["failure_signature"]:
        add("VERIFICATION_NOT_BOUND_TO_FAILURE_SIGNATURE", "$/recovery/verification/failure_signature_to_recheck")
    if not recovery["stop_conditions"]:
        add("RECOVERY_STOP_CONDITIONS_MISSING", "$/recovery/stop_conditions")

    failure_fp = _failure_fingerprint(failure)
    action_fp = _action_fingerprint(recovery)
    for index, attempt in enumerate(payload["prior_attempts"]):
        if attempt["failure_fingerprint_sha256"] != failure_fp or attempt["action_fingerprint_sha256"] != action_fp:
            continue
        if attempt["outcome"] == "FAILED":
            add("UNCHANGED_ACTION_REPEATS_FAILED_SIGNATURE", f"$/prior_attempts/{index}")
        elif attempt["outcome"] == "PASSED":
            add("SAME_RECOVERY_ALREADY_PASSED", f"$/prior_attempts/{index}")
        elif attempt["outcome"] == "UNKNOWN":
            add("SAME_RECOVERY_PRIOR_OUTCOME_UNKNOWN", f"$/prior_attempts/{index}")

    ready = not findings
    return {
        "schema_version": "toolbox-failure-anchored-recovery-output-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": "READY_FOR_HUMAN_REVIEW" if ready else "BLOCKED",
        "next_action": "HUMAN_REVIEW" if ready else "STOP_NO_RETRY",
        "failure_ref": failure["run_ref"],
        "run_head_sha": failure["run_head_sha"],
        "failure_fingerprint_sha256": failure_fp,
        "action_fingerprint_sha256": action_fp,
        "supported_diagnosis_ids": [row["diagnosis_id"] for row in selected_diagnoses],
        "supporting_evidence_ids": recovery["evidence_ids"],
        "proposed_instructions": recovery["instructions"] if ready else [],
        "verification": recovery["verification"] if ready else None,
        "stop_conditions": recovery["stop_conditions"] if ready else [],
        "findings": findings,
        "source_authentication": "NOT_PERFORMED",
        "execution_authorized": False,
        "retry_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded UTF-8 JSON object from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        print(json.dumps({"error": "INPUT_TOO_LARGE"}), file=sys.stderr)
        return 2
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        result = evaluate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, InputError, OSError) as exc:
        code = exc.args[0] if isinstance(exc, InputError) and exc.args else "INPUT_INVALID"
        print(json.dumps({"error": code}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
