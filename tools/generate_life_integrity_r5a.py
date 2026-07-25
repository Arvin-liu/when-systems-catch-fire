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
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from life_integrity_r5a import (  # noqa: E402
    annex,
    concept_mapping,
    embodied_view,
    life_integrity,
    manifest,
    non_impact,
    registries,
    safety_envelope,
    tradition_translation,
)

OUT_DIR = os.path.join(REPO_ROOT, "docs", "architecture", "ignition-r5a-life-integrity-r1")

GENERATED_BY = "tools/generate_life_integrity_r5a.py"


def _meta() -> dict:
    return {
        "task_id": registries.TASK_ID,
        "control_commit": registries.CONTROL_COMMIT,
        "formal_predecessor": registries.FORMAL_PREDECESSOR,
        "frozen_head": registries.FROZEN_HEAD,
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
    return {
        "meta": _meta(),
        "schema": "r5a/life-integrity-assessment/v1",
        "title": "LifeIntegrityAssessment",
        "type": "object",
        "properties": {
            "proposal": {
                "type": ["object", "null"],
                "title": "LocalOptimizationProposal",
                "properties": {
                    "intended_benefit": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "affected_views": {
                        "type": "array",
                        "items": {"enum": list(registries.EMBODIED_VIEW_IDS)},
                        "minItems": 1,
                    },
                    "short_term_effects": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "long_term_effects": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "externalities_tradeoffs": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "uncertainty": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "consent_autonomy_status": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "reversibility": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "stop_conditions": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "referral_boundary": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                    "residual_harm_after_rollback": {"type": "string", "not_unknowns": ["UNKNOWN", ""]},
                },
                "required": fields,
            },
            "notes": {"type": "string"},
        },
        "required": ["proposal"],
        "field_set": fields,
        "field_set_complete": life_integrity.local_optimization_field_set_complete(),
        "fail_closed_rules": [
            "affected_views must be non-empty and drawn from the seven embodied views",
            "every required disclosure must be present and not UNKNOWN/empty",
            "the gate only validates the contract; it never executes the proposal",
        ],
    }


# ---------------------------------------------------------------------------
# 6. Embodied-view projection schema
# ---------------------------------------------------------------------------
def _embodied_view_projection_schema() -> dict:
    return {
        "meta": _meta(),
        "schema": "r5a/embodied-view-projection/v1",
        "title": "EmbodiedViewProjection",
        "type": "object",
        "properties": {
            "view_id": {"enum": list(registries.EMBODIED_VIEW_IDS)},
            "subject_identity": {"type": "string", "minLength": 1},
            "observations": {"type": "array"},
            "confidence": {"type": "number"},
            "time_scope": {"type": "string"},
            "unknown": {"type": "boolean"},
            "provenance": {"type": "string"},
        },
        "required": ["view_id", "subject_identity"],
        "related": {
            "CrossViewRelation": {
                "type": "object",
                "properties": {
                    "relation_type": {"type": "string"},
                    "source_view": {"enum": list(registries.EMBODIED_VIEW_IDS)},
                    "target_view": {"enum": list(registries.EMBODIED_VIEW_IDS)},
                    "asserts_causality": {"type": "boolean", "const": False},
                    "notes": {"type": "string"},
                },
                "required": ["relation_type", "source_view", "target_view"],
            },
            "Contradiction": {
                "type": "object",
                "properties": {
                    "view_a": {"enum": list(registries.EMBODIED_VIEW_IDS)},
                    "view_b": {"enum": list(registries.EMBODIED_VIEW_IDS)},
                    "description": {"type": "string"},
                },
                "required": ["view_a", "view_b"],
            },
        },
        "fail_closed_rules": [
            "view_id must be in the seven-view closed set",
            "subject_identity must be a non-empty string and shared across all views",
            "asserts_causality must be false for every cross-view relation",
            "a single view may never assert WHOLE_PERSON_COMPLETE",
        ],
    }


# ---------------------------------------------------------------------------
# 7. Translated-claim schema
# ---------------------------------------------------------------------------
def _translated_claim_schema() -> dict:
    return {
        "meta": _meta(),
        "schema": "r5a/translated-claim/v1",
        "title": "TranslatedClaim",
        "type": "object",
        "properties": {
            "source_provenance": {"type": "string", "minLength": 1},
            "source_language": {"type": "string"},
            "translation_status": {"type": "string"},
            "attribution_status": {"type": "string"},
            "claim_class": {"enum": list(registries.TRADITION_CLAIM_CLASS_IDS)},
            "literal_reference": {"type": "string"},
            "interpretation_layer": {"type": "string"},
            "evidence_grade": {"type": "string"},
            "mechanism_status": {"type": "string"},
            "applicability_scope": {"type": "string"},
            "rights_boundary": {"type": "string"},
            "confidence": {"type": "number"},
            "unknowns": {"type": "array", "items": {"type": "string"}},
            "prohibited_upgrades": {"type": "array", "items": {"type": "string"}},
            "revision_history": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["source_provenance", "claim_class"],
        "forbidden_upgrades": [
            {"from": a, "to": b}
            for (a, b) in sorted(registries.TRADITION_FORBIDDEN_TRANSITIONS)
        ],
        "fail_closed_rules": [
            "claim_class must be in the eight-class closed set",
            "the five forbidden silent upgrades are rejected at build time",
            "mechanism_status/interpretation_layer may not realize a forbidden upgrade target",
        ],
    }


# ---------------------------------------------------------------------------
# 8. Practice safety-envelope schema
# ---------------------------------------------------------------------------
def _practice_safety_envelope_schema() -> dict:
    fields = list(safety_envelope.REQUIRED_ENVELOPE_FIELDS)
    return {
        "meta": _meta(),
        "schema": "r5a/practice-safety-envelope/v1",
        "title": "PracticeSafetyEnvelope",
        "type": "object",
        "properties": {f: {"type": "string", "not_unknowns": ["UNKNOWN", ""]} for f in fields},
        "required": fields,
        "field_set": fields,
        "field_set_complete": safety_envelope.envelope_field_set_complete(),
        "stop_treatment_language": {
            "forbidden": True,
            "detector_phrases": list(safety_envelope._STOP_PHRASES),
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
        "meta": _meta(),
        "schema": "r5a/concept-mapping-transition/v1",
        "title": "ConceptMapping",
        "type": "object",
        "properties": {
            "concept_id": {"type": "string", "minLength": 1},
            "source_state": {"enum": list(registries.CONCEPT_MAPPING_STATE_IDS)},
            "current_state": {"enum": list(registries.CONCEPT_MAPPING_STATE_IDS)},
            "provenance": {"type": "string"},
            "transitions": {
                "type": "array",
                "items": {
                    "type": "object",
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
                    },
                    "required": [
                        "from", "to", "required_evidence_class",
                        "provided_evidence_class", "reviewer_role",
                        "reversibility", "contradiction_handling", "reason", "receipt",
                    ],
                },
            },
        },
        "required": ["concept_id", "source_state"],
        "forbidden_direct_jumps": ["UNMAPPED->PARTIALLY_SUPPORTED", "SYMBOLIC_DESCRIPTION->PARTIALLY_SUPPORTED"],
        "fail_closed_rules": [
            "target state must be in the eight-state closed set",
            "UNMAPPED/SYMBOLIC_DESCRIPTION may not jump directly to PARTIALLY_SUPPORTED",
            "transition must be in the allowed graph",
            "every transition records evidence_class, reviewer_role, reversibility, contradiction_handling, reason and receipt",
            "CONTRADICTED and UNKNOWN remain first-class outcomes",
        ],
    }


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
