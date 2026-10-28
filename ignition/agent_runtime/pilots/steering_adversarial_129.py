"""Adversarial matrix for IGNITION-129 steering boundaries."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from agent_runtime.namespace import DelegationGrant, NamespaceBinding, NamespaceGuard, NamespaceIsolationError, PrincipalIdentity, PrincipalRegistry
from agent_runtime.steering import (
    AuthorityProvenance,
    CompletionContract,
    ConflictArbiter,
    ConflictCandidate,
    DependencyEdge,
    DriftReport,
    GoalDependencyGraph,
    GoalDriftGuard,
    GoalEpisodeBinder,
    GoalRecord,
    GraphNode,
    IntentCapsule,
    IntentRecord,
    IntentRegistry,
    MemoryProfileBoundary,
    MemoryProfileObservation,
    OwnerOverride,
    PriorityInputs,
    PriorityPolicy,
    SteeringDurabilityAdapter,
    SteeringNamespaceGuard,
    SteeringScope,
    SteeringState,
    SteeringValidationError,
    TemporalWindow,
    build_intent_capsule,
    evaluate_completion,
    evaluate_temporal,
)


ADVERSARIAL_SCHEMA = "os-steering-intent-obligation-r1.adversarial-matrix"
NOW = "2026-08-21T12:00:00+08:00"
ALLOWED_OUTCOMES = frozenset({"FAIL_CLOSED", "RECONCILIATION_REQUIRED", "HUMAN_REVIEW", "PAUSE_RECONCILE", "PASS_GUARD"})


def _owner() -> AuthorityProvenance:
    return AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-adversarial-owner", "synthetic adversarial authority", authorized=True)


def _goal(*, source: str = "OWNER_DECLARED", status: str = "ACTIVE") -> tuple[IntentRecord, GoalRecord, CompletionContract, AuthorityProvenance]:
    owner = _owner()
    provenance = owner if source == "OWNER_DECLARED" else AuthorityProvenance(source, "system.synthetic", "auth-adversarial-proposal", "synthetic proposal", authorized=False)
    intent = IntentRecord("intent-adversarial", "Adversarial synthetic direction", "adversarial.synthetic", provenance, status=status if source == "OWNER_DECLARED" else "PROPOSED", created_at=NOW, updated_at=NOW)
    contract = CompletionContract("contract-adversarial", ("predicate-a",), ("EVIDENCE_A",), "OWNER_ONLY", ("run_pass", "episode_pass"))
    goal = GoalRecord("goal-adversarial", intent.intent_id, "Adversarial synthetic Goal", "adversarial.synthetic", contract.contract_id, provenance, status=status, created_at=NOW, updated_at=NOW)
    return intent, goal, contract, owner


def _namespace_setup() -> tuple[SteeringNamespaceGuard, NamespaceBinding, SteeringScope, NamespaceBinding, SteeringScope, DelegationGrant]:
    registry = PrincipalRegistry()
    registry.register(PrincipalIdentity("principal-a", "OPERATOR", "system-root"))
    registry.register(PrincipalIdentity("principal-b", "OPERATOR", "system-root"))
    guard = SteeringNamespaceGuard(NamespaceGuard(registry))
    a = NamespaceBinding("ns-a", "principal-a", "workspace-a", "episode-a", "run-a", "memory-a", "pack-a", "lease-a", "snapshot-a", "soft-a")
    b = NamespaceBinding("ns-b", "principal-b", "workspace-b", "episode-b", "run-b", "memory-b", "pack-b", "lease-b", "snapshot-b", "soft-b")
    scope_a = SteeringScope("scope-a", "ns-a", goal_ids=("goal-adversarial",), intent_ids=("intent-adversarial",), shared_scope_ref="shared-adversarial")
    scope_b = SteeringScope("scope-b", "ns-b", goal_ids=("goal-adversarial",), intent_ids=("intent-adversarial",), shared_scope_ref="shared-adversarial")
    grant = DelegationGrant("grant-adversarial", "ns-a", "ns-b", "principal-a", "principal-b", ("steering.goal.read",), 200.0, "approval-adversarial", "a" * 64)
    return guard, a, scope_a, b, scope_b, grant


def run_adversarial_matrix() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def add(case_id: str, expected: str, action: Callable[[], tuple[str, str]]) -> None:
        try:
            observed, evidence = action()
        except Exception as exc:  # unexpected exceptions are themselves visible evidence
            observed, evidence = "UNEXPECTED_ERROR", type(exc).__name__
        cases.append({"case_id": case_id, "expected_outcome": expected, "observed_outcome": observed, "evidence": evidence, "passed": observed == expected})

    add("run-pass-not-completion", "FAIL_CLOSED", lambda: ("FAIL_CLOSED", evaluate_completion(_goal()[1], _goal()[2], {"run_pass": True}, authority=_owner(), decided_at=NOW).outcome) if evaluate_completion(_goal()[1], _goal()[2], {"run_pass": True}, authority=_owner(), decided_at=NOW).outcome == "UNVERIFIABLE" else ("UNEXPECTED", "run_pass"))
    add("forbidden-shortcut-completion", "FAIL_CLOSED", lambda: ("FAIL_CLOSED", evaluate_completion(_goal()[1], _goal()[2], {"predicate_results": {"predicate-a": True}, "evidence_types": ["EVIDENCE_A"], "shortcut_flags": ["run_pass"]}, authority=_owner(), decided_at=NOW).outcome) if evaluate_completion(_goal()[1], _goal()[2], {"predicate_results": {"predicate-a": True}, "evidence_types": ["EVIDENCE_A"], "shortcut_flags": ["run_pass"]}, authority=_owner(), decided_at=NOW).outcome == "REJECTED" else ("UNEXPECTED", "shortcut"))
    add("permission-overdue", "FAIL_CLOSED", lambda: ("FAIL_CLOSED", "permission_ineligible") if not PriorityPolicy().evaluate(PriorityInputs("goal-adversarial", 0, deadline_state="OVERDUE", permission_eligible=False)).eligible else ("UNEXPECTED", "permission"))
    add("blocked-high-risk", "FAIL_CLOSED", lambda: ("FAIL_CLOSED", "blocked") if not PriorityPolicy().evaluate(PriorityInputs("goal-adversarial", 0, risk_level="HIGH", blocked=True, approval_required=True)).eligible else ("UNEXPECTED", "blocked"))
    add("unknown-temporal", "RECONCILIATION_REQUIRED", lambda: ("RECONCILIATION_REQUIRED", evaluate_temporal(TemporalWindow("window-adversarial", "UTC", "OWNER_DECLARED", "owner.synthetic", unknown_time=True), now=NOW).state) if evaluate_temporal(TemporalWindow("window-adversarial", "UTC", "OWNER_DECLARED", "owner.synthetic", unknown_time=True), now=NOW).state == "UNKNOWN" else ("UNEXPECTED", "temporal"))

    def goal_episode_mixup() -> tuple[str, str]:
        _, goal, _, _ = _goal()
        binder = GoalEpisodeBinder()
        binding = binder.bind(goal, "episode-adversarial", ("run-adversarial",), created_at=NOW)
        try:
            binder.record_run_outcome(binding.binding_id, "run-other", "PASS", updated_at=NOW)
        except SteeringValidationError:
            return "FAIL_CLOSED", "run_outside_binding"
        return "UNEXPECTED", "run_outside_binding"
    add("goal-episode-mixup", "FAIL_CLOSED", goal_episode_mixup)

    def drift_objective() -> tuple[str, str]:
        _, goal, _, _ = _goal()
        report = GoalDriftGuard().inspect("drift-adversarial", goal, "a" * 64, ("criterion-a",), ("criterion-a",), created_at=NOW)
        return report.outcome, ",".join(report.reasons)
    add("objective-drift", "PAUSE_RECONCILE", drift_objective)
    add("acceptance-loss", "PAUSE_RECONCILE", lambda: (lambda report: (report.outcome, ",".join(report.reasons)))(GoalDriftGuard().inspect("drift-acceptance", _goal()[1], _goal()[1].objective_digest(), ("criterion-a", "criterion-b"), ("criterion-a",), created_at=NOW)))
    add("proposal-owner-escalation", "HUMAN_REVIEW", lambda: (lambda report: (report.outcome, ",".join(report.reasons)))(GoalDriftGuard().inspect("drift-escalation", _goal(source="SYSTEM_DERIVED_PROPOSAL")[1], _goal(source="SYSTEM_DERIVED_PROPOSAL")[1].objective_digest(), (), (), observed_provenance=_owner(), created_at=NOW)))
    add("memory-canonical-conflict", "PASS_GUARD", lambda: (lambda decision: ("PASS_GUARD", ",".join(decision.reasons)) if decision.decision == "CANONICAL_INTENT_WINS" else ("UNEXPECTED", decision.decision))(MemoryProfileBoundary().evaluate(MemoryProfileObservation("memory-adversarial", "OPERATIONAL_MEMORY", "stale synthetic memory", "old direction", True, True, True, NOW), canonical_intent=_goal()[0])))
    add("superseded-intent", "RECONCILIATION_REQUIRED", lambda: (lambda receipt: (receipt.outcome, ",".join(receipt.reasons)))(ConflictArbiter().arbitrate("arb-superseded", "SUPERSEDED_INTENT", (ConflictCandidate(PriorityInputs("goal-adversarial", 0), intent_status="SUPERSEDED", superseded=True),), created_at=NOW)))
    add("executor-unavailable", "RECONCILIATION_REQUIRED", lambda: (lambda receipt: (receipt.outcome, ",".join(receipt.reasons)))(ConflictArbiter().arbitrate("arb-executor", "EXECUTOR_UNAVAILABLE", (ConflictCandidate(PriorityInputs("goal-adversarial", 0), executor_available=False),), created_at=NOW)))

    def namespace_no_grant() -> tuple[str, str]:
        guard, a, scope_a, b, scope_b, _ = _namespace_setup()
        try:
            guard.authorize(a, scope_a, b, scope_b, record_kind="goal", record_id="goal-adversarial", action="read", now=100.0)
        except NamespaceIsolationError:
            return "FAIL_CLOSED", "delegation_required"
        return "UNEXPECTED", "delegation_required"
    add("namespace-no-delegation", "FAIL_CLOSED", namespace_no_grant)

    def namespace_canonical_write() -> tuple[str, str]:
        guard, a, scope_a, b, scope_b, grant = _namespace_setup()
        try:
            guard.authorize(a, scope_a, b, scope_b, record_kind="intent", record_id="intent-adversarial", action="canonical_write", now=100.0, delegation=grant)
        except NamespaceIsolationError:
            return "FAIL_CLOSED", "canonical_write_denied"
        return "UNEXPECTED", "canonical_write_denied"
    add("namespace-canonical-write", "FAIL_CLOSED", namespace_canonical_write)

    def capsule_mutation() -> tuple[str, str]:
        intent, goal, _, _ = _goal()
        capsule = build_intent_capsule(intent, goal, success_criteria=("criterion-a",), permission_summary=("repo.read",), report_contract_refs=("report-adversarial",), created_at=NOW)
        try:
            replace(capsule, executor_can_mutate_canonical=True)
        except SteeringValidationError:
            return "FAIL_CLOSED", "executor_can_mutate_canonical_false"
        return "UNEXPECTED", "capsule_mutation"
    add("capsule-canonical-mutation", "FAIL_CLOSED", capsule_mutation)

    def graph_cycle() -> tuple[str, str]:
        graph = GoalDependencyGraph((GraphNode("goal-a", "GOAL", "ns-a"), GraphNode("goal-b", "GOAL", "ns-a")))
        graph.add_edge(DependencyEdge("edge-a", "goal-a", "goal-b", "PREREQUISITE", "a-before-b"))
        try:
            graph.add_edge(DependencyEdge("edge-b", "goal-b", "goal-a", "PREREQUISITE", "b-before-a"))
        except Exception:
            return "FAIL_CLOSED", "dependency_cycle"
        return "UNEXPECTED", "dependency_cycle"
    add("goal-graph-cycle", "FAIL_CLOSED", graph_cycle)

    def proposal_promotion() -> tuple[str, str]:
        proposal = IntentRecord("intent-proposal-adversarial", "Proposal only", "adversarial.synthetic", AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "system.synthetic", "auth-proposal", "proposal"), status="PROPOSED", created_at=NOW, updated_at=NOW)
        registry = IntentRegistry((proposal,))
        try:
            registry.transition(proposal.intent_id, "ACTIVE", provenance=proposal.provenance, reason="attempted promotion", updated_at=NOW)
        except Exception:
            return "FAIL_CLOSED", "proposal_promotion_denied"
        return "UNEXPECTED", "proposal_promotion"
    add("proposal-promotion", "FAIL_CLOSED", proposal_promotion)

    def private_durability_field() -> tuple[str, str]:
        try:
            SteeringState(intents=({"prompt_body": "private"},))
        except SteeringValidationError:
            return "FAIL_CLOSED", "private_field_denied"
        return "UNEXPECTED", "private_field"
    add("durability-private-field", "FAIL_CLOSED", private_durability_field)

    add("external-self-completion", "FAIL_CLOSED", lambda: ("FAIL_CLOSED", evaluate_completion(_goal()[1], _goal()[2], {"predicate_results": {"predicate-a": True}, "evidence_types": ["EVIDENCE_A"]}, authority=AuthorityProvenance("EXTERNAL_REQUESTED_PROPOSAL", "external.synthetic", "external-1", "external report"), decided_at=NOW).outcome) if evaluate_completion(_goal()[1], _goal()[2], {"predicate_results": {"predicate-a": True}, "evidence_types": ["EVIDENCE_A"]}, authority=AuthorityProvenance("EXTERNAL_REQUESTED_PROPOSAL", "external.synthetic", "external-1", "external report"), decided_at=NOW).outcome == "UNVERIFIABLE" else ("UNEXPECTED", "external_authority"))
    add("unknown-owner-rank", "RECONCILIATION_REQUIRED", lambda: ("RECONCILIATION_REQUIRED", "unknown_inputs_preserved") if "unknown_inputs_preserved" in PriorityPolicy().evaluate(PriorityInputs("goal-adversarial", None, unknowns=("owner_rank",))).reasons else ("UNEXPECTED", "unknown_owner_rank"))

    def score_not_authority() -> tuple[str, str]:
        first, second = PriorityPolicy().order((PriorityInputs("goal-score-a", 0), PriorityInputs("goal-score-b", 1, fairness_age=100000)))
        return ("PASS_GUARD", "lexicographic_key_wins_over_telemetry") if first.goal_id == "goal-score-a" and first.authority == "LEXICOGRAPHIC_RULES_R1" else ("UNEXPECTED", "score_authority")
    add("telemetry-score-not-authority", "PASS_GUARD", score_not_authority)

    def expired_delegation() -> tuple[str, str]:
        guard, a, scope_a, b, scope_b, grant = _namespace_setup()
        try:
            expired = replace(grant, expires_at=1.0, grant_digest=None)
            guard.authorize(a, scope_a, b, scope_b, record_kind="goal", record_id="goal-adversarial", action="read", now=100.0, delegation=expired)
        except NamespaceIsolationError:
            return "FAIL_CLOSED", "expired_delegation_denied"
        return "UNEXPECTED", "expired_delegation"
    add("expired-delegation", "FAIL_CLOSED", expired_delegation)

    return {"schema": ADVERSARIAL_SCHEMA, "case_count": len(cases), "cases": cases, "all_pass": all(case["passed"] for case in cases), "allowed_outcomes": sorted(ALLOWED_OUTCOMES), "claim_ceiling": "Adversarial repository-local boundary tests only; no live safety or external truth is established."}


__all__ = ["ADVERSARIAL_SCHEMA", "ALLOWED_OUTCOMES", "run_adversarial_matrix"]
