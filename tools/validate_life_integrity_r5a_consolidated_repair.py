#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Machine acceptance gate for the consolidated R5-A contract repair."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from life_integrity_r5a import consolidated_repair_gate as CR  # noqa: E402
from life_integrity_r5a import fixtures as FX  # noqa: E402
from life_integrity_r5a import validators  # noqa: E402
import tools.generate_life_integrity_r5a as generator  # noqa: E402


REPAIR_BRANCH = (
    "repair/ignition-r5a-consolidated-contract-bypass-narrow-repair-r1-20260726"
)
SCHEMA_BUILDERS = {
    "life-integrity-assessment-schema.json": generator._life_integrity_assessment_schema,
    "embodied-view-projection-schema.json": generator._embodied_view_projection_schema,
    "translated-claim-schema.json": generator._translated_claim_schema,
    "practice-safety-envelope-schema.json": generator._practice_safety_envelope_schema,
    "concept-mapping-transition-schema.json": generator._concept_mapping_transition_schema,
    "longitudinal-feedback-schema.json": generator._longitudinal_feedback_schema,
}


def schema_documents() -> dict[str, dict[str, Any]]:
    return {name: builder() for name, builder in SCHEMA_BUILDERS.items()}


def _jsonable(value: object) -> dict[str, Any]:
    return json.loads(json.dumps(asdict(value), ensure_ascii=False))


def valid_schema_instances() -> dict[str, dict[str, Any]]:
    embodied = FX.sample_embodied_agent().get_view("PhysiologicalView")
    return {
        "life-integrity-assessment-schema.json": {
            "proposal": _jsonable(FX.sample_local_optimization_proposal())
        },
        "embodied-view-projection-schema.json": _jsonable(embodied),
        "translated-claim-schema.json": _jsonable(FX.sample_translated_claim()),
        "practice-safety-envelope-schema.json": _jsonable(FX.sample_safety_envelope()),
        "concept-mapping-transition-schema.json": _jsonable(FX.sample_concept_mapping()),
        "longitudinal-feedback-schema.json": _jsonable(
            FX.sample_longitudinal_contract()
        ),
    }


def invalid_schema_instances() -> dict[str, dict[str, Any]]:
    return {
        "life-integrity-assessment-schema.json": CR._UNKNOWN_LIFE_ASSESSMENT,
        "embodied-view-projection-schema.json": {
            "view_id": "PhysiologicalView",
            "subject_identity": "synthetic-subject",
            "observations": ["synthetic"],
            "confidence": 2,
            "time_scope": "UNKNOWN",
            "unknown": False,
            "provenance": "",
            "provenance_boundary": "boundary-A",
        },
        "translated-claim-schema.json": {
            "source_provenance": "synthetic",
            "claim_class": "HISTORICAL_SOURCE",
        },
        "practice-safety-envelope-schema.json": _jsonable(
            replace(
                FX.sample_safety_envelope(),
                long_term_followup_plan="stop taking your medication",
            )
        ),
        "concept-mapping-transition-schema.json": CR._CONCEPT_INVALID,
        "longitudinal-feedback-schema.json": CR._INTEGER_LONGITUDINAL,
    }


def _unknown_keyword_paths(value: object, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        if "not_unknowns" in value:
            errors.append(f"non-enforcing keyword remains at {path}.not_unknowns")
        for key, child in value.items():
            errors.extend(_unknown_keyword_paths(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_unknown_keyword_paths(child, f"{path}[{index}]"))
    return errors


def validate_schema_matrix(
    schemas: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool, list[dict[str, Any]], list[str]]:
    active_schemas = schema_documents() if schemas is None else schemas
    valid = valid_schema_instances()
    invalid = invalid_schema_instances()
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    if set(active_schemas) != set(SCHEMA_BUILDERS):
        errors.append("schema document set does not equal the exact public schema set")
    for name in SCHEMA_BUILDERS:
        schema = active_schemas[name]
        try:
            if schema.get("$schema") != generator.JSON_SCHEMA_DIALECT:
                raise AssertionError("declared dialect is not Draft 2020-12")
            Draft202012Validator.check_schema(schema)
            keyword_errors = _unknown_keyword_paths(schema)
            if keyword_errors:
                raise AssertionError("; ".join(keyword_errors))
            validator = Draft202012Validator(
                schema, format_checker=FormatChecker()
            )
            validator.validate(valid[name])
            try:
                validator.validate(invalid[name])
            except ValidationError as exc:
                results.append(
                    {
                        "schema": name,
                        "metaschema": "PASS",
                        "valid_instance": "ACCEPTED",
                        "invalid_instance": "REJECTED",
                        "invalid_error": exc.message,
                        "passed": True,
                    }
                )
            else:
                raise AssertionError("invalid instance was accepted")
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            results.append(
                {
                    "schema": name,
                    "metaschema": "BLOCKED",
                    "valid_instance": "UNKNOWN",
                    "invalid_instance": "BYPASS_OR_WRONG_REJECTION",
                    "invalid_error": f"{type(exc).__name__}: {exc}",
                    "passed": False,
                }
            )
    return (not errors, results, errors)


def run_mutation_probes(
    schemas: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool, list[dict[str, Any]], list[str]]:
    active_schemas = schema_documents() if schemas is None else schemas
    cases = CR.CONSOLIDATED_REPAIR_CASES
    required = CR.REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS
    valid_first = dict(cases[0].concrete_input)
    valid_first["mechanism_status"] = "NOT_ASSERTED"
    mutations = (
        ("missing_case", cases[:-1], required),
        ("duplicate_case", cases + (cases[-1],), required),
        (
            "changed_expectation",
            (replace(cases[0], expected_error="TranslatedClaimContractError"),)
            + cases[1:],
            required,
        ),
        (
            "bypassed_fixture",
            (replace(cases[0], concrete_input=valid_first),) + cases[1:],
            required,
        ),
        ("deleted_required_id", cases, required[:-1]),
    )
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for name, mutated_cases, mutated_required in mutations:
        receipt = CR.run_consolidated_repair_gate(
            cases=mutated_cases,
            required_ids=mutated_required,
            schema_documents=active_schemas,
        )
        blocked = receipt["status"] == "BLOCKED"
        results.append(
            {
                "mutation": name,
                "expected": "BLOCKED",
                "observed": receipt["status"],
                "passed": blocked,
            }
        )
        if not blocked:
            errors.append(f"mutation did not block: {name}")
    return (not errors, results, errors)


def _git_changed_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", CR.REJECTED_CANDIDATE_HEAD],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(
        set(filter(None, completed.stdout.splitlines()))
        | set(filter(None, untracked.stdout.splitlines()))
    )


def _artifact_errors() -> list[str]:
    errors: list[str] = []
    for name, builder in generator._ARTIFACTS:
        path = Path(generator.OUT_DIR) / name
        if not path.is_file():
            errors.append(f"missing generated artifact: {path.relative_to(REPO_ROOT)}")
            continue
        actual = json.loads(path.read_text(encoding="utf-8"))
        expected = builder()
        if actual != expected:
            errors.append(f"stale generated artifact: {path.relative_to(REPO_ROOT)}")
    return errors


def _scope_errors(changed_paths: list[str]) -> list[str]:
    errors: list[str] = []
    prohibited_prefixes = (
        "domain-packs/",
        "tools/ignition_runtime/",
        "schemas/ignition_runtime/",
        "tests/ignition_runtime/",
        "tools/adaptive_relational_runtime/",
    )
    for path in changed_paths:
        if path.startswith(prohibited_prefixes):
            errors.append(f"prohibited later-stage/runtime path changed: {path}")
    return errors


def main() -> int:
    schemas = schema_documents()
    instance_receipt = CR.run_consolidated_repair_gate(schema_documents=schemas)
    schema_ok, schema_results, schema_errors = validate_schema_matrix(schemas)
    mutation_ok, mutation_results, mutation_errors = run_mutation_probes(schemas)
    aggregate_ok, aggregate_failures = validators.validate_all()
    changed_paths = _git_changed_paths()
    errors: list[str] = []
    if instance_receipt["status"] != "PASS":
        errors.extend(instance_receipt["identity_errors"])
        errors.extend(
            f"failed exact case: {case_id}"
            for case_id in instance_receipt["failed_case_ids"]
        )
    if not schema_ok:
        errors.extend(schema_errors)
    if not mutation_ok:
        errors.extend(mutation_errors)
    if not aggregate_ok:
        errors.extend(aggregate_failures)
    errors.extend(_artifact_errors())
    errors.extend(_scope_errors(changed_paths))

    receipt = {
        "schema": "r5a/consolidated-contract-bypass-repair-machine-gate/v1",
        "task_id": CR.TASK_ID,
        "rejected_candidate_head": CR.REJECTED_CANDIDATE_HEAD,
        "required_case_ids": list(CR.REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS),
        "executed_case_ids": instance_receipt["executed_case_ids"],
        "instance_gate_status": instance_receipt["status"],
        "instance_results": instance_receipt["results"],
        "schema_dialect": generator.JSON_SCHEMA_DIALECT,
        "schema_matrix": schema_results,
        "mutation_matrix": mutation_results,
        "aggregate_validator": "PASS" if aggregate_ok else "BLOCKED",
        "changed_paths": changed_paths,
        "formal_branch": REPAIR_BRANCH,
        "r5b_started": False,
        "r5c_started": False,
        "r6_started": False,
        "ready_transition_performed": False,
        "merge_performed": False,
        "main_changed": False,
        "independent_acceptance_claimed": False,
        "claim_ceiling": "repository_contract_repair_implemented_awaiting_independent_review",
        "count_is_not_acceptance": True,
        "errors": errors,
        "status": "PASS" if not errors else "BLOCKED",
    }
    print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
