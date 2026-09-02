#!/usr/bin/env python3
"""Run the seven-case offline stranger-Agent regression for Operating Method R1.

The runner composes existing Current contracts. It does not implement a second
classifier, planner, canonical resolver, collision protocol or output contract,
and it exposes no repository or external-action effect adapter.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / "tools/foundation"))

from classify_ignition_run_mode import classify_mode  # noqa: E402
from evaluate_object_collision_run import render_run, validate_run  # noqa: E402
from plan_ignition_operation_run import LIFECYCLE_STAGES, plan_run  # noqa: E402
from resolve_current_canonical_asset import (  # noqa: E402
    RESOLVED,
    UNRESOLVED,
    resolve_reference,
)
from validate_ignition_run_output import validate_output  # noqa: E402


FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/stranger-agent-adversarial-r1.json"
UNIFIED_FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/unified-output-r1.json"
RECEIPT_PATH = ROOT / "data/operations/iterations/148/step13-stranger-agent-adversarial-regression.json"
CURRENT_REF = "TASK148_STEP12_PARENT_3a8ffb04eb1263f105810479346ce8576309a58e"
# The receipt was refreshed from this exact source tree.  CURRENT_REF is the
# formal Current reference embedded in the evidence and predates the suite's
# source files; it is therefore not itself sufficient to replay the receipt.
HISTORICAL_SOURCE_COMMIT = "6f6919b4b183f0041448ced7c3e7234c7354c0a3"
REQUIRED_CASE_IDS = (
    "A_NOTE_URL_DEFAULT_READ_ONLY",
    "B_EXPLICIT_PROTOCOL_CHANGE_ROUTES_ITERATION",
    "C_INPUT_OBJECT_COMMAND_INJECTION_IS_DATA",
    "D_LEGACY_D5_T7_CURRENT_RESOLUTION",
    "E_SOURCE_EXPLICIT_AUTHORITY_HOWL_NOT_DISCOVERY",
    "F_OWNER_DEFERRED_LIVE_EXTERNAL_FAILS_CLOSED",
    "G_UNREGISTERED_OPERATION_FAILS_CLOSED",
)
CONTRACT_PATHS = (
    "ignition/tools/operations/classify_ignition_run_mode.py",
    "ignition/tools/operations/plan_ignition_operation_run.py",
    "ignition/tools/foundation/resolve_current_canonical_asset.py",
    "ignition/tools/operations/evaluate_object_collision_run.py",
    "ignition/tools/operations/validate_ignition_run_output.py",
    "ignition/data/operations/ignition-operation-capability-registry-r1.json",
    "ignition/data/operations/ignition-run-output-contract-r1.json",
)
SOURCE_DIGEST_PATHS = (
    "tools/operations/run_ignition_stranger_agent_regression.py",
    "tests/fixtures/ignition-operating-method/stranger-agent-adversarial-r1.json",
    "tools/operations/classify_ignition_run_mode.py",
    "tools/operations/plan_ignition_operation_run.py",
    "tools/foundation/resolve_current_canonical_asset.py",
    "tools/operations/evaluate_object_collision_run.py",
    "tools/operations/validate_ignition_run_output.py",
    "data/operations/ignition-operation-capability-registry-r1.json",
    "data/operations/ignition-run-output-contract-r1.json",
)


class StrangerAgentRegressionError(ValueError):
    """Raised when the fixture or checked receipt is structurally invalid."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_hash(document: dict[str, Any]) -> str:
    payload = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _source_digests_for_root(ignition_root: Path) -> dict[str, str]:
    return {
        f"ignition/{relative}": _sha256_bytes((ignition_root / relative).read_bytes())
        for relative in SOURCE_DIGEST_PATHS
    }


def _source_digests() -> dict[str, str]:
    return _source_digests_for_root(ROOT)


def _validated_source_digests(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise StrangerAgentRegressionError("historical source_digests must be an object")
    expected_keys = {f"ignition/{relative}" for relative in SOURCE_DIGEST_PATHS}
    if set(value) != expected_keys:
        raise StrangerAgentRegressionError("historical source_digests keys differ from the suite contract")
    if any(
        not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        for digest in value.values()
    ):
        raise StrangerAgentRegressionError("historical source_digests contain a non-SHA256 value")
    return dict(value)


def _subset_errors(actual: Any, expected: Any, path: str = "$") -> list[str]:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {type(actual).__name__}"]
        errors: list[str] = []
        for key, value in expected.items():
            if key not in actual:
                errors.append(f"{path}.{key}: missing")
            else:
                errors.extend(_subset_errors(actual[key], value, f"{path}.{key}"))
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected array, got {type(actual).__name__}"]
        if len(actual) != len(expected):
            return [f"{path}: expected length {len(expected)}, got {len(actual)}"]
        errors: list[str] = []
        for index, value in enumerate(expected):
            errors.extend(_subset_errors(actual[index], value, f"{path}[{index}]"))
        return errors
    return [] if actual == expected else [f"{path}: expected {expected!r}, got {actual!r}"]


def _base_unified_output() -> dict[str, Any]:
    return copy.deepcopy(load_json(UNIFIED_FIXTURE_PATH)["base_output"])


def _route_complete_output(
    case: dict[str, Any], mode: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    output = _base_unified_output()
    output["run_id"] = f"step13-{case['case_id'].lower()}"
    output["request"]["request_id"] = case["case_id"]
    output["request"]["natural_language_intent"] = case["request"]["request_envelope"]["user_request"]
    output["run_mode"] = mode["mode"]
    output["operation_path"].update(
        {
            "operation_id": case["operation_id"],
            "registry_status": plan["operation_status"],
            "decision": plan["decision"],
            "playbook_source": plan.get("playbook_source"),
        }
    )
    if case["request"]["input_objects"]:
        content = json.dumps(
            case["request"]["input_objects"][0],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        output["input_object_provenance"]["objects"][0]["provenance"]["content_sha256"] = _sha256_bytes(content)
    return output


def _stopped_output(
    case: dict[str, Any], mode: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    output = _base_unified_output()
    case_id = case["case_id"]
    stop_reason = plan["stop_reason"]
    output["run_id"] = f"step13-{case_id.lower()}"
    output["request"] = {
        "request_id": case_id,
        "natural_language_intent": case["request"]["request_envelope"]["user_request"],
        "request_envelope_locator": "fixture.request.request_envelope",
        "explicit_permissions": {
            "repository_mutation": False,
            "external_action": mode["mode"] == "EXTERNAL_ACTION_RUN",
        },
    }
    output["run_mode"] = mode["mode"]
    stop_index = (
        LIFECYCLE_STAGES.index("RESOLVE_OPERATION")
        if plan["operation_status"] == "UNREGISTERED"
        else LIFECYCLE_STAGES.index("CHECK_CAPABILITY_STATUS")
    )
    output["operation_path"] = {
        "operation_id": case["operation_id"],
        "registry_status": plan["operation_status"],
        "decision": "STOP",
        "playbook_source": None,
        "lifecycle_stages_completed": list(LIFECYCLE_STAGES[: stop_index + 1])
        + ["STOP / HANDOFF"],
    }
    input_payload = case["request"].get("input_objects", [])
    content_hash = _sha256_bytes(
        json.dumps(
            input_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    output["input_object_provenance"]["objects"][0].update(
        {
            "object_id": f"{case_id}-REQUEST-OBJECT",
            "object_type": "TASK",
        }
    )
    output["input_object_provenance"]["objects"][0]["provenance"].update(
        {
            "source_locator": "fixture.request",
            "content_sha256": content_hash,
            "version_or_captured_at": "step13-offline-fixture-r1",
        }
    )
    gap_id = f"{case_id}-STOP"
    evidence_id = f"{case_id}-VALIDATOR"
    uncertainty_id = f"{case_id}-UNCERTAINTY"
    output["input_derived_findings"] = []
    output["existing_canonical_matches"] = []
    output["collision_relations"] = []
    output["candidate_deltas"] = []
    output["contradictions_gaps"] = [
        {
            "item_id": gap_id,
            "kind": "GAP",
            "statement": f"The requested operation stopped at the Current capability gate: {stop_reason}.",
            "basis_refs": [evidence_id],
            "resolution_status": "OPEN",
        }
    ]
    output["evidence_sources"] = [
        {
            "source_id": evidence_id,
            "source_kind": "VALIDATOR_OUTPUT",
            "locator": "ignition/tools/operations/run_ignition_stranger_agent_regression.py",
            "provenance": "Offline deterministic composition of the Current mode and lifecycle contracts.",
            "supports_refs": [gap_id],
            "authority_effect": "VALIDATION_ONLY",
            "limitations": ["A fail-closed route proves no capability or external result."],
        }
    ]
    output["uncertainty"] = [
        {
            "uncertainty_id": uncertainty_id,
            "statement": "No stopped operation was executed by this offline regression.",
            "scope": "Operation execution and external effects.",
            "status": "OPEN",
            "consequence": "Only the Current stop boundary is reported.",
        }
    ]
    output["claim_ceiling"] = plan.get(
        "operation_claim_ceiling",
        "Unregistered-operation routing only; no capability, execution, truth or authority is established.",
    )
    output["result"] = {
        "status": "STOPPED",
        "summary": f"Stopped fail closed: {stop_reason}.",
        "implementation_status": "NOT_APPLICABLE",
        "epistemic_status": "NOT_ESTABLISHED",
        "epistemic_acceptance_authority": None,
        "artifacts": [],
    }
    output["stop"] = {
        "stop_reason": stop_reason,
        "optional_next_action": None,
    }
    return output


def _source_derived_output(statement: str) -> dict[str, Any]:
    output = _base_unified_output()
    output["run_id"] = "step13-e-source-explicit-authority-howl"
    output["request"]["request_id"] = "E_SOURCE_EXPLICIT_AUTHORITY_HOWL_NOT_DISCOVERY"
    output["request"]["natural_language_intent"] = "用点火碰撞这段已经写出‘权力啸叫’的输入。"
    output["input_object_provenance"]["objects"][0]["provenance"].update(
        {
            "source_locator": "fixture.case.E.source_statement",
            "content_sha256": _sha256_bytes(statement.encode("utf-8")),
            "version_or_captured_at": "step13-offline-fixture-r1",
        }
    )
    finding_id = "E-SOURCE-FINDING"
    gap_id = "E-CANONICAL-RELATION-GAP"
    source_id = "E-INPUT-SOURCE"
    validator_id = "E-COLLISION-VALIDATOR"
    output["input_derived_findings"] = [
        {
            "finding_id": finding_id,
            "statement": statement,
            "input_object_ids": ["INPUT-NOTE-001"],
            "provenance_locators": ["fixture.case.E.source_statement"],
            "origin": "SOURCE_EXPLICIT",
            "ignition_discovery_status": "NOT_IGNITION_DISCOVERY",
        }
    ]
    output["existing_canonical_matches"] = []
    output["collision_relations"] = []
    output["candidate_deltas"] = []
    output["contradictions_gaps"] = [
        {
            "item_id": gap_id,
            "kind": "GAP",
            "statement": "The source phrase remains input-derived; no Current canonical relation is established by merely repeating it.",
            "basis_refs": [finding_id],
            "resolution_status": "OPEN",
        }
    ]
    output["evidence_sources"] = [
        {
            "source_id": source_id,
            "source_kind": "INPUT_SOURCE",
            "locator": "fixture.case.E.source_statement",
            "provenance": "User-supplied source-explicit phrase in the offline fixture.",
            "supports_refs": [finding_id],
            "authority_effect": "SOURCE_PROVENANCE_ONLY",
            "limitations": ["The source phrase is not an Ignition discovery or proof."],
        },
        {
            "source_id": validator_id,
            "source_kind": "VALIDATOR_OUTPUT",
            "locator": "ignition/tools/operations/evaluate_object_collision_run.py",
            "provenance": "Deterministic source-derived and candidate-overlap validation.",
            "supports_refs": [gap_id],
            "authority_effect": "VALIDATION_ONLY",
            "limitations": ["Validator PASS establishes contract conformance only."],
        },
    ]
    output["uncertainty"] = [
        {
            "uncertainty_id": "E-RELATION-UNCERTAINTY",
            "statement": "No canonical relation or external evidence was established for the source phrase in this fixture.",
            "scope": "Current-asset relation and external truth.",
            "status": "OPEN",
            "consequence": "The phrase remains INPUT_DERIVED and cannot enter candidate deltas.",
        }
    ]
    output["claim_ceiling"] = "Repository-local source-provenance classification only; no discovery, candidate, canonical relation, external truth or epistemic acceptance is established."
    output["result"] = {
        "status": "COMPLETED_BOUNDED",
        "summary": "The phrase remains source-explicit INPUT_DERIVED content; no candidate delta was created.",
        "implementation_status": "NOT_APPLICABLE",
        "epistemic_status": "NOT_ESTABLISHED",
        "epistemic_acceptance_authority": None,
        "artifacts": [],
    }
    output["stop"] = {
        "stop_reason": "COMPLETED_WITHIN_CLAIM_CEILING",
        "optional_next_action": "Only a separately grounded collision can establish a relation to Current assets.",
    }
    return output


def _run_route_case(case: dict[str, Any]) -> dict[str, Any]:
    mode = classify_mode(case["request"])
    plan = plan_run(case["request"], case["operation_id"], CURRENT_REF)
    output_errors: list[str] = []
    if case.get("output_profile") == "VALID_BOUNDED_COLLISION":
        output_errors = validate_output(_route_complete_output(case, mode, plan))
    elif case.get("output_profile") == "VALID_STOPPED":
        output_errors = validate_output(_stopped_output(case, mode, plan))
    effect_events: list[dict[str, Any]] = []
    contracts = ["IGNITION_MODE_ROUTER_R1", "IGNITION_OPERATION_LIFECYCLE_R1"]
    if case.get("output_profile"):
        contracts.append("IGNITION_RUN_OUTPUT_CONTRACT_R1")
    return {
        "run_mode": mode["mode"],
        "mode_reason": mode["reason_code"],
        "input_object_content_used_for_routing": mode["input_object_content_used_for_routing"],
        "iteration_method_required": mode["iteration_method_required"],
        "operation_status": plan["operation_status"],
        "decision": plan["decision"],
        "stop_reason": plan["stop_reason"],
        "iteration_method_loaded": "ignition/ITERATION.md" in plan["minimal_read_plan"],
        "side_effects_authorized": (
            mode["side_effects_authorized_by_classification"]
            or plan["side_effects_authorized_by_plan"]
        ),
        "repository_mutation_attempted": any(
            row.get("effect_class") == "REPOSITORY_MUTATION" for row in effect_events
        ),
        "git_mutation_attempted": any(
            row.get("effect_class") == "GIT_MUTATION" for row in effect_events
        ),
        "external_action_attempted": any(
            row.get("effect_class") == "EXTERNAL_ACTION" for row in effect_events
        ),
        "effect_events": effect_events,
        "unified_output_valid": not output_errors if case.get("output_profile") else None,
        "unified_output_errors": output_errors,
        "contracts_exercised": contracts,
    }


def _run_canonical_case(case: dict[str, Any]) -> dict[str, Any]:
    resolutions = [resolve_reference(reference) for reference in case["references"]]
    allowed = {RESOLVED, UNRESOLVED}
    projected = [
        {
            "input_reference": row["input_reference"],
            "resolution_status": row["resolution_status"],
            "canonical_id": row.get("canonical_id"),
            "final_disposition": row.get("final_disposition"),
        }
        for row in resolutions
    ]
    return {
        "all_current_or_fail_closed": all(
            row["resolution_status"] in allowed for row in resolutions
        ),
        "memory_or_fuzzy_resolution_used": any(
            row["memory_or_fuzzy_resolution_used"] for row in resolutions
        ),
        "historical_file_used_as_identity": any(
            row["historical_file_used_as_identity"] for row in resolutions
        ),
        "references": projected,
        "contracts_exercised": ["CURRENT_CANONICAL_RESOLUTION_R1"],
    }


def _run_source_derived_case(case: dict[str, Any]) -> dict[str, Any]:
    statement = case["source_statement"]
    collision_run = {
        "schema_version": "ignition-object-collision-run-r1",
        "run_id": "step13-e-source-explicit-authority-howl",
        "current_ref": CURRENT_REF,
        "operation_id": "knowledge.collide_object",
        "run_mode": "READ_ONLY_RUN",
        "input_object": {
            "object_id": "INPUT-E-SOURCE",
            "object_type": "NOTE",
            "provenance": {
                "source_kind": "USER_PASTED",
                "source_locator": "fixture.case.E.source_statement",
                "supplied_by": "CURRENT_USER",
                "content_sha256": _sha256_bytes(statement.encode("utf-8")),
                "version_or_captured_at": "step13-offline-fixture-r1",
            },
        },
        "normalized_units": [
            {
                "unit_id": "E-U1",
                "category": "SOURCE_CLAIM",
                "text": statement,
                "source_locator": "fixture.case.E.source_statement",
                "input_origin": "SOURCE_EXPLICIT",
            }
        ],
        "canonical_search": {
            "registries_searched": [
                "ignition/data/foundation/function-assets/identity-cards.jsonl",
                "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl",
            ],
            "matches": [],
        },
        "findings": [
            {
                "finding_id": "E-F1",
                "statement": statement,
                "relationship": "SOURCE_DERIVED",
                "unit_ids": ["E-U1"],
                "canonical_match_ids": [],
                "post_collision_increment": False,
            }
        ],
        "candidate_new": [],
        "quantitative_assessments": [],
        "side_effects": {
            "repository_mutation": False,
            "external_action": False,
            "registry_write": False,
        },
    }
    collision_errors = validate_run(collision_run)
    rendered = render_run(collision_run) if not collision_errors else None
    output_errors = validate_output(_source_derived_output(statement))
    input_derived = rendered["input_derived_findings"] if rendered else []
    candidates = rendered["candidate_new"] if rendered else []
    return {
        "collision_valid": not collision_errors,
        "collision_errors": collision_errors,
        "collision_result_status": rendered["result_status"] if rendered else None,
        "input_derived_statements": [row["statement"] for row in input_derived],
        "candidate_new_count": len(candidates),
        "source_statement_relabelled_candidate": any(
            row.get("statement") == statement for row in candidates
        ),
        "candidate_registry_action": rendered["candidate_registry_action"] if rendered else None,
        "side_effects_authorized": rendered["side_effects_authorized"] if rendered else False,
        "repository_mutation_attempted": False,
        "external_action_attempted": False,
        "unified_output_valid": not output_errors,
        "unified_output_errors": output_errors,
        "contracts_exercised": [
            "IGNITION_OBJECT_COLLISION_RUN_R1",
            "IGNITION_RUN_OUTPUT_CONTRACT_R1",
        ],
    }


def _validate_fixture(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("suite_id") != "IGNITION_OPERATING_METHOD_R1_STRANGER_AGENT_ADVERSARIAL":
        errors.append("suite_id is missing or changed")
    if document.get("task_id") != "IGNITION-20260829-148":
        errors.append("task_id is missing or changed")
    if document.get("current_ref") != CURRENT_REF:
        errors.append("fixture Current ref differs from the Step12 proven parent")
    if document.get("critical_case_policy") != "ANY_CASE_FAILURE_BLOCKS_R1_COMPLETION":
        errors.append("critical failure policy is missing or changed")
    cases = document.get("cases")
    if not isinstance(cases, list):
        return errors + ["cases must be an array"]
    case_ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if tuple(case_ids) != REQUIRED_CASE_IDS:
        errors.append("required A-G case ids are missing, duplicated or reordered")
    if not all(case.get("critical") is True for case in cases if isinstance(case, dict)):
        errors.append("every A-G case must be critical")
    return errors


def run_suite(
    fixture_document: dict[str, Any] | None = None,
    *,
    source_digests: dict[str, str] | None = None,
) -> dict[str, Any]:
    fixture = (
        copy.deepcopy(fixture_document)
        if fixture_document is not None
        else load_json(FIXTURE_PATH)
    )
    fixture_errors = _validate_fixture(fixture)
    results: list[dict[str, Any]] = []
    for case in fixture.get("cases", []) if isinstance(fixture, dict) else []:
        case_id = (
            case.get("case_id", "MISSING_CASE_ID")
            if isinstance(case, dict)
            else "INVALID_CASE"
        )
        actual: dict[str, Any] = {}
        errors: list[str] = []
        try:
            if case["case_kind"] == "REQUEST_ROUTE":
                actual = _run_route_case(case)
            elif case["case_kind"] == "CANONICAL_REFERENCES":
                actual = _run_canonical_case(case)
            elif case["case_kind"] == "SOURCE_DERIVED_COLLISION":
                actual = _run_source_derived_case(case)
            else:
                raise StrangerAgentRegressionError(
                    f"unsupported case_kind: {case['case_kind']}"
                )
            errors.extend(_subset_errors(actual, case.get("expected", {})))
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
        results.append(
            {
                "case_id": case_id,
                "case_kind": case.get("case_kind") if isinstance(case, dict) else None,
                "critical": case.get("critical") is True if isinstance(case, dict) else False,
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
                "actual": actual,
            }
        )

    all_errors = fixture_errors + [
        f"{row['case_id']}: {error}"
        for row in results
        for error in row["errors"]
    ]
    report_source_digests = (
        _source_digests()
        if source_digests is None
        else _validated_source_digests(source_digests)
    )
    report: dict[str, Any] = {
        "schema_version": "ignition-stranger-agent-adversarial-result-r1",
        "suite_id": "IGNITION_OPERATING_METHOD_R1_STRANGER_AGENT_ADVERSARIAL",
        "task_id": "IGNITION-20260829-148",
        "current_ref": CURRENT_REF,
        "execution_scope": "OFFLINE_DETERMINISTIC_NO_REPOSITORY_OR_EXTERNAL_EFFECT_ADAPTER",
        "critical_case_policy": "ANY_CASE_FAILURE_BLOCKS_R1_COMPLETION",
        "status": "PASS" if not all_errors and len(results) == 7 else "FAIL",
        "case_count": len(results),
        "passed_case_count": sum(row["status"] == "PASS" for row in results),
        "failed_case_count": sum(row["status"] == "FAIL" for row in results),
        "fixture_errors": fixture_errors,
        "cases": results,
        "effect_summary": {
            "effect_event_count": sum(
                len(row["actual"].get("effect_events", [])) for row in results
            ),
            "repository_mutation_attempted": any(
                row["actual"].get("repository_mutation_attempted") is True
                for row in results
            ),
            "git_mutation_attempted": any(
                row["actual"].get("git_mutation_attempted") is True for row in results
            ),
            "external_action_attempted": any(
                row["actual"].get("external_action_attempted") is True for row in results
            ),
        },
        "contracts_exercised": list(CONTRACT_PATHS),
        "source_digests": report_source_digests,
        "claim_ceiling": "Task148 offline stranger-Agent contract-composition evidence only; PASS proves deterministic routing, fail-closed and source-boundary behavior for the seven fixtures, not external truth, live execution, repository mutation, production readiness, Owner acceptance, merge, Current-on-main or epistemic acceptance.",
    }
    report["receipt_sha256"] = _canonical_hash(report)
    return report


def replay_historical_receipt(persisted: dict[str, Any]) -> dict[str, Any]:
    """Replay the receipt against the exact historical source snapshot.

    Task148's receipt is historical evidence.  Later Current closeout work can
    legitimately change a contract source, fixture, or canonical projection
    without rewriting that receipt.  Re-running the current code while merely
    copying old digests would therefore be a false historical replay.  This
    function materializes the source tree whose bytes match the receipt's
    recorded digests, runs that tree's own JSON emitter, and returns its
    independently recomputed report.
    """
    expected_digests = _validated_source_digests(persisted.get("source_digests"))
    if persisted.get("current_ref") != CURRENT_REF:
        raise StrangerAgentRegressionError("historical receipt Current ref differs from the Step13 contract")

    with tempfile.TemporaryDirectory(prefix="ignition-stranger-agent-replay-") as temporary:
        temporary_root = Path(temporary)
        archive_path = temporary_root / "historical-source.tar"
        materialized_root = temporary_root / "repository"
        materialized_root.mkdir()
        try:
            subprocess.run(
                [
                    "git",
                    "archive",
                    "--format=tar",
                    f"--output={archive_path}",
                    HISTORICAL_SOURCE_COMMIT,
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )
            with tarfile.open(archive_path, mode="r") as archive:
                archive.extractall(materialized_root)
        except (OSError, subprocess.CalledProcessError, tarfile.TarError) as exc:
            raise StrangerAgentRegressionError(
                f"historical source materialization failed: {exc}"
            ) from exc

        historical_ignition_root = materialized_root / "ignition"
        actual_digests = _source_digests_for_root(historical_ignition_root)
        if actual_digests != expected_digests:
            raise StrangerAgentRegressionError(
                "historical source snapshot does not match the receipt's recorded digests"
            )

        runner = historical_ignition_root / "tools/operations/run_ignition_stranger_agent_regression.py"
        result = subprocess.run(
            [sys.executable, str(runner), "--emit-json"],
            cwd=materialized_root,
            env={**os.environ, "PYTHONPATH": str(historical_ignition_root)},
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise StrangerAgentRegressionError(
                f"historical stranger-Agent emitter failed: {detail}"
            )
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise StrangerAgentRegressionError(
                "historical stranger-Agent emitter did not return JSON"
            ) from exc
        if report.get("source_digests") != expected_digests:
            raise StrangerAgentRegressionError(
                "historical stranger-Agent report source digests drifted"
            )
        return report


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-json", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = run_suite()
    if args.emit_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["status"] == "PASS" else 1
    if not RECEIPT_PATH.is_file():
        print(f"IGNITION_STRANGER_AGENT_RECEIPT_MISSING path={RECEIPT_PATH}")
        return 1
    persisted = load_json(RECEIPT_PATH)
    replay = replay_historical_receipt(persisted)
    source_digests_changed = persisted.get("source_digests") != report["source_digests"]
    comparison = replay if source_digests_changed else report
    if persisted != comparison:
        print(
            "IGNITION_STRANGER_AGENT_RECEIPT_STALE "
            f"expected={comparison['receipt_sha256']} actual={persisted.get('receipt_sha256')}"
        )
        return 1
    print(
        "IGNITION_STRANGER_AGENT_ADVERSARIAL_OK "
        f"cases={report['case_count']} passed={report['passed_case_count']} "
        f"effects={report['effect_summary']['effect_event_count']} "
        f"receipt_sha256={persisted['receipt_sha256']} "
        f"source_mode={'HISTORICAL_RECEIPT_REPLAY' if source_digests_changed else 'CURRENT_SOURCE'} "
        f"current_source_digests_changed={str(source_digests_changed).lower()}"
    )
    return 0 if comparison["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
