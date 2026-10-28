#!/usr/bin/env python3
"""Close an R0.3 successor ledger once and attest to its frozen bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any


IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
PACKET_DIR = IGNITION_ROOT / "evaluation" / "heldout" / "r0.3" / "successor-visible"
MANIFEST_PATH = PACKET_DIR / "packet-manifest-r0.3.json"
MANIFEST_REL = MANIFEST_PATH.relative_to(REPO_ROOT).as_posix()
LEDGER_SCHEMA_PATH = PACKET_DIR / "successor-read-ledger-r0.3.schema.json"
RECEIPT_SCHEMA_PATH = PACKET_DIR / "successor-ledger-validation-receipt-r0.3.schema.json"
SOURCE_PATH = Path(__file__).resolve()

TASK_ID = "IGNITION-20260918-182-R3"
LEDGER_SCHEMA_VERSION = "successor-read-ledger-r0.3"
MANIFEST_SCHEMA_VERSION = "heldout-successor-packet-manifest-r0.3"
RECEIPT_SCHEMA_VERSION = "successor-ledger-validation-receipt-r0.3"
PROTOCOL_VERSION = "r0.3"
VALIDATOR_COMPONENT_ID = "final-read-ledger-validator-r0.3"
VALIDATOR_SOURCE_REL = SOURCE_PATH.relative_to(REPO_ROOT).as_posix()
FINAL_SCOPE = "FINAL_VALIDATOR_OUTSIDE_CERTIFIED_LEDGER_SCOPE"
CERTIFIED_SCOPE = "CERTIFIED_LEDGER_SCOPE"
CLOSED_STATE = "PRE_FINAL_VALIDATION_CLOSED"

PASS = "PASS_READ_LEDGER_CLEAN"
CONTAMINATED = "FAIL_READ_LEDGER_CONTAMINATED"
INVALID = "FAIL_READ_LEDGER_INVALID"
STATUS_CODES = (PASS, CONTAMINATED, INVALID)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def formatted_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _schema_valid(value: Any, schema_bytes: bytes) -> bool:
    try:
        import jsonschema

        schema = json.loads(schema_bytes.decode("utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        return not list(jsonschema.Draft202012Validator(schema).iter_errors(value))
    except (ImportError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False


def _parse_object(payload: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _summary(entries: list[dict[str, Any]], contaminated_count: int) -> dict[str, int]:
    return {
        "cognitive_reads": sum(row["action_kind"] == "COGNITIVE_READ" for row in entries),
        "operational_executions": sum(row["action_kind"] == "OPERATIONAL_EXECUTION" for row in entries),
        "operational_status_observations": sum(
            row["action_kind"] == "OPERATIONAL_STATUS_OBSERVED" for row in entries
        ),
        "prohibited_cognitive_reads": sum(
            row["action_kind"] == "PROHIBITED_COGNITIVE_READ" for row in entries
        ),
        "contaminated_entries": contaminated_count,
    }


def _manifest_context(
    manifest: dict[str, Any], manifest_bytes: bytes
) -> tuple[str, dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION
        or manifest.get("manifest_path") != MANIFEST_REL
        or manifest.get("task_id") != TASK_ID
    ):
        return INVALID, {}, {}

    try:
        file_rows = manifest["cognitive_evidence_surface"]["files"]
        component_rows = manifest["operational_control_surface"]["components"]
    except (KeyError, TypeError):
        return INVALID, {}, {}
    if not isinstance(file_rows, list) or not isinstance(component_rows, list):
        return INVALID, {}, {}

    files: dict[str, dict[str, Any]] = {}
    for row in file_rows:
        if not isinstance(row, dict):
            return INVALID, {}, {}
        path = row.get("path")
        digest = row.get("sha256")
        if not isinstance(path, str) or not path or not isinstance(digest, str) or len(digest) != 64:
            return INVALID, {}, {}
        if any(ch not in "0123456789abcdef" for ch in digest) or path in files:
            return INVALID, {}, {}
        files[path] = row

    components: dict[str, dict[str, Any]] = {}
    component_paths: set[str] = set()
    for row in component_rows:
        if not isinstance(row, dict):
            return INVALID, {}, {}
        component_id = row.get("component_id")
        path = row.get("path")
        if not isinstance(component_id, str) or not component_id or not isinstance(path, str) or not path:
            return INVALID, {}, {}
        if component_id in components or path in component_paths:
            return INVALID, {}, {}
        if row.get("evidence_scope") not in {CERTIFIED_SCOPE, "FINAL_ATTESTATION_SURFACE"}:
            return INVALID, {}, {}
        if row.get("successor_access") != "EXECUTE_STATUS_ONLY":
            return INVALID, {}, {}
        if not isinstance(row.get("permitted_actions"), list) or not isinstance(row.get("allowed_status_codes"), list):
            return INVALID, {}, {}
        if not isinstance(row.get("source_sha256"), str) or len(row["source_sha256"]) != 64:
            return INVALID, {}, {}
        components[component_id] = row
        component_paths.add(path)

    validator = components.get(VALIDATOR_COMPONENT_ID)
    expected_statuses = set(STATUS_CODES)
    if (
        validator is None
        or validator.get("path") != VALIDATOR_SOURCE_REL
        or validator.get("evidence_scope") != "FINAL_ATTESTATION_SURFACE"
        or validator.get("source_sha256") != sha256(SOURCE_PATH.read_bytes())
        or not {"EXECUTE", "OBSERVE_STATUS"}.issubset(set(validator.get("permitted_actions", [])))
        or not expected_statuses.issubset(set(validator.get("allowed_status_codes", [])))
    ):
        return INVALID, {}, {}
    return "OK", files, components


def _entry_status(
    row: dict[str, Any],
    *,
    files: dict[str, dict[str, Any]],
    components: dict[str, dict[str, Any]],
    manifest_path: str,
    manifest_sha256: str,
) -> str | None:
    action = row["action_kind"]
    path = row["path"]
    if action == "PROHIBITED_COGNITIVE_READ":
        if (
            row["content_exposure"] != "YES"
            or row["component_id"] is not None
            or row["observed_status_code"] is not None
            or row["digest"] is None
        ):
            return INVALID
        return CONTAMINATED

    if action == "COGNITIVE_READ":
        if (
            row["content_exposure"] != "YES"
            or row["component_id"] is not None
            or row["observed_status_code"] is not None
            or row["digest"] is None
        ):
            return INVALID
        if row["case_specific_information_exposed"]:
            return CONTAMINATED
        if path == manifest_path:
            return None if row["digest"] == manifest_sha256 else CONTAMINATED
        allowed = files.get(path)
        return None if allowed is not None and row["digest"] == allowed.get("sha256") else CONTAMINATED

    component = components.get(row["component_id"] or "")
    if component is None or component.get("path") != path:
        return CONTAMINATED
    if component.get("evidence_scope") == "FINAL_ATTESTATION_SURFACE":
        return INVALID
    if (
        row["content_exposure"] != "NO"
        or row["case_specific_information_exposed"]
        or row["digest"] is not None
    ):
        return CONTAMINATED

    permitted = set(component.get("permitted_actions", []))
    if action == "OPERATIONAL_EXECUTION":
        if "EXECUTE" not in permitted:
            return CONTAMINATED
        return None if row["observed_status_code"] is None else INVALID
    if action == "OPERATIONAL_STATUS_OBSERVED":
        if "OBSERVE_STATUS" not in permitted:
            return CONTAMINATED
        return None if row["observed_status_code"] in component.get("allowed_status_codes", []) else CONTAMINATED
    return INVALID


def validate_ledger_bytes(
    ledger_bytes: bytes,
    manifest_bytes: bytes,
    *,
    require_closed: bool,
    ledger_schema_bytes: bytes | None = None,
) -> str:
    ledger = _parse_object(ledger_bytes)
    manifest = _parse_object(manifest_bytes)
    if ledger is None or manifest is None:
        return INVALID
    try:
        schema_bytes = ledger_schema_bytes or LEDGER_SCHEMA_PATH.read_bytes()
    except OSError:
        return INVALID
    if not _schema_valid(ledger, schema_bytes):
        return INVALID

    expected_state = CLOSED_STATE if require_closed else "OPEN"
    if ledger["ledger_state"] != expected_state:
        return INVALID
    manifest_sha = sha256(manifest_bytes)
    if ledger["manifest_path"] != MANIFEST_REL or ledger["manifest_sha256"] != manifest_sha:
        return INVALID
    manifest_status, files, components = _manifest_context(manifest, manifest_bytes)
    if manifest_status != "OK":
        return INVALID

    closure = ledger["closure"]
    if require_closed:
        if (
            not isinstance(closure, dict)
            or closure.get("closure_kind") != CLOSED_STATE
            or closure.get("closed_entry_count") != len(ledger["entries"])
            or closure.get("closed_summary") != ledger["summary"]
            or closure.get("manifest_sha256") != manifest_sha
        ):
            return INVALID
    elif closure is not None:
        return INVALID

    dispositions = [
        _entry_status(
            row,
            files=files,
            components=components,
            manifest_path=MANIFEST_REL,
            manifest_sha256=manifest_sha,
        )
        for row in ledger["entries"]
    ]
    if INVALID in dispositions:
        return INVALID
    expected_row_dispositions = [
        "CONTAMINATED" if disposition == CONTAMINATED else "CLEAN"
        for disposition in dispositions
    ]
    if any(
        row["contamination_disposition"] != expected
        for row, expected in zip(ledger["entries"], expected_row_dispositions)
    ):
        return INVALID

    contaminated_count = sum(disposition == CONTAMINATED for disposition in dispositions)
    expected_summary = _summary(ledger["entries"], contaminated_count)
    expected_trial = "PROTOCOL_CONTAMINATED" if contaminated_count else "CLEAN"
    if ledger["summary"] != expected_summary or ledger["trial_disposition"] != expected_trial:
        return INVALID
    return CONTAMINATED if contaminated_count else PASS


def finalize_ledger_bytes(
    ledger_bytes: bytes,
    manifest_bytes: bytes,
    *,
    ledger_schema_bytes: bytes | None = None,
) -> tuple[bytes | None, str]:
    ledger = _parse_object(ledger_bytes)
    if ledger is None:
        return None, INVALID

    if ledger.get("ledger_state") == CLOSED_STATE:
        status = validate_ledger_bytes(
            ledger_bytes,
            manifest_bytes,
            require_closed=True,
            ledger_schema_bytes=ledger_schema_bytes,
        )
        return (ledger_bytes, status) if status in {PASS, CONTAMINATED} else (None, status)

    status = validate_ledger_bytes(
        ledger_bytes,
        manifest_bytes,
        require_closed=False,
        ledger_schema_bytes=ledger_schema_bytes,
    )
    if status not in {PASS, CONTAMINATED}:
        return None, status

    manifest_sha = sha256(manifest_bytes)
    closed = dict(ledger)
    closed["ledger_state"] = CLOSED_STATE
    closed["closure"] = {
        "closure_kind": CLOSED_STATE,
        "closed_entry_count": len(ledger["entries"]),
        "closed_summary": ledger["summary"],
        "manifest_sha256": manifest_sha,
    }
    closed_bytes = formatted_json_bytes(closed)
    closed_status = validate_ledger_bytes(
        closed_bytes,
        manifest_bytes,
        require_closed=True,
        ledger_schema_bytes=ledger_schema_bytes,
    )
    if closed_status not in {PASS, CONTAMINATED}:
        return None, closed_status
    return closed_bytes, closed_status


def _receipt_object(ledger_bytes: bytes, manifest_bytes: bytes, status: str) -> dict[str, Any]:
    ledger = _parse_object(ledger_bytes)
    if ledger is None or not isinstance(ledger.get("closure"), dict):
        raise ValueError("closed ledger is required")
    schema_bytes = LEDGER_SCHEMA_PATH.read_bytes()
    base: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "protocol_version": PROTOCOL_VERSION,
        "receipt_kind": "DETERMINISTIC_LOCAL_ATTESTATION_NOT_SIGNATURE",
        "evidence_scope": CERTIFIED_SCOPE,
        "final_validator_scope": FINAL_SCOPE,
        "ledger_state": CLOSED_STATE,
        "ledger_sha256": sha256(ledger_bytes),
        "manifest_sha256": sha256(manifest_bytes),
        "closed_entry_count": ledger["closure"]["closed_entry_count"],
        "closed_summary": ledger["closure"]["closed_summary"],
        "validator_component_id": VALIDATOR_COMPONENT_ID,
        "validator_source_sha256": sha256(SOURCE_PATH.read_bytes()),
        "read_ledger_schema_sha256": sha256(schema_bytes),
        "validator_status": status,
    }
    base["receipt_sha256"] = sha256(canonical_json_bytes(base))
    return base


def receipt_bytes_for(ledger_bytes: bytes, manifest_bytes: bytes, status: str) -> bytes:
    return formatted_json_bytes(_receipt_object(ledger_bytes, manifest_bytes, status))


def verify_receipt_bytes(
    receipt_bytes: bytes,
    ledger_bytes: bytes,
    manifest_bytes: bytes,
    *,
    ledger_schema_bytes: bytes | None = None,
    receipt_schema_bytes: bytes | None = None,
) -> bool:
    receipt = _parse_object(receipt_bytes)
    if receipt is None:
        return False
    try:
        ledger_schema = ledger_schema_bytes or LEDGER_SCHEMA_PATH.read_bytes()
        receipt_schema = receipt_schema_bytes or RECEIPT_SCHEMA_PATH.read_bytes()
    except OSError:
        return False
    if not _schema_valid(receipt, receipt_schema):
        return False
    status = validate_ledger_bytes(
        ledger_bytes,
        manifest_bytes,
        require_closed=True,
        ledger_schema_bytes=ledger_schema,
    )
    if status not in {PASS, CONTAMINATED}:
        return False
    try:
        expected = _receipt_object(ledger_bytes, manifest_bytes, status)
    except (OSError, KeyError, TypeError, ValueError):
        return False
    return receipt == expected and receipt_bytes == formatted_json_bytes(expected)


def _resolve_argument(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _atomic_replace(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def finalize_files(ledger_path: Path, manifest_path: Path, receipt_path: Path) -> str:
    if (
        ledger_path.resolve() == receipt_path.resolve()
        or receipt_path.name != "successor-ledger-validation-receipt-r0.3.json"
        or _is_within(receipt_path, PACKET_DIR)
    ):
        return INVALID
    try:
        original_ledger_bytes = ledger_path.read_bytes()
        manifest_bytes = manifest_path.read_bytes()
        existing_receipt_bytes = receipt_path.read_bytes() if receipt_path.exists() else None
    except OSError:
        return INVALID

    original_ledger = _parse_object(original_ledger_bytes)
    if original_ledger is None:
        return INVALID
    if existing_receipt_bytes is not None:
        if original_ledger.get("ledger_state") != CLOSED_STATE:
            return INVALID
        if not verify_receipt_bytes(existing_receipt_bytes, original_ledger_bytes, manifest_bytes):
            return INVALID
        return validate_ledger_bytes(original_ledger_bytes, manifest_bytes, require_closed=True)

    closed_bytes, status = finalize_ledger_bytes(original_ledger_bytes, manifest_bytes)
    if closed_bytes is None or status not in {PASS, CONTAMINATED}:
        return status
    output_receipt = receipt_bytes_for(closed_bytes, manifest_bytes, status)

    if original_ledger.get("ledger_state") == "OPEN":
        try:
            if ledger_path.read_bytes() != original_ledger_bytes:
                return INVALID
            mode = stat.S_IMODE(ledger_path.stat().st_mode)
            _atomic_replace(ledger_path, closed_bytes, mode)
            if ledger_path.read_bytes() != closed_bytes:
                return INVALID
        except OSError:
            return INVALID
    elif original_ledger_bytes != closed_bytes:
        return INVALID

    final_status = validate_ledger_bytes(closed_bytes, manifest_bytes, require_closed=True)
    if final_status != status:
        return INVALID
    output_receipt = receipt_bytes_for(closed_bytes, manifest_bytes, final_status)
    try:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_replace(receipt_path, output_receipt, 0o600)
    except OSError:
        return INVALID
    return final_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, help="open or already closed R0.3 ledger")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH), help="exact R0.3 packet manifest")
    parser.add_argument("--receipt-output", required=True, help="separate receipt destination")
    args = parser.parse_args(argv)
    try:
        status = finalize_files(
            _resolve_argument(args.ledger),
            _resolve_argument(args.manifest),
            _resolve_argument(args.receipt_output),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        status = INVALID
    print(status)
    return 0 if status == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
