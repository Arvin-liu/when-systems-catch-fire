# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Instance-complete acceptance gate for the R5-A narrow repair.

Every required case has a stable id, concrete input, one evidence object, an
expected outcome, and an executable handler.  A total count is never used as a
substitute for the required id set or for executing each instance.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable

from . import concept_mapping as CM
from . import embodied_view as EV
from . import fixtures as FX
from . import life_integrity as LI
from . import longitudinal as LG
from . import registries as R
from . import safety_envelope as SE
from . import tradition_translation as TT
from .evidence import EvidenceObject


REQUIRED_ATTACK_CASE_IDS = (
    "R5A-NR-001-CANDIDATE-HEAD-IDENTITY",
    "R5A-NR-002-FUTURE-PROTOCOL-SUPREMACY",
    "R5A-NR-003-AFFECTED-VIEWS-TYPE-CONFUSION",
    "R5A-NR-004-WHITESPACE-DISCLOSURE",
    "R5A-NR-005-ASSUMED-CONSENT",
    "R5A-NR-006-IRREVERSIBLE-LOCAL-OPTIMIZATION",
    "R5A-NR-007-COMPLETE-BUT-HARMFUL-PROPOSAL",
    "R5A-NR-008-UNKNOWN-AFFECTED-VIEW",
    "R5A-NR-009-MISSING-RISK-EVIDENCE-OBJECT",
    "R5A-NR-010-WHOLE-PERSON-COMPLETE",
    "R5A-NR-011-MULTIVIEW-WITHOUT-EVIDENCE-OBJECT",
    "R5A-NR-012-OBSERVED-VIEW-WITHOUT-PROVENANCE",
    "R5A-NR-013-SCIENTIFICALLY-PROVEN-ALIAS",
    "R5A-NR-014-UNKNOWN-TRANSLATION-TARGET",
    "R5A-NR-015-WRONG-TRANSITION-EVIDENCE-CLASS",
    "R5A-NR-016-WRONG-TRANSITION-REVIEWER",
    "R5A-NR-017-WRONG-TRANSITION-REVERSIBILITY",
    "R5A-NR-018-SUPERSEDED-INTERPRETATION-PRESERVED",
    "R5A-NR-019-CHINESE-STOP-TREATMENT",
    "R5A-NR-020-PARAPHRASED-THERAPY-REPLACEMENT",
    "R5A-NR-021-HIGH-COERCION-RISK",
    "R5A-NR-022-WHITESPACE-SAFETY-FIELD",
    "R5A-NR-023-LONGITUDINAL-TIME-ORDER",
    "R5A-NR-024-DELAYED-HARM-WITHOUT-REOPEN",
    "R5A-NR-025-DELAYED-HARM-REOPENED",
    "R5A-NR-026-ACTIVATED-ATTRIBUTE-IMMUTABLE",
    "R5A-NR-027-PACKAGE-IMPORT-BOUNDARY",
    "R5A-NR-028-EXPLICIT-CASE-ID-GATE",
    "R5A-NR-029-EXACT-CHARTER-HIERARCHY",
    "R5A-NR-030-EVIDENCE-OBJECT-ROLE-MISMATCH",
)


@dataclass(frozen=True)
class AttackCase:
    case_id: str
    finding: str
    title: str
    handler: str
    expected_outcome: str
    expected_error: str | None
    concrete_input: dict[str, Any]
    evidence_object: EvidenceObject

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["evidence_object"] = self.evidence_object.as_dict()
        return result


def _case_evidence(case_id: str, finding: str) -> EvidenceObject:
    return EvidenceObject(
        evidence_id=f"EV-{case_id}",
        evidence_class="attack_reproduction",
        provenance=f"1111 night queue {finding}; reproduced in R5-A narrow repair",
        reviewer_role="H",
        claim_ceiling="software_behavior_reproduced",
        supports=(f"attack:{case_id}",),
        observed_facts=("concrete repository fixture executed by the machine gate",),
    )


_CASE_SPECS = (
    ("R5A-NR-001-CANDIDATE-HEAD-IDENTITY", "TASK-01", "candidate frozen head names the exact R5-A head", "candidate_head", "ACCEPTED", None, {"expected_head": "0e9d1e5823b41b7e9375e5f634388371b9b024ac"}),
    ("R5A-NR-002-FUTURE-PROTOCOL-SUPREMACY", "TASK-02", "future protocol claims supremacy", "future_supremacy", "REJECTED", "CharterHierarchyError", {"protocol_id": "synthetic-domain-pack", "parent": "LifeIntegrityGateCandidate", "claims_supremacy": True}),
    ("R5A-NR-003-AFFECTED-VIEWS-TYPE-CONFUSION", "TASK-03", "affected_views is a string", "local_type_confusion", "REJECTED", "LocalOptimizationIncompleteError", {"affected_views": "PhysiologicalView"}),
    ("R5A-NR-004-WHITESPACE-DISCLOSURE", "TASK-03", "whitespace-only intended benefit", "local_whitespace", "REJECTED", "LocalOptimizationIncompleteError", {"intended_benefit": "   "}),
    ("R5A-NR-005-ASSUMED-CONSENT", "TASK-03", "assumed consent in complete proposal", "local_assumed_consent", "REJECTED", "LocalOptimizationSafetyError", {"consent_autonomy_status": "ASSUMED"}),
    ("R5A-NR-006-IRREVERSIBLE-LOCAL-OPTIMIZATION", "TASK-03", "irreversible local optimization", "local_irreversible", "REJECTED", "LocalOptimizationSafetyError", {"reversibility": "IRREVERSIBLE"}),
    ("R5A-NR-007-COMPLETE-BUT-HARMFUL-PROPOSAL", "TASK-03", "complete proposal hides catastrophic residual harm and never-stop condition", "local_harmful", "REJECTED", "LocalOptimizationSafetyError", {"stop_conditions": "never stop", "residual_harm_after_rollback": "catastrophic residual harm"}),
    ("R5A-NR-008-UNKNOWN-AFFECTED-VIEW", "TASK-03", "proposal names a view outside the closed set", "local_unknown_view", "REJECTED", "LocalOptimizationIncompleteError", {"affected_views": ["SyntheticTotalScore"]}),
    ("R5A-NR-009-MISSING-RISK-EVIDENCE-OBJECT", "TASK-03", "complete proposal omits typed risk evidence", "local_missing_evidence", "REJECTED", "LocalOptimizationIncompleteError", {"evidence_objects": []}),
    ("R5A-NR-010-WHOLE-PERSON-COMPLETE", "TASK-04", "seven views assert WHOLE_PERSON_COMPLETE", "whole_person_complete", "REJECTED", "WholePersonClaimError", {"claim_scope": "WHOLE_PERSON_COMPLETE"}),
    ("R5A-NR-011-MULTIVIEW-WITHOUT-EVIDENCE-OBJECT", "TASK-04", "bounded seven-view assessment omits evidence object", "multiview_missing_evidence", "REJECTED", "WholePersonClaimError", {"evidence_objects": []}),
    ("R5A-NR-012-OBSERVED-VIEW-WITHOUT-PROVENANCE", "TASK-04", "observed view omits provenance", "view_missing_provenance", "REJECTED", "EmbodiedViewError", {"view_id": "MeaningView", "unknown": False, "observations": ["synthetic observation"], "time_scope": "2026-07", "provenance": ""}),
    ("R5A-NR-013-SCIENTIFICALLY-PROVEN-ALIAS", "TASK-05", "phenomenological report uses SCIENTIFICALLY_PROVEN alias", "tradition_alias", "REJECTED", "ForbiddenClaimUpgradeError", {"claim_class": "PHENOMENOLOGICAL_REPORT", "mechanism_status": "SCIENTIFICALLY_PROVEN"}),
    ("R5A-NR-014-UNKNOWN-TRANSLATION-TARGET", "TASK-05", "translation uses an unregistered mechanism label", "tradition_unknown", "REJECTED", "UnknownTranslationStatusError", {"claim_class": "HISTORICAL_SOURCE", "mechanism_status": "QUANTUM_CERTAINTY"}),
    ("R5A-NR-015-WRONG-TRANSITION-EVIDENCE-CLASS", "TASK-06", "concept transition supplies wrong evidence class", "concept_wrong_evidence", "REJECTED", "TransitionEvidenceError", {"provided": "source_identification", "required": "phenomenology_report"}),
    ("R5A-NR-016-WRONG-TRANSITION-REVIEWER", "TASK-06", "concept transition supplies wrong reviewer role", "concept_wrong_reviewer", "REJECTED", "TransitionEvidenceError", {"provided": "A", "required": "D"}),
    ("R5A-NR-017-WRONG-TRANSITION-REVERSIBILITY", "TASK-06", "concept transition contradicts reversibility metadata", "concept_wrong_reversibility", "REJECTED", "TransitionEvidenceError", {"provided": False, "required": True}),
    ("R5A-NR-018-SUPERSEDED-INTERPRETATION-PRESERVED", "TASK-06", "concept transition preserves the prior interpretation", "concept_preserve_history", "ACCEPTED", None, {"prior": "synthetic prior interpretation", "next": "synthetic revised interpretation"}),
    ("R5A-NR-019-CHINESE-STOP-TREATMENT", "TASK-07", "Chinese stop-prescription substitution", "safety_chinese", "REJECTED", "StopTreatmentRecommendationError", {"raw_text": "停用你的处方药，改用这个方案代替治疗"}),
    ("R5A-NR-020-PARAPHRASED-THERAPY-REPLACEMENT", "TASK-07", "paraphrased therapy replacement", "safety_paraphrase", "REJECTED", "StopTreatmentRecommendationError", {"raw_text": "this replaces your therapy"}),
    ("R5A-NR-021-HIGH-COERCION-RISK", "TASK-07", "structured high coercion risk", "safety_high_coercion", "REJECTED", "SafetyViolationError", {"dependency_coercion_risk": "HIGH"}),
    ("R5A-NR-022-WHITESPACE-SAFETY-FIELD", "TASK-07", "whitespace-only contraindications", "safety_whitespace", "REJECTED", "EnvelopeIncompleteError", {"contraindications": "   "}),
    ("R5A-NR-023-LONGITUDINAL-TIME-ORDER", "TASK-08", "review precedes intervention", "longitudinal_time_order", "REJECTED", "LongitudinalContractError", {"review_time": "2026-07-02T00:00:00+00:00", "intervention_time": "2026-07-03T00:00:00+00:00"}),
    ("R5A-NR-024-DELAYED-HARM-WITHOUT-REOPEN", "TASK-08", "delayed harm leaves candidate active", "longitudinal_no_reopen", "REJECTED", "LongitudinalContractError", {"reopen_trigger": "NONE", "revision_status": "ACTIVE"}),
    ("R5A-NR-025-DELAYED-HARM-REOPENED", "TASK-08", "delayed harm explicitly reopens the candidate", "longitudinal_reopened", "ACCEPTED", None, {"reopen_trigger": "DELAYED_ADVERSE_OUTCOME", "revision_status": "REOPENED"}),
    ("R5A-NR-026-ACTIVATED-ATTRIBUTE-IMMUTABLE", "TASK-09", "caller attempts to activate the candidate gate", "activated_immutable", "REJECTED", "AttributeError", {"activated": True}),
    ("R5A-NR-027-PACKAGE-IMPORT-BOUNDARY", "TASK-09", "candidate package has no production-runtime imports", "import_boundary", "ACCEPTED", None, {"forbidden_roots": ["adaptive_relational_runtime", "function_os", "tools.ignition_runtime"]}),
    ("R5A-NR-028-EXPLICIT-CASE-ID-GATE", "TASK-19", "machine gate binds the exact explicit case id set", "explicit_ids", "ACCEPTED", None, {"required_ids": list(REQUIRED_ATTACK_CASE_IDS)}),
    ("R5A-NR-029-EXACT-CHARTER-HIERARCHY", "TASK-02", "exact closed charter hierarchy remains valid", "exact_hierarchy", "ACCEPTED", None, {"hierarchy": list(R.CHARTER_HIERARCHY)}),
    ("R5A-NR-030-EVIDENCE-OBJECT-ROLE-MISMATCH", "TASK-06", "transition evidence object role differs from transition reviewer", "concept_evidence_role_mismatch", "REJECTED", "TransitionEvidenceError", {"transition_role": "D", "evidence_role": "F"}),
)


ATTACK_CASES = tuple(
    AttackCase(
        case_id=spec[0],
        finding=spec[1],
        title=spec[2],
        handler=spec[3],
        expected_outcome=spec[4],
        expected_error=spec[5],
        concrete_input=spec[6],
        evidence_object=_case_evidence(spec[0], spec[1]),
    )
    for spec in _CASE_SPECS
)


def _transition_evidence(
    evidence_class: str = "phenomenology_report", reviewer_role: str = "D"
) -> EvidenceObject:
    return EvidenceObject(
        evidence_id=f"EV-TRANSITION-{evidence_class}-{reviewer_role}",
        evidence_class=evidence_class,
        provenance="synthetic attack fixture",
        reviewer_role=reviewer_role,
        supports=("transition:SYMBOLIC_DESCRIPTION->PHENOMENOLOGICAL_CANDIDATE",),
        observed_facts=("synthetic transition evidence",),
    )


def _run_handler(case: AttackCase) -> None:
    handler = case.handler
    data = case.concrete_input
    if handler == "candidate_head":
        assert R.CANDIDATE_FROZEN_HEAD == data["expected_head"]
    elif handler == "future_supremacy":
        R.validate_future_protocol_declaration(**data)
    elif handler.startswith("local_"):
        proposal = FX.sample_local_optimization_proposal()
        if handler == "local_type_confusion":
            proposal.affected_views = data["affected_views"]  # type: ignore[assignment]
        elif handler == "local_whitespace":
            proposal.intended_benefit = data["intended_benefit"]
        elif handler == "local_assumed_consent":
            proposal.consent_autonomy_status = data["consent_autonomy_status"]
        elif handler == "local_irreversible":
            proposal.reversibility = data["reversibility"]
        elif handler == "local_harmful":
            proposal.stop_conditions = data["stop_conditions"]
            proposal.residual_harm_after_rollback = data["residual_harm_after_rollback"]
        elif handler == "local_unknown_view":
            proposal.affected_views = data["affected_views"]
        elif handler == "local_missing_evidence":
            proposal.evidence_objects = []
        LI.LifeIntegrityGate().validate_proposal(proposal)
    elif handler in {"whole_person_complete", "multiview_missing_evidence"}:
        agent = FX.sample_embodied_agent()
        evidence = [FX.sample_multi_view_evidence()]
        if handler == "multiview_missing_evidence":
            evidence = []
        agent.require_whole_person_disclosure(
            claimed_views=list(R.EMBODIED_VIEW_IDS),
            missing_disclosed=True,
            contradictions_surfaced=True,
            evidence_objects=evidence,
            claim_scope=data.get("claim_scope", "BOUNDED_MULTI_VIEW_ASSESSMENT"),
        )
    elif handler == "view_missing_provenance":
        EV.EmbodiedViewProjection(subject_identity="synthetic-subject", confidence=0.5, **data)
    elif handler in {"tradition_alias", "tradition_unknown"}:
        TT.translate_claim(source_provenance="synthetic-source", **data)
    elif handler.startswith("concept_"):
        mapping = CM.ConceptMapping(
            concept_id="synthetic-concept",
            source_state="SYMBOLIC_DESCRIPTION",
            current_interpretation=data.get("prior", "synthetic prior interpretation"),
        )
        evidence_class = "phenomenology_report"
        reviewer_role = "D"
        reversibility = True
        evidence_role = data.get("evidence_role", reviewer_role)
        if handler == "concept_wrong_evidence":
            evidence_class = data["provided"]
        elif handler == "concept_wrong_reviewer":
            reviewer_role = data["provided"]
            evidence_role = reviewer_role
        elif handler == "concept_wrong_reversibility":
            reversibility = data["provided"]
        elif handler == "concept_evidence_role_mismatch":
            reviewer_role = data["transition_role"]
        evidence = _transition_evidence(evidence_class, evidence_role)
        CM.apply_transition(
            mapping,
            "PHENOMENOLOGICAL_CANDIDATE",
            evidence_class,
            reviewer_role,
            "synthetic executed attack",
            reversibility,
            evidence_object=evidence,
            new_interpretation=data.get("next", "synthetic revised interpretation"),
        )
        if handler == "concept_preserve_history":
            assert mapping.superseded_interpretations == [
                {
                    "interpretation": data["prior"],
                    "superseded_by_evidence_id": evidence.evidence_id,
                    "transition": "SYMBOLIC_DESCRIPTION->PHENOMENOLOGICAL_CANDIDATE",
                }
            ]
    elif handler.startswith("safety_"):
        env = FX.sample_safety_envelope()
        for key, value in data.items():
            setattr(env, key, value)
        SE.validate_envelope(env)
    elif handler.startswith("longitudinal_"):
        contract = FX.sample_longitudinal_contract(
            reopen_delayed_harm=handler != "longitudinal_no_reopen"
        )
        if handler == "longitudinal_time_order":
            contract = replace(contract, **data)
        LG.validate_longitudinal_contract(contract)
    elif handler == "activated_immutable":
        setattr(LI.LifeIntegrityGate(), "activated", data["activated"])
    elif handler == "import_boundary":
        package_root = Path(__file__).resolve().parent
        forbidden = tuple(data["forbidden_roots"])
        for path in package_root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module]
                assert not any(name.startswith(forbidden) for name in names), (path, names)
    elif handler == "explicit_ids":
        assert tuple(case_item.case_id for case_item in ATTACK_CASES) == REQUIRED_ATTACK_CASE_IDS
    elif handler == "exact_hierarchy":
        R.validate_charter_hierarchy(data["hierarchy"])
    else:
        raise AssertionError(f"unknown attack handler: {handler}")


def run_case(case: AttackCase) -> dict[str, Any]:
    observed_outcome = "ACCEPTED"
    observed_error: str | None = None
    detail = "completed without exception"
    try:
        _run_handler(case)
    except Exception as exc:  # the receipt records the exact fail-closed surface
        observed_outcome = "REJECTED"
        observed_error = type(exc).__name__
        detail = str(exc)
    passed = (
        observed_outcome == case.expected_outcome
        and (case.expected_error is None or observed_error == case.expected_error)
    )
    return {
        "case_id": case.case_id,
        "finding": case.finding,
        "title": case.title,
        "expected_outcome": case.expected_outcome,
        "expected_error": case.expected_error,
        "observed_outcome": observed_outcome,
        "observed_error": observed_error,
        "detail": detail,
        "evidence_id": case.evidence_object.evidence_id,
        "passed": passed,
    }


def run_attack_gate() -> dict[str, Any]:
    ids = tuple(case.case_id for case in ATTACK_CASES)
    evidence_ids = tuple(case.evidence_object.evidence_id for case in ATTACK_CASES)
    identity_errors: list[str] = []
    if ids != REQUIRED_ATTACK_CASE_IDS:
        identity_errors.append("case ids do not equal the explicit required id tuple")
    if len(set(ids)) != len(ids):
        identity_errors.append("duplicate case id")
    if len(set(evidence_ids)) != len(evidence_ids):
        identity_errors.append("duplicate evidence id")
    for case in ATTACK_CASES:
        if not case.evidence_object.supports_all({f"attack:{case.case_id}"}):
            identity_errors.append(f"evidence object does not bind {case.case_id}")

    results = [run_case(case) for case in ATTACK_CASES]
    failed_case_ids = [result["case_id"] for result in results if not result["passed"]]
    return {
        "schema": "r5a/narrow-repair-attack-acceptance/v1",
        "adjudication": "NIGHT_QUEUE_R1_PARTIAL_SALVAGE_NOT_ACCEPTED",
        "claim_ceiling": "software_behavior_reproduced",
        "required_case_ids": list(REQUIRED_ATTACK_CASE_IDS),
        "identity_errors": identity_errors,
        "results": results,
        "failed_case_ids": failed_case_ids,
        "status": "PASS" if not identity_errors and not failed_case_ids else "BLOCKED",
        "count_is_not_acceptance": True,
    }


def attack_case_registry() -> dict[str, Any]:
    return {
        "schema": "r5a/narrow-repair-attack-case-registry/v1",
        "adjudication": "NIGHT_QUEUE_R1_PARTIAL_SALVAGE_NOT_ACCEPTED",
        "required_case_ids": list(REQUIRED_ATTACK_CASE_IDS),
        "cases": [case.as_dict() for case in ATTACK_CASES],
        "acceptance_rule": (
            "Every explicit case id must have one concrete input, one evidence object, "
            "one executed result, and PASS. A count cannot substitute for an instance."
        ),
    }
