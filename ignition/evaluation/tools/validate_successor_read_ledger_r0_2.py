#!/usr/bin/env python3
"""Return a finite status for the Task182-R2 typed read ledger."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
PACKET_DIR = IGNITION_ROOT / "evaluation" / "heldout" / "r0.2" / "successor-visible"
MANIFEST_PATH = PACKET_DIR / "packet-manifest.json"
MANIFEST_REL = MANIFEST_PATH.relative_to(REPO_ROOT).as_posix()
SCHEMA_PATH = PACKET_DIR / "successor-read-ledger-r0.2.schema.json"
PASS = "PASS_READ_LEDGER_CLEAN"
CONTAMINATED = "FAIL_READ_LEDGER_CONTAMINATED"
INVALID = "FAIL_READ_LEDGER_INVALID"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_schema(ledger: dict[str, Any]) -> bool:
    try:
        import jsonschema

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        return not list(jsonschema.Draft202012Validator(schema).iter_errors(ledger))
    except (ImportError, OSError, json.JSONDecodeError, ValueError):
        return False


def _summary(entries: list[dict[str, Any]], contaminated_count: int) -> dict[str, int]:
    return {
        "cognitive_reads": sum(row["action_kind"] == "COGNITIVE_READ" for row in entries),
        "operational_executions": sum(row["action_kind"] == "OPERATIONAL_EXECUTION" for row in entries),
        "operational_status_observations": sum(row["action_kind"] == "OPERATIONAL_STATUS_OBSERVED" for row in entries),
        "prohibited_cognitive_reads": sum(row["action_kind"] == "PROHIBITED_COGNITIVE_READ" for row in entries),
        "contaminated_entries": contaminated_count,
    }


def _entry_is_clean(
    row: dict[str, Any],
    *,
    cognitive_files: dict[str, dict[str, Any]],
    components: dict[str, dict[str, Any]],
    manifest_path: str,
    manifest_sha256: str,
) -> bool:
    action = row["action_kind"]
    path = row["path"]
    component_id = row["component_id"]
    if action == "COGNITIVE_READ":
        if row["content_exposure"] != "YES" or component_id is not None or row["observed_status_code"] is not None:
            return False
        if path == manifest_path:
            return row["digest"] == manifest_sha256
        allowed = cognitive_files.get(path)
        return allowed is not None and row["digest"] == allowed["sha256"]

    if action == "PROHIBITED_COGNITIVE_READ":
        return False

    component = components.get(component_id or "")
    if component is None or component["path"] != path or component["successor_access"] != "EXECUTE_STATUS_ONLY":
        return False
    if row["content_exposure"] != "NO" or row["case_specific_information_exposed"]:
        return False

    if action == "OPERATIONAL_EXECUTION":
        return (
            "EXECUTE" in component["permitted_actions"]
            and row["observed_status_code"] is None
        )
    if action == "OPERATIONAL_STATUS_OBSERVED":
        return (
            "OBSERVE_STATUS" in component["permitted_actions"]
            and row["observed_status_code"] in component["allowed_status_codes"]
        )
    return False


def validate_payload(ledger: dict[str, Any], manifest: dict[str, Any], manifest_bytes: bytes) -> str:
    if not _validate_schema(ledger):
        return INVALID
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if ledger["allowed_manifest_sha256"] != manifest_sha256:
        return INVALID
    if manifest.get("schema_version") != "heldout-successor-packet-manifest-r0.2":
        return INVALID
    if manifest.get("manifest_path") != MANIFEST_REL:
        return INVALID

    try:
        cognitive_files = {
            row["path"]: row for row in manifest["cognitive_evidence_surface"]["files"]
        }
        components = {
            row["component_id"]: row for row in manifest["operational_control_surface"]["components"]
        }
    except (KeyError, TypeError):
        return INVALID

    dispositions = [
        _entry_is_clean(
            row,
            cognitive_files=cognitive_files,
            components=components,
            manifest_path=MANIFEST_REL,
            manifest_sha256=manifest_sha256,
        )
        for row in ledger["entries"]
    ]
    contaminated_count = sum(not value for value in dispositions)
    if contaminated_count:
        return CONTAMINATED

    expected_summary = _summary(ledger["entries"], contaminated_count)
    expected_trial = "CLEAN"
    if ledger["summary"] != expected_summary or ledger["trial_disposition"] != expected_trial:
        return INVALID
    for row in ledger["entries"]:
        if row["contamination_disposition"] != "CLEAN":
            return INVALID
    return PASS


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    ledger_path = Path(args[0]) if len(args) == 1 else None
    if ledger_path is None:
        print(INVALID)
        return 2
    try:
        manifest_bytes = MANIFEST_PATH.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        status = validate_payload(ledger, manifest, manifest_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError):
        status = INVALID
    print(status)
    return 0 if status == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
