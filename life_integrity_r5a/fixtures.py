# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Synthetic fixtures for R5-A contract tests.

All fixtures are synthetic and contain NO private notes, personal health
records, copyrighted source corpora, or reconstructive religious-text extracts.
They exist only to exercise the fail-closed contracts deterministically.
"""

from __future__ import annotations

from . import concept_mapping as CM
from . import embodied_view as EV
from . import life_integrity as LI
from . import registries as R
from . import safety_envelope as SE
from . import tradition_translation as TT


def sample_embodied_agent(subject_identity: str = "synthetic-subject") -> EV.EmbodiedAgent:
    agent = EV.EmbodiedAgent(subject_identity=subject_identity)
    for vid in R.EMBODIED_VIEW_IDS:
        agent.add_view(
            EV.EmbodiedViewProjection(
                view_id=vid,
                subject_identity=subject_identity,
                unknown=False,
                observations=[f"synthetic-observation-{vid}"],
                confidence=0.5,
            )
        )
    return agent


def sample_translated_claim() -> TT.TranslatedClaim:
    return TT.translate_claim(
        source_provenance="synthetic-source",
        claim_class="HISTORICAL_SOURCE",
        source_language="zh",
        translation_status="literal",
        attribution_status="author",
        literal_reference="synthetic-ref-001",
        interpretation_layer="neutral summary",
        evidence_grade="historical",
        applicability_scope="historical context only",
        rights_boundary="public domain summary",
        confidence=0.6,
        unknowns=["author intent"],
    )


def sample_concept_mapping() -> CM.ConceptMapping:
    m = CM.ConceptMapping(concept_id="synthetic-concept", source_state="SYMBOLIC_DESCRIPTION")
    CM.apply_transition(
        m, "PHENOMENOLOGICAL_CANDIDATE", "phenomenology_report", "D", "synthetic"
    )
    return m


def sample_safety_envelope() -> SE.PracticeSafetyEnvelope:
    return SE.PracticeSafetyEnvelope(
        educational_vs_individualized="educational",
        intended_population="general adults",
        exclusion_criteria="none known",
        contraindications="none known",
        risk_severity="low",
        informed_consent_required=True,
        dependency_coercion_risk="low",
        stop_conditions="discontinue if adverse",
        rollback_exit_path="stop practice",
        professional_referral_boundary="licensed clinician",
        emergency_boundary="call emergency services",
        interaction_with_existing_care="coordinate with provider",
        evidence_grade="low",
        unknowns=["long-term data"],
        long_term_followup_plan="annual review",
        raw_text="discuss options with a licensed clinician",
    )


def sample_local_optimization_proposal() -> LI.LocalOptimizationProposal:
    return LI.LocalOptimizationProposal(
        intended_benefit="improve sleep hygiene",
        affected_views=["PhysiologicalView", "BehavioralView"],
        short_term_effects="faster sleep onset",
        long_term_effects="unknown",
        externalities_tradeoffs="minimal",
        uncertainty="moderate",
        consent_autonomy_status="informed",
        reversibility="reversible",
        stop_conditions="discontinue if adverse",
        referral_boundary="sleep specialist",
        residual_harm_after_rollback="minimal",
    )
