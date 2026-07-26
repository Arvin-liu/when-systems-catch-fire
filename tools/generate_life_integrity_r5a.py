# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Deterministic generator for the R5-A Life Integrity Charter Candidate artifacts.

Produces the public candidate registries and schemas under
``docs/architecture/ignition-r5a-life-integrity-r1/`` from the versioned R5-A
package ``life_integrity_r5a``. Running it twice yields byte-identical output
(deterministic). It never reads or emits private corpus content.

NOTE: this generator lives at the top level of ``tools/`` (NOT under
``tools/adaptive_relational_runtime``) because it legitimately imports from the
top-level ``life_integrity_r5a`` package and writes files; the ARR
anti-second-executor static gate only scans ``tools/adaptive_relational_runtime``.
"""

from __future__ import annotations

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from life_integrity_r5a import (  # noqa: E402
    annex,
    concept_mapping,
    consolidated_repair_gate,
    embodied_view,
    evidence,
    life_integrity,
    manifest,
    non_impact,
    registries,
    safety_envelope,
    tradition_translation,
    longitudinal,
    attack_gate,
)

OUT_DIR = os.path.join(REPO_ROOT, "docs", "architecture", "ignition-r5a-life-integrity-r1")

GENERATED_BY = "tools/generate_life_integrity_r5a.py"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


def _nonblank_string_schema(*, reject_unknown: bool = False) -> dict:
    schema: dict[str, object] = {
        "type": "string",
        "minLength": 1,
        "pattern": r".*\S.*",
    }
    if reject_unknown:
        schema["not"] = {"enum": ["", "UNKNOWN", "NOT_OBSERVED"]}
    return schema


def _evidence_object_schema(*, evidence_class: str | None = None) -> dict:
    evidence_class_schema: dict[str, object]
    if evidence_class is None:
        evidence_class_schema = {"type": "string", "minLength": 1}
    else:
        evidence_class_schema = {"const": evidence_class}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "evidence_id": _nonblank_string_schema(),
            "evidence_class": evidence_class_schema,
            "provenance": _nonblank_string_schema(),
            "reviewer_role": {"enum": list(evidence.REVIEWER_ROLE_IDS)},
            "claim_ceiling": {"enum": list(evidence.CLAIM_CEILING_IDS)},
            "supports": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": _nonblank_string_schema(),
            },
            "observed_facts": {
                "type": "array",
                "items": _nonblank_string_schema(),
            },
            "unresolved_risks": {
                "type": "array",
                "items": _nonblank_string_schema(),
            },
        },
        "required": [
            "evidence_id",
            "evidence_class",
            "provenance",
            "reviewer_role",
            "claim_ceiling",
            "supports",
            "observed_facts",
            "unresolved_risks",
        ],
    }


def _meta() -> dict:
    return {
        "task_id": registries.TASK_ID,
        "repair_task_id": consolidated_repair_gate.TASK_ID,
        "control_commit": registries.CONTROL_COMMIT,
        "formal_predecessor": registries.FORMAL_PREDECESSOR,
        "candidate_frozen_head": registries.CANDIDATE_FROZEN_HEAD,
        "schema_version": registries.SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "activation_status": "CANDIDATE_ONLY",
        "human_intervention_enabled": False,
        "medical_claims_authorized": False,
        "modern_wuzhen_pack_started": False,
        "domain_pack_federation_started": False,
        "external_acceptance_claimed": False,
        "supreme_charter": registries.SUPREME_CHARTER,
    }


def _write(name: str, obj: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, sort_keys=True, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


# ---------------------------------------------------------------------------
# 1. Candidate charter manifest
# ---------------------------------------------------------------------------
def _candidate_charter_manifest() -> dict:
    m = dict(manifest.CANDIDATE_MANIFEST)
    return {
        "meta": _meta(),
        "schema": "r5a/candidate-charter-manifest/v1",
        "candidate_manifest": m,
        "annex_principle": annex.USER_AUTHORIZED_PRINCIPLE,
        "annex_principle_not_authorized_as": list(annex.PRINCIPLE_NOT_AUTHORIZED_AS),
        "charter_hierarchy": list(registries.CHARTER_HIERARCHY),
        "annex_beneath_supreme_charter": annex.annex_beneath_supreme_charter(),
        "non_impact": non_impact.build_non_impact_proof(),
        "fail_closed_rules": [
            "activation_status must remain CANDIDATE_ONLY",
            "human_intervention_enabled must remain false",
            "medical_claims_authorized must remain false",
            "modern_wuzhen_pack_started must remain false",
            "domain_pack_federation_started must remain false",
            "external_acceptance_claimed must remain false",
            "Life Community Value Charter remains the supreme node; no competing supreme node may be inserted",
        ],
    }


# ---------------------------------------------------------------------------
# 2. Embodied-view registry (exactly seven views)
# ---------------------------------------------------------------------------
def _embodied_view_registry() -> dict:
    return {
        "meta": _meta(),
        "schema": "r5a/embodied-view-registry/v1",
        "closed_set": list(embodied_view.EMBODIED_VIEW_IDS),
        "view_count": len(embodied_view.EMBODIED_VIEW_IDS),
        "closed_set_complete": embodied_view.embodied_view_closed_set_complete(),
        "same_subject_identity_required": True,
        "missing_views_disposition": "UNKNOWN / NOT_OBSERVED; must not be inferred from other views",
        "cross_view_relations": "typed; must not assert causality",
        "contradictions": "preserved and surfaced; never silently merged",
        "whole_person_claim": "forbidden; single view/score/diagnosis/behavior/self-report may never assert WHOLE_PERSON_COMPLETE",
        "fail_closed_rules": [
            "every view id must be in the closed set of seven",
            "every view must share the agent subject_identity",
            "missing views remain UNKNOWN and are not inferred",
            "a single view may never claim the whole person",
            "cross-view relations must not assert causality",
            "contradictory views are surfaced, not merged",
        ],
    }


# ---------------------------------------------------------------------------
# 3. Tradition claim-class registry (exactly eight) + forbidden upgrades
# ---------------------------------------------------------------------------
def _tradition_claim_class_registry() -> dict:
    forbidden = [
        {"from": a, "to": b, "requires": "separately linked empirical evidence and independent review"}
        for (a, b) in sorted(registries.TRADITION_FORBIDDEN_TRANSITIONS)
    ]
    return {
        "meta": _meta(),
        "schema": "r5a/tradition-claim-class-registry/v1",
        "closed_set": list(tradition_translation.TRADITION_CLAIM_CLASS_IDS),
        "claim_class_count": len(tradition_translation.TRADITION_CLAIM_CLASS_IDS),
        "closed_set_complete": tradition_translation.claim_class_closed_set_complete(),
        "normative_empirical_type_tags": list(registries.NORMATIVE_EMPIRICAL_TYPE_TAGS),
        "forbidden_upgrades": forbidden,
        "fail_closed_rules": [
            "every translated claim must carry a claim class from the closed set of eight",
            "a claim class outside the closed set is rejected",
            "the five forbidden silent upgrades are never permitted without separate empirical evidence and independent review",
            "mechanism_status and interpretation_layer may not silently realize a forbidden upgrade target",
        ],
    }


# ---------------------------------------------------------------------------
# 4. Concept-mapping lifecycle registry (exactly eight states + graph)
# ---------------------------------------------------------------------------
def _concept_mapping_lifecycle_registry() -> dict:
    transitions: dict[str, dict[str, dict[str, object]]] = {}
    for src in registries.CONCEPT_MAPPING_STATE_IDS:
        targets = registries.CONCEPT_MAPPING_TRANSITIONS.get(src, {})
        transitions[src] = {tgt: dict(meta) for tgt, meta in targets.items()}
    return {
        "meta": _meta(),
        "schema": "r5a/concept-mapping-lifecycle-registry/v1",
        "closed_set": list(concept_mapping.CONCEPT_MAPPING_STATE_IDS),
        "state_count": len(concept_mapping.CONCEPT_MAPPING_STATE_IDS),
        "closed_set_complete": concept_mapping.concept_state_closed_set_complete(),
        "direct_jump_to_partially_supported_forbidden": (
            concept_mapping.transition_graph_has_no_direct_jump_to_partially_supported()
        ),
        "contradicted_and_unknown_first_class": True,
        "transitions": transitions,
        "fail_closed_rules": [
            "every state must be in the closed set of eight",
            "UNMAPPED and SYMBOLIC_DESCRIPTION may not jump directly to PARTIALLY_SUPPORTED",
            "every transition requires evidence_class, reviewer_role, reversibility, contradiction_handling, reason and receipt",
            "CONTRADICTED and UNKNOWN remain first-class reachable outcomes; never silently upgraded to PARTIALLY_SUPPORTED",
        ],
    }


# ---------------------------------------------------------------------------
# 5. Life-integrity assessment schema (local-optimization gate)
# ---------------------------------------------------------------------------
def _life_integrity_assessment_schema() -> dict:
    fields = list(life_integrity.LOCAL_OPTIMIZATION_FIELDS)
    evidence_support = {
        "allOf": [
            {"contains": {"const": field_name}}
            for field_name in life_integrity.LOCAL_OPTIMIZATION_FIELDS
        ]
    }
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "meta": _meta(),
        "schema": "r5a/life-integrity-assessment/v1",
        "title": "LifeIntegrityAssessment",
        "type": "object",
        "$defs": {
            "evidence_object": _evidence_object_schema(
                evidence_class="local_optimization_risk_review"
            )
        },
        "properties": {
            "proposal": {
                "type": "object",
                "title": "LocalOptimizationProposal",
                "additionalProperties": False,
                "properties": {
                    "intended_benefit": _nonblank_string_schema(reject_unknown=True),
                    "affected_views": {
                        "type": "array",
                        "items": {"enum": list(registries.EMBODIED_VIEW_IDS)},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "short_term_effects": _nonblank_string_schema(reject_unknown=True),
                    "long_term_effects": _nonblank_string_schema(reject_unknown=True),
                    "externalities_tradeoffs": _nonblank_string_schema(reject_unknown=True),
                    "uncertainty": _nonblank_string_schema(reject_unknown=True),
                    "consent_autonomy_status": {
                        "enum": ["INFORMED_VOLUNTARY", "NOT_APPLICABLE_EDUCATIONAL"]
                    },
                    "reversibility": {
                        "enum": ["REVERSIBLE", "PARTIALLY_REVERSIBLE"]
                    },
                    "stop_conditions": _nonblank_string_schema(reject_unknown=True),
                    "referral_boundary": _nonblank_string_schema(reject_unknown=True),
                    "residual_harm_after_rollback": _nonblank_string_schema(reject_unknown=True),
                    "evidence_objects": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/$defs/evidence_object"},
                        "contains": {
                            "type": "object",
                            "properties": {"supports": evidence_support},
                            "required": ["supports"],
                        },
                    },
                },
                "required": fields + ["evidence_objects"],
            },
            "notes": {"type": "string"},
        },
        "required": ["proposal"],
        "additionalProperties": False,
        "field_set": fields,
        "field_set_complete": life_integrity.local_optimization_field_set_complete(),
        "fail_closed_rules": [
            "affected_views must be non-empty and drawn from the seven embodied views",
            "every required disclosure must be present and not UNKNOWN/empty",
            "a local_optimization_risk_review evidence object must support every disclosure",
            "consent and reversibility use fail-closed status sets",
            "the gate only validates the contract; it never executes the proposal",
        ],
    }


# ---------------------------------------------------------------------------
# 6. Embodied-view projection schema
# ---------------------------------------------------------------------------
def _embodied_view_projection_schema() -> dict:
    cross_view_relation = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "relation_type": _nonblank_string_schema(),
            "source_view": {"enum": list(registries.EMBODIED_VIEW_IDS)},
            "target_view": {"enum": list(registries.EMBODIED_VIEW_IDS)},
            "asserts_causality": {"type": "boolean", "const": False},
            "notes": {"type": "string"},
        },
        "required": [
            "relation_type",
            "source_view",
            "target_view",
            "asserts_causality",
        ],
    }
    contradiction = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "view_a": {"enum": list(registries.EMBODIED_VIEW_IDS)},
            "view_b": {"enum": list(registries.EMBODIED_VIEW_IDS)},
            "description": {"type": "string"},
        },
        "required": ["view_a", "view_b"],
    }
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "meta": _meta(),
        "schema": "r5a/embodied-view-projection/v1",
        "title": "EmbodiedViewProjection",
        "type": "object",
        "$defs": {
            "CrossViewRelation": cross_view_relation,
            "Contradiction": contradiction,
        },
        "properties": {
            "view_id": {"enum": list(registries.EMBODIED_VIEW_IDS)},
            "subject_identity": _nonblank_string_schema(),
            "observations": {"type": "array"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "time_scope": _nonblank_string_schema(),
            "unknown": {"type": "boolean"},
            "provenance": {"type": "string"},
            "provenance_boundary": _nonblank_string_schema(),
        },
        "required": [
            "view_id",
            "subject_identity",
            "observations",
            "confidence",
            "time_scope",
            "unknown",
            "provenance",
            "provenance_boundary",
        ],
        "additionalProperties": False,
        "allOf": [
            {
                "if": {"properties": {"unknown": {"const": True}}, "required": ["unknown"]},
                "then": {"properties": {"observations": {"maxItems": 0}}},
                "else": {
                    "properties": {
                        "observations": {"minItems": 1},
                        "time_scope": _nonblank_string_schema(reject_unknown=True),
                        "provenance": _nonblank_string_schema(),
                    }
                },
            }
        ],
        "related": {
            "CrossViewRelation": cross_view_relation,
            "Contradiction": contradiction,
        },
        "fail_closed_rules": [
            "view_id must be in the seven-view closed set",
            "subject_identity must be a non-empty string and shared across all views",
            "an observed view requires observations, bounded time_scope and provenance",
            "asserts_causality must be false for every cross-view relation",
            "a single view may never assert WHOLE_PERSON_COMPLETE",
        ],
    }


# ---------------------------------------------------------------------------
# 7. Translated-claim schema
# ---------------------------------------------------------------------------
def _translated_claim_schema() -> dict:
    required = list(tradition_translation.TRANSLATED_CLAIM_REQUIRED_FIELDS)
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "meta": _meta(),
        "schema": "r5a/translated-claim/v1",
        "title": "TranslatedClaim",
        "type": "object",
        "properties": {
            "source_provenance": _nonblank_string_schema(),
            "source_language": _nonblank_string_schema(),
            "translation_status": _nonblank_string_schema(),
            "attribution_status": _nonblank_string_schema(),
            "claim_class": {"enum": list(registries.TRADITION_CLAIM_CLASS_IDS)},
            "literal_reference": _nonblank_string_schema(),
            "interpretation_layer": {"enum": list(registries.TRADITION_INTERPRETATION_LAYER_IDS)},
            "evidence_grade": _nonblank_string_schema(),
            "mechanism_status": {"enum": list(registries.TRADITION_MECHANISM_STATUS_IDS)},
            "applicability_scope": _nonblank_string_schema(),
            "rights_boundary": _nonblank_string_schema(),
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "unknowns": {"type": "array", "items": _nonblank_string_schema()},
            "prohibited_upgrades": {"type": "array", "items": _nonblank_string_schema()},
            "revision_history": {"type": "array", "items": {"type": "object"}},
        },
        "required": required,
        "additionalProperties": False,
        "allOf": [
            {
                "not": {
                    "properties": {
                        "claim_class": {"const": source},
                        "mechanism_status": {"const": target},
                    },
                    "required": ["claim_class", "mechanism_status"],
                }
            }
            for source, target in (
                ("PHENOMENOLOGICAL_REPORT", "EMPIRICALLY_SUPPORTED_MECHANISM"),
                ("METAPHYSICAL_CLAIM", "SCIENTIFIC_FACT"),
                ("PRACTICE_PROTOCOL", "CLINICAL_EFFICACY"),
            )
        ]
        + [
            {
                "not": {
                    "properties": {
                        "interpretation_layer": {"const": "LATER_INTERPRETATION"},
                        "attribution_status": {"const": "AUTHOR_INTENT"},
                    },
                    "required": ["interpretation_layer", "attribution_status"],
                }
            }
        ],
        "forbidden_upgrades": [
            {"from": a, "to": b}
            for (a, b) in sorted(registries.TRADITION_FORBIDDEN_TRANSITIONS)
        ],
        "fail_closed_rules": [
            "claim_class must be in the eight-class closed set",
            "the five forbidden silent upgrades are rejected at build time",
            "mechanism_status/interpretation_layer may not realize a forbidden upgrade target",
            "out-of-set aliases fail closed instead of being treated as semantic evidence",
        ],
    }


# ---------------------------------------------------------------------------
# 8. Practice safety-envelope schema
# ---------------------------------------------------------------------------
def _practice_safety_envelope_schema() -> dict:
    fields = list(safety_envelope.REQUIRED_ENVELOPE_FIELDS)
    structured_string_fields = [
        field_name
        for field_name in fields
        if field_name not in {"informed_consent_required", "unknowns"}
    ]
    unsafe_patterns = list(safety_envelope._UNSAFE_PATTERNS) + [
        re.escape(phrase) for phrase in safety_envelope._STOP_PHRASES
    ]
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "meta": _meta(),
        "schema": "r5a/practice-safety-envelope/v1",
        "title": "PracticeSafetyEnvelope",
        "type": "object",
        "properties": {
            "educational_vs_individualized": {"enum": list(safety_envelope.EDUCATIONAL_STATUS_IDS)},
            "intended_population": _nonblank_string_schema(reject_unknown=True),
            "exclusion_criteria": _nonblank_string_schema(reject_unknown=True),
            "contraindications": _nonblank_string_schema(reject_unknown=True),
            "risk_severity": {"enum": list(safety_envelope.RISK_SEVERITY_IDS)},
            "informed_consent_required": {"type": "boolean", "const": True},
            "dependency_coercion_risk": {
                "enum": [
                    item for item in safety_envelope.COERCION_RISK_IDS if item != "HIGH"
                ]
            },
            "stop_conditions": _nonblank_string_schema(reject_unknown=True),
            "rollback_exit_path": _nonblank_string_schema(reject_unknown=True),
            "professional_referral_boundary": _nonblank_string_schema(reject_unknown=True),
            "emergency_boundary": _nonblank_string_schema(reject_unknown=True),
            "interaction_with_existing_care": {"enum": list(safety_envelope.CARE_DISPOSITION_IDS)},
            "evidence_grade": {"enum": list(safety_envelope.EVIDENCE_GRADE_IDS)},
            "unknowns": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": _nonblank_string_schema(),
            },
            "long_term_followup_plan": _nonblank_string_schema(reject_unknown=True),
            "raw_text": {"type": "string"},
        },
        "required": fields,
        "additionalProperties": False,
        "allOf": [
            {
                "not": {
                    "properties": {
                        field_name: {
                            "anyOf": [{"pattern": pattern} for pattern in unsafe_patterns]
                        }
                    },
                    "required": [field_name],
                }
            }
            for field_name in structured_string_fields + ["raw_text"]
        ],
        "field_set": fields,
        "field_set_complete": safety_envelope.envelope_field_set_complete(),
        "stop_treatment_language": {
            "forbidden": True,
            "detector_phrases": list(safety_envelope._STOP_PHRASES),
            "bounded_multilingual_patterns": list(safety_envelope._UNSAFE_PATTERNS),
        },
        "fail_closed_rules": [
            "every required field must be present and not UNKNOWN/empty",
            "informed_consent_required must be true for any intervention protocol",
            "stop_conditions, rollback_exit_path and professional_referral_boundary must be declared",
            "language recommending stopping prescribed treatment or substituting an unverified practice is rejected",
        ],
    }


# ---------------------------------------------------------------------------
# 9. Concept-mapping transition schema
# ---------------------------------------------------------------------------
def _concept_mapping_transition_schema() -> dict:
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "meta": _meta(),
        "schema": "r5a/concept-mapping-transition/v1",
        "title": "ConceptMapping",
        "type": "object",
        "properties": {
            "concept_id": _nonblank_string_schema(),
            "source_state": {"enum": list(registries.CONCEPT_MAPPING_STATE_IDS)},
            "current_state": {"enum": list(registries.CONCEPT_MAPPING_STATE_IDS)},
            "provenance": {"type": "string"},
            "current_interpretation": {"type": "string"},
            "superseded_interpretations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "interpretation": _nonblank_string_schema(),
                        "superseded_by_evidence_id": _nonblank_string_schema(),
                        "transition": _nonblank_string_schema(),
                    },
                    "required": [
                        "interpretation",
                        "superseded_by_evidence_id",
                        "transition",
                    ],
                },
            },
            "transitions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "from": {"enum": list(registries.CONCEPT_MAPPING_STATE_IDS)},
                        "to": {"enum": list(registries.CONCEPT_MAPPING_STATE_IDS)},
                        "required_evidence_class": {"type": "string"},
                        "provided_evidence_class": {"type": "string"},
                        "reviewer_role": {"type": "string"},
                        "reversibility": {"type": "boolean"},
                        "contradiction_handling": {"type": "string"},
                        "reason": {"type": "string"},
                        "receipt": {"type": "string"},
                        "evidence_id": {"type": "string"},
                        "superseded_interpretations_preserved": {"type": "integer", "minimum": 0},
                    },
                    "required": [
                        "from", "to", "required_evidence_class",
                        "provided_evidence_class", "reviewer_role",
                        "reversibility", "contradiction_handling", "reason", "receipt",
                        "evidence_id", "superseded_interpretations_preserved",
                    ],
                },
            },
        },
        "required": ["concept_id", "source_state", "current_state", "transitions"],
        "additionalProperties": False,
        "forbidden_direct_jumps": ["UNMAPPED->PARTIALLY_SUPPORTED", "SYMBOLIC_DESCRIPTION->PARTIALLY_SUPPORTED"],
        "fail_closed_rules": [
            "target state must be in the eight-state closed set",
            "UNMAPPED/SYMBOLIC_DESCRIPTION may not jump directly to PARTIALLY_SUPPORTED",
            "transition must be in the allowed graph",
            "every transition records evidence_class, reviewer_role, reversibility, contradiction_handling, reason and receipt",
            "provided evidence class, reviewer role and reversibility must equal registry metadata",
            "superseded interpretations are preserved with evidence identity",
            "CONTRADICTED and UNKNOWN remain first-class outcomes",
        ],
    }


# ---------------------------------------------------------------------------
# 10. Longitudinal feedback and revision contract
# ---------------------------------------------------------------------------
def _longitudinal_feedback_schema() -> dict:
    event_required = [
        "event_id", "observation_time", "review_time", "consent_autonomy_version",
        "evidence_chain_id", "short_term_benefit", "short_term_harm",
        "long_term_benefit", "long_term_harm", "rollback_status",
        "residual_harm_after_rollback", "evidence_object",
    ]
    event_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "event_id": _nonblank_string_schema(),
            "observation_time": {"type": "string", "format": "date-time"},
            "review_time": {"type": "string", "format": "date-time"},
            "consent_autonomy_version": _nonblank_string_schema(),
            "evidence_chain_id": _nonblank_string_schema(),
            "short_term_benefit": _nonblank_string_schema(),
            "short_term_harm": _nonblank_string_schema(),
            "long_term_benefit": _nonblank_string_schema(),
            "long_term_harm": _nonblank_string_schema(),
            "rollback_status": {"enum": list(longitudinal.ROLLBACK_STATUS_IDS)},
            "residual_harm_after_rollback": _nonblank_string_schema(),
            "evidence_object": _evidence_object_schema(
                evidence_class="longitudinal_observation"
            ),
        },
        "required": event_required,
    }
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "meta": _meta(),
        "schema": "r5a/longitudinal-feedback/v1",
        "title": "LongitudinalRevisionContract",
        "type": "object",
        "$defs": {"event": event_schema},
        "properties": {
            "contract_id": _nonblank_string_schema(),
            "observation_time": {"type": "string", "format": "date-time"},
            "decision_time": {"type": "string", "format": "date-time"},
            "intervention_time": {"type": "string", "format": "date-time"},
            "review_time": {"type": "string", "format": "date-time"},
            "consent_autonomy_version": _nonblank_string_schema(),
            "evidence_chain_id": _nonblank_string_schema(),
            "reopen_trigger": {"enum": list(longitudinal.REOPEN_TRIGGER_IDS)},
            "revision_status": {"enum": list(longitudinal.REVISION_STATUS_IDS)},
            "retirement_state": {"enum": list(longitudinal.REVISION_STATUS_IDS)},
            "revision_authority_role": {
                "enum": list(longitudinal.REVISION_AUTHORITY_ROLE_IDS)
            },
            "evidence_threshold": {"enum": list(longitudinal.EVIDENCE_THRESHOLD_IDS)},
            "events": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"$ref": "#/$defs/event"},
            },
        },
        "required": [
            "contract_id", "observation_time", "decision_time", "intervention_time",
            "review_time", "consent_autonomy_version", "evidence_chain_id",
            "reopen_trigger", "revision_status", "retirement_state",
            "revision_authority_role", "evidence_threshold", "events",
        ],
        "additionalProperties": False,
        "closed_sets": {
            "revision_status": list(longitudinal.REVISION_STATUS_IDS),
            "reopen_trigger": list(longitudinal.REOPEN_TRIGGER_IDS),
            "rollback_status": list(longitudinal.ROLLBACK_STATUS_IDS),
            "revision_authority_role": list(longitudinal.REVISION_AUTHORITY_ROLE_IDS),
            "evidence_threshold": list(longitudinal.EVIDENCE_THRESHOLD_IDS),
        },
        "event_required": event_required,
        "fail_closed_rules": [
            "observation, decision, intervention and review time are distinct ordered fields",
            "consent/autonomy changes append immutable versions",
            "delayed adverse outcomes explicitly reopen the candidate",
            "rollback status and residual harm remain separate",
            "deprecation or retirement requires independent role H",
        ],
    }


def _attack_case_registry() -> dict:
    return attack_gate.attack_case_registry()


def _attack_acceptance_receipt() -> dict:
    return attack_gate.run_attack_gate()


def _consolidated_repair_case_registry() -> dict:
    return consolidated_repair_gate.consolidated_repair_case_registry()


def _consolidated_repair_acceptance_receipt() -> dict:
    return consolidated_repair_gate.run_consolidated_repair_gate(
        schema_documents={
            "life-integrity-assessment-schema.json": _life_integrity_assessment_schema(),
            "embodied-view-projection-schema.json": _embodied_view_projection_schema(),
            "translated-claim-schema.json": _translated_claim_schema(),
            "practice-safety-envelope-schema.json": _practice_safety_envelope_schema(),
            "concept-mapping-transition-schema.json": _concept_mapping_transition_schema(),
            "longitudinal-feedback-schema.json": _longitudinal_feedback_schema(),
        }
    )


_ARTIFACTS = (
    ("candidate-charter-manifest.json", _candidate_charter_manifest),
    ("embodied-view-registry.json", _embodied_view_registry),
    ("tradition-claim-class-registry.json", _tradition_claim_class_registry),
    ("concept-mapping-lifecycle-registry.json", _concept_mapping_lifecycle_registry),
    ("life-integrity-assessment-schema.json", _life_integrity_assessment_schema),
    ("embodied-view-projection-schema.json", _embodied_view_projection_schema),
    ("translated-claim-schema.json", _translated_claim_schema),
    ("practice-safety-envelope-schema.json", _practice_safety_envelope_schema),
    ("concept-mapping-transition-schema.json", _concept_mapping_transition_schema),
    ("longitudinal-feedback-schema.json", _longitudinal_feedback_schema),
    ("r5a-narrow-repair-attack-case-registry.json", _attack_case_registry),
    ("r5a-narrow-repair-attack-acceptance.json", _attack_acceptance_receipt),
    (
        "r5a-consolidated-repair-attack-case-registry.json",
        _consolidated_repair_case_registry,
    ),
    (
        "r5a-consolidated-repair-attack-acceptance.json",
        _consolidated_repair_acceptance_receipt,
    ),
)


def generate(out_dir: str = OUT_DIR) -> list[str]:
    written = []
    for name, builder in _ARTIFACTS:
        written.append(_write(name, builder(), out_dir))
    return written


def main() -> None:
    for path in generate(OUT_DIR):
        print("wrote", os.path.relpath(path, REPO_ROOT))


if __name__ == "__main__":
    main()
