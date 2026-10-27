#!/usr/bin/env python3
"""repair-r3 per-capability semantic evaluator specifications.

This module is the SINGLE source of truth for wiring each of the 9 capability
gates to the shared evaluator primitive in ``semantic_evaluator.semantic_evaluate``.

For every capability we provide:
  * ``matrix``  – rule_id -> {"roles":[allowed declared_role], "types":[allowed record_type]}
                 (the req-6 evidence role/type matrix; defeats cross-evidence laundering)
  * ``rule_fields`` – rule_id -> the primary boundedField whose ``value`` must be
                 corroborated by evidence bytes for that rule.

The role/type vocabularies are taken verbatim from the Semantic Contract
Architect's ``SEMANTIC_EVALUATOR_ARCHITECTURE.json`` (per_capability_matrix).
Every rule is grounded in the capability's EXISTING ``fields`` (no fabricated
record/schema fields). The evaluator recomputes each rule from ``records``
values + evidence bytes; caller ``facts`` / ``rule_assertions[].status`` are
declarations only and are never trusted.

Each capability exposes ``evaluate_<cap>(bundle, config, evidence)`` (req-7
hook) so the gate file can bind ``CONFIG["evaluator"] = evaluate_<cap>``.
"""
from tools.governance.semantic_evaluator import semantic_evaluate

CAPABILITY_SPECS = {
    "decision_integrity": {
        "matrix": {
            "success_not_process_proof": {"roles": ["PROCESS_QUALITY_EVIDENCE", "OUTCOME_QUALITY_EVIDENCE"], "types": ["structured_record", "text"]},
            "failure_not_process_disproof": {"roles": ["PROCESS_QUALITY_EVIDENCE"], "types": ["structured_record"]},
            "ex_ante_record_immutable": {"roles": ["EX_ANTE_DECISION_RECORD"], "types": ["text", "json"]},
            "principle_relabel_blocked": {"roles": ["PRINCIPLE_REGISTRY"], "types": ["structured_record"]},
            "competence_required": {"roles": ["COMPETENCE_BOUNDARY"], "types": ["structured_record"]},
            "utility_before_bargain": {"roles": ["UTILITY_BARGAIN_RECORD"], "types": ["structured_record"]},
            "fomo_not_need": {"roles": ["UTILITY_BARGAIN_RECORD"], "types": ["structured_record"]},
            "intake_not_integration": {"roles": ["INTAKE_INTEGRATION_LOG"], "types": ["structured_record"]},
            "integration_requires_output": {"roles": ["INTAKE_INTEGRATION_LOG"], "types": ["structured_record"]},
            "revision_versioned_authorized": {"roles": ["REVISION_AUTHORITY"], "types": ["structured_record"]},
            "original_record_preserved": {"roles": ["EX_ANTE_DECISION_RECORD"], "types": ["text", "json"]},
            "claim_ceiling_preserved": {"roles": ["PROCESS_QUALITY_EVIDENCE"], "types": ["text"]},
        },
        "rule_fields": {
            "success_not_process_proof": "process_outcome_quadrant",
            "failure_not_process_disproof": "post_hoc_narrative_diff",
            "ex_ante_record_immutable": "ex_ante_decision_record",
            "principle_relabel_blocked": "principle_version",
            "competence_required": "competence_boundary",
            "utility_before_bargain": "usefulness_necessity_gate",
            "fomo_not_need": "bargain_fomo_signal",
            "intake_not_integration": "information_intake",
            "integration_requires_output": "integration_evidence",
            "revision_versioned_authorized": "legitimate_revision",
            "original_record_preserved": "principle_capture",
            "claim_ceiling_preserved": "claim_ceiling",
        },
    },
    "epistemic_state_control_plane": {
        "matrix": {
            "self_rating_not_evidence": {"roles": ["EPISTEMIC_LEDGER"], "types": ["structured_record"]},
            "unknown_needs_evidence_transition": {"roles": ["UNKNOWN_REGISTER", "EPISTEMIC_LEDGER"], "types": ["structured_record"]},
            "non_identifiable_not_solved": {"roles": ["CANDIDATE_HYPOTHESIS"], "types": ["structured_record"]},
            "dominant_view_not_fact": {"roles": ["EPISTEMIC_LEDGER"], "types": ["structured_record"]},
            "good_outcome_not_bad_process_erasure": {"roles": ["EPISTEMIC_LEDGER"], "types": ["structured_record"]},
            "failure_changes_plan": {"roles": ["FEEDBACK_TRANSITION"], "types": ["structured_record"]},
            "retracted_not_active": {"roles": ["RETRACTED_STATE"], "types": ["structured_record"]},
            "plan_authorized_and_stopped": {"roles": ["ACQUISITION_PLAN"], "types": ["structured_record"]},
            "exploration_bounded": {"roles": ["ACQUISITION_PLAN"], "types": ["structured_record"]},
            "cost_risk_present": {"roles": ["ACQUISITION_PLAN"], "types": ["structured_record"]},
            "ceiling_noninflation": {"roles": ["EPISTEMIC_LEDGER"], "types": ["text"]},
            "no_circular_evidence": {"roles": ["EPISTEMIC_LEDGER"], "types": ["structured_record"]},
        },
        "rule_fields": {
            "self_rating_not_evidence": "committed_knowledge",
            "unknown_needs_evidence_transition": "insufficient_evidence",
            "non_identifiable_not_solved": "non_identifiable",
            "dominant_view_not_fact": "epistemic_state_ledger",
            "good_outcome_not_bad_process_erasure": "conflicts",
            "failure_changes_plan": "unresolved_failures",
            "retracted_not_active": "retracted_states",
            "plan_authorized_and_stopped": "authorized_acquisition_plan",
            "exploration_bounded": "cost_risk_time_priority",
            "cost_risk_present": "next_action_type",
            "ceiling_noninflation": "claim_ceiling",
            "no_circular_evidence": "epistemic_state_ledger",
        },
    },
    "world_feedback_anomaly": {
        "matrix": {
            "anomaly_not_hidden_system": {"roles": ["ANOMALY_LOG"], "types": ["structured_record"]},
            "recurrence_required": {"roles": ["RESIDUAL_AGGREGATION", "DIVERGENCE_RECORD"], "types": ["structured_record"]},
            "threshold_declared": {"roles": ["THRESHOLD_SOURCE"], "types": ["structured_record"]},
            "single_deviation_no_rebuild": {"roles": ["DIVERGENCE_RECORD"], "types": ["structured_record"]},
            "repair_budget_bounded": {"roles": ["REPAIR_BUDGET"], "types": ["structured_record"]},
            "authority_required": {"roles": ["ESCALATION_AUTHORITY"], "types": ["structured_record"]},
            "stop_rollback_present": {"roles": ["ANOMALY_LOG"], "types": ["structured_record"]},
            "failure_sampling_balanced": {"roles": ["FAILURE_SAMPLE"], "types": ["structured_record"]},
            "q39_updated": {"roles": ["DIVERGENCE_RECORD"], "types": ["structured_record"]},
            "metacognition_updated": {"roles": ["DIVERGENCE_RECORD"], "types": ["structured_record"]},
        },
        "rule_fields": {
            "anomaly_not_hidden_system": "world_feedback_anomaly",
            "recurrence_required": "recurrence_window",
            "threshold_declared": "escalation_authority",
            "single_deviation_no_rebuild": "expected_observed_divergence",
            "repair_budget_bounded": "model_repair_budget",
            "authority_required": "governance_decision",
            "stop_rollback_present": "stop_rollback",
            "failure_sampling_balanced": "residual_failure_aggregation",
            "q39_updated": "q39_update",
            "metacognition_updated": "metacognition_update",
        },
    },
    "latent_system_identifiability": {
        "matrix": {
            "residual_not_entity": {"roles": ["LATENT_CANDIDATE"], "types": ["structured_record"]},
            "pattern_not_common_cause": {"roles": ["ANCESTOR_GRAPH"], "types": ["structured_record"]},
            "equivalent_decompositions_preserved": {"roles": ["EQUIVALENT_DECOMPOSITION"], "types": ["structured_record"]},
            "distinguishing_evidence_required": {"roles": ["DISTINGUISHING_EVIDENCE"], "types": ["structured_record"]},
            "non_identifiable_stays_unresolved": {"roles": ["LATENT_CANDIDATE"], "types": ["structured_record"]},
            "contradictions_preserved": {"roles": ["CONTRADICTION_REGISTER"], "types": ["structured_record"]},
            "unsupported_not_promoted": {"roles": ["UNSUPPORTED_REGISTER"], "types": ["structured_record"]},
            "claim_ceiling_preserved": {"roles": ["LATENT_CANDIDATE"], "types": ["text"]},
        },
        "rule_fields": {
            "residual_not_entity": "latent_system_candidate",
            "pattern_not_common_cause": "cross_system_ancestor_graph",
            "equivalent_decompositions_preserved": "equivalent_decompositions",
            "distinguishing_evidence_required": "distinguishing_evidence_request",
            "non_identifiable_stays_unresolved": "candidate_status",
            "contradictions_preserved": "contradictions",
            "unsupported_not_promoted": "unsupported_elements",
            "claim_ceiling_preserved": "claim_ceiling",
        },
    },
    "multi_history_world_projection": {
        "matrix": {
            "every_world_evidence_bound": {"roles": ["SHARED_EVIDENCE", "WORLD_CANDIDATE"], "types": ["structured_record"]},
            "no_forced_unique_story": {"roles": ["WORLD_CANDIDATE"], "types": ["structured_record"]},
            "indistinguishable_not_ranked_fact": {"roles": ["INDISTINGUISHABLE_SET"], "types": ["structured_record"]},
            "weights_need_justification": {"roles": ["WEIGHT_JUSTIFICATION"], "types": ["structured_record"]},
            "possibility_not_probability": {"roles": ["WORLD_CANDIDATE"], "types": ["structured_record"]},
            "falsifier_required": {"roles": ["FALSIFIER"], "types": ["structured_record"]},
            "unresolved_paths_preserved": {"roles": ["UNRESOLVED_PATH"], "types": ["structured_record"]},
            "narrative_ceiling_preserved": {"roles": ["WORLD_CANDIDATE"], "types": ["text"]},
        },
        "rule_fields": {
            "every_world_evidence_bound": "shared_evidence",
            "no_forced_unique_story": "world_candidates",
            "indistinguishable_not_ranked_fact": "indistinguishable_set",
            "weights_need_justification": "justified_weights",
            "possibility_not_probability": "world_candidates",
            "falsifier_required": "falsifiers",
            "unresolved_paths_preserved": "unresolved_paths",
            "narrative_ceiling_preserved": "narrative_ceiling",
        },
    },
    "counterfactual_unrealized_path": {
        "matrix": {
            "types_separated": {"roles": ["COUNTERFACTUAL"], "types": ["structured_record"]},
            "identifiability_gate_required": {"roles": ["IDENTIFIABILITY_STATUS"], "types": ["structured_record"]},
            "unobservable_not_promoted": {"roles": ["IDENTIFIABILITY_STATUS"], "types": ["structured_record"]},
            "evidence_required": {"roles": ["BASELINE", "ALTERED_CONDITION"], "types": ["structured_record"]},
            "intervention_difference_explicit": {"roles": ["ALTERED_CONDITION"], "types": ["structured_record"]},
            "speculation_labeled": {"roles": ["SPECULATIVE_NARRATIVE"], "types": ["structured_record"]},
            "no_if_then_causal_upgrade": {"roles": ["COUNTERFACTUAL"], "types": ["structured_record"]},
            "claim_ceiling_preserved": {"roles": ["COUNTERFACTUAL"], "types": ["text"]},
        },
        "rule_fields": {
            "types_separated": "counterfactuals",
            "identifiability_gate_required": "identifiability_status",
            "unobservable_not_promoted": "unobservable_portion",
            "evidence_required": "evidence",
            "intervention_difference_explicit": "intervention_differences",
            "speculation_labeled": "speculative_narratives",
            "no_if_then_causal_upgrade": "counterfactuals",
            "claim_ceiling_preserved": "claim_ceiling",
        },
    },
    "graded_intervention_escalation": {
        "matrix": {
            "risk_class_required": {"roles": ["RISK_CLASS"], "types": ["structured_record"]},
            "reversibility_required": {"roles": ["REVERSIBILITY"], "types": ["structured_record"]},
            "evidence_grade_required": {"roles": ["EVIDENCE_GRADE"], "types": ["structured_record"]},
            "authority_required": {"roles": ["AUTHORITY"], "types": ["structured_record"]},
            "expertise_boundary_enforced": {"roles": ["EXPERTISE"], "types": ["structured_record"]},
            "automatic_only_repository_local": {"roles": ["REPOSITORY_LOCAL_ACTION"], "types": ["structured_record"]},
            "confirmation_for_external": {"roles": ["CONFIRMATION"], "types": ["structured_record"]},
            "high_risk_request_only": {"roles": ["HIGH_RISK_REQUEST"], "types": ["structured_record"]},
            "prohibited_never_executed": {"roles": ["PROHIBITED_ACTION"], "types": ["structured_record"]},
            "stop_rollback_return_present": {"roles": ["STOP_ROLLBACK"], "types": ["structured_record"]},
        },
        "rule_fields": {
            "risk_class_required": "action_risk_class",
            "reversibility_required": "reversibility",
            "evidence_grade_required": "evidence_grade",
            "authority_required": "authority",
            "expertise_boundary_enforced": "expertise_requirement",
            "automatic_only_repository_local": "automatic_repository_local_action",
            "confirmation_for_external": "user_confirmation_required",
            "high_risk_request_only": "request_only_external_action",
            "prohibited_never_executed": "prohibited_action",
            "stop_rollback_return_present": "stop_rollback_result_return",
        },
    },
    "coaching_commitment_subcapability": {
        "matrix": {
            "goal_user_declared": {"roles": ["USER_GOAL"], "types": ["structured_record"]},
            "commitment_informed": {"roles": ["INFORMED_COMMITMENT"], "types": ["structured_record"]},
            "consent_reversible": {"roles": ["REVISE_PAUSE_STOP"], "types": ["structured_record"]},
            "no_goal_substitution": {"roles": ["USER_GOAL"], "types": ["structured_record"]},
            "no_shame_pressure": {"roles": ["SUPPORT_OPTION"], "types": ["structured_record"]},
            "multiple_narratives_preserved": {"roles": ["NARRATIVE_SET"], "types": ["structured_record"]},
            "process_outcome_separate": {"roles": ["USER_GOAL"], "types": ["structured_record"]},
            "support_not_control": {"roles": ["SUPPORT_OPTION"], "types": ["structured_record"]},
            "escalation_boundary_enforced": {"roles": ["ESCALATION_BOUNDARY"], "types": ["structured_record"]},
        },
        "rule_fields": {
            "goal_user_declared": "user_declared_goal",
            "commitment_informed": "informed_commitment",
            "consent_reversible": "revise_pause_stop",
            "no_goal_substitution": "user_declared_goal",
            "no_shame_pressure": "support_options",
            "multiple_narratives_preserved": "multi_perspective_narrative",
            "process_outcome_separate": "outcome_process_separation",
            "support_not_control": "support_options",
            "escalation_boundary_enforced": "escalation",
        },
    },
    "open_scientific_context_protocol": {
        "matrix": {
            "version_negotiated": {"roles": ["PROTOCOL_VERSION"], "types": ["structured_record"]},
            "identity_authorized": {"roles": ["IDENTITY_AUTH"], "types": ["structured_record"]},
            "capability_not_authority": {"roles": ["CAPABILITY_RECORD"], "types": ["structured_record"]},
            "artifact_exact_head_bound": {"roles": ["ARTIFACT_BINDING"], "types": ["structured_record"]},
            "rights_preserved": {"roles": ["RIGHTS_CONTEXT"], "types": ["structured_record"]},
            "failure_retry_typed": {"roles": ["FAILURE_RETRY"], "types": ["structured_record"]},
            "compatibility_fail_closed": {"roles": ["COMPAT_POLICY"], "types": ["structured_record"]},
            "sensitive_local_first": {"roles": ["SENSITIVE_LOCAL"], "types": ["structured_record"]},
            "hardware_request_only": {"roles": ["HARDWARE_REQUEST"], "types": ["structured_record"]},
            "no_ecosystem_overclaim": {"roles": ["CAPABILITY_RECORD"], "types": ["text"]},
            "stop_rollback_present": {"roles": ["STOP_ROLLBACK"], "types": ["structured_record"]},
        },
        "rule_fields": {
            "version_negotiated": "protocol_version",
            "identity_authorized": "identity_authorization",
            "capability_not_authority": "authority_capability",
            "artifact_exact_head_bound": "artifact_binding",
            "rights_preserved": "source_rights_context",
            "failure_retry_typed": "failure_retry_semantics",
            "compatibility_fail_closed": "compatibility_policy",
            "sensitive_local_first": "sensitive_data_network_local_first",
            "hardware_request_only": "experiment_hardware_request_result",
            "no_ecosystem_overclaim": "capability_negotiation",
            "stop_rollback_present": "stop_rollback",
        },
    },
}


def _make_evaluator(cap):
    spec = CAPABILITY_SPECS[cap]

    def _evaluate(bundle, config, evidence):
        return semantic_evaluate(bundle, config, evidence, spec["matrix"], spec["rule_fields"])

    _evaluate.__name__ = "evaluate_" + cap
    return _evaluate


# Public API: a ready-to-bind callable per capability.
EVALUATORS = {cap: _make_evaluator(cap) for cap in CAPABILITY_SPECS}

# Also expose legacy attribute-style names for clarity in gate files.
evaluate_decision_integrity = EVALUATORS["decision_integrity"]
evaluate_epistemic_state_control_plane = EVALUATORS["epistemic_state_control_plane"]
evaluate_world_feedback_anomaly = EVALUATORS["world_feedback_anomaly"]
evaluate_latent_system_identifiability = EVALUATORS["latent_system_identifiability"]
evaluate_multi_history_world_projection = EVALUATORS["multi_history_world_projection"]
evaluate_counterfactual_unrealized_path = EVALUATORS["counterfactual_unrealized_path"]
evaluate_graded_intervention_escalation = EVALUATORS["graded_intervention_escalation"]
evaluate_coaching_commitment_subcapability = EVALUATORS["coaching_commitment_subcapability"]
evaluate_open_scientific_context_protocol = EVALUATORS["open_scientific_context_protocol"]


def get_matrix(cap):
    return CAPABILITY_SPECS[cap]["matrix"]


def get_evaluator(cap):
    return EVALUATORS[cap]
