#!/usr/bin/env python3
"""Adversarial tests for the task-111 failure-case evidence gate."""
import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import failure_case_evidence_gate as G  # noqa: E402


ZERO_SHA = "0" * 64
ONE_COMMIT = "1" * 40


def valid_record():
    return {
        "schema_version": "1.0.0",
        "case_id": "CF-fixture-valid",
        "source_path": "case_failures/examples/fixture.md",
        "original_classification": "IMPLEMENTATION_DEFECT",
        "case_label": "REPRODUCED_IMPLEMENTATION_DEFECT",
        "claim_ceiling": "A bounded implementation defect in the named repository target only.",
        "status_dimensions": {
            "external_evidence": "EVIDENCE_SUPPORTED_WITHIN_SCOPE",
            "executable_target": "TARGET_FOUND_AND_FROZEN",
            "formalization": "FORMALIZATION_FAITHFUL_WITHIN_SCOPE",
            "reproduction": "REPRODUCED_IMPLEMENTATION_DEFECT",
        },
        "evidence_gate": {
            "target": {
                "kind": "repository_executable",
                "path": "tests/fixtures/failure_case_evidence_gate/target.py",
                "commit": ONE_COMMIT,
                "interface": "fixture_target(case_id, exact_input)",
                "case_binding": "CF-fixture-valid",
            },
            "exact_input": {"path": "tests/fixtures/failure_case_evidence_gate/input.json", "sha256": ZERO_SHA},
            "actual_output": {"path": "tests/fixtures/failure_case_evidence_gate/output.json", "sha256": ZERO_SHA, "status": "WRONG_RESULT"},
            "trace": {"path": "tests/fixtures/failure_case_evidence_gate/trace.jsonl", "sha256": ZERO_SHA},
            "run_id": "TASK111-FIXTURE-RUN-1",
            "repeat_count": 2,
            "oracle": {"kind": "versioned_contract_oracle", "basis": "The fixture contract expects WRONG_RESULT to be rejected."},
            "claim_ceiling": "A bounded implementation defect in the named repository target only.",
            "first_failure": {"preserved": True, "path": "tests/fixtures/failure_case_evidence_gate/first-failure.json", "sha256": ZERO_SHA, "observed_at": "2026-08-01T22:00:00+08:00"},
            "formalization_frozen": True,
            "regression": {"status": "REGRESSION_GUARD_ESTABLISHED", "test": "test_fixture_rejects_wrong_result", "command": "python3 tests/test_failure_case_evidence_gate.py"},
            "external_evidence_refs": ["fixture:versioned-contract-oracle"],
        },
    }


def errors(record):
    return G.validate_case(record)


def test_valid_reproduced_defect_passes():
    assert errors(valid_record()) == []


def test_hypothetical_phrase_without_gate_fails():
    record = valid_record()
    record["evidence_gate"] = None
    assert any("evidence_gate: is required" in item for item in errors(record))


def test_missing_target_commit_fails():
    record = valid_record()
    record["evidence_gate"]["target"]["commit"] = ""
    assert any("target.commit" in item for item in errors(record))


def test_missing_run_and_trace_fail():
    record = valid_record()
    record["evidence_gate"].pop("run_id")
    record["evidence_gate"].pop("trace")
    result = errors(record)
    assert any("run_id" in item for item in result)
    assert any("trace" in item for item in result)


def test_llm_output_is_not_a_target():
    record = valid_record()
    record["evidence_gate"]["target"]["kind"] = "llm_output"
    assert any("target.kind" in item for item in errors(record))


def test_wrong_semantic_target_fails_closed():
    record = valid_record()
    record["evidence_gate"]["target"]["case_binding"] = "CF-other-case"
    assert any("case_binding" in item for item in errors(record))


def test_no_external_evidence_or_oracle_reference_fails():
    record = valid_record()
    record["evidence_gate"]["external_evidence_refs"] = []
    assert any("external_evidence_refs" in item for item in errors(record))


def test_formalization_change_invalidates_result():
    record = valid_record()
    record["evidence_gate"]["formalization_frozen"] = False
    assert any("formalization_frozen" in item for item in errors(record))


def test_deleted_first_failure_invalidates_result():
    record = valid_record()
    record["evidence_gate"]["first_failure"]["preserved"] = False
    assert any("first_failure.preserved" in item for item in errors(record))


def test_directory_placement_is_not_evidence():
    record = valid_record()
    record["source_path"] = "docs/failure_cases/fixture.md"
    assert any("source_path" in item for item in errors(record))


def test_reproduction_dimension_cannot_hide_non_defect_label():
    record = valid_record()
    record["case_label"] = "NARRATIVE_HYPOTHESIS"
    assert any("case_label" in item for item in errors(record))


def test_task111_case_status_document_passes():
    payload = json.loads((REPO / "data/operations/iterations/111/case-status.json").read_text())
    assert G.validate_document(payload) == []


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    passed = 0
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
        passed += 1
    print(f"{passed}/{len(tests)} passed")
