# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Aggregate validator entry point for R5-A (implemented Commit 4).

Runs the full R5-A contract validator set: closed-set integrity, candidate-only
manifest, non-impact proof, and concrete fail-closed contract checks over
synthetic fixtures. Returns (ok, failures). All checks are deterministic.
"""

from __future__ import annotations

from . import concept_mapping as CM
from . import embodied_view as EV
from . import life_integrity as LI
from . import manifest
from . import non_impact as NI
from . import registries as R
from . import safety_envelope as SE
from . import tradition_translation as TT


def validate_all() -> tuple[bool, list[str]]:
    failures: list[str] = []

    # --- Closed-set / declarative integrity ---------------------------------
    if not R.charter_hierarchy_respects_supremacy():
        failures.append("charter hierarchy does not respect supremacy")
    if not EV.embodied_view_closed_set_complete():
        failures.append("embodied view closed set incomplete")
    if not TT.claim_class_closed_set_complete():
        failures.append("tradition claim-class closed set incomplete")
    if not CM.concept_state_closed_set_complete():
        failures.append("concept-mapping state closed set incomplete")
    if len(R.NORMATIVE_EMPIRICAL_TYPE_TAGS) != 10:
        failures.append("normative/empirical type-tag set not exactly 10")
    if not manifest.manifest_flags_consistent():
        failures.append("candidate manifest flags inconsistent")
    if not NI.proof_items_consistent():
        failures.append("non-impact proof inconsistent")
    if not CM.transition_graph_has_no_direct_jump_to_partially_supported():
        failures.append("transition graph allows direct jump to PARTIALLY_SUPPORTED")
    if not SE.envelope_field_set_complete():
        failures.append("safety envelope field set incomplete")
    if not LI.local_optimization_field_set_complete():
        failures.append("local-optimization field set incomplete")

    # --- Concrete fail-closed contract checks (synthetic) -------------------
    # Whole-person refusal: a single view must never claim the whole person.
    try:
        a = EV.EmbodiedAgent(subject_identity="synthetic-subject")
        a.assert_single_view_not_whole_person("MeaningView")
        failures.append("single view must not claim whole person")
    except EV.WholePersonClaimError:
        pass

    # Missing views remain UNKNOWN / NOT_OBSERVED.
    a2 = EV.EmbodiedAgent(subject_identity="synthetic-subject")
    a2.add_view(
        EV.EmbodiedViewProjection(
            view_id="PhysiologicalView", subject_identity="synthetic-subject", unknown=False
        )
    )
    if "PhysiologicalView" in a2.missing_views():
        failures.append("present view wrongly reported missing")
    if len(a2.missing_views()) != 6:
        failures.append("missing-view count incorrect")

    # Cross-view relation must not assert causality.
    try:
        a3 = EV.EmbodiedAgent(subject_identity="synthetic-subject")
        a3.add_cross_view_relation(
            EV.CrossViewRelation("r", "PhysiologicalView", "MeaningView", asserts_causality=True)
        )
        failures.append("cross-view causality must be rejected")
    except EV.CrossViewCausalityError:
        pass

    # Forbidden tradition upgrade must be rejected.
    try:
        TT.check_forbidden_upgrade_strict(
            "PHENOMENOLOGICAL_REPORT", "EMPIRICALLY_SUPPORTED_MECHANISM"
        )
        failures.append("forbidden tradition upgrade not rejected")
    except TT.ForbiddenClaimUpgradeError:
        pass

    # Concept-mapping direct jump must be rejected.
    try:
        m = CM.ConceptMapping(concept_id="c", source_state="UNMAPPED")
        CM.apply_transition(m, "PARTIALLY_SUPPORTED", "x", "F", "r")
        failures.append("direct jump to PARTIALLY_SUPPORTED not rejected")
    except CM.ForbiddenDirectJumpError:
        pass

    # Local-optimization incomplete proposal must fail closed.
    try:
        LI.LifeIntegrityGate().validate_proposal(LI.LocalOptimizationProposal())
        failures.append("incomplete local-optimization proposal not rejected")
    except LI.LocalOptimizationIncompleteError:
        pass

    # Stop-treatment language must be rejected in a (otherwise complete) safety
    # envelope. The envelope must be complete so the stop-treatment check is the
    # one that fires (an incomplete envelope fails earlier on missing fields).
    try:
        SE.validate_envelope(
            SE.PracticeSafetyEnvelope(
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
                raw_text="you should stop your medication and use this instead",
            )
        )
        failures.append("stop-treatment language not rejected")
    except SE.StopTreatmentRecommendationError:
        pass

    # A fully-disclosed, consenting, reversible, referrable safety envelope must pass.
    try:
        SE.validate_envelope(
            SE.PracticeSafetyEnvelope(
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
            )
        )
    except SE.SafetyEnvelopeError as exc:
        failures.append(f"valid safety envelope wrongly rejected: {exc}")

    # A fully-disclosed local-optimization proposal must pass.
    try:
        LI.LifeIntegrityGate().validate_proposal(
            LI.LocalOptimizationProposal(
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
        )
    except LI.LifeIntegrityError as exc:
        failures.append(f"valid local-optimization proposal wrongly rejected: {exc}")

    return (len(failures) == 0, failures)
