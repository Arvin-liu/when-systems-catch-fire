"""Import historical live-attempt receipts into the append-only R1 ledger.

The importer deliberately projects only sanitized public evidence.  Historical
receipt files remain immutable source material; fields that were not observed
by the old transport are represented as ``UNRECOVERED`` instead of inferred.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json
from agent_federation.live_attempt_ledger import LiveAttemptLedger


TASK_ID = "IGNITION-20260825-139"
LEDGER_RELATIVE_PATH = Path("ignition/data/operations/iterations/139/live-attempt-ledger.jsonl")
ARTIFACT_RELATIVE_PATH = Path("ignition/data/operations/iterations/139/step05-historical-attempt-import.json")
REPORT_RELATIVE_PATH = Path("ignition/reports/operations/ignition-139-step05-historical-attempt-import.md")


def _read_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    value = json.loads((repo_root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"historical source is not an object: {relative_path}")
    return value


def _source_ref(relative_path: str, fragment: str | None = None) -> str:
    return f"historical://{relative_path}{'#' + fragment if fragment else ''}"


def _record(
    *,
    task_id: str,
    dispatch_id: str,
    attempt_id: str,
    executor_id: str,
    adapter_id: str,
    executor_version: str,
    capability_lease_digest: str,
    lease_binding_status: str,
    workspace_ref: str,
    workspace_digest_before: str,
    workspace_digest_after: str,
    runtime_scratch_lifecycle_digest: str,
    started_at: str,
    ended_at: str,
    process: Mapping[str, Any],
    public_events: Mapping[str, Any],
    structured_result: Mapping[str, Any],
    validator: Mapping[str, Any],
    reconciliation_status: str,
    evidence_completeness: str,
    claim_ceiling: str,
    source_refs: list[str],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "dispatch_id": dispatch_id,
        "attempt_id": attempt_id,
        "executor_id": executor_id,
        "adapter_id": adapter_id,
        "executor_version": executor_version,
        "capability_lease_digest": capability_lease_digest,
        "lease_binding_status": lease_binding_status,
        "workspace_ref": workspace_ref,
        "workspace_digest_before": workspace_digest_before,
        "workspace_digest_after": workspace_digest_after,
        "runtime_scratch_lifecycle_digest": runtime_scratch_lifecycle_digest,
        "started_at": started_at,
        "ended_at": ended_at,
        "process": dict(process),
        "public_events": dict(public_events),
        "structured_result": dict(structured_result),
        "validator": dict(validator),
        "reconciliation_status": reconciliation_status,
        "evidence_completeness": evidence_completeness,
        "claim_ceiling": claim_ceiling,
        "source_refs": list(source_refs),
        "history_classification": "HISTORICAL_IMPORTED",
    }


def build_historical_records(repo_root: Path) -> list[dict[str, Any]]:
    """Build the four canonical historical records without writing anything."""

    hermes_path = "ignition/data/operations/iterations/136/step13-live-execution-receipt.json"
    hermes = _read_json(repo_root, hermes_path)
    hermes_receipt = hermes["receipt"]
    hermes_fixture = hermes["fixture"]
    hermes_policy_version = str(hermes["policy"]["version"]).split(" Install directory", 1)[0]

    codex137_path = "ignition/data/operations/iterations/137/step09-live-codex-attempt.json"
    codex137_validation_path = "ignition/data/operations/iterations/137/step10-independent-validation-outcome.json"
    codex137 = _read_json(repo_root, codex137_path)
    codex137_validation = _read_json(repo_root, codex137_validation_path)
    codex137_process = codex137["process"]
    codex137_receipt = codex137["executor_receipt"]
    codex137_fixture = codex137["fixture"]

    codex138_first_path = "ignition/data/operations/iterations/138/step08-first-codex-dispatch.json"
    codex138_first = _read_json(repo_root, codex138_first_path)
    codex138_first_process = codex138_first["process"]
    codex138_first_workspace = codex138_first["workspace"]
    codex138_first_scratch = codex138_first["runtime_scratch"]

    codex138_second_path = "ignition/data/operations/iterations/138/step08-amendment-01-live-codex-reconciliation.json"
    codex138_second = _read_json(repo_root, codex138_second_path)

    # The old Hermes transport recorded a bounded timeout receipt but did not
    # persist raw streams or a scratch lifecycle.  The migration plan treats
    # the receipt as complete historical evidence while preserving those
    # unavailable sub-fields explicitly.
    hermes_record = _record(
        task_id=hermes_receipt["task_id"],
        dispatch_id=hermes_receipt["dispatch_id"],
        attempt_id=hermes_receipt["attempt_id"],
        executor_id=hermes_receipt["executor_id"],
        adapter_id=hermes_receipt["adapter_id"],
        executor_version=hermes_policy_version,
        capability_lease_digest="UNRECOVERED",
        lease_binding_status="UNRECOVERED",
        workspace_ref="DISPOSABLE_HISTORICAL_WORKSPACE_136",
        workspace_digest_before=hermes_fixture["workspace_before_digest"],
        workspace_digest_after=hermes_fixture["workspace_after_digest"],
        runtime_scratch_lifecycle_digest="UNRECOVERED",
        started_at=hermes_receipt["started_at"],
        ended_at=hermes_receipt["ended_at"],
        process={
            "state": "TIMED_OUT_EFFECT_UNKNOWN",
            "return_code": hermes_receipt["exit_code"],
            "timed_out": True,
            "signal": "SIGTERM",
            "cleanup_status": "REQUIRES_RECONCILIATION",
            "process_group_status": "UNKNOWN",
        },
        public_events={
            "capture_ref": _source_ref(hermes_path, "receipt"),
            "capture_digest": hermes_receipt["receipt_digest"],
            "event_count": hermes_receipt["event_count"],
            "capture_completeness": "COMPLETE",
            "stdout_digest": "UNRECOVERED",
            "stderr_digest": "UNRECOVERED",
            "stdout_byte_count": 0,
            "stderr_byte_count": 0,
        },
        structured_result={"present": False, "ref": None, "digest": "UNRECOVERED"},
        validator={"status": "NOT_RUN", "ref": None, "digest": "NOT_APPLICABLE"},
        reconciliation_status="REQUIRES_RECONCILIATION",
        evidence_completeness="COMPLETE",
        claim_ceiling="Historical Hermes timeout evidence only; external effect and completion remain unresolved.",
        source_refs=[hermes_path],
    )

    # Task137 used a normalized ledger attempt identity from the Step01
    # migration plan.  The source receipt identity is retained in the source
    # artifact and source refs; no source file is rewritten.
    codex137_record = _record(
        task_id=codex137["task_id"],
        dispatch_id=codex137["dispatch_id"],
        attempt_id="attempt-137-live-01",
        executor_id=codex137["executor_id"],
        adapter_id=codex137["adapter_id"],
        executor_version=codex137["preflight"]["executor_version"],
        capability_lease_digest=codex137["preflight"]["lease_digest"],
        lease_binding_status="BOUND",
        workspace_ref=codex137["envelope"]["workspace_ref"],
        workspace_digest_before=codex137_fixture["before_digest"],
        workspace_digest_after=codex137_fixture["after_digest"],
        runtime_scratch_lifecycle_digest="UNRECOVERED",
        started_at=codex137_process["started_at"],
        ended_at=codex137_process["ended_at"],
        process={
            "state": "FAILED_VALIDATION",
            "return_code": codex137_process["returncode"],
            "timed_out": codex137_process["timed_out"],
            "signal": None,
            "cleanup_status": "CLEANED",
            "process_group_status": codex137_process["process_group_status"],
        },
        public_events={
            "capture_ref": _source_ref(codex137_path, "executor_receipt"),
            "capture_digest": codex137_receipt["receipt_digest"],
            "event_count": codex137_receipt["event_count"],
            "capture_completeness": "COMPLETE",
            "stdout_digest": codex137_process["stdout_digest"],
            "stderr_digest": codex137_process["stderr_digest"],
            "stdout_byte_count": codex137_process["stdout_byte_count"],
            "stderr_byte_count": codex137_process["stderr_byte_count"],
        },
        structured_result={"present": False, "ref": None, "digest": "NOT_APPLICABLE"},
        validator={
            "status": "FAIL",
            "ref": _source_ref(codex137_validation_path, "independent_validation"),
            "digest": "UNRECOVERED",
        },
        reconciliation_status="NOT_REQUIRED",
        evidence_completeness="COMPLETE",
        claim_ceiling="Historical Codex startup failure and failed validation only; no validated completion is inferred.",
        source_refs=[codex137_path, codex137_validation_path],
    )

    codex138_first_record = _record(
        task_id=codex138_first["task_id"],
        dispatch_id=codex138_first["dispatch"]["dispatch_id"],
        attempt_id=codex138_first["dispatch"]["attempt_id"],
        executor_id="external.codex",
        adapter_id=codex138_first["dispatch"]["adapter_id"],
        executor_version="codex-live-r3; runtime version UNRECOVERED",
        capability_lease_digest=codex138_first["dispatch"]["capability_lease_digest"],
        lease_binding_status="BOUND",
        workspace_ref="DISPOSABLE_HISTORICAL_WORKSPACE_138_FIRST",
        workspace_digest_before=codex138_first_workspace["before_digest"],
        workspace_digest_after=codex138_first_workspace["after_digest"],
        runtime_scratch_lifecycle_digest=sha256_json(codex138_first_scratch),
        started_at="UNRECOVERED",
        ended_at="UNRECOVERED",
        process={
            "state": "STARTUP_FAILURE",
            "return_code": codex138_first_process["returncode"],
            "timed_out": codex138_first_process["timed_out"],
            "signal": None,
            "cleanup_status": "CLEANED",
            "process_group_status": codex138_first_process["process_group_status"],
        },
        public_events={
            "capture_ref": _source_ref(codex138_first_path, "process"),
            "capture_digest": sha256_json(codex138_first),
            "event_count": 0,
            "capture_completeness": "COMPLETE",
            "stdout_digest": codex138_first_process["stdout_digest"],
            "stderr_digest": codex138_first_process["stderr_digest"],
            "stdout_byte_count": codex138_first_process["stdout_bytes"],
            "stderr_byte_count": codex138_first_process["stderr_bytes"],
        },
        structured_result={"present": False, "ref": None, "digest": "NOT_APPLICABLE"},
        validator={"status": "NOT_RUN", "ref": None, "digest": "NOT_APPLICABLE"},
        reconciliation_status="NOT_REQUIRED",
        evidence_completeness="COMPLETE",
        claim_ceiling="Historical Codex pre-inference startup failure only; no external completion is inferred.",
        source_refs=[codex138_first_path],
    )

    # This record is intentionally sparse.  The host recovered only the fact
    # that dispatch happened and that the outer context overflowed.  No return
    # code, lease, result, workspace, or validator fact is invented.
    second_dispatch = codex138_second["dispatch"]
    codex138_second_record = _record(
        task_id=codex138_second["task_id"],
        dispatch_id=second_dispatch["dispatch_id"],
        attempt_id=second_dispatch["attempt_id"],
        executor_id=second_dispatch["executor_id"],
        adapter_id=second_dispatch["adapter_id"],
        executor_version="codex-live-r3; runtime version UNRECOVERED",
        capability_lease_digest="UNRECOVERED",
        lease_binding_status="UNRECOVERED",
        workspace_ref="UNRECOVERED",
        workspace_digest_before="UNRECOVERED",
        workspace_digest_after="UNRECOVERED",
        runtime_scratch_lifecycle_digest="UNRECOVERED",
        started_at="UNRECOVERED",
        ended_at="UNRECOVERED",
        process={
            "state": "OBSERVATION_INCOMPLETE",
            "return_code": None,
            "timed_out": False,
            "signal": None,
            "cleanup_status": "NOT_OBSERVED",
            "process_group_status": "UNKNOWN",
        },
        public_events={
            "capture_ref": _source_ref(codex138_second_path, "host_recovery_observation"),
            "capture_digest": "UNRECOVERED",
            "event_count": 0,
            "capture_completeness": "INCOMPLETE",
            "stdout_digest": "UNRECOVERED",
            "stderr_digest": "UNRECOVERED",
            "stdout_byte_count": 0,
            "stderr_byte_count": 0,
        },
        structured_result={"present": False, "ref": None, "digest": "UNRECOVERED"},
        validator={"status": "UNKNOWN", "ref": None, "digest": "UNRECOVERED"},
        reconciliation_status="REQUIRES_RECONCILIATION",
        evidence_completeness="INCOMPLETE",
        claim_ceiling="Canonical historical fact: the second Codex launch happened, but host observation evidence is incomplete; no result or process outcome is inferred.",
        source_refs=[codex138_second_path],
    )

    return [hermes_record, codex137_record, codex138_first_record, codex138_second_record]


def import_history(
    repo_root: Path,
    *,
    ledger_path: Path | None = None,
    artifact_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Append the four records once and emit a sanitized import receipt."""

    root = repo_root.resolve()
    ledger_path = ledger_path or root / LEDGER_RELATIVE_PATH
    artifact_path = artifact_path or root / ARTIFACT_RELATIVE_PATH
    report_path = report_path or root / REPORT_RELATIVE_PATH
    if ledger_path.exists() and ledger_path.read_text(encoding="utf-8").strip():
        raise RuntimeError(f"refusing to append to a non-empty historical ledger: {ledger_path}")

    ledger = LiveAttemptLedger(ledger_path)
    records = build_historical_records(root)
    imported: list[dict[str, Any]] = []
    for record in records:
        imported.append(
            ledger.append(
                record,
                expected_task_id=record["task_id"],
                expected_executor_id=record["executor_id"],
                expected_lease_digest=(
                    record["capability_lease_digest"]
                    if record["lease_binding_status"] == "BOUND"
                    else None
                ),
            )
        )

    audit = ledger.audit()
    source_identity = {
        "task137_canonical_attempt_id": "attempt-137-live-01",
        "task137_source_attempt_id": "live-attempt-137",
        "task137_identity_note": "Canonical ledger identity follows Step01 migration plan; source receipt remains unchanged.",
    }
    artifact = {
        "schema_version": "ignition-139-step05-historical-attempt-import-r1",
        "task_id": TASK_ID,
        "step": "05",
        "target_ledger": str(LEDGER_RELATIVE_PATH),
        "source_identity": source_identity,
        "records": [
            {
                "sequence": record["sequence"],
                "task_id": record["task_id"],
                "dispatch_id": record["dispatch_id"],
                "attempt_id": record["attempt_id"],
                "executor_id": record["executor_id"],
                "state": record["process"]["state"],
                "evidence_completeness": record["evidence_completeness"],
                "reconciliation_status": record["reconciliation_status"],
                "capture_completeness": record["public_events"]["capture_completeness"],
                "return_code": record["process"]["return_code"],
                "structured_result_present": record["structured_result"]["present"],
                "validator_status": record["validator"]["status"],
                "source_refs": record["source_refs"],
                "record_hash": record["record_hash"],
            }
            for record in imported
        ],
        "canonical_task138_second_fact": "ATTEMPT_HAPPENED_OBSERVATION_INCOMPLETE",
        "historical_sources_rewritten": False,
        "audit": audit,
        "claim_ceiling": "Historical attempt import and append-only ledger integrity only; no external completion is inferred.",
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# IGNITION-139 Step 05 — Historical Attempt Import",
        "",
        "The four historical live attempts are now represented by the append-only `LiveAttemptLedger`. Source receipts remain unchanged.",
        "",
        "| Seq | Task | Executor | State | Evidence | Reconciliation | Return | Validator |",
        "| ---: | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for record in imported:
        return_code = record["process"]["return_code"]
        return_display = "UNRECOVERED" if return_code is None else str(return_code)
        lines.append(
            f"| {record['sequence']} | `{record['task_id']}` | `{record['executor_id']}` | "
            f"`{record['process']['state']}` | `{record['evidence_completeness']}` | "
            f"`{record['reconciliation_status']}` | `{return_display}` | "
            f"`{record['validator']['status']}` |"
        )
    lines.extend([
        "",
        "## Canonical correction",
        "",
        "Task138 second Codex dispatch is recorded as `OBSERVATION_INCOMPLETE`: it happened, the outer host lost the full observation after context overflow, and return code, structured result, lease receipt, workspace result, and validator input remain `UNRECOVERED`. The old narrative that it was forbidden is not imported as attempt fact.",
        "",
        "## Integrity",
        "",
        f"- Ledger records: `{audit['record_count']}`; unique dispatches: `{audit['dispatch_count']}`; unique attempts: `{audit['attempt_count']}`.",
        f"- Hash-chain head: `{audit['head_hash']}`.",
        "- Historical source files were not modified.",
        "- Raw/private process output was not imported; only bounded public receipt fields and stable source pointers are projected.",
        "",
        "Claim ceiling: historical attempt import and append-only ledger integrity only; no external completion is inferred.",
        "",
    ])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    artifact = import_history(args.repo_root)
    print(json.dumps({"status": "PASS", "record_count": artifact["audit"]["record_count"], "head_hash": artifact["audit"]["head_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
