#!/usr/bin/env python3
"""Validate runtime-attestation receipts without contacting a model/provider."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
SCHEMA_PATH = TASK_DIR / "evaluator/runtime-attestation/receipt-r0.schema.json"
INDEPENDENT_REQUIRED_FIELDS = {
    "provider",
    "model_id",
    "model_version",
    "deployment_id_or_not_applicable",
    "api_version_or_not_applicable",
    "runtime_mode",
    "system_prompt_sha256",
    "developer_prompt_sha256",
    "user_prompt_sha256",
    "packet_manifest_sha256",
    "output_schema_sha256",
    "sampling",
    "response_format",
    "tool_configuration_sha256",
}
SECRET_KEY_PATTERN = re.compile(r"(api[_-]?key|access[_-]?token|refresh[_-]?token|password|authorization|private[_-]?key|secret)", re.IGNORECASE)


def canonical_receipt_hash(receipt: dict) -> str:
    payload = dict(receipt)
    payload.pop("receipt_sha256", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def find_secret_keys(value: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if SECRET_KEY_PATTERN.search(str(key)):
                found.append(f"{path}.{key}")
            found.extend(find_secret_keys(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found.extend(find_secret_keys(nested, f"{path}[{index}]"))
    return found


def validate_receipt(receipt: dict, schema: dict) -> list[str]:
    problems = [error.message for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(receipt)]
    if problems:
        return problems
    if receipt["receipt_sha256"] != canonical_receipt_hash(receipt):
        problems.append("receipt_sha256 does not match canonical receipt bytes")
    secret_keys = find_secret_keys(receipt)
    if secret_keys:
        problems.append("secret-like property names present: " + ", ".join(secret_keys))

    status = receipt["attestation_status"]
    evidence = receipt["verification_evidence"]
    verification = receipt["independent_verification"]
    independently_supported = {
        row["field"]
        for row in evidence
        if row["independent_source"]
        and row["evidence_type"] in {"SIGNED_PROVIDER_ATTESTATION", "INDEPENDENT_RUNTIME_LOG", "SIGNED_BUILD_METADATA"}
    }
    declared = set(verification["verified_fields"])
    if not declared.issubset(independently_supported):
        problems.append("verified_fields include items without qualifying independent evidence")
    if status == "COMMAND_ASSIGNED_NOT_INDEPENDENTLY_VERIFIED" and declared:
        problems.append("command-assigned status cannot declare independently verified fields")
    if status == "PARTIALLY_INDEPENDENTLY_VERIFIED" and not declared:
        problems.append("partial verification status requires at least one independently verified field")
    if status == "INDEPENDENTLY_VERIFIED":
        if verification["independence_status"] != "INDEPENDENT_OF_CONFIGURATION_AND_RUN":
            problems.append("independent verification requires a verifier independent of configuration and run")
        if verification["verifier_pseudonym"] is None:
            problems.append("independent verification requires verifier_pseudonym")
        if not INDEPENDENT_REQUIRED_FIELDS.issubset(declared):
            problems.append("independent verification does not cover every required runtime/configuration field")
    return problems


def check_contract() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    print("TASK207_RUNTIME_ATTESTATION_CONTRACT_VALID: schema valid; provider/model execution not invoked")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", nargs="?", type=Path)
    parser.add_argument("--check-contract", action="store_true")
    args = parser.parse_args()
    if args.check_contract:
        if args.receipt is not None:
            parser.error("--check-contract does not accept a receipt")
        return check_contract()
    if args.receipt is None:
        parser.error("provide a receipt file or use --check-contract")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    problems = validate_receipt(receipt, schema)
    if problems:
        print("INVALID_RUNTIME_ATTESTATION_RECEIPT")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("RUNTIME_ATTESTATION_RECEIPT_VALID: internal contract only; no cross-model authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
