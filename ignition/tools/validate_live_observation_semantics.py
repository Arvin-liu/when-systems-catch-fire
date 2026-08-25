#!/usr/bin/env python3
"""Run the Task139 live-observation semantic negative/positive fixtures."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Callable, Mapping

try:
    from agent_federation.live_attempt_ledger import (
        LiveAttemptDuplicateError,
        LiveAttemptLedger,
        LiveAttemptLedgerError,
        validate_record,
    )
    from agent_federation.live_capture_fault_matrix import run_capture_fault_matrix
    from agent_federation.live_current_projection import validate_projection
    from agent_federation.local_executor_census import LocalExecutorCensusError, validate_census
    from tools import build_current_snapshot, validate_current_surface_semantics
except ImportError:  # direct execution with ignition/tools on sys.path
    from live_attempt_ledger import LiveAttemptDuplicateError, LiveAttemptLedger, LiveAttemptLedgerError, validate_record
    from live_capture_fault_matrix import run_capture_fault_matrix
    from live_current_projection import validate_projection
    from local_executor_census import LocalExecutorCensusError, validate_census
    import build_current_snapshot
    import validate_current_surface_semantics


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
FIXTURE_PATH = ROOT / "data/operations/iterations/139/fixtures/live-observation-semantic-fixtures-r1.json"
LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
PROJECTION_PATH = ROOT / "data/operations/iterations/139/live-current-projection-r1.json"
CENSUS_PATH = ROOT / "data/operations/iterations/138/local-executor-census-r1.json"
SECOND_ATTEMPT_ID = "attempt-138-live-02"
DIGEST = "a" * 64
ZERO_HASH = "0" * 64


class LiveObservationSemanticError(RuntimeError):
    """Raised when a semantic fixture cannot be evaluated safely."""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    expected_status: str
    observed_status: str
    observed: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "case_id": self.case_id,
            "expected_status": self.expected_status,
            "observed_status": self.observed_status,
            "observed": self.observed,
            "detail": self.detail,
            "status": "PASS" if self.expected_status == self.observed_status else "FAIL",
        }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveObservationSemanticError(f"cannot read {path.relative_to(REPO_ROOT)}") from exc


def _load_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(validate_record(json.loads(line)))
    return records


def _second_attempt(records: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [record for record in records if record.get("attempt_id") == SECOND_ATTEMPT_ID]
    if len(matches) != 1:
        raise LiveObservationSemanticError("canonical second Codex attempt is not unique")
    return matches[0]


def _current_claim_errors(record: Mapping[str, Any], narrative: str) -> list[str]:
    """Return violations when a Current narrative overclaims one attempt."""

    folded = narrative.casefold()
    errors: list[str] = []
    happened = record.get("attempt_id") == SECOND_ATTEMPT_ID
    if happened and re.search(r"second\s+(?:codex\s+)?(?:invocation|dispatch|launch).*?(?:forbidden|not\s+run|did\s+not\s+run)", folded):
        errors.append("CURRENT_SPLIT_BRAIN_SECOND_ATTEMPT_FORBIDDEN")
    positive_completion = re.search(
        r"(?:validated\s+live\s+completion\s+succeeded|live\s+completion\s+succeeded|successful\s+live\s+completion|completed\s+validated)",
        folded,
    )
    if record.get("evidence_completeness") == "INCOMPLETE" and positive_completion:
        errors.append("INCOMPLETE_EVIDENCE_CANNOT_CLAIM_SUCCESS")
    process = record.get("process", {})
    validator = record.get("validator", {})
    if process.get("return_code") == 0 and validator.get("status") != "PASS" and positive_completion:
        errors.append("EXIT_ZERO_WITHOUT_VALIDATOR_CANNOT_CLAIM_SUCCESS")
    return errors


def _valid_record(*, dispatch_id: str = "dispatch-semantic-1", attempt_id: str = "attempt-semantic-1") -> dict[str, Any]:
    return {
        "task_id": "IGNITION-20260825-139",
        "dispatch_id": dispatch_id,
        "attempt_id": attempt_id,
        "executor_id": "external.synthetic",
        "adapter_id": "synthetic-live-r1",
        "executor_version": "1.0",
        "capability_lease_digest": DIGEST,
        "lease_binding_status": "BOUND",
        "workspace_ref": "fixture://ignition-139",
        "workspace_digest_before": DIGEST,
        "workspace_digest_after": DIGEST,
        "runtime_scratch_lifecycle_digest": DIGEST,
        "started_at": "2026-08-25T00:00:00Z",
        "ended_at": "2026-08-25T00:00:01Z",
        "process": {
            "state": "COMPLETED_VALIDATED",
            "return_code": 0,
            "timed_out": False,
            "signal": None,
            "cleanup_status": "CLEANED",
            "process_group_status": "CONFIRMED_GONE",
        },
        "public_events": {
            "capture_ref": "capture://attempt-semantic-1",
            "capture_digest": DIGEST,
            "event_count": 2,
            "capture_completeness": "COMPLETE",
            "stdout_digest": DIGEST,
            "stderr_digest": DIGEST,
            "stdout_byte_count": 10,
            "stderr_byte_count": 0,
        },
        "structured_result": {"present": True, "ref": "result://attempt-semantic-1", "digest": DIGEST},
        "validator": {"status": "PASS", "ref": "validator://attempt-semantic-1", "digest": DIGEST},
        "reconciliation_status": "NOT_REQUIRED",
        "evidence_completeness": "COMPLETE",
        "claim_ceiling": "One bounded synthetic result independently validated; no external truth is inferred.",
        "source_refs": ["ignition/tools/validate_live_observation_semantics.py"],
        "history_classification": "CURRENT_ATTEMPT",
    }


def _append_valid(ledger: LiveAttemptLedger, record: Mapping[str, Any]) -> dict[str, Any]:
    return ledger.append(
        record,
        expected_task_id="IGNITION-20260825-139",
        expected_executor_id="external.synthetic",
        expected_lease_digest=DIGEST,
    )


def _negative(case_id: str, expected: str, fn: Callable[[], str]) -> CaseResult:
    try:
        observed = fn()
    except Exception as exc:  # fail closed: an unexpected validator error is not a PASS
        return CaseResult(case_id, expected, "PASS", "UNEXPECTED_EXCEPTION", type(exc).__name__)
    return CaseResult(case_id, expected, "FAIL" if observed else "PASS", observed or "GUARD_NOT_TRIGGERED", "negative guard evaluated")


def _positive(case_id: str, fn: Callable[[], str]) -> CaseResult:
    try:
        observed = fn()
    except Exception as exc:
        return CaseResult(case_id, "PASS", "FAIL", "UNEXPECTED_EXCEPTION", type(exc).__name__)
    return CaseResult(case_id, "PASS", "PASS" if observed else "FAIL", observed or "POSITIVE_GUARD_NOT_MET", "positive guard evaluated")


def _case_happened_forbidden(records: list[dict[str, Any]]) -> str:
    errors = _current_claim_errors(_second_attempt(records), "Task138 second Codex invocation was forbidden and was not run.")
    return errors[0] if errors else ""


def _case_incomplete_success(records: list[dict[str, Any]]) -> str:
    errors = _current_claim_errors(_second_attempt(records), "A validated live completion succeeded despite the incomplete capsule.")
    return errors[0] if errors else ""


def _case_exit_zero_without_validator() -> str:
    record = _valid_record()
    record["process"]["state"] = "RETURNED_UNVALIDATED"
    record["validator"] = {"status": "NOT_RUN", "ref": None, "digest": "NOT_APPLICABLE"}
    validate_record({**record, "schema_version": "live-attempt-ledger-r1", "sequence": 0, "previous_record_hash": ZERO_HASH, "record_hash": ZERO_HASH}, check_hash=False)
    return _current_claim_errors(record, "A live completion succeeded after exit code 0.")[0]


def _case_exact_binding() -> str:
    with tempfile.TemporaryDirectory(prefix="ignition-139-semantic-") as directory:
        ledger = LiveAttemptLedger(Path(directory) / "attempts.jsonl")
        result = _append_valid(ledger, _valid_record())
        return "EXACT_TASK_EXECUTOR_LEASE_RESULT_VALIDATOR_BINDING" if result["process"]["state"] == "COMPLETED_VALIDATED" else ""


def _case_historical_narrative() -> str:
    issues = validate_current_surface_semantics.validate_documents(
        {"ignition/STATE-CHANGELOG.md": "## Historical Task138\n- second invocation was forbidden.\n"},
        snapshot=build_current_snapshot.build_snapshot(),
        surface_specs=[{"surface_id": "state-changelog", "path": "ignition/STATE-CHANGELOG.md", "profile": "ai"}],
        require_blocks=False,
    )
    return "HISTORICAL_NARRATIVE_EXEMPT" if not issues else ""


def _case_duplicate_overwrite() -> str:
    with tempfile.TemporaryDirectory(prefix="ignition-139-semantic-") as directory:
        ledger = LiveAttemptLedger(Path(directory) / "attempts.jsonl")
        first = _valid_record()
        _append_valid(ledger, first)
        try:
            _append_valid(ledger, deepcopy(first))
        except LiveAttemptDuplicateError:
            return "DUPLICATE_ATTEMPT_OVERWRITE_REJECTED"
    return ""


def _case_private_output() -> str:
    with tempfile.TemporaryDirectory(prefix="ignition-139-semantic-") as directory:
        ledger = LiveAttemptLedger(Path(directory) / "attempts.jsonl")
        normalized = _append_valid(ledger, _valid_record())
        normalized["claim_ceiling"] = "raw_prompt must never enter the formal ledger"
        try:
            validate_record(normalized, check_hash=False)
        except LiveAttemptLedgerError:
            return "RAW_PRIVATE_OUTPUT_REJECTED"
    return ""


def _case_context_complete(matrix: Mapping[str, Any]) -> str:
    observed = {item["case_id"]: item["observed"] for item in matrix["cases"]}
    return "CAPSULE_COMPLETE_RECOVERABLE" if observed.get("context_unavailable_capsule_complete") == "CONTEXT_LOST_CAPTURE_COMPLETE" else ""


def _case_context_absent(records: list[dict[str, Any]]) -> str:
    record = deepcopy(_second_attempt(records))
    record["public_events"]["capture_ref"] = "UNRECOVERED"
    if (
        record["evidence_completeness"] == "INCOMPLETE"
        and record["process"]["state"] == "OBSERVATION_INCOMPLETE"
        and record["reconciliation_status"] == "REQUIRES_RECONCILIATION"
    ):
        validate_record(record, check_hash=False)
        return "CAPSULE_ABSENT_REQUIRES_RECONCILIATION"
    return ""


def _case_plain_gh() -> str:
    census = _load_json(CENSUS_PATH)
    candidate = next(item for item in census["candidates"] if item["executor_id"] == "tool.github-cli")
    mutated = deepcopy(census)
    changed = next(item for item in mutated["candidates"] if item["executor_id"] == "tool.github-cli")
    changed["kind"] = "AGENTIC_EXECUTOR"
    try:
        validate_census(mutated)
    except LocalExecutorCensusError:
        return "TOOL_ONLY_GH_PROMOTION_REJECTED"
    return "" if candidate["kind"] != "AGENTIC_EXECUTOR" else ""


def _case_reasoner_runtime() -> str:
    census = _load_json(CENSUS_PATH)
    runtime_id = next(item["executor_id"] for item in census["candidates"] if item["kind"] == "REASONER_RUNTIME")
    mutated = deepcopy(census)
    changed = next(item for item in mutated["candidates"] if item["executor_id"] == runtime_id)
    changed["admission_status"] = "ADMITTED"
    try:
        validate_census(mutated)
    except LocalExecutorCensusError:
        return "REASONER_RUNTIME_CANNOT_CLOSE_AGENT_OBLIGATION"
    return ""


def _case_soft_governance() -> str:
    issues = validate_current_surface_semantics.validate_documents(
        {"fixture.md": "Structural Governance Surface is authority and may authorize the live completion.\n"},
        snapshot=build_current_snapshot.build_snapshot(),
        surface_specs=[{"surface_id": "fixture", "path": "fixture.md", "profile": "human"}],
        require_blocks=False,
    )
    return "SOFT_GOVERNANCE_AUTHORITY_ESCALATION_REJECTED" if any(item["kind"] == "soft_governance_authority_escalation" for item in issues) else ""


def _case_handlers(records: list[dict[str, Any]], matrix: Mapping[str, Any]) -> dict[str, Callable[[], str]]:
    return {
        "ledger-says-happened-current-says-forbidden": lambda: _case_happened_forbidden(records),
        "incomplete-capsule-current-says-success": lambda: _case_incomplete_success(records),
        "exit-zero-without-validator": _case_exit_zero_without_validator,
        "validated-completion-exact-binding": _case_exact_binding,
        "historical-narrative-preserved": _case_historical_narrative,
        "duplicate-attempt-overwrite": _case_duplicate_overwrite,
        "raw-private-output-formal-ledger": _case_private_output,
        "context-lost-capsule-complete": lambda: _case_context_complete(matrix),
        "context-lost-capsule-absent": lambda: _case_context_absent(records),
        "plain-gh-promoted-to-agent": _case_plain_gh,
        "reasoner-runtime-closes-agent-obligation": _case_reasoner_runtime,
        "soft-governance-raises-authority": _case_soft_governance,
    }


def run_semantic_gate() -> dict[str, Any]:
    fixture = _load_json(FIXTURE_PATH)
    if fixture.get("schema_version") != "live-observation-semantic-fixtures-r1" or fixture.get("task_id") != "IGNITION-20260825-139":
        raise LiveObservationSemanticError("semantic fixture manifest is not bound to Task139")
    records = _load_records()
    projection = _load_json(PROJECTION_PATH)
    validate_projection(projection)
    second = _second_attempt(records)
    if second["process"]["state"] != "OBSERVATION_INCOMPLETE" or second["evidence_completeness"] != "INCOMPLETE":
        raise LiveObservationSemanticError("canonical second attempt is not incomplete as required")
    identity = _load_json(ROOT / "data/architecture/current-system-identity.json")
    identity_text = json.dumps(identity.get("known_open_obligations", []), ensure_ascii=False)
    if _current_claim_errors(second, identity_text):
        raise LiveObservationSemanticError("canonical Current identity conflicts with the ledger")
    matrix = run_capture_fault_matrix()
    handlers = _case_handlers(records, matrix)
    expected_ids = {item.get("id") for item in fixture.get("cases", [])}
    if expected_ids != set(handlers):
        raise LiveObservationSemanticError("semantic fixture manifest does not cover the required 12 cases")
    results: list[dict[str, str]] = []
    for case in fixture["cases"]:
        case_id = case["id"]
        expected = case["expected_status"]
        result = handlers[case_id]()
        observed_status = ("FAIL" if result else "PASS") if case["kind"] == "negative" else ("PASS" if result else "FAIL")
        results.append(CaseResult(case_id, expected, observed_status, result or "GUARD_NOT_TRIGGERED", case["guard"]).to_dict())
    passed = all(item["status"] == "PASS" for item in results)
    return {
        "schema_version": "ignition-139-step08-live-observation-semantic-gate-r1",
        "task_id": "IGNITION-20260825-139",
        "status": "PASS" if passed else "FAIL",
        "case_count": len(results),
        "cases": results,
        "canonical_sources": [
            "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl",
            "ignition/data/operations/iterations/139/live-current-projection-r1.json",
            "ignition/data/architecture/current-system-identity.json",
        ],
        "claim_ceiling": "Task139 repository-local live-observation semantic-boundary evidence only; no live completion, external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="run the deterministic semantic fixture gate")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    try:
        report = run_semantic_gate()
    except LiveObservationSemanticError as exc:
        print(f"LIVE_OBSERVATION_SEMANTIC_GATE_INVALID\n- {exc}")
        return 1
    if report["status"] != "PASS":
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    print(f"LIVE_OBSERVATION_SEMANTIC_GATE_OK cases={report['case_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
