from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reos_vnext import (
    ArtifactRefRecord,
    ClaimCandidate,
    ContractError,
    EvidenceRequest,
    ResearchObligation,
    ReviewDecision,
    ReviewRequest,
    add_obligation,
    amend_question,
    compute_case_status,
    load_case,
    new_case,
    prepare_handoff,
    record_artifact,
    record_claim_candidate,
    record_evidence_request,
    record_review,
    request_review,
    serialize_case,
    set_case_state,
    sha256_json,
    validate_case,
)


ROOT = Path(__file__).resolve().parents[1]
PREREG_REF = "pilot/preregistration.md@18dbd49c259cf4685d8a40491a539260c3c3a28c"
SUMMARY = {
    "question": "Does the bounded pilot proposition hold under its stated scope?",
    "scope": "public non-high-stakes pilot",
    "estimand": "bounded descriptive difference",
    "measurement_boundaries": ["observed measure vs proxy"],
    "claim_ceiling": "source-scoped descriptive result only",
    "stop_conditions": ["missing primary evidence", "scope exceeded"],
}
PREREG_DIGEST = sha256_json({"preregistration_ref": PREREG_REF, "frozen_validation_summary": SUMMARY})


def make_case():
    return new_case(
        case_id="case:test-r1",
        activation_reason="several source families and an independent review are required",
        observed_need=["contradiction tracking", "typed handoff"],
        simpler_baseline="ordinary research notes and a source table",
        unnecessary_modules=["ExecutionPacket", "ExecutorLease", "ResumeCapsule", "supervisor"],
        preregistration_ref=PREREG_REF,
        preregistration_digest=PREREG_DIGEST,
        frozen_validation_summary=SUMMARY,
        budget_contract={"max_minutes": 60, "method": "operator-accounted"},
        stop_conditions=["do not infer causality", "preserve blocked routes"],
    )


def obligation(obligation_id="obl:source-a", *, depends_on=(), status="OPEN", review_required=False):
    return ResearchObligation(
        obligation_id=obligation_id,
        type="RECOVER_PRIMARY_SOURCE",
        question_ref=PREREG_REF,
        depends_on=tuple(depends_on),
        inputs=(),
        required_capabilities=("public-web-read",),
        permission_scope="ordinary-research",
        completion_contract="record source identity, family, access state and limitation",
        stop_fail_conditions=("source unavailable",),
        status=status,
        output_artifact_refs=(),
        review_required=review_required,
    )


def artifact(artifact_id="art:source-a", family="family-a"):
    return ArtifactRefRecord(
        artifact_id=artifact_id,
        ref="https://example.test/source-a",
        sha256="a" * 64,
        provenance={"kind": "public-primary", "retrieved_at": "2026-08-14T00:00:00Z"},
        scope="pilot scope",
        privacy_class="PUBLIC_SAFE_CANDIDATE",
        source_family=family,
        derivation_refs=(),
        limitations=("example fixture",),
    )


class MinimalKernelTests(unittest.TestCase):
    def assertCode(self, document, expected):
        with self.assertRaises(ContractError) as context:
            validate_case(document)
        self.assertIn(expected, {issue.code for issue in context.exception.issues})

    def test_new_case_is_valid_and_serialization_is_deterministic(self):
        document = make_case()
        validate_case(document)
        self.assertEqual(serialize_case(document), serialize_case(json.loads(serialize_case(document))))
        self.assertEqual(document["case"]["question_contract"]["validation_summary_digest"], sha256_json(SUMMARY))
        self.assertEqual(document["case"]["question_contract"]["preregistration_digest"], PREREG_DIGEST)
        self.assertEqual(compute_case_status(document), "OPEN")

    def test_cycle_and_unknown_dependency_are_rejected(self):
        document = make_case()
        document["case"]["obligations"] = [
            obligation("obl:a", depends_on=("obl:b",)).as_dict(),
            obligation("obl:b", depends_on=("obl:a",)).as_dict(),
        ]
        self.assertCode(document, "CYCLE")
        document["case"]["obligations"][1]["depends_on"] = ["obl:missing"]
        self.assertCode(document, "UNKNOWN_DEPENDENCY")

    def test_question_amendment_is_append_only(self):
        amended = amend_question(
            make_case(),
            frozen_validation_summary={**SUMMARY, "scope": "narrower public pilot scope"},
            reason="pilot selection required a narrower population boundary",
            amendment_id="amend:1",
        )
        validate_case(amended)
        self.assertEqual(amended["case"]["question_contract"]["version"], 2)
        mutated = copy.deepcopy(make_case())
        mutated["case"]["question_contract"]["current_validation_summary"]["scope"] = "silent mutation"
        self.assertCode(mutated, "QUESTION_MUTATION")
        coordinated = copy.deepcopy(make_case())
        coordinated["case"]["question_contract"]["current_validation_summary"]["scope"] = "silent replacement"
        coordinated["case"]["question_contract"]["initial_validation_summary_digest"] = sha256_json(
            coordinated["case"]["question_contract"]["current_validation_summary"]
        )
        coordinated["case"]["question_contract"]["validation_summary_digest"] = sha256_json(
            coordinated["case"]["question_contract"]["current_validation_summary"]
        )
        self.assertCode(coordinated, "QUESTION_MUTATION")
        coordinated_frozen = copy.deepcopy(make_case())
        replacement = {**SUMMARY, "scope": "coordinated frozen replacement"}
        coordinated_frozen["case"]["question_contract"]["frozen_validation_summary"] = replacement
        coordinated_frozen["case"]["question_contract"]["current_validation_summary"] = replacement
        coordinated_frozen["case"]["question_contract"]["initial_validation_summary_digest"] = sha256_json(replacement)
        coordinated_frozen["case"]["question_contract"]["validation_summary_digest"] = sha256_json(replacement)
        self.assertCode(coordinated_frozen, "QUESTION_MUTATION")
        bool_version = copy.deepcopy(make_case())
        bool_version["case"]["question_contract"]["version"] = True
        self.assertCode(bool_version, "QUESTION_MUTATION")
        with self.assertRaises(ContractError) as context:
            amend_question(
                bool_version,
                frozen_validation_summary={**SUMMARY, "scope": "repair input"},
                reason="must not normalize malformed version",
                amendment_id="amend:bad",
            )
        self.assertIn("QUESTION_MUTATION", {issue.code for issue in context.exception.issues})
        with self.assertRaises(ContractError) as context:
            amend_question(
                amended,
                frozen_validation_summary={**SUMMARY, "scope": "third scope"},
                reason="second bounded amendment",
                amendment_id="amend:1",
            )
        self.assertIn("DUPLICATE_ID", {issue.code for issue in context.exception.issues})

    def test_question_contract_does_not_copy_full_preregistration(self):
        expanded = copy.deepcopy(make_case())
        expanded["case"]["question_contract"]["current_validation_summary"]["source_rules"] = {
            "include": "external preregistration detail"
        }
        self.assertCode(expanded, "UNKNOWN_FIELD")

    def test_evidence_retrieval_cannot_upgrade_truth(self):
        document = make_case()
        document["case"]["obligations"] = [obligation().as_dict()]
        document["case"]["evidence_requests"] = [
            {
                "request_id": "req:a",
                "obligation_id": "obl:source-a",
                "question": "Can source A be recovered?",
                "desired_evidence_type": "primary source",
                "source_family_requirement": "independent family",
                "retrieval_state": "FULLTEXT_RECOVERED",
                "access_limitation": "none",
                "result_artifact_ids": [],
                "epistemic_status": "ACCEPTED",
            }
        ]
        self.assertCode(document, "EVIDENCE_TRUTH_UPGRADE")

    def test_review_owner_acceptance_is_rejected(self):
        document = make_case()
        document = request_review(
            document,
            ReviewRequest(
                review_id="review:r1",
                named_question="Are source families independently identified?",
                input_refs=["case:test-r1"],
                independence_requirement="fresh session with no baseline evaluator context",
                forbidden_assumptions=("review agreement is not truth",),
            ),
        )
        document["case"]["reviews"][0]["decision"] = {
            "review_id": "review:r1",
            "reviewer_ref": "role-g",
            "exact_input_refs": ["case:test-r1"],
            "independent": True,
            "verdict": "PASS_WITHIN_QUESTION_SCOPE",
            "material_findings": [],
            "repair_obligation_ids": [],
            "residuals": [],
            "scope_ceiling": "pilot scope",
            "owner_acceptance": True,
        }
        self.assertCode(document, "REVIEW_OWNER_ACCEPTANCE")

    def test_noncanonical_claim_and_artifact_provenance_boundaries(self):
        document = record_artifact(make_case(), artifact())
        candidate = ClaimCandidate(
            candidate_id="claim:c1",
            proposition="The bounded observation is associated with the stated measure.",
            scope="pilot scope",
            supporting_artifact_ids=("art:source-a",),
            contradicting_artifact_ids=(),
            alternative_explanations=("measurement mismatch",),
            measurement_definition="the stated measure only",
            claim_ceiling="source-scoped descriptive result",
            uncertainty=("not causal",),
        )
        document = record_claim_candidate(document, candidate)
        validate_case(document)
        forged = copy.deepcopy(document)
        forged["case"]["claim_candidates"][0]["canonical_status"] = "CANONICAL"
        self.assertCode(forged, "CANONICAL_CLAIM_MASQUERADE")
        missing = copy.deepcopy(make_case())
        missing["case"]["artifact_refs"] = [artifact().as_dict()]
        missing["case"]["artifact_refs"][0]["provenance"] = {}
        self.assertCode(missing, "ARTIFACT_PROVENANCE")
        nested = copy.deepcopy(missing)
        nested["case"]["artifact_refs"][0]["provenance"] = {
            "kind": "public-primary",
            "retrieved_at": "2026-08-14T00:00:00Z",
            "evidence": {"body": "copied source text"},
        }
        self.assertCode(nested, "UNKNOWN_FIELD")
        budget_store = copy.deepcopy(make_case())
        budget_store["case"]["budget_contract"]["canonical_truth"] = {"status": "accepted"}
        self.assertCode(budget_store, "UNKNOWN_FIELD")

    def test_provider_full_state_namespace_and_generic_success_are_rejected(self):
        document = make_case()
        for capability in (
            "provider:example-model",
            "model:example",
            "openai/gpt-5",
            "gpt-5",
            "anthropic/claude-3",
            "azure-openai",
            "provider_openai",
            "model.foo",
            "vertex-ai",
            "bedrock-claude",
            "ollama-llama3",
            "acme-llm-42",
            "acme-inference-engine-v2",
            "vendor:acme",
            "deployment:acme",
            "backend:acme",
            "acme-7b-instruct",
            "xai:grok",
            "cohere-command",
            "o1-mini",
        ):
            provider = obligation().as_dict()
            provider["required_capabilities"] = [capability]
            document["case"]["obligations"] = [provider]
            self.assertCode(document, "PROVIDER_HARD_DEPENDENCY")
        full = copy.deepcopy(make_case())
        full["case"]["activation"]["mode"] = "REOS_FULL"
        self.assertCode(full, "FULL_UNAVAILABLE")
        conflict = copy.deepcopy(make_case())
        conflict["case"]["case_state"] = "WAITING_REVIEW"
        self.assertCode(conflict, "CONFLICTING_STATE_NAMESPACE")
        success = copy.deepcopy(make_case())
        success["case"]["case_state"] = "SUCCESS"
        self.assertCode(success, "GENERIC_SUCCESS")
        owner_acceptance = copy.deepcopy(make_case())
        owner_acceptance["case"]["owner_boundary"] = "OWNER_ACCEPTED"
        self.assertCode(owner_acceptance, "OWNER_BOUNDARY")

    def test_cross_record_refs_and_nonfinite_values_are_rejected(self):
        malformed = copy.deepcopy(make_case())
        malformed["case"]["case_id"] = []
        self.assertCode(malformed, "MALFORMED_STATE")
        malformed_mode = copy.deepcopy(make_case())
        malformed_mode["case"]["activation"]["mode"] = []
        self.assertCode(malformed_mode, "MALFORMED_STATE")
        nonfinite_summary = copy.deepcopy(SUMMARY)
        nonfinite_summary["stop_conditions"] = [float("nan")]
        with self.assertRaises(ContractError) as context:
            amend_question(
                make_case(),
                frozen_validation_summary=nonfinite_summary,
                reason="non-finite fixture",
                amendment_id="amend:nan",
            )
        self.assertIn("MALFORMED_STATE", {issue.code for issue in context.exception.issues})
        malformed_document = {"schema_version": "reos.vnext.minimal-kernel.r1", "case": {}}
        for mutator in (
            lambda value: add_obligation(value, obligation()),
            lambda value: record_artifact(value, artifact()),
            lambda value: record_evidence_request(value, {}),
            lambda value: record_claim_candidate(value, {}),
            lambda value: request_review(value, {}),
            lambda value: set_case_state(value, "OPEN"),
        ):
            with self.assertRaises(ContractError) as context:
                mutator(malformed_document)
            self.assertTrue(context.exception.issues)
        document = add_obligation(make_case(), obligation())
        document["case"]["obligations"][0]["output_artifact_refs"] = ["art:missing"]
        self.assertCode(document, "UNKNOWN_REF")
        document = record_artifact(make_case(), artifact())
        document["case"]["artifact_refs"][0]["derivation_refs"] = ["art:missing"]
        self.assertCode(document, "UNKNOWN_REF")
        document = record_artifact(make_case(), artifact())
        document = request_review(
            document,
            ReviewRequest(
                review_id="review:refs",
                named_question="Are the artifact references inspectable?",
                input_refs=["art:source-a"],
                independence_requirement="fresh reviewer",
                forbidden_assumptions=(),
            ),
        )
        malformed_decision = {
            "review_id": "review:refs",
            "reviewer_ref": "role-g",
            "exact_input_refs": ["art:source-a"],
            "independent": True,
            "verdict": "MATERIAL_REPAIR_REQUIRED",
            "material_findings": [],
            "repair_obligation_ids": "not-a-list",
            "residuals": [],
            "scope_ceiling": "pilot scope",
        }
        with self.assertRaises(ContractError) as context:
            record_review(document, malformed_decision, [obligation("obl:repair")])
        self.assertIn("MALFORMED_STATE", {issue.code for issue in context.exception.issues})
        document["case"]["reviews"][0]["decision"] = {
            "review_id": "review:refs",
            "reviewer_ref": "role-g",
            "exact_input_refs": ["art:missing"],
            "independent": True,
            "verdict": "ABSTAIN",
            "material_findings": [],
            "repair_obligation_ids": [],
            "residuals": ["missing input"],
            "scope_ceiling": "pilot scope",
        }
        self.assertCode(document, "UNKNOWN_REF")
        nonfinite = copy.deepcopy(make_case())
        nonfinite["case"]["question_contract"]["current_validation_summary"]["measurement_boundaries"].append(float("nan"))
        self.assertCode(nonfinite, "NON_DETERMINISTIC_VALUE")

    def test_review_repair_reload_and_typed_handoff(self):
        document = add_obligation(make_case(), obligation(status="SATISFIED_WITH_SCOPE"))
        document = record_artifact(document, artifact())
        document = request_review(
            document,
            ReviewRequest(
                review_id="review:repair",
                named_question="Did the source-family ledger avoid duplicate publisher copies?",
                input_refs=["art:source-a"],
                independence_requirement="fresh independent evidence reviewer",
                forbidden_assumptions=("same publisher is not an independent family",),
            ),
        )
        repair = obligation("obl:repair", status="SATISFIED_WITH_RESIDUALS")
        document = record_review(
            document,
            ReviewDecision(
                review_id="review:repair",
                reviewer_ref="role-g",
                exact_input_refs=("art:source-a",),
                independent=True,
                verdict="MATERIAL_REPAIR_REQUIRED",
                material_findings=("publisher duplicates need explicit family labels",),
                repair_obligation_ids=(),
                residuals=(),
                scope_ceiling="pilot scope only",
            ),
            [repair],
        )
        validate_case(document)
        reloaded = json.loads(serialize_case(document))
        validate_case(reloaded)
        self.assertEqual(compute_case_status(reloaded), "HANDOFF_READY_WITH_BOUNDED_RESULTS")
        for malformed_repairs in (1, {}):
            with self.assertRaises(ContractError) as context:
                record_review(reloaded, {}, malformed_repairs)
            self.assertIn("MALFORMED_STATE", {issue.code for issue in context.exception.issues})
        handoff = prepare_handoff(
            reloaded,
            bundle_id="handoff:foundation-l0",
            bundle_type="FOUNDATION_SOURCE_HANDOFF",
            receiving_authority="Foundation L0",
            object_refs=["case:test-r1", "art:source-a", "review:repair"],
            allowed_claims=["source identity and bounded scope only"],
            noncanonical_status="CANDIDATE_NOT_CANONICAL",
            scope="pilot scope",
            prohibited_inference=["does not prove truth, causality, external validity, Owner acceptance or epistemic acceptance"],
            residuals=["independent source-family review remains scoped to this pilot"],
        )
        self.assertEqual(handoff["receiving_authority"], "Foundation L0")
        with self.assertRaises(ContractError) as context:
            prepare_handoff(
                reloaded,
                bundle_id="handoff:malformed",
                bundle_type="FOUNDATION_SOURCE_HANDOFF",
                receiving_authority="Foundation L0",
                object_refs=[[]],
                allowed_claims=["bounded scope only"],
                noncanonical_status="CANDIDATE_NOT_CANONICAL",
                scope="pilot scope",
                prohibited_inference=["does not prove truth, causality, external validity, Owner acceptance or epistemic acceptance"],
                residuals=["malformed ref fixture"],
            )
        self.assertIn("MALFORMED_STATE", {issue.code for issue in context.exception.issues})
        with self.assertRaises(ContractError) as context:
            record_review(
                reloaded,
                ReviewDecision(
                    review_id="review:repair",
                    reviewer_ref="role-h",
                    exact_input_refs=("art:source-a",),
                    independent=True,
                    verdict="ABSTAIN",
                    residuals=("replacement must not overwrite prior decision",),
                    scope_ceiling="pilot scope only",
                ),
            )
        self.assertIn("DUPLICATE_ID", {issue.code for issue in context.exception.issues})
        missing_boundary = copy.deepcopy(handoff)
        missing_boundary["prohibited_inference"] = []
        with self.assertRaises(ContractError):
            from reos_vnext import validate_handoff

            validate_handoff(missing_boundary)
        bad_status = copy.deepcopy(handoff)
        bad_status["noncanonical_status"] = "CANONICAL"
        with self.assertRaises(ContractError):
            from reos_vnext import validate_handoff

            validate_handoff(bad_status)
        contradictory_claim = copy.deepcopy(handoff)
        contradictory_claim["allowed_claims"] = ["truth is established"]
        with self.assertRaises(ContractError) as context:
            from reos_vnext import validate_handoff

            validate_handoff(contradictory_claim)
        self.assertIn("HANDOFF_PROHIBITED_INFERENCE", {issue.code for issue in context.exception.issues})

    def test_cli_init_validate_status(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            summary_path = directory_path / "summary.json"
            case_path = directory_path / "case.json"
            summary_path.write_text(json.dumps(SUMMARY), encoding="utf-8")
            command = [
                sys.executable,
                "-m",
                "reos_vnext",
                "init",
                "--case-id",
                "case:cli",
                "--activation-reason",
                "pilot needs explicit review and handoff",
                "--observed-need",
                "source-family control",
                "--simpler-baseline",
                "ordinary notes",
                "--preregistration-ref",
                PREREG_REF,
                "--preregistration-digest",
                PREREG_DIGEST,
                "--frozen-validation-summary",
                str(summary_path),
                "--stop-condition",
                "bounded scope",
                "--output",
                str(case_path),
            ]
            created = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(created.returncode, 0, created.stderr)
            checked = subprocess.run(
                [sys.executable, "-m", "reos_vnext", "validate", str(case_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            malformed_review_path = directory_path / "malformed-review.json"
            malformed_review_path.write_text("[]", encoding="utf-8")
            malformed_review = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "reos_vnext",
                    "record-review",
                    str(case_path),
                    "--record",
                    str(malformed_review_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(malformed_review.returncode, 2)
            self.assertNotIn("Traceback", malformed_review.stderr)
            duplicate_case_path = directory_path / "duplicate-case.json"
            duplicate_case_path.write_text(
                serialize_case(make_case()).replace('"case_state":"OPEN"', '"case_state":"SUCCESS","case_state":"OPEN"', 1),
                encoding="utf-8",
            )
            with self.assertRaises(ContractError) as context:
                load_case(duplicate_case_path)
            self.assertIn("MALFORMED_STATE", {issue.code for issue in context.exception.issues})
            status = subprocess.run(
                [sys.executable, "-m", "reos_vnext", "status", str(case_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(json.loads(status.stdout)["computed_status"], "OPEN")


if __name__ == "__main__":
    unittest.main()
