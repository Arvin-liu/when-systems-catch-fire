#!/usr/bin/env python3
"""Q36-INT core tests — drive the REAL fail-closed validator CLI and assert exit codes.

No constant assertions, no string-presence-only checks: every test runs
tools/intervention/validate_intervention_failure_gate.py via subprocess and asserts the
machine-readable exit code. Mirrors tests/observation/test_observation_prediction_core.py.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = ROOT / "tools" / "intervention" / "validate_intervention_failure_gate.py"
CLAIMS = ROOT / "data" / "agent" / "q34-claims-registry.json"
NOW = "2026-07-21T12:00:00+00:00"
CURRENT_HEAD = "9087e494c782b405b5bbdb0d1ae4bd1707792d95"
PILOT = ROOT / "data" / "intervention" / "pilot-controlled-intervention.json"


def _base_bundle():
    # The repair pilot is the canonical byte-bound positive template. Core tests
    # mutate exactly one semantic dimension instead of rebuilding placeholder
    # authority and digest fields in test code.
    return json.loads(PILOT.read_text(encoding="utf-8"))

    # Historical pre-repair construction retained below as dead reference text.
    return {
        "intervention_requests": [{
            "intervention_id": "int-core-001",
            "initiator": "zhiyuan",
            "q34_claim_ref": "q33.seven_governance_components.current_in_main",
            "q35_actor_ref": "actor-zhiyuan",
            "q35_grant_ref": "grant-core-001",
            "q35_action_ref": "action-core-001",
            "q35_trajectory_event_digest": "sha256:" + "1" * 64,
            "q36_obs_ref": "obs-core-001",
            "target_resource": "data/observation",
            "normalized_intervention_type": "dry_run_replay",
            "intended_change": "controlled deterministic replay",
            "mechanism_hypothesis": "Hypothesis: the same tool reproduces the output.",
            "mechanism_hypothesis_status": "hypothesis",
            "applicability_scope": "repo:data/observation controlled fixture regeneration only",
            "uncertainty": "deterministic",
            "expected_effect": "output matches recorded digest",
            "evaluation_window": {"start": "2026-07-21T10:00:00+00:00", "end": "2026-07-21T11:00:00+00:00"},
            "claim_ceiling": "candidate_only: single controlled repo-local replay; no real-world causal claim",
            "exact_head": CURRENT_HEAD,
            "artifact_digest": "sha256:" + "2" * 64,
            "proposed_at": "2026-07-21T10:00:00+00:00",
            "authorized_at": "2026-07-21T10:05:00+00:00",
            "external_action": False,
            "source_ref": "data/observation/fixtures/20-retrospective-replay-pilot.json",
        }],
        "safety_envelopes": [{
            "envelope_id": "env-core-001",
            "request_id": "int-core-001",
            "allowed_target_scope": "repo:data/observation controlled fixture regeneration only",
            "max_change_magnitude": 1.0,
            "allowed_side_effects": ["none"],
            "forbidden_surfaces": ["main", "external_network"],
            "prerequisites": ["snapshot present"],
            "stop_conditions": ["digest mismatch"],
            "abort_conditions": ["external call"],
            "observation_cadence": "per-execution",
            "authority_escalation_threshold": "residual to Q39",
            "rollback_readiness": True,
            "expiry": "2026-07-22T00:00:00+00:00",
            "rollback_plan": {"plan_id": "rb-core-001", "steps": ["restore"], "verification_method": "sha256 compare"},
        }],
        "q35_grants": [{
            "grant_id": "grant-core-001",
            "status": "active",
            "grant_expires_at": "2026-07-22T00:00:00+00:00",
            "scope": "repo:data/observation controlled fixture regeneration only",
            "grantee": "actor-zhiyuan",
            "granted_by": "actor-reviewer",
            "action_refs": ["action-core-001"],
        }],
        "q36_obs_snapshots": [{
            "observation_id": "obs-core-001",
            "target_scope": "repo:data/observation controlled fixture regeneration only",
            "sampling_window": {"start": "2026-07-21T09:00:00+00:00", "end": "2026-07-21T10:00:00+00:00"},
            "quality_status": "accepted",
            "exact_head": CURRENT_HEAD,
            "do_not_infer_cause": True,
        }],
        "plans": [{
            "plan_id": "plan-core-001",
            "request_id": "int-core-001",
            "envelope_id": "env-core-001",
            "state": "succeeded_within_scope",
            "high_risk": False,
            "execution_events": [{
                "event_id": "ev-core-001",
                "state": "succeeded_within_scope",
                "pre_state_digest": "sha256:" + "3" * 64,
                "command": "python tools/observation/validate_observation_prediction_gate.py",
                "executor": "actor-zhiyuan",
                "start_time": "2026-07-21T10:10:00+00:00",
                "end_time": "2026-07-21T10:30:00+00:00",
                "affected_surfaces": ["data/observation/fixtures/20-retrospective-replay-pilot.json"],
                "actual_change_magnitude": 0.0,
                "output_artifact_digests": ["sha256:" + "4" * 64],
                "side_effects": [],
                "stop_condition_status": "not_triggered",
                "trajectory_event_digest": "sha256:" + "5" * 64,
                "no_silent_mutation": True,
            }],
        }],
        "outcome_evaluations": [{
            "evaluation_id": "eval-core-001",
            "plan_id": "plan-core-001",
            "execution_event_id": "ev-core-001",
            "q36_obs_observation_ref": "obs-core-001",
            "expected_effect": "output matches recorded digest",
            "observed_effect": "output matches recorded digest",
            "evaluation_method": "sha256 compare",
            "baseline_comparator": "pre-state digest 3333...",
            "uncertainty": "0",
            "residual_change": "none",
            "unintended_effects": [],
            "scope_validity": "valid for single controlled replay",
            "evaluator_ref": "actor-zhiyuan",
            "causal_interpretation_status": "NOT_IDENTIFIED",
            "do_not_overclaim_causality": True,
            "exact_head": CURRENT_HEAD,
        }],
        "failure_records": [],
        "stop_rollback_records": [],
    }


def _run(bundle, rejects=None):
    path = _tmp / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    cmd = [sys.executable, str(VALIDATOR), "--bundle", str(path),
           "--claims", str(CLAIMS), "--current-head", CURRENT_HEAD, "--now", NOW]
    if rejects is not None:
        rpath = _tmp / "rejects.json"
        rpath.write_text(json.dumps({"rejected": rejects}), encoding="utf-8")
        cmd += ["--q33-rejects", str(rpath)]
    return subprocess.run(cmd, capture_output=True, text=True)


_tmp = None


def setup_module(module):
    global _tmp
    _tmp = Path(__file__).resolve().parent / ".int_test_tmp"
    _tmp.mkdir(exist_ok=True)


# ---------- happy path ----------
def test_pilot_passes_gate():
    r = _run(_base_bundle())
    assert r.returncode == 0, r.stdout + r.stderr


# ---------- schema / refs ----------
def test_schema_error_on_missing_required():
    b = _base_bundle()
    del b["failure_records"]
    r = _run(b)
    assert r.returncode == 2, r.stdout


def test_unresolvable_exact_head():
    b = _base_bundle()
    b["intervention_requests"][0]["exact_head"] = "b8eab57bf2a2465c48d5d624e22681a1ad1bc20c"
    r = _run(b)
    assert r.returncode == 5, r.stdout


# ---------- Q34 / Q35 / Q33 ----------
def test_uncommitted_q34_claim_fails():
    b = _base_bundle()
    b["intervention_requests"][0]["q34_claim_ref"] = "q34.hypothesis.example"
    r = _run(b)
    assert r.returncode == 6, r.stdout


def test_missing_q35_authority_fails():
    b = _base_bundle()
    b["intervention_requests"][0]["q35_grant_ref"] = "grant-does-not-exist"
    r = _run(b)
    assert r.returncode == 7, r.stdout


def test_expired_q35_grant_fails():
    b = _base_bundle()
    b["q35_grants"][0]["grant_expires_at"] = "2026-07-21T01:00:00+00:00"
    r = _run(b)
    assert r.returncode == 7, r.stdout


def test_q35_scope_mismatch_fails():
    b = _base_bundle()
    b["q35_grants"][0]["scope"] = "unrelated surface"
    r = _run(b)
    assert r.returncode == 7, r.stdout


def test_q33_gate_bypass_fails():
    b = _base_bundle()
    b["intervention_requests"][0]["source_ref"] = "banned/source.json"
    r = _run(b, rejects=["banned/source.json"])
    assert r.returncode == 8, r.stdout


# ---------- safety envelope / external action ----------
def test_safety_envelope_incomplete_fails():
    b = _base_bundle()
    # envelope points at a request that does not exist -> incomplete envelope binding
    b["safety_envelopes"][0]["request_id"] = "int-nonexistent"
    r = _run(b)
    assert r.returncode == 9, r.stdout


def test_external_action_forbidden():
    b = _base_bundle()
    b["intervention_requests"][0]["external_action"] = True
    r = _run(b)
    assert r.returncode == 10, r.stdout


# ---------- envelope / stop / failure / effect ----------
def test_envelope_exceeded_fails():
    b = _base_bundle()
    b["plans"][0]["execution_events"][0]["actual_change_magnitude"] = 5.0
    r = _run(b)
    assert r.returncode == 11, r.stdout


def test_stop_condition_violated_fails():
    b = _base_bundle()
    evs = b["plans"][0]["execution_events"]
    evs[0]["stop_condition_status"] = "triggered"
    later = copy.deepcopy(evs[0])
    later.update({
        "event_id": "ev-core-002", "state": "executing", "command": "another repository-local dry run",
        "start_time": "2026-07-21T10:35:00+00:00", "end_time": "2026-07-21T10:40:00+00:00",
        "stop_condition_status": "not_triggered",
    })
    evs.append(later)
    r = _run(b)
    assert r.returncode == 12, r.stdout


def test_failure_rewrite_forbidden():
    b = _base_bundle()
    plan_id = b["plans"][0]["plan_id"]
    # failure record exists but plan is silently marked success with no rollback
    b["failure_records"] = [{
        "failure_id": "fail-core-001", "plan_id": plan_id,
        "failure_type": "side_effect_unexpected", "trigger": "unexpected output",
        "detected_at": "2026-07-21T10:31:00+00:00",
        "affected_surfaces": ["data/observation/fixtures/20-retrospective-replay-pilot.json"],
        "severity": "medium", "reversibility": "reversible", "residual_impact": "none",
        "responsibility_state": "ATTRIBUTED_WITHIN_REPOSITORY_SCOPE",
        "known_cause": "input typo", "unknown_cause": False, "competing_explanations": [],
        "escalation_target": "none", "claim_ceiling": "candidate_only", "exact_head": CURRENT_HEAD,
        "evidence_binding": copy.deepcopy(b["canonical_bindings"]["q36_obs_source"]),
    }]
    r = _run(b)
    assert r.returncode == 13, r.stdout


def test_expected_effect_rewrite_fails():
    b = _base_bundle()
    b["outcome_evaluations"][0]["expected_effect"] = "completely different success criterion"
    r = _run(b)
    assert r.returncode == 14, r.stdout


# ---------- causal / rollback / ownership / obs / sod / baseline ----------
def test_causal_overclaim_fails():
    b = _base_bundle()
    b["intervention_requests"][0]["claim_ceiling"] = "this replay establishes causation of the observation"
    r = _run(b)
    assert r.returncode == 15, r.stdout


def test_rollback_incomplete_fails():
    b = _base_bundle()
    plan_id = b["plans"][0]["plan_id"]
    pre = b["plans"][0]["execution_events"][0]["pre_state_digest"]
    post = b["plans"][0]["execution_events"][0]["trajectory_event_digest"]
    b["stop_rollback_records"] = [{
        "record_id": "rb-core-fail", "plan_id": plan_id,
        "triggering_stop_condition": "digest mismatch", "stop_authority": "actor-reviewer",
        "rollback_plan_ref": b["safety_envelopes"][0]["rollback_plan"]["plan_id"], "rollback_action": "restore from pre-state",
        "pre_digest": pre, "post_digest": post,
        "restored_surfaces": [], "not_restored_surfaces": [],
        "irreversible_residue": "none", "verification_result": "failed",
        "follow_up_restrictions": "none", "history_preservation": True, "exact_head": CURRENT_HEAD,
        "evidence_binding": copy.deepcopy(b["canonical_bindings"]["q36_obs_source"]),
    }]
    r = _run(b)
    assert r.returncode == 16, r.stdout


def test_single_owner_forged_fails():
    b = _base_bundle()
    b["plans"][0]["state"] = "failed"
    plan_id = b["plans"][0]["plan_id"]
    b["failure_records"] = [{
        "failure_id": "fail-core-002", "plan_id": plan_id,
        "failure_type": "data_quality_anomaly", "trigger": "ambiguous cause",
        "detected_at": "2026-07-21T10:31:00+00:00",
        "affected_surfaces": ["data/observation/fixtures/20-retrospective-replay-pilot.json"],
        "severity": "high", "reversibility": "irreversible", "residual_impact": "large",
        "responsibility_state": "UNRESOLVED_MANY_HANDS",
        "known_cause": "", "unknown_cause": True, "competing_explanations": ["A", "B"],
        "escalation_target": "q39_failure_memory", "claim_ceiling": "sole owner is actor-zhiyuan",
        "exact_head": CURRENT_HEAD,
        "evidence_binding": copy.deepcopy(b["canonical_bindings"]["q36_obs_source"]),
    }]
    r = _run(b)
    assert r.returncode == 17, r.stdout


def test_obs_not_validated_fails():
    b = _base_bundle()
    b["q36_obs_snapshots"][0]["quality_status"] = "rejected"
    r = _run(b)
    assert r.returncode == 18, r.stdout


def test_separation_of_duty_violation():
    b = _base_bundle()
    b["plans"][0]["high_risk"] = True
    b["plans"][0]["separation_of_duty"] = {
        "proposer": "actor-zhiyuan", "authorizer": "actor-zhiyuan",
        "executor": "actor-zhiyuan", "verifier": "actor-zhiyuan",
    }
    r = _run(b)
    assert r.returncode == 19, r.stdout


def test_baseline_missing_fails():
    b = _base_bundle()
    b["outcome_evaluations"][0]["baseline_comparator"] = ""
    b["outcome_evaluations"][0]["uncertainty"] = ""
    r = _run(b)
    assert r.returncode == 20, r.stdout


def test_target_mismatch_fails():
    b = _base_bundle()
    b["q36_obs_snapshots"][0]["target_scope"] = "repo:completely/different/scope"
    r = _run(b)
    assert r.returncode == 4, r.stdout


def test_temporal_leak_fails():
    b = _base_bundle()
    b["plans"][0]["execution_events"][0]["end_time"] = "2026-07-23T00:00:00+00:00"
    r = _run(b)
    assert r.returncode == 3, r.stdout
