# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Instance-level gate for the consolidated R5-A contract-bypass repair.

Each adjudicated case has one stable identity, one concrete non-private input,
one typed evidence object, one expected rejection and executed surface results.
Cases that describe the same object on runtime and JSON Schema surfaces execute
both representations.  Aggregate counts and deterministic generation are never
used as substitutes for a required case result.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator

from . import concept_mapping as CM
from . import embodied_view as EV
from . import fixtures as FX
from . import longitudinal as LG
from . import safety_envelope as SE
from . import tradition_translation as TT
from .evidence import EvidenceObject


TASK_ID = "IGNITION-R5A-CONSOLIDATED-CONTRACT-BYPASS-NARROW-REPAIR-R1-20260726"
REJECTED_CANDIDATE_HEAD = "f33be64b26ef14d14098f42ec947bd93fddd245c"
SCHEMA_DIR = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "architecture"
    / "ignition-r5a-life-integrity-r1"
)

REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS = tuple(
    f"R5A-CR-{index:03d}" for index in range(1, 12)
)


@dataclass(frozen=True)
class ConsolidatedRepairCase:
    case_id: str
    title: str
    handler: str
    primary_surface: str
    expected_outcome: str
    expected_error: str
    concrete_input: dict[str, Any]
    evidence_object: EvidenceObject

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["evidence_object"] = self.evidence_object.as_dict()
        return result


def _case_evidence(case_id: str, surface: str) -> EvidenceObject:
    return EvidenceObject(
        evidence_id=f"EV-{case_id}",
        evidence_class="attack_reproduction",
        provenance=(
            "1111 consolidated exact-head review; synthetic repository fixture "
            "replayed by the bounded R5-A repair"
        ),
        reviewer_role="H",
        claim_ceiling="software_behavior_reproduced",
        supports=(f"attack:{case_id}", f"surface:{surface}"),
        observed_facts=("exact concrete fixture executed by the machine gate",),
        unresolved_risks=("independent exact-head acceptance remains external",),
    )


_TRANSLATED_COMPLETE = {
    "source_provenance": "synthetic-source",
    "source_language": "zh",
    "translation_status": "literal",
    "attribution_status": "reported",
    "claim_class": "PHENOMENOLOGICAL_REPORT",
    "literal_reference": "synthetic-ref-001",
    "interpretation_layer": "SOURCE_LITERAL",
    "evidence_grade": "SOFTWARE_CONTRACT_ONLY",
    "mechanism_status": "EMPIRICALLY_SUPPORTED_MECHANISM",
    "applicability_scope": "synthetic software fixture only",
    "rights_boundary": "synthetic public fixture",
    "confidence": 0.5,
    "unknowns": ["real-world validity"],
    "prohibited_upgrades": [
        "PHENOMENOLOGICAL_REPORT->EMPIRICALLY_SUPPORTED_MECHANISM"
    ],
    "revision_history": [],
}

_TRANSLATED_INCOMPLETE = {
    **_TRANSLATED_COMPLETE,
    "source_provenance": "",
    "source_language": "",
    "translation_status": "",
    "attribution_status": "",
    "claim_class": "HISTORICAL_SOURCE",
    "mechanism_status": "NOT_ASSERTED",
    "confidence": 2.5,
}

_RELATION_INPUT = {
    "relation_type": "   ",
    "source_view": "PhysiologicalView",
    "target_view": "BehavioralView",
    "asserts_causality": False,
    "notes": "synthetic whitespace type",
}

_SAFETY_OVERRIDES = {
    "long_term_followup_plan": "stop taking your medication",
    "raw_text": "discuss options with a licensed clinician",
}

_SAFETY_TYPE_CONFUSION = {
    "informed_consent_required": 1,
    "unknowns": {"unknown": "long-term data"},
}

_CONCEPT_INVALID = {
    "concept_id": "synthetic-concept",
    "source_state": "UNMAPPED",
    "current_state": "BOGUS_STATE",
    "transitions": [],
    "provenance": "synthetic-fixture",
    "current_interpretation": "",
    "superseded_interpretations": [],
}

_UNKNOWN_LIFE_ASSESSMENT = {
    "proposal": {
        "intended_benefit": "UNKNOWN",
        "affected_views": ["PhysiologicalView"],
        "short_term_effects": "UNKNOWN",
        "long_term_effects": "UNKNOWN",
        "externalities_tradeoffs": "UNKNOWN",
        "uncertainty": "UNKNOWN",
        "consent_autonomy_status": "UNKNOWN",
        "reversibility": "UNKNOWN",
        "stop_conditions": "UNKNOWN",
        "referral_boundary": "UNKNOWN",
        "residual_harm_after_rollback": "UNKNOWN",
    }
}

_INTEGER_LONGITUDINAL = {
    key: 1
    for key in (
        "contract_id",
        "observation_time",
        "decision_time",
        "intervention_time",
        "review_time",
        "consent_autonomy_version",
        "evidence_chain_id",
        "reopen_trigger",
        "revision_status",
        "retirement_state",
        "revision_authority_role",
        "evidence_threshold",
        "events",
    )
}


_CASE_SPECS = (
    ("R5A-CR-001", "direct forbidden translated-claim construction", "translated_forbidden", "tradition_translation.direct_constructor", "ForbiddenClaimUpgradeError", _TRANSLATED_COMPLETE),
    ("R5A-CR-002", "incomplete and overconfident translated claim", "translated_incomplete", "tradition_translation.required_fields", "TranslatedClaimContractError", _TRANSLATED_INCOMPLETE),
    ("R5A-CR-003", "view crosses the agent provenance boundary", "view_boundary", "embodied_view.provenance_boundary", "EmbodiedViewError", {"agent_provenance_boundary": "boundary-A", "view_provenance_boundary": "boundary-B"}),
    ("R5A-CR-004", "whitespace-only cross-view relation type", "relation_whitespace", "embodied_view.cross_view_relation", "EmbodiedViewError", _RELATION_INPUT),
    ("R5A-CR-005", "stop-treatment language hidden in a structured field", "safety_structured_text", "safety_envelope.structured_text", "StopTreatmentRecommendationError", _SAFETY_OVERRIDES),
    ("R5A-CR-006", "boolean and array runtime type confusion", "safety_type_confusion", "safety_envelope.runtime_types", "SafetyViolationError", _SAFETY_TYPE_CONFUSION),
    ("R5A-CR-007", "equal longitudinal observation and decision times", "longitudinal_equal_times", "longitudinal.distinct_times", "LongitudinalContractError", {"observation_time": "2026-07-01T00:00:00+00:00", "decision_time": "2026-07-01T00:00:00+00:00"}),
    ("R5A-CR-008", "caller-supplied concept state outside the closed set", "concept_current_state", "concept_mapping.current_state", "UnknownConceptStateError", _CONCEPT_INVALID),
    ("R5A-CR-009", "life-integrity schema accepts UNKNOWN disclosures without evidence", "schema_life_integrity", "schema.life_integrity_assessment", "ValidationError", _UNKNOWN_LIFE_ASSESSMENT),
    ("R5A-CR-010", "translated-claim schema accepts only two fields", "schema_translated_claim", "schema.translated_claim", "ValidationError", {"source_provenance": "synthetic", "claim_class": "HISTORICAL_SOURCE"}),
    ("R5A-CR-011", "longitudinal schema accepts integers for all required fields", "schema_longitudinal", "schema.longitudinal_feedback", "ValidationError", _INTEGER_LONGITUDINAL),
)


CONSOLIDATED_REPAIR_CASES = tuple(
    ConsolidatedRepairCase(
        case_id=case_id,
        title=title,
        handler=handler,
        primary_surface=surface,
        expected_outcome="REJECTED",
        expected_error=error,
        concrete_input=dict(concrete_input),
        evidence_object=_case_evidence(case_id, surface),
    )
    for case_id, title, handler, surface, error, concrete_input in _CASE_SPECS
)


def _schema_documents_from_disk() -> dict[str, dict[str, Any]]:
    names = (
        "life-integrity-assessment-schema.json",
        "embodied-view-projection-schema.json",
        "translated-claim-schema.json",
        "practice-safety-envelope-schema.json",
        "concept-mapping-transition-schema.json",
        "longitudinal-feedback-schema.json",
    )
    return {
        name: json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
        for name in names
    }


def _as_json_object(value: object) -> dict[str, Any]:
    return json.loads(json.dumps(asdict(value), ensure_ascii=False))


def _probe(
    surface: str,
    callable_: Callable[[], None],
    expected_errors: tuple[str, ...],
) -> dict[str, Any]:
    try:
        callable_()
    except Exception as exc:
        observed_error = type(exc).__name__
        return {
            "surface": surface,
            "expected_outcome": "REJECTED",
            "expected_errors": list(expected_errors),
            "observed_outcome": "REJECTED",
            "observed_error": observed_error,
            "detail": str(exc),
            "passed": observed_error in expected_errors,
        }
    return {
        "surface": surface,
        "expected_outcome": "REJECTED",
        "expected_errors": list(expected_errors),
        "observed_outcome": "ACCEPTED",
        "observed_error": None,
        "detail": "completed without exception",
        "passed": False,
    }


def _schema_probe(
    schemas: Mapping[str, dict[str, Any]],
    schema_name: str,
    instance: dict[str, Any],
) -> None:
    schema = schemas[schema_name]
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(instance)


def _surface_probes(
    case: ConsolidatedRepairCase,
    schemas: Mapping[str, dict[str, Any]],
) -> list[tuple[str, Callable[[], None], tuple[str, ...]]]:
    data = case.concrete_input
    if case.handler in {"translated_forbidden", "translated_incomplete"}:
        return [
            (
                "runtime.TranslatedClaim",
                lambda: TT.TranslatedClaim(**data),
                (case.expected_error,),
            ),
            (
                "schema.translated-claim",
                lambda: _schema_probe(
                    schemas, "translated-claim-schema.json", data
                ),
                ("ValidationError",),
            ),
        ]
    if case.handler == "view_boundary":
        def mismatched_view() -> None:
            agent = EV.EmbodiedAgent(
                "synthetic-subject",
                provenance_boundary=data["agent_provenance_boundary"],
            )
            agent.add_view(
                EV.EmbodiedViewProjection(
                    view_id="PhysiologicalView",
                    subject_identity="synthetic-subject",
                    observations=["synthetic observation"],
                    confidence=0.5,
                    time_scope="2026-07",
                    unknown=False,
                    provenance="synthetic-view",
                    provenance_boundary=data["view_provenance_boundary"],
                )
            )
        return [("runtime.EmbodiedAgent.add_view", mismatched_view, (case.expected_error,))]
    if case.handler == "relation_whitespace":
        return [
            (
                "runtime.CrossViewRelation",
                lambda: EV.CrossViewRelation(**data),
                (case.expected_error,),
            ),
            (
                "schema.CrossViewRelation",
                lambda: Draft202012Validator(
                    schemas["embodied-view-projection-schema.json"]["$defs"][
                        "CrossViewRelation"
                    ]
                ).validate(data),
                ("ValidationError",),
            ),
        ]
    if case.handler == "safety_structured_text":
        env = replace(FX.sample_safety_envelope(), **data)
        instance = _as_json_object(env)
        return [
            (
                "runtime.validate_envelope",
                lambda: SE.validate_envelope(env),
                (case.expected_error,),
            ),
            (
                "schema.practice-safety-envelope",
                lambda: _schema_probe(
                    schemas, "practice-safety-envelope-schema.json", instance
                ),
                ("ValidationError",),
            ),
        ]
    if case.handler == "safety_type_confusion":
        combined = replace(FX.sample_safety_envelope(), **data)
        consent_only = replace(FX.sample_safety_envelope(), informed_consent_required=1)
        unknowns_only = replace(
            FX.sample_safety_envelope(), unknowns={"unknown": "long-term data"}
        )
        return [
            (
                "runtime.validate_envelope.combined",
                lambda: SE.validate_envelope(combined),
                (case.expected_error,),
            ),
            (
                "runtime.validate_envelope.integer-consent",
                lambda: SE.validate_envelope(consent_only),
                (case.expected_error,),
            ),
            (
                "runtime.validate_envelope.mapping-unknowns",
                lambda: SE.validate_envelope(unknowns_only),
                (case.expected_error,),
            ),
            (
                "schema.practice-safety-envelope",
                lambda: _schema_probe(
                    schemas,
                    "practice-safety-envelope-schema.json",
                    _as_json_object(combined),
                ),
                ("ValidationError",),
            ),
        ]
    if case.handler == "longitudinal_equal_times":
        contract = replace(FX.sample_longitudinal_contract(), **data)
        return [
            (
                "runtime.validate_longitudinal_contract",
                lambda: LG.validate_longitudinal_contract(contract),
                (case.expected_error,),
            )
        ]
    if case.handler == "concept_current_state":
        return [
            (
                "runtime.ConceptMapping",
                lambda: CM.ConceptMapping(
                    concept_id=data["concept_id"],
                    source_state=data["source_state"],
                    current_state=data["current_state"],
                ),
                (case.expected_error,),
            ),
            (
                "schema.concept-mapping-transition",
                lambda: _schema_probe(
                    schemas, "concept-mapping-transition-schema.json", data
                ),
                ("ValidationError",),
            ),
        ]
    schema_handlers = {
        "schema_life_integrity": "life-integrity-assessment-schema.json",
        "schema_translated_claim": "translated-claim-schema.json",
        "schema_longitudinal": "longitudinal-feedback-schema.json",
    }
    if case.handler in schema_handlers:
        schema_name = schema_handlers[case.handler]
        return [
            (
                f"schema.{schema_name}",
                lambda: _schema_probe(schemas, schema_name, data),
                (case.expected_error,),
            )
        ]
    raise AssertionError(f"unknown consolidated repair handler: {case.handler}")


def run_case(
    case: ConsolidatedRepairCase,
    *,
    schema_documents: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    schemas = schema_documents or _schema_documents_from_disk()
    surface_results = [
        _probe(surface, callable_, expected_errors)
        for surface, callable_, expected_errors in _surface_probes(case, schemas)
    ]
    passed = bool(surface_results) and all(item["passed"] for item in surface_results)
    return {
        "case_id": case.case_id,
        "title": case.title,
        "primary_surface": case.primary_surface,
        "expected_outcome": case.expected_outcome,
        "expected_error": case.expected_error,
        "observed_outcome": "REJECTED" if passed else "BYPASS_OR_WRONG_REJECTION",
        "evidence_id": case.evidence_object.evidence_id,
        "surface_results": surface_results,
        "passed": passed,
    }


def run_consolidated_repair_gate(
    *,
    cases: tuple[ConsolidatedRepairCase, ...] | None = None,
    required_ids: tuple[str, ...] | None = None,
    schema_documents: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    active_cases = CONSOLIDATED_REPAIR_CASES if cases is None else cases
    active_required_ids = (
        REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS
        if required_ids is None
        else required_ids
    )
    ids = tuple(case.case_id for case in active_cases)
    evidence_ids = tuple(case.evidence_object.evidence_id for case in active_cases)
    identity_errors: list[str] = []
    if ids != active_required_ids:
        identity_errors.append("case ids do not equal the exact required-id tuple")
    if len(set(ids)) != len(ids):
        identity_errors.append("duplicate case id")
    if len(set(evidence_ids)) != len(evidence_ids):
        identity_errors.append("duplicate evidence id")
    for case in active_cases:
        if not case.evidence_object.supports_all({f"attack:{case.case_id}"}):
            identity_errors.append(f"evidence object does not bind {case.case_id}")

    results = [
        run_case(case, schema_documents=schema_documents) for case in active_cases
    ]
    executed_ids = [result["case_id"] for result in results]
    if executed_ids != list(active_required_ids):
        identity_errors.append("executed ids do not equal the exact required-id tuple")
    failed_case_ids = [result["case_id"] for result in results if not result["passed"]]
    return {
        "schema": "r5a/consolidated-contract-bypass-repair-acceptance/v1",
        "task_id": TASK_ID,
        "rejected_candidate_head": REJECTED_CANDIDATE_HEAD,
        "claim_ceiling": "software_behavior_reproduced",
        "required_case_ids": list(active_required_ids),
        "executed_case_ids": executed_ids,
        "identity_errors": identity_errors,
        "results": results,
        "failed_case_ids": failed_case_ids,
        "status": "PASS" if not identity_errors and not failed_case_ids else "BLOCKED",
        "count_is_not_acceptance": True,
        "independent_acceptance_claimed": False,
    }


def consolidated_repair_case_registry() -> dict[str, Any]:
    return {
        "schema": "r5a/consolidated-contract-bypass-repair-case-registry/v1",
        "task_id": TASK_ID,
        "rejected_candidate_head": REJECTED_CANDIDATE_HEAD,
        "required_case_ids": list(REQUIRED_CONSOLIDATED_REPAIR_CASE_IDS),
        "cases": [case.as_dict() for case in CONSOLIDATED_REPAIR_CASES],
        "acceptance_rule": (
            "Every exact id must retain one concrete input, one typed evidence "
            "object, one expected rejection and executed PASS results on every "
            "bound runtime/schema surface. Aggregate counts, green CI and "
            "deterministic generation cannot substitute for an instance."
        ),
    }
