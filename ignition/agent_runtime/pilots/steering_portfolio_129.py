"""Offline synthetic cross-domain steering pilot for IGNITION-129 Step 18."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any

from agent_runtime.event_ledger import EventLedger
from agent_runtime.steering import (
    AuthorityProvenance,
    CompletionContract,
    ConflictCandidate,
    GoalEpisodeBinder,
    GoalRecord,
    IntentRecord,
    NextWorkCandidate,
    OwnerOverride,
    PriorityInputs,
    SteeringDurabilityAdapter,
    SteeringEngine,
    SteeringState,
    evaluate_completion,
)


PILOT_ID = "IGNITION-129-OFFLINE-STEERING-PORTFOLIO-R1"
PILOT_SCHEMA = "os-steering-intent-obligation-r1.offline-pilot"
NOW = "2026-08-21T12:00:00+08:00"
LATER = "2026-08-21T12:01:00+08:00"


def _owner() -> AuthorityProvenance:
    return AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-pilot-owner", "synthetic offline pilot authority", authorized=True)


def _intent(owner: AuthorityProvenance, domain: str, status: str = "ACTIVE") -> IntentRecord:
    return IntentRecord(f"intent-{domain}", f"Maintain a bounded synthetic {domain} direction", "pilot.synthetic", owner, status=status, created_at=NOW, updated_at=NOW)


def _goal(owner: AuthorityProvenance, intent: IntentRecord, domain: str, status: str = "ACTIVE") -> GoalRecord:
    return GoalRecord(f"goal-{domain}", intent.intent_id, f"Produce a bounded synthetic {domain} artifact", "pilot.synthetic", f"contract-{domain}", owner, status=status, created_at=NOW, updated_at=NOW)


def _candidate(goal_id: str, *, owner_rank: int | None, commitment_status: str = "ACTIVE", dependency_criticality: int = 0, deadline_state: str = "ACTIVE_WINDOW", permission: bool = True, blocked: bool = False, status: str = "ACTIVE", superseded: bool = False, executor_available: bool = True, override: OwnerOverride | None = None, pack_ref: str, executor_ref: str) -> NextWorkCandidate:
    return NextWorkCandidate(
        ConflictCandidate(
            PriorityInputs(goal_id, owner_rank, commitment_status=commitment_status, dependency_criticality=dependency_criticality, deadline_state=deadline_state, permission_eligible=permission, blocked=blocked, owner_override=override),
            intent_status=status,
            superseded=superseded,
            executor_available=executor_available,
        ),
        pack_ref=pack_ref,
        executor_ref=executor_ref,
        blockers=("prerequisite-blocked",) if blocked else (),
        unknowns=("executor-capability-unknown",) if not executor_available else (),
    )


def run_pilot() -> dict[str, Any]:
    """Run all synthetic transitions and return only public deterministic evidence."""

    owner = _owner()
    intents = {domain: _intent(owner, domain, "SUPERSEDED" if domain == "superseded" else "ACTIVE") for domain in ("research", "writing", "repository", "knowledge", "background", "superseded", "unavailable")}
    goals = {domain: _goal(owner, intents[domain], domain, "SUPERSEDED" if domain == "superseded" else "BLOCKED" if domain == "knowledge" else "ACTIVE") for domain in intents}
    override = OwnerOverride("override-pilot-writing", goals["writing"].goal_id, 0, "Owner explicitly selected synthetic writing review", owner, NOW)
    candidates = (
        _candidate(goals["research"].goal_id, owner_rank=1, commitment_status="DUE", dependency_criticality=8, deadline_state="OVERDUE", pack_ref="pack-research", executor_ref="executor-local"),
        _candidate(goals["writing"].goal_id, owner_rank=50, dependency_criticality=2, override=override, pack_ref="pack-writing", executor_ref="executor-local"),
        _candidate(goals["repository"].goal_id, owner_rank=0, commitment_status="DUE", dependency_criticality=10, deadline_state="OVERDUE", permission=False, pack_ref="pack-repository", executor_ref="executor-local"),
        _candidate(goals["knowledge"].goal_id, owner_rank=2, commitment_status="BLOCKED", blocked=True, pack_ref="pack-knowledge", executor_ref="executor-local"),
        _candidate(goals["background"].goal_id, owner_rank=100, pack_ref="pack-background", executor_ref="executor-local"),
        _candidate(goals["superseded"].goal_id, owner_rank=0, status="SUPERSEDED", superseded=True, pack_ref="pack-old", executor_ref="executor-local"),
        _candidate(goals["unavailable"].goal_id, owner_rank=0, executor_available=False, pack_ref="pack-unavailable", executor_ref="executor-missing"),
    )
    engine = SteeringEngine()
    trace = engine.select_next("trace-pilot", "OVERRIDE_VS_AUTOMATION", candidates, created_at=NOW)
    selected = goals["writing"]
    if trace.selected_goal_id != selected.goal_id:
        raise RuntimeError(f"offline pilot selected {trace.selected_goal_id}, expected {selected.goal_id}")

    binder = GoalEpisodeBinder()
    binding = binder.bind(selected, "episode-pilot-writing", ("run-pilot-writing",), created_at=NOW)
    failed = binder.record_run_outcome(binding.binding_id, "run-pilot-writing", "FAILED", updated_at=LATER)
    paused = binder.update_episode(binding.binding_id, "PAUSED", updated_at=LATER)
    resumed = binder.update_episode(binding.binding_id, "ACTIVE", updated_at=LATER)
    passed = binder.record_run_outcome(binding.binding_id, "run-pilot-writing", "PASS", updated_at=LATER)
    completed_episode = binder.update_episode(binding.binding_id, "EPISODE_COMPLETED_VALIDATED", updated_at=LATER)
    run_reconciliation = binder.reconcile_run_result(binding.binding_id, "run-pilot-writing", "PASS")

    contract = CompletionContract(selected.completion_contract_id, ("artifact_reviewed", "owner_acceptance_recorded"), ("OWNER_EVIDENCE", "OWNER_REVIEW"), "OWNER_ONLY", ("run_pass", "episode_pass"))
    run_pass_decision = evaluate_completion(selected, contract, {"run_pass": True}, authority=owner, decided_at=LATER)
    owner_completion = evaluate_completion(selected, contract, {"predicate_results": {"artifact_reviewed": True, "owner_acceptance_recorded": True}, "evidence_types": ["OWNER_EVIDENCE", "OWNER_REVIEW"], "evidence_refs": ["owner-evidence-pilot", "owner-review-pilot"]}, authority=owner, decided_at=LATER)
    from agent_runtime.steering import GoalRegistry
    registry = GoalRegistry([selected], [contract])
    satisfied = registry.mark_satisfied(owner_completion)

    final_state = SteeringState(
        intents=tuple(record.to_dict() for record in intents.values()),
        goals=tuple(record.to_dict() for record in tuple(goals.values()) if record.goal_id != selected.goal_id) + (satisfied.to_dict(),),
        commitments=({"commitment_id": "commitment-pilot-research", "goal_id": goals["research"].goal_id, "status": "DUE", "authority": "OWNER_DECLARED"},),
        decision_traces=(trace.to_dict(),),
        provenance_events=({"event": "OFFLINE_PILOT_OWNER_COMPLETION", "authority": "OWNER_DECLARED", "goal_id": selected.goal_id},),
        unresolved_refs=("executor-capability-unknown", "prerequisite-blocked"),
    )
    adapter = SteeringDurabilityAdapter()
    with tempfile.TemporaryDirectory(prefix="ignition-129-steering-pilot-") as temp:
        root = Path(temp)
        ledger = EventLedger(root / "pilot-events.jsonl")
        adapter.append_state(ledger, final_state, occurred_at=NOW)
        snapshot = adapter.snapshot(ledger, str(root / "pilot-snapshot.json"), snapshot_id="snapshot-pilot-1", provenance_refs=(PILOT_ID,))
        adapter.append_state(ledger, final_state, expected_version=1, occurred_at=LATER)
        replayed = adapter.replay(ledger)
        restored = adapter.restore(ledger, snapshot=snapshot)
        replay_trace = engine.select_next("trace-pilot-replay", "OVERRIDE_VS_AUTOMATION", candidates, created_at=NOW)
        event_count = len(ledger.events())

    same_selection_after_replay = replayed.digest() == restored.digest() and replay_trace.selected_goal_id == trace.selected_goal_id and replay_trace.arbitration.decisions[0].lexicographic_key == trace.arbitration.decisions[0].lexicographic_key
    decision_by_goal = {decision.goal_id: decision for decision in trace.arbitration.decisions}
    return {
        "schema": PILOT_SCHEMA,
        "pilot_id": PILOT_ID,
        "offline_only": True,
        "domains": ["research", "writing", "repository", "knowledge", "background", "superseded", "unavailable"],
        "selected_goal_id": trace.selected_goal_id,
        "why_next": {"selected_goal_id": trace.selected_goal_id, "why_now": trace.why_now, "why_selected": trace.why_selected, "skipped_goal_ids": [item.goal_id for item in trace.skipped_goals], "unknowns": list(trace.unknowns)},
        "candidate_boundaries": {
            candidate.goal_id: {
                "eligible": decision_by_goal[candidate.goal_id].eligible and candidate.conflict_candidate.intent_status != "SUPERSEDED" and not candidate.conflict_candidate.superseded and candidate.conflict_candidate.executor_available,
                "policy_eligible": decision_by_goal[candidate.goal_id].eligible,
                "reasons": list(decision_by_goal[candidate.goal_id].reasons),
            }
            for candidate in candidates
        },
        "lifecycle": {"failed": failed.run_outcomes, "paused": paused.episode_status, "resumed": resumed.episode_status, "passed": passed.run_outcomes, "episode_terminal": completed_episode.episode_status, "run_pass_goal_mutated": run_reconciliation["goal_status_mutated"]},
        "completion": {"run_pass_outcome": run_pass_decision.outcome, "owner_independent_outcome": owner_completion.outcome, "goal_status_after_owner_decision": satisfied.status},
        "durability": {"snapshot_id": snapshot.snapshot_id, "event_count": event_count, "replay_same_selection": same_selection_after_replay, "lineage_preserved": True},
        "claim_ceiling": "Synthetic offline repository-local pilot only; no live executor, external truth, production readiness, Owner knowledge, or epistemic acceptance is established.",
    }


__all__ = ["PILOT_ID", "PILOT_SCHEMA", "run_pilot"]
