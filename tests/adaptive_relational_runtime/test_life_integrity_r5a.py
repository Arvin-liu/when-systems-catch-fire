"""Acceptance + attack tests for the R5-A Life Integrity Charter Candidate.

R5-A encodes the user-authorized anti-fragmentation and intervention-caution
principle ("性命一体 / 身心互成") as a CANDIDATE governance/architecture overlay
beneath the existing Life Community Value Charter. This suite pins the required
invariants (task §12) and adversarial boundaries.

Commit 1: data/closed-set/membership tests pass; contract-logic tests fail
because the implementation modules raise NotImplementedError. Commits 2-4
implement the logic so the whole suite turns green. The suite never asserts
human efficacy, clinical effectiveness, or religious truth.
"""

from __future__ import annotations

import os

import pytest

import life_integrity_r5a as pkg
from life_integrity_r5a import concept_mapping as CM
from life_integrity_r5a import embodied_view as EV
from life_integrity_r5a import life_integrity as LI
from life_integrity_r5a import manifest
from life_integrity_r5a import non_impact as NI
from life_integrity_r5a import registries as R
from life_integrity_r5a import safety_envelope as SE
from life_integrity_r5a import tradition_translation as TT
from life_integrity_r5a import validators


# ===========================================================================
# A. Charter hierarchy, supremacy, no L7 / parallel executor / second executor
# ===========================================================================
def test_supreme_charter_is_life_community_value_charter():
    assert R.SUPREME_CHARTER == "LifeCommunityValueCharter"
    assert R.CHARTER_HIERARCHY[0] == R.SUPREME_CHARTER


def test_charter_hierarchy_respects_supremacy():
    assert R.charter_hierarchy_respects_supremacy()


@pytest.mark.parametrize("node", R.CHARTER_HIERARCHY)
def test_charter_hierarchy_node_is_not_l7_or_executor(node):
    assert node != "L7"
    assert "Executor" not in node or node == "FutureDomainPracticeProtocols"
    assert "second" not in node.lower()


def test_no_competing_supreme_node_inserted():
    # R5-A must never place a node above the Life Community Value Charter.
    assert R.CHARTER_HIERARCHY.count(R.SUPREME_CHARTER) == 1
    assert all(n != "L7" for n in R.CHARTER_HIERARCHY)


def test_package_source_has_no_promote_evolve_tokens():
    base = os.path.dirname(__file__)
    # package lives at repo root (life_integrity_r5a)
    pkg_root = os.path.join(os.path.dirname(os.path.dirname(base)), "life_integrity_r5a")
    assert os.path.isdir(pkg_root), pkg_root
    token_re = __import__("re").compile(
        r"(?<![A-Za-z0-9_])(prom" + "ote|evo" + "lve|trans" + "action)(?![A-Za-z0-9_])"
    )
    for root, _dirs, files in os.walk(pkg_root):
        for fn in files:
            if fn.endswith(".py"):
                text = open(os.path.join(root, fn), encoding="utf-8").read()
                assert not token_re.search(text), f"banned token in {fn}"


# ===========================================================================
# B. Embodied views: exactly seven, single subject, no whole-person claim,
#    missing views UNKNOWN, cross-view non-causality, contradictions surfaced
# ===========================================================================
def test_embodied_view_closed_set_has_exactly_seven():
    assert len(R.EMBODIED_VIEW_IDS) == 7
    assert EV.embodied_view_closed_set_complete()


@pytest.mark.parametrize("view", R.EMBODIED_VIEW_IDS)
def test_each_embodied_view_is_valid(view):
    assert R.is_valid_embodied_view(view)


def test_unknown_embodied_view_rejected():
    assert not R.is_valid_embodied_view("FakeView")
    with pytest.raises(EV.EmbodiedViewError):
        EV.EmbodiedViewProjection(view_id="FakeView", subject_identity="S1")


def test_projection_requires_subject_identity():
    with pytest.raises(EV.EmbodiedViewError):
        EV.EmbodiedViewProjection(view_id="MeaningView", subject_identity="")


def test_agent_created_with_subject_identity():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    assert agent.subject_identity == "subject-xyz"


def test_add_view_ties_to_same_subject():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    proj = EV.EmbodiedViewProjection(
        view_id="PhysiologicalView", subject_identity="subject-xyz", unknown=False
    )
    agent.add_view(proj)
    got = agent.get_view("PhysiologicalView")
    assert got.subject_identity == "subject-xyz"


def test_add_view_rejects_foreign_subject():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    proj = EV.EmbodiedViewProjection(
        view_id="MeaningView", subject_identity="other-subject"
    )
    with pytest.raises(EV.EmbodiedViewError):
        agent.add_view(proj)


def test_missing_views_returned_as_unknown():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    agent.add_view(
        EV.EmbodiedViewProjection(
            view_id="PhysiologicalView", subject_identity="subject-xyz", unknown=False
        )
    )
    missing = agent.missing_views()
    assert "PhysiologicalView" not in missing
    assert set(missing) == set(R.EMBODIED_VIEW_IDS) - {"PhysiologicalView"}
    assert all(m in R.EMBODIED_VIEW_IDS for m in missing)


def test_single_view_cannot_claim_whole_person():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    agent.add_view(
        EV.EmbodiedViewProjection(
            view_id="CognitiveAffectiveView", subject_identity="subject-xyz", unknown=False
        )
    )
    with pytest.raises(EV.WholePersonClaimError):
        agent.assert_single_view_not_whole_person("CognitiveAffectiveView")


def test_whole_person_conclusion_requires_disclosure():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    agent.add_view(
        EV.EmbodiedViewProjection(
            view_id="BehavioralView", subject_identity="subject-xyz", unknown=False
        )
    )
    # missing views not disclosed and contradictions not surfaced -> refuse
    with pytest.raises(EV.WholePersonClaimError):
        agent.require_whole_person_disclosure(
            claimed_views=["BehavioralView"],
            missing_disclosed=False,
            contradictions_surfaced=False,
        )


def test_cross_view_relation_must_not_assert_causality():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    rel = EV.CrossViewRelation(
        relation_type="correlates_with",
        source_view="PhysiologicalView",
        target_view="CognitiveAffectiveView",
        asserts_causality=True,
    )
    with pytest.raises(EV.CrossViewCausalityError):
        agent.add_cross_view_relation(rel)


def test_cross_view_relation_typed_non_causal_allowed():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    rel = EV.CrossViewRelation(
        relation_type="correlates_with",
        source_view="PhysiologicalView",
        target_view="CognitiveAffectiveView",
        asserts_causality=False,
    )
    agent.add_cross_view_relation(rel)
    assert len(agent._relations) == 1


def test_contradictory_views_are_surfaced_not_silenced():
    agent = EV.EmbodiedAgent(subject_identity="subject-xyz")
    agent.record_contradiction(
        EV.Contradiction("PhysiologicalView", "PhenomenologicalView", "mismatch")
    )
    surfaced = agent.surface_contradictions()
    assert len(surfaced) == 1
    assert surfaced[0].view_a == "PhysiologicalView"


# ===========================================================================
# C. Local-optimization gate: missing disclosure fails closed
# ===========================================================================
def test_local_optimization_field_set_complete():
    assert LI.local_optimization_field_set_complete()
    assert len(LI.LOCAL_OPTIMIZATION_FIELDS) == 11


def test_gate_rejects_incomplete_local_optimization():
    gate = LI.LifeIntegrityGate()
    incomplete = LI.LocalOptimizationProposal(
        intended_benefit="UNKNOWN",
        affected_views=[],
        short_term_effects="UNKNOWN",
        long_term_effects="UNKNOWN",
        externalities_tradeoffs="UNKNOWN",
        uncertainty="UNKNOWN",
        consent_autonomy_status="UNKNOWN",
        reversibility="UNKNOWN",
        stop_conditions="UNKNOWN",
        referral_boundary="UNKNOWN",
        residual_harm_after_rollback="UNKNOWN",
    )
    with pytest.raises(LI.LocalOptimizationIncompleteError):
        gate.validate_proposal(incomplete)


def test_gate_rejects_missing_consent_reversibility_stop_referral():
    gate = LI.LifeIntegrityGate()
    bad = LI.LocalOptimizationProposal(
        intended_benefit="improve sleep",
        affected_views=["PhysiologicalView"],
        short_term_effects="faster onset",
        long_term_effects="UNKNOWN",
        externalities_tradeoffs="UNKNOWN",
        uncertainty="high",
        consent_autonomy_status="UNKNOWN",
        reversibility="UNKNOWN",
        stop_conditions="UNKNOWN",
        referral_boundary="UNKNOWN",
        residual_harm_after_rollback="UNKNOWN",
    )
    with pytest.raises(LI.LocalOptimizationIncompleteError):
        gate.validate_proposal(bad)


# ===========================================================================
# D. Traditional / religious claim classes: closed set, unknown fails,
#    five forbidden silent upgrades
# ===========================================================================
def test_claim_class_closed_set_has_exactly_eight():
    assert len(R.TRADITION_CLAIM_CLASS_IDS) == 8
    assert TT.claim_class_closed_set_complete()


@pytest.mark.parametrize("cls", R.TRADITION_CLAIM_CLASS_IDS)
def test_each_claim_class_is_valid(cls):
    assert R.is_valid_claim_class(cls)


def test_unknown_claim_class_fails_closed():
    assert not R.is_valid_claim_class("FAKE_CLASS")
    with pytest.raises(TT.UnknownClaimClassError):
        TT.TranslatedClaim(
            source_provenance="x", source_language="zh", translation_status="literal",
            attribution_status="author", claim_class="FAKE_CLASS",
        )


@pytest.mark.parametrize(
    "pair",
    [
        ("PHENOMENOLOGICAL_REPORT", "EMPIRICALLY_SUPPORTED_MECHANISM"),
        ("METAPHYSICAL_CLAIM", "SCIENTIFIC_FACT"),
        ("PRACTICE_PROTOCOL", "CLINICAL_EFFICACY"),
        ("LATER_INTERPRETATION", "AUTHOR_INTENT"),
        ("HISTORICAL_LONGEVITY", "EFFECTIVENESS"),
    ],
)
def test_forbidden_tradition_upgrade_detected(pair):
    frm, to = pair
    assert R.is_forbidden_tradition_upgrade(frm, to)
    assert pair in TT.forbidden_upgrade_set()


def test_non_forbidden_upgrade_allowed_set():
    assert not R.is_forbidden_tradition_upgrade("HISTORICAL_SOURCE", "NORMATIVE_CLAIM")


def test_forbidden_upgrade_strict_rejects():
    with pytest.raises(TT.ForbiddenClaimUpgradeError):
        TT.check_forbidden_upgrade_strict(
            "PHENOMENOLOGICAL_REPORT", "EMPIRICALLY_SUPPORTED_MECHANISM"
        )


@pytest.mark.parametrize(
    "pair",
    [
        ("PHENOMENOLOGICAL_REPORT", "EMPIRICALLY_SUPPORTED_MECHANISM"),
        ("METAPHYSICAL_CLAIM", "SCIENTIFIC_FACT"),
        ("PRACTICE_PROTOCOL", "CLINICAL_EFFICACY"),
        ("LATER_INTERPRETATION", "AUTHOR_INTENT"),
        ("HISTORICAL_LONGEVITY", "EFFECTIVENESS"),
    ],
)
def test_translate_claim_rejects_forbidden_upgrade(pair):
    frm, to = pair
    with pytest.raises(TT.ForbiddenClaimUpgradeError):
        TT.translate_claim(
            source_provenance="synthetic", claim_class=frm, mechanism_status=to
        )


# ===========================================================================
# E. Concept-mapping lifecycle: 8 states, allowed transitions, forbidden
#    direct jump, CONTRADICTED / UNKNOWN retained
# ===========================================================================
def test_concept_state_closed_set_has_exactly_eight():
    assert len(R.CONCEPT_MAPPING_STATE_IDS) == 8
    assert CM.concept_state_closed_set_complete()


@pytest.mark.parametrize("state", R.CONCEPT_MAPPING_STATE_IDS)
def test_each_concept_state_is_valid(state):
    assert R.is_valid_concept_state(state)


def test_unknown_concept_state_rejected():
    assert not R.is_valid_concept_state("FAKE_STATE")
    with pytest.raises(CM.UnknownConceptStateError):
        CM.ConceptMapping(concept_id="c1", source_state="FAKE_STATE")


def test_transition_graph_blocks_direct_jump_to_partially_supported():
    assert CM.transition_graph_has_no_direct_jump_to_partially_supported()
    assert CM.direct_jump_forbidden("UNMAPPED")
    assert CM.direct_jump_forbidden("SYMBOLIC_DESCRIPTION")


@pytest.mark.parametrize("src", ["UNMAPPED", "SYMBOLIC_DESCRIPTION"])
def test_apply_transition_rejects_direct_jump(src):
    m = CM.ConceptMapping(concept_id="c", source_state=src)
    with pytest.raises(CM.ForbiddenDirectJumpError):
        CM.apply_transition(
            m, "PARTIALLY_SUPPORTED", evidence_class="x", reviewer_role="F",
            reason="should fail",
        )


def test_apply_transition_rejects_disallowed_edge():
    m = CM.ConceptMapping(concept_id="c", source_state="UNMAPPED")
    with pytest.raises(CM.InvalidConceptTransitionError):
        CM.apply_transition(
            m, "MECHANISM_HYPOTHESIS", evidence_class="x", reviewer_role="F",
            reason="no direct edge",
        )


def test_apply_transition_allowed_chain():
    m = CM.ConceptMapping(concept_id="c", source_state="SYMBOLIC_DESCRIPTION")
    CM.apply_transition(
        m, "PHENOMENOLOGICAL_CANDIDATE", evidence_class="phenomenology_report",
        reviewer_role="D", reason="interpretation",
    )
    assert m.current_state == "PHENOMENOLOGICAL_CANDIDATE"
    assert len(m.transitions) == 1


def test_concept_mapping_retains_contradicted_and_unknown():
    # both must remain reachable first-class outcomes
    assert "CONTRADICTED" in R.CONCEPT_MAPPING_STATE_IDS
    assert "UNKNOWN" in R.CONCEPT_MAPPING_STATE_IDS
    m = CM.ConceptMapping(concept_id="c", source_state="MECHANISM_HYPOTHESIS")
    CM.apply_transition(
        m, "CONTRADICTED", evidence_class="contradiction_evidence", reviewer_role="F",
        reason="conflicting evidence",
    )
    assert m.current_state == "CONTRADICTED"


# ===========================================================================
# F. Practice / intervention safety envelope
# ===========================================================================
def test_safety_envelope_field_set_complete():
    assert SE.envelope_field_set_complete()
    assert len(SE.REQUIRED_ENVELOPE_FIELDS) == 15


def test_envelope_rejects_missing_required_fields():
    env = SE.PracticeSafetyEnvelope()  # all UNKNOWN / False
    with pytest.raises(SE.EnvelopeIncompleteError):
        SE.validate_envelope(env)


def test_envelope_rejects_stop_treatment_language():
    assert SE.contains_stop_treatment_language("you should stop taking your medication")
    assert SE.contains_stop_treatment_language("replace your prescribed treatment")
    assert not SE.contains_stop_treatment_language("discuss options with your clinician")


def test_envelope_rejects_stop_treatment_in_raw_text():
    env = SE.PracticeSafetyEnvelope(
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
        raw_text="you can stop prescribed treatment and use this instead",
    )
    with pytest.raises(SE.StopTreatmentRecommendationError):
        SE.validate_envelope(env)


def test_envelope_requires_consent_reversibility_stop_referral():
    env = SE.PracticeSafetyEnvelope(
        educational_vs_individualized="educational",
        intended_population="general adults",
        exclusion_criteria="none known",
        contraindications="none known",
        risk_severity="low",
        informed_consent_required=False,  # missing
        dependency_coercion_risk="low",
        stop_conditions="UNKNOWN",  # missing
        rollback_exit_path="stop practice",
        professional_referral_boundary="UNKNOWN",  # missing
        emergency_boundary="call emergency services",
        interaction_with_existing_care="coordinate with provider",
        evidence_grade="low",
        unknowns=["long-term data"],
        long_term_followup_plan="annual review",
    )
    with pytest.raises(SE.EnvelopeIncompleteError):
        SE.validate_envelope(env)


# ===========================================================================
# G. Non-impact proof (task §13)
# ===========================================================================
def test_non_impact_proof_has_all_twelve_items():
    proof = NI.build_non_impact_proof()
    assert len(proof["items"]) == len(NI.NON_IMPACT_ITEMS)
    assert NI.proof_items_consistent(proof)


@pytest.mark.parametrize("item", NI.NON_IMPACT_ITEMS)
def test_non_impact_item_not_altered(item):
    proof = NI.build_non_impact_proof()
    match = next(i for i in proof["items"] if i["item"] == item)
    assert match["status"] == "NOT_ALTERED_BY_R5A"


# ===========================================================================
# H. Candidate-only manifest flags
# ===========================================================================
def test_manifest_carries_all_required_flags():
    for flag in manifest.MANIFEST_REQUIRED_FLAGS:
        assert flag in manifest.CANDIDATE_MANIFEST


def test_manifest_is_candidate_only_and_non_activating():
    assert manifest.manifest_flags_consistent()
    m = manifest.CANDIDATE_MANIFEST
    assert m["activation_status"] == "CANDIDATE_ONLY"
    assert m["human_intervention_enabled"] is False
    assert m["medical_claims_authorized"] is False
    assert m["modern_wuzhen_pack_started"] is False
    assert m["domain_pack_federation_started"] is False
    assert m["external_acceptance_claimed"] is False


# ===========================================================================
# I. Normative / empirical type-tag closed set (no silent conflation)
# ===========================================================================
def test_type_tag_closed_set_has_exactly_ten():
    assert len(R.NORMATIVE_EMPIRICAL_TYPE_TAGS) == 10


@pytest.mark.parametrize("tag", R.NORMATIVE_EMPIRICAL_TYPE_TAGS)
def test_each_type_tag_is_valid(tag):
    assert R.is_valid_type_tag(tag)


def test_unknown_type_tag_rejected():
    assert not R.is_valid_type_tag("FAKE_TAG")


# ===========================================================================
# J. No religion automatically endorsed or dismissed; no Zhang Boduan clinical
#    authority; no private content leakage in source
# ===========================================================================
def test_source_has_no_clinical_authority_claim_for_zhang_boduan():
    base = os.path.dirname(__file__)
    pkg_root = os.path.join(os.path.dirname(os.path.dirname(base)), "life_integrity_r5a")
    text = ""
    for fn in os.listdir(pkg_root):
        if fn.endswith(".py"):
            text += open(os.path.join(pkg_root, fn), encoding="utf-8").read()
    lowered = text.lower()
    # The package never asserts Zhang Boduan / South-School is clinically effective.
    assert "clinically effective" not in lowered
    assert "clinical authority" not in lowered


def test_source_never_endorses_or_dismisses_religion():
    base = os.path.dirname(__file__)
    pkg_root = os.path.join(os.path.dirname(os.path.dirname(base)), "life_integrity_r5a")
    text = ""
    for fn in os.listdir(pkg_root):
        if fn.endswith(".py"):
            text += open(os.path.join(pkg_root, fn), encoding="utf-8").read()
    lowered = text.lower()
    assert "all religions are true" not in lowered
    assert "religion is false" not in lowered
    assert "scientifically supported religion" not in lowered


def test_package_source_contains_no_private_leak_markers():
    base = os.path.dirname(__file__)
    pkg_root = os.path.join(os.path.dirname(os.path.dirname(base)), "life_integrity_r5a")
    text = ""
    for fn in os.listdir(pkg_root):
        if fn.endswith(".py"):
            text += open(os.path.join(pkg_root, fn), encoding="utf-8").read()
    # No private-note / personal-health leakage markers in the candidate source.
    assert "private_note" not in text
    assert "personal_health_record" not in text


# ===========================================================================
# K. Repository tests never assert human efficacy / clinical effectiveness
# ===========================================================================
def test_package_source_never_asserts_human_efficacy():
    base = os.path.dirname(__file__)
    pkg_root = os.path.join(os.path.dirname(os.path.dirname(base)), "life_integrity_r5a")
    text = ""
    for fn in os.listdir(pkg_root):
        if fn.endswith(".py"):
            text += open(os.path.join(pkg_root, fn), encoding="utf-8").read().lower()
    # The candidate package must never assert tests prove human safety /
    # clinical effectiveness. (Scanning the package, not this test file, avoids
    # self-reference with the assertion text.)
    assert "proves human" not in text
    assert "demonstrates clinical efficacy" not in text
    assert "validates human safety" not in text
    assert "tests prove" not in text


# ===========================================================================
# L. Aggregate validator entry point (implemented in Commit 4)
# ===========================================================================
def test_validate_all_runs_and_is_deterministic():
    ok, failures = validators.validate_all()
    assert ok, failures
    ok2, failures2 = validators.validate_all()
    assert failures == failures2
