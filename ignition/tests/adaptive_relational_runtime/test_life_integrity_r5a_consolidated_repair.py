# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Attack and acceptance tests for R5A-CR-001 through R5A-CR-011."""

from __future__ import annotations

from dataclasses import replace

import pytest

from life_integrity_r5a import consolidated_repair_gate as CR
import tools.generate_life_integrity_r5a as GEN
import tools.validate_life_integrity_r5a_consolidated_repair as VALIDATE


@pytest.mark.parametrize(
    "case", CR.CONSOLIDATED_REPAIR_CASES, ids=lambda case: case.case_id
)
def test_each_consolidated_repair_case_executes_every_bound_surface(case):
    result = CR.run_case(case, schema_documents=VALIDATE.schema_documents())
    assert result["passed"], result
    assert result["observed_outcome"] == "REJECTED"
    assert result["evidence_id"] == case.evidence_object.evidence_id
    assert result["surface_results"]
    assert all(surface["passed"] for surface in result["surface_results"])


def test_exact_required_ids_and_typed_evidence_are_not_count_substitutes():
    cases = CR.CONSOLIDATED_REPAIR_CASES
    assert tuple(case.case_id for case in cases) == (
        CR.REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS
    )
    assert len({case.case_id for case in cases}) == len(cases)
    assert len({case.evidence_object.evidence_id for case in cases}) == len(cases)
    for case in cases:
        assert case.expected_outcome == "REJECTED"
        assert case.concrete_input
        assert case.evidence_object.supports_all({f"attack:{case.case_id}"})

    receipt = CR.run_consolidated_repair_gate(
        schema_documents=VALIDATE.schema_documents()
    )
    assert receipt["status"] == "PASS", receipt
    assert receipt["executed_case_ids"] == list(
        CR.REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS
    )
    assert receipt["failed_case_ids"] == []
    assert receipt["count_is_not_acceptance"] is True
    assert receipt["independent_acceptance_claimed"] is False


def test_every_public_schema_declares_draft_2020_12_and_rejects_invalid_instance():
    ok, results, errors = VALIDATE.validate_schema_matrix()
    assert ok, errors
    assert [result["schema"] for result in results] == list(
        VALIDATE.SCHEMA_BUILDERS
    )
    for result in results:
        assert result["metaschema"] == "PASS"
        assert result["valid_instance"] == "ACCEPTED"
        assert result["invalid_instance"] == "REJECTED"
        assert result["passed"] is True


def test_gate_blocks_missing_duplicate_changed_bypassed_and_deleted_identity():
    ok, results, errors = VALIDATE.run_mutation_probes()
    assert ok, errors
    assert {result["mutation"] for result in results} == {
        "missing_case",
        "duplicate_case",
        "changed_expectation",
        "bypassed_fixture",
        "deleted_required_id",
    }
    assert all(result["observed"] == "BLOCKED" for result in results)


def test_direct_changed_expectation_cannot_self_pass():
    cases = CR.CONSOLIDATED_REPAIR_CASES
    mutated = (
        replace(cases[0], expected_error="TranslatedClaimContractError"),
    ) + cases[1:]
    receipt = CR.run_consolidated_repair_gate(
        cases=mutated,
        schema_documents=VALIDATE.schema_documents(),
    )
    assert receipt["status"] == "BLOCKED"
    assert "R5A-CR-001" in receipt["failed_case_ids"]


def test_generated_registry_and_receipt_bind_the_exact_executed_cases():
    registry = GEN._consolidated_repair_case_registry()
    receipt = GEN._consolidated_repair_acceptance_receipt()
    assert registry["required_case_ids"] == list(
        CR.REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS
    )
    assert [case["case_id"] for case in registry["cases"]] == list(
        CR.REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS
    )
    assert receipt["status"] == "PASS", receipt
    assert receipt["executed_case_ids"] == list(
        CR.REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS
    )
