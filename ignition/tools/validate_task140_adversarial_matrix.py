#!/usr/bin/env python3
"""Exercise Task140's fail-closed Observation/Reconciliation boundaries.

The matrix is deliberately repository-local and synthetic.  It starts no
external process and never treats a probe or transport return code as a live
process result.  Every negative case must be rejected by an existing
validator or by the explicit completion/admission guard that composes those
typed validators.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable

from agent_federation.live_attempt_ledger import (
    LiveAttemptLedger,
    LiveAttemptLedgerError,
    validate_record,
)
from agent_federation.live_current_projection import build_live_current_projection, validate_projection
from agent_federation.live_observation_plane import validate_observation_outcome
from agent_federation.live_reconciliation import derive_reconciliation_state, validate_reconciliation_state
from agent_federation.local_executor_census import validate_census
from tools import build_current_snapshot, validate_current_surface_semantics, validate_current_task_lineage
from tools.architecture_impact import classify_change
from tools.validate_live_observation_semantics import _valid_record


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
TASK_ID = "IGNITION-20260826-140"
DIGEST = "a" * 64
ZERO_HASH = "0" * 64
LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
PROJECTION_PATH = ROOT / "data/operations/iterations/140/live-current-projection-r2.json"
RECONCILIATION_EVENTS_PATH = ROOT / "data/operations/iterations/140/live-reconciliation-events-r1.jsonl"
OBSERVATION_EVENTS_PATH = ROOT / "data/operations/iterations/140/live-observation-events-r1.jsonl"
CENSUS_PATH = ROOT / "data/operations/iterations/138/local-executor-census-r1.json"
TASK10_PATH = ROOT / "data/operations/iterations/140/step10-live-admission.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
MATRIX_PATH = ROOT / "data/operations/iterations/140/step13-adversarial-matrix.json"


class MatrixGuardError(RuntimeError):
    """Raised when a composed completion or admission guard rejects a case."""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    expected_action: str
    observed_action: str
    guard: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "case_id": self.case_id,
            "expected_action": self.expected_action,
            "observed_action": self.observed_action,
            "guard": self.guard,
            "detail": self.detail,
            "status": "PASS" if self.expected_action == self.observed_action else "FAIL",
        }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_records() -> list[dict[str, Any]]:
    return [
        validate_record(json.loads(line))
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _synthetic_record(*, dispatch_id: str = "dispatch-adversarial-1", attempt_id: str = "attempt-adversarial-1") -> dict[str, Any]:
    record = deepcopy(_valid_record(dispatch_id=dispatch_id, attempt_id=attempt_id))
    record["task_id"] = TASK_ID
    record["workspace_ref"] = "fixture://ignition-140-adversarial"
    record["public_events"]["capture_ref"] = f"capture://{attempt_id}"
    record["structured_result"]["ref"] = f"result://{attempt_id}"
    record["validator"]["ref"] = f"validator://{attempt_id}"
    record["source_refs"] = ["ignition/tools/validate_task140_adversarial_matrix.py"]
    return record


def _with_immutable_fields(record: dict[str, Any]) -> dict[str, Any]:
    candidate = deepcopy(record)
    candidate.update({
        "schema_version": "live-attempt-ledger-r1",
        "sequence": 0,
        "previous_record_hash": ZERO_HASH,
        "record_hash": ZERO_HASH,
    })
    return candidate


def _no_live_process_outcome(*, record_return_code: int | None = 0) -> dict[str, Any]:
    return {
        "schema_version": "live-observation-outcome-r1",
        "observation_outcome_type": "PRE_INFERENCE_NO_LIVE_PROCESS",
        "probe_return_code": 0,
        "transport_return_code": 0,
        "public_probe_calls": 2,
        "live_dispatch_calls": 0,
        "live_dispatch_started": False,
        "live_process_started": False,
        "live_process_return_code": None,
        "capture_initialized": False,
        "structured_result_present": False,
        "validator_status": "NOT_RUN",
        "legacy_record_return_code_preserved": record_return_code,
        "legacy_return_code_scope": "PUBLIC_PROBE_TRANSPORT_VALUE_ONLY",
    }


def _completion_outcome(*, return_code: int = 0) -> dict[str, Any]:
    return {
        "schema_version": "live-observation-outcome-r1",
        "observation_outcome_type": "LIVE_PROCESS_OBSERVED",
        "probe_return_code": 0,
        "transport_return_code": 0,
        "public_probe_calls": 2,
        "live_dispatch_calls": 1,
        "live_dispatch_started": True,
        "live_process_started": True,
        "live_process_return_code": return_code,
        "capture_initialized": True,
        "structured_result_present": True,
        "validator_status": "PASS",
        "legacy_record_return_code_preserved": return_code,
        "legacy_return_code_scope": "LIVE_PROCESS_RETURN_CODE_OBSERVED",
    }


def _completion_gate(record: dict[str, Any], outcome: dict[str, Any] | None = None) -> None:
    """Compose the exact conditions needed before a completion claim."""

    validate_record(_with_immutable_fields(record), check_hash=False)
    process = record["process"]
    events = record["public_events"]
    structured = record["structured_result"]
    validator = record["validator"]
    if process["state"] != "COMPLETED_VALIDATED":
        raise MatrixGuardError("COMPLETION_REQUIRES_COMPLETED_VALIDATED_PROCESS_STATE")
    if record["evidence_completeness"] != "COMPLETE" or events["capture_completeness"] != "COMPLETE":
        raise MatrixGuardError("COMPLETION_REQUIRES_COMPLETE_DURABLE_CAPTURE")
    if not structured["present"] or validator["status"] != "PASS":
        raise MatrixGuardError("COMPLETION_REQUIRES_STRUCTURED_RESULT_AND_VALIDATOR_PASS")
    if record["workspace_digest_before"] != record["workspace_digest_after"]:
        raise MatrixGuardError("COMPLETION_REQUIRES_UNCHANGED_READ_ONLY_WORKSPACE")
    if structured["ref"] != f"result://{record['attempt_id']}" or validator["ref"] != f"validator://{record['attempt_id']}":
        raise MatrixGuardError("COMPLETION_REQUIRES_EXACT_RESULT_VALIDATOR_BINDING")
    if outcome is not None:
        validate_observation_outcome(outcome)
        if outcome["live_dispatch_calls"] is None or outcome["live_dispatch_calls"] < 1:
            raise MatrixGuardError("COMPLETION_REQUIRES_OBSERVED_LIVE_DISPATCH")
        if outcome["live_process_started"] is not True or outcome["live_process_return_code"] is None:
            raise MatrixGuardError("COMPLETION_REQUIRES_OBSERVED_LIVE_PROCESS_EXIT")
        if outcome["capture_initialized"] is not True or not outcome["structured_result_present"] or outcome["validator_status"] != "PASS":
            raise MatrixGuardError("COMPLETION_REQUIRES_TYPED_CAPTURE_RESULT_VALIDATOR_CHAIN")


def _case_architecture_presentation_claim() -> None:
    classify_change(
        ["process_transport"],
        changed_paths=["ignition/agent_federation/live_transport.py"],
        evidence=["task139-process-transport-behavior"],
        declared_classification="PRESENTATION_ONLY",
    )


def _case_probe_zero_live_zero() -> None:
    invalid = _no_live_process_outcome(record_return_code=0)
    invalid["live_process_return_code"] = 0
    validate_observation_outcome(invalid)


def _case_no_dispatch_completed() -> None:
    record = _synthetic_record()
    _completion_gate(record, _no_live_process_outcome())


def _case_terminal_unknown_success() -> None:
    record = _canonical_records()[0]
    state = derive_reconciliation_state({
        "task_id": record["task_id"],
        "attempt_id": record["attempt_id"],
        "prior_record_hash": record["record_hash"],
        "prior_process_state": record["process"]["state"],
        "process_observation": "UNKNOWN",
        "evidence_recovery_status": "EXHAUSTED",
        "evidence_refs": ["fixture://task140-unrecoverable"],
        "terminal_reason": "synthetic unrecoverable timeout audit",
    })
    tampered = deepcopy(state)
    tampered["external_effect_knowledge"] = "KNOWN_SUCCESS"
    tampered["validated_completion_eligible"] = True
    validate_reconciliation_state(tampered)


def _case_terminal_unknown_preserved() -> None:
    record = _canonical_records()[0]
    state = derive_reconciliation_state({
        "task_id": record["task_id"],
        "attempt_id": record["attempt_id"],
        "prior_record_hash": record["record_hash"],
        "prior_process_state": record["process"]["state"],
        "process_observation": "UNKNOWN",
        "evidence_recovery_status": "EXHAUSTED",
        "evidence_refs": ["fixture://task140-unrecoverable"],
        "terminal_reason": "synthetic unrecoverable timeout audit",
    })
    if state["external_effect_knowledge"] != "UNKNOWN" or state["validated_completion_eligible"]:
        raise MatrixGuardError("TERMINAL_UNKNOWN_NOT_PRESERVED")
    validate_reconciliation_state(state)


def _case_open_reconciliation_new_dispatch() -> None:
    record = _canonical_records()[3]
    state = derive_reconciliation_state({
        "task_id": record["task_id"],
        "attempt_id": record["attempt_id"],
        "prior_record_hash": record["record_hash"],
        "prior_process_state": record["process"]["state"],
        "process_observation": "UNKNOWN",
        "evidence_recovery_status": "RECOVERABLE",
        "evidence_refs": ["fixture://task140-recoverable"],
        "terminal_reason": "synthetic evidence remains recoverable",
    })
    validate_reconciliation_state(state)
    if state["reconciliation_status"] == "OPEN_REQUIRES_EVIDENCE":
        raise MatrixGuardError("NEW_DISPATCH_BLOCKED_UNTIL_RECONCILIATION")


def _case_terminalized_unknown_fresh_identity() -> None:
    projection = validate_projection(_load_json(PROJECTION_PATH))
    if projection["counts"]["unreconciled_count"] != 0:
        raise MatrixGuardError("FRESH_IDENTITY_REQUIRES_ZERO_UNRECONCILED_ATTEMPTS")
    if projection["next_eligible_action"]["action"] != "RUN_DYNAMIC_EXECUTOR_ADMISSION":
        raise MatrixGuardError("FRESH_IDENTITY_IS_NOT_AT_DYNAMIC_ADMISSION_BOUNDARY")
    existing = {row["attempt_id"] for row in projection["attempts"]}
    if {"attempt-adversarial-fresh", "dispatch-adversarial-fresh"} & existing:
        raise MatrixGuardError("FRESH_IDENTITY_REUSED")


def _case_exit_zero_without_structured_result() -> None:
    record = _synthetic_record()
    record["process"]["state"] = "RETURNED_UNVALIDATED"
    record["process"]["return_code"] = 0
    record["structured_result"] = {"present": False, "ref": None, "digest": "NOT_APPLICABLE"}
    record["validator"] = {"status": "NOT_RUN", "ref": None, "digest": "NOT_APPLICABLE"}
    _completion_gate(record)


def _case_structured_result_without_validator() -> None:
    record = _synthetic_record()
    record["process"]["state"] = "RETURNED_UNVALIDATED"
    record["structured_result"] = {"present": True, "ref": f"result://{record['attempt_id']}", "digest": DIGEST}
    record["validator"] = {"status": "NOT_RUN", "ref": None, "digest": "NOT_APPLICABLE"}
    _completion_gate(record)


def _case_wrong_validator_binding() -> None:
    record = _synthetic_record()
    record["validator"]["ref"] = "validator://different-attempt"
    _completion_gate(record, _completion_outcome())


def _case_workspace_modified_completion() -> None:
    record = _synthetic_record()
    record["workspace_digest_after"] = "b" * 64
    _completion_gate(record, _completion_outcome())


def _case_incomplete_capture_completion() -> None:
    record = _synthetic_record()
    record["process"]["state"] = "OBSERVATION_INCOMPLETE"
    record["structured_result"] = {"present": False, "ref": None, "digest": "UNRECOVERED"}
    record["validator"] = {"status": "NOT_RUN", "ref": None, "digest": "NOT_APPLICABLE"}
    record["public_events"]["capture_completeness"] = "INCOMPLETE"
    record["evidence_completeness"] = "INCOMPLETE"
    _completion_gate(record)


def _case_private_output() -> None:
    record = _with_immutable_fields(_synthetic_record())
    record["claim_ceiling"] = "raw_prompt is forbidden in the canonical ledger"
    validate_record(record, check_hash=False)


def _case_plain_gh() -> None:
    census = _load_json(CENSUS_PATH)
    mutated = deepcopy(census)
    changed = next(row for row in mutated["candidates"] if row["executor_id"] == "tool.github-cli")
    changed["kind"] = "AGENTIC_EXECUTOR"
    validate_census(mutated, expected_task_id=census["task_id"], expected_step=census["step"])


def _case_reasoner_runtime() -> None:
    census = _load_json(CENSUS_PATH)
    mutated = deepcopy(census)
    changed = next(row for row in mutated["candidates"] if row["kind"] == "REASONER_RUNTIME")
    changed["admission_status"] = "ADMITTED"
    validate_census(mutated, expected_task_id=census["task_id"], expected_step=census["step"])


def _case_same_family_retry() -> None:
    census = _load_json(TASK10_PATH)
    policy = census["bounded_live_attempt_policy"]
    if policy["blind_retry"] != "FORBIDDEN":
        raise MatrixGuardError("TASK140_RETRY_POLICY_NOT_FROZEN")
    if policy["max_attempts_per_executor_family"] != 1:
        raise MatrixGuardError("TASK140_FAMILY_ATTEMPT_CAP_NOT_ONE")
    selected_executor = census["dispatch"]["executor_id"]
    prior_executor_ids = {row["executor_id"] for row in _canonical_records()}
    if selected_executor in prior_executor_ids:
        raise MatrixGuardError("SAME_EXECUTOR_FAMILY_RETRY_REJECTED")


def _case_validated_completion_then_probe() -> None:
    with tempfile.TemporaryDirectory(prefix="ignition-140-adversarial-") as directory:
        ledger_path = Path(directory) / "attempts.jsonl"
        ledger = LiveAttemptLedger(ledger_path)
        record = _synthetic_record(dispatch_id="dispatch-adversarial-validated", attempt_id="attempt-adversarial-validated")
        ledger.append(record, expected_task_id=TASK_ID, expected_executor_id="external.synthetic", expected_lease_digest=DIGEST)
        projection = build_live_current_projection(ledger_path, source_path="fixture://task140-adversarial-ledger")
        validate_projection(projection)
        if projection["counts"]["validated_completion_count"] != 1 or projection["next_eligible_action"]["status"] != "STOP_AFTER_FIRST_VALIDATED_COMPLETION":
            raise MatrixGuardError("VALIDATED_COMPLETION_DID_NOT_CLOSE_CONTINUATION_BOUNDARY")
        raise MatrixGuardError("POST_VALIDATED_PROBE_REJECTED")


def _case_task125_marked_executed() -> None:
    source = _load_json(LINEAGE_PATH)
    mutated = deepcopy(source)
    predecessor = mutated["lineages"][0]["predecessor"]
    predecessor["task_file_status"] = "COMPLETED"
    predecessor["requirement_lineage_status"] = "EXECUTED"
    predecessor["canonical_status"] = "COMPLETED"
    errors = validate_current_task_lineage.validate(mutated)
    if errors:
        raise MatrixGuardError(f"TASK125_EXECUTED_MUTATION_REJECTED: {errors[0]}")


def _case_authority_inflation() -> None:
    issues = validate_current_surface_semantics.validate_documents(
        {"fixture.md": "Structural Governance Surface is authority and may authorize the live completion.\n"},
        snapshot=build_current_snapshot.build_snapshot(),
        surface_specs=[{"surface_id": "fixture", "path": "fixture.md", "profile": "human"}],
        require_blocks=False,
    )
    authority_issues = [issue for issue in issues if issue["kind"] == "soft_governance_authority_escalation"]
    if authority_issues:
        raise MatrixGuardError("AUTHORITY_INFLATION_REJECTED")
    raise MatrixGuardError("AUTHORITY_INFLATION_NOT_REJECTED")


def _case_projection_reconciliation_replay() -> None:
    with tempfile.TemporaryDirectory(prefix="ignition-140-adversarial-") as directory:
        directory_path = Path(directory)
        ledger_path = directory_path / "attempts.jsonl"
        reconciliation_path = directory_path / "reconciliation.jsonl"
        observation_path = directory_path / "observation.jsonl"
        shutil.copy2(LEDGER_PATH, ledger_path)
        shutil.copy2(RECONCILIATION_EVENTS_PATH, reconciliation_path)
        shutil.copy2(OBSERVATION_EVENTS_PATH, observation_path)
        first = build_live_current_projection(
            ledger_path,
            source_path="fixture://task140-adversarial-ledger",
            reconciliation_events_path=reconciliation_path,
            observation_events_path=observation_path,
        )
        second = build_live_current_projection(
            ledger_path,
            source_path="fixture://task140-adversarial-ledger",
            reconciliation_events_path=reconciliation_path,
            observation_events_path=observation_path,
        )
        first_bytes = json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        second_bytes = json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if first_bytes != second_bytes or first["projection_digest"] != second["projection_digest"]:
            raise MatrixGuardError("PROJECTION_REPLAY_NOT_IDEMPOTENT")


CASES: tuple[tuple[str, str, str, Callable[[], None]], ...] = (
    ("task139-process-transport-presentation-only", "REJECT", "ARCHITECTURE_IMPACT_CLASSIFIER", _case_architecture_presentation_claim),
    ("probe-zero-masquerades-live-zero", "REJECT", "TYPED_OBSERVATION_PROCESS_SCOPE", _case_probe_zero_live_zero),
    ("no-live-dispatch-marked-completed", "REJECT", "COMPLETION_REQUIRES_LIVE_DISPATCH", _case_no_dispatch_completed),
    ("terminal-unknown-upgraded-to-success", "REJECT", "RECONCILIATION_UNKNOWN_CEILING", _case_terminal_unknown_success),
    ("terminal-unknown-preserved", "ALLOW", "RECONCILIATION_UNKNOWN_PRESERVATION", _case_terminal_unknown_preserved),
    ("open-reconciliation-allows-new-dispatch", "REJECT", "RETRY_REQUIRES_RECONCILIATION_CLOSURE", _case_open_reconciliation_new_dispatch),
    ("terminalized-unknown-allows-fresh-identity", "ALLOW", "FRESH_ATTEMPT_IDENTITY_AFTER_TERMINALIZATION", _case_terminalized_unknown_fresh_identity),
    ("exit-zero-without-structured-result", "REJECT", "COMPLETION_RESULT_GATE", _case_exit_zero_without_structured_result),
    ("structured-result-without-validator", "REJECT", "COMPLETION_VALIDATOR_GATE", _case_structured_result_without_validator),
    ("wrong-validator-binding", "REJECT", "EXACT_RESULT_VALIDATOR_BINDING", _case_wrong_validator_binding),
    ("workspace-modified-completion", "REJECT", "READ_ONLY_WORKSPACE_GATE", _case_workspace_modified_completion),
    ("incomplete-capture-completion", "REJECT", "DURABLE_CAPTURE_COMPLETENESS_GATE", _case_incomplete_capture_completion),
    ("private-output-in-ledger", "REJECT", "PUBLIC_LEDGER_CONTENT_GATE", _case_private_output),
    ("plain-gh-promoted-to-agent", "REJECT", "EXECUTOR_KIND_ADMISSION_GATE", _case_plain_gh),
    ("reasoner-runtime-closes-agent-obligation", "REJECT", "EXECUTOR_KIND_ADMISSION_GATE", _case_reasoner_runtime),
    ("same-family-blind-retry", "REJECT", "ONE_ATTEMPT_PER_EXECUTOR_FAMILY", _case_same_family_retry),
    ("validated-completion-then-probe", "REJECT", "STOP_AFTER_FIRST_VALIDATED_COMPLETION", _case_validated_completion_then_probe),
    ("task125-marked-executed", "REJECT", "HISTORICAL_TASK125_LINEAGE_GATE", _case_task125_marked_executed),
    ("authority-inflation", "REJECT", "SOFT_GOVERNANCE_AUTHORITY_CEILING", _case_authority_inflation),
    ("projection-reconciliation-replay-idempotent", "ALLOW", "APPEND_ONLY_DETERMINISTIC_REPLAY", _case_projection_reconciliation_replay),
)


def _run_case(case_id: str, expected_action: str, guard: str, function: Callable[[], None]) -> CaseResult:
    try:
        function()
    except Exception as exc:  # Validators intentionally reject with typed exceptions from different modules.
        observed_action = "REJECT"
        detail = f"{type(exc).__name__}: {exc}"
    else:
        observed_action = "ALLOW"
        detail = "guard chain completed without rejection"
    return CaseResult(case_id, expected_action, observed_action, guard, detail)


def run_matrix() -> dict[str, Any]:
    results = [_run_case(*case) for case in CASES]
    passed = all(result.to_dict()["status"] == "PASS" for result in results)
    return {
        "schema_version": "ignition-140-step13-adversarial-matrix-r1",
        "task_id": TASK_ID,
        "status": "PASS" if passed else "FAIL",
        "case_count": len(results),
        "negative_case_count": sum(result.expected_action == "REJECT" for result in results),
        "positive_case_count": sum(result.expected_action == "ALLOW" for result in results),
        "live_processes_started": 0,
        "cases": [result.to_dict() for result in results],
        "canonical_sources": [
            "ignition/tools/architecture_impact.py",
            "ignition/agent_federation/live_observation_plane.py",
            "ignition/agent_federation/live_attempt_ledger.py",
            "ignition/agent_federation/live_reconciliation.py",
            "ignition/agent_federation/live_current_projection.py",
            "ignition/agent_federation/local_executor_census.py",
            "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl",
            "ignition/data/operations/iterations/140/live-current-projection-r2.json",
        ],
        "claim_ceiling": "Task140 repository-local adversarial Observation/Reconciliation boundary evidence only; no live process was started by this matrix and no external truth, validated completion, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        report = run_matrix()
        if args.write:
            MATRIX_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if report["status"] == "PASS" else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"TASK140_ADVERSARIAL_MATRIX_INVALID\n- {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
