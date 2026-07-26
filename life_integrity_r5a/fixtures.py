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
from . import longitudinal as LG
from .evidence import EvidenceObject


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
                time_scope="synthetic-window-2026-07",
                provenance="synthetic-fixture",
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
        interpretation_layer="SOURCE_LITERAL",
        evidence_grade="historical",
        applicability_scope="historical context only",
        rights_boundary="public domain summary",
        confidence=0.6,
        unknowns=["author intent"],
    )


def sample_concept_mapping() -> CM.ConceptMapping:
    m = CM.ConceptMapping(concept_id="synthetic-concept", source_state="SYMBOLIC_DESCRIPTION")
    evidence = EvidenceObject(
        evidence_id="EV-SYNTHETIC-CONCEPT-001",
        evidence_class="phenomenology_report",
        provenance="synthetic-fixture",
        reviewer_role="D",
        supports=("transition:SYMBOLIC_DESCRIPTION->PHENOMENOLOGICAL_CANDIDATE",),
        observed_facts=("synthetic transition fixture",),
    )
    CM.apply_transition(
        m,
        "PHENOMENOLOGICAL_CANDIDATE",
        "phenomenology_report",
        "D",
        "synthetic",
        evidence_object=evidence,
        new_interpretation="synthetic phenomenological candidate",
    )
    return m


def sample_safety_envelope() -> SE.PracticeSafetyEnvelope:
    return SE.PracticeSafetyEnvelope(
        educational_vs_individualized="EDUCATIONAL_ONLY",
        intended_population="general adults",
        exclusion_criteria="none known",
        contraindications="none known",
        risk_severity="LOW",
        informed_consent_required=True,
        dependency_coercion_risk="LOW",
        stop_conditions="discontinue if adverse",
        rollback_exit_path="stop practice",
        professional_referral_boundary="licensed clinician",
        emergency_boundary="call emergency services",
        interaction_with_existing_care="COORDINATE_WITH_PROFESSIONAL",
        evidence_grade="SOFTWARE_CONTRACT_ONLY",
        unknowns=["long-term data"],
        long_term_followup_plan="annual review",
        raw_text="discuss options with a licensed clinician",
    )


def sample_local_optimization_proposal() -> LI.LocalOptimizationProposal:
    return LI.LocalOptimizationProposal(
        intended_benefit="improve sleep hygiene",
        affected_views=["PhysiologicalView", "BehavioralView"],
        short_term_effects="faster sleep onset",
        long_term_effects="no long-term effect asserted; evidence remains bounded to this synthetic fixture",
        externalities_tradeoffs="minimal",
        uncertainty="moderate",
        consent_autonomy_status="INFORMED_VOLUNTARY",
        reversibility="REVERSIBLE",
        stop_conditions="discontinue if adverse",
        referral_boundary="sleep specialist",
        residual_harm_after_rollback="minimal",
        evidence_objects=[
            EvidenceObject(
                evidence_id="EV-SYNTHETIC-LOCAL-001",
                evidence_class="local_optimization_risk_review",
                provenance="synthetic-fixture",
                reviewer_role="E",
                supports=tuple(LI.LOCAL_OPTIMIZATION_FIELDS),
                observed_facts=("all eleven disclosures inspected",),
            )
        ],
    )


def sample_multi_view_evidence() -> EvidenceObject:
    return EvidenceObject(
        evidence_id="EV-SYNTHETIC-MULTIVIEW-001",
        evidence_class="multi_view_observation",
        provenance="synthetic-fixture",
        reviewer_role="F",
        supports=tuple(f"view:{view_id}" for view_id in R.EMBODIED_VIEW_IDS),
        observed_facts=("seven synthetic view projections are present",),
    )


def sample_longitudinal_contract(*, reopen_delayed_harm: bool = True) -> LG.LongitudinalRevisionContract:
    evidence = EvidenceObject(
        evidence_id="EV-SYNTHETIC-LONGITUDINAL-001",
        evidence_class="longitudinal_observation",
        provenance="synthetic-fixture",
        reviewer_role="E",
        supports=("longitudinal:synthetic-contract",),
        observed_facts=("delayed synthetic harm recorded",),
    )
    event = LG.LongitudinalEvent(
        event_id="event-001",
        observation_time="2026-07-01T00:00:00+00:00",
        review_time="2026-07-04T00:00:00+00:00",
        consent_autonomy_version="consent-v1",
        evidence_chain_id="chain-001",
        short_term_benefit="NONE_OBSERVED",
        short_term_harm="NONE_OBSERVED",
        long_term_benefit="NOT_YET_OBSERVED",
        long_term_harm="synthetic delayed sleep disruption",
        rollback_status="SUCCEEDED",
        residual_harm_after_rollback="synthetic residual fatigue",
        evidence_object=evidence,
    )
    return LG.LongitudinalRevisionContract(
        contract_id="synthetic-contract",
        observation_time="2026-07-01T00:00:00+00:00",
        decision_time="2026-07-02T00:00:00+00:00",
        intervention_time="2026-07-03T00:00:00+00:00",
        review_time="2026-07-04T00:00:00+00:00",
        consent_autonomy_version="consent-v1",
        evidence_chain_id="chain-001",
        reopen_trigger=("DELAYED_ADVERSE_OUTCOME" if reopen_delayed_harm else "NONE"),
        revision_status=("REOPENED" if reopen_delayed_harm else "ACTIVE"),
        retirement_state="ACTIVE",
        revision_authority_role="E",
        evidence_threshold="INDEPENDENT_REVIEW_REQUIRED",
        events=(event,),
    )
