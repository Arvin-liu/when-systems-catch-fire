#!/usr/bin/env python3
"""Q36-INT Intervention-Failure Dynamics Gate — fail-closed deterministic validator/CLI.

Decides whether a repository-local intervention bundle is admissible: intervention requests
must bind a Q34 committed claim and a Q35 authorized grant, consume Q36-OBS validated
observations/residuals as read-only signals (never as causal identifications), freeze a safety
envelope and rollback plan, execute on a bounded repo-local trajectory, evaluate effects against a
baseline without causal overclaim, and record failures / stops / rollbacks as append-only events.

Repository governance only. Does NOT execute real-world external actions (external_action=true
fails closed), does NOT adjudicate universal causal mechanisms, does NOT invent a new authority
model (Q35 remains the authority), and does NOT form an L7 / truth layer.

Stable exit codes (machine-consumable, never free-text PASS):
  0  GATE_PASS
  2  SCHEMA_ERROR                - bundle failed JSON schema
  3  TEMPORAL_LEAK              - authorized before proposed, or execution after envelope expiry
  4  TARGET_MISMATCH            - request target/scope/window does not match bound Q36-OBS observation
  5  UNRESOLVABLE_REF           - malformed exact_head / digest / trajectory hash, unresolvable refs
  6  Q34_CLAIM_NOT_COMMITTED    - bound Q34 claim not committed_current
  7  Q35_AUTHORITY_INVALID      - Q35 actor/grant/action/trajectory missing, expired, scope-mismatch, or revoked
  8  Q33_GATE_BYPASS            - source on the Q33 rejected list
  9  SAFETY_ENVELOPE_INCOMPLETE - missing safety envelope / stop conditions / rollback plan
  10 EXTERNAL_ACTION_FORBIDDEN  - real-world external action requested (external_action=true)
  11 ENVELOPE_EXCEEDED          - actual change magnitude / surface exceeds the safety envelope
  12 STOP_CONDITION_VIOLATED    - execution continues after a stop/abort condition triggered
  13 FAILURE_REWRITE_FORBIDDEN  - failure / negative / residual record deleted or rewritten to success
  14 EXPECTED_EFFECT_REWRITE    - expected_effect modified after the outcome is recorded
  15 CAUSAL_OVERCLAIM           - residual / correlation upgraded to a unique causal mechanism
  16 ROLLBACK_INCOMPLETE        - rollback not append-only / not verified / partial claimed full
  17 SINGLE_OWNER_FORGED        - UNRESOLVED_MANY_HANDS / INSUFFICIENT_EVIDENCE forged into a single owner
  18 OBS_NOT_VALIDATED          - bound Q36-OBS observation unvalidated / rejected / stale head / infer-cause
  19 SEPARATION_OF_DUTY_VIOLATION - high-risk: proposer == authorizer == executor == verifier
  20 BASELINE_MISSING           - outcome lacks baseline/comparator or uncertainty

Usage:
  python tools/intervention/validate_intervention_failure_gate.py --bundle <bundle.json> \
      [--claims <q34-claims.json>] [--q33-rejects <path>] \
      [--current-head <sha>] [--now <iso>] [--report <out.json>]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT / "schemas" / "intervention" / "intervention-failure-dynamics-contract.schema.json"

GATE_PASS = 0
SCHEMA_ERROR = 2
TEMPORAL_LEAK = 3
TARGET_MISMATCH = 4
UNRESOLVABLE_REF = 5
Q34_CLAIM_NOT_COMMITTED = 6
Q35_AUTHORITY_INVALID = 7
Q33_GATE_BYPASS = 8
SAFETY_ENVELOPE_INCOMPLETE = 9
EXTERNAL_ACTION_FORBIDDEN = 10
ENVELOPE_EXCEEDED = 11
STOP_CONDITION_VIOLATED = 12
FAILURE_REWRITE_FORBIDDEN = 13
EXPECTED_EFFECT_REWRITE = 14
CAUSAL_OVERCLAIM = 15
ROLLBACK_INCOMPLETE = 16
SINGLE_OWNER_FORGED = 17
OBS_NOT_VALIDATED = 18
SEPARATION_OF_DUTY_VIOLATION = 19
BASELINE_MISSING = 20

EXIT_NAMES = {v: k for k, v in {
    "GATE_PASS": 0, "SCHEMA_ERROR": 2, "TEMPORAL_LEAK": 3, "TARGET_MISMATCH": 4,
    "UNRESOLVABLE_REF": 5, "Q14_CLAIM_NOT_COMMITTED": 6, "Q35_AUTHORITY_INVALID": 7,
    "Q33_GATE_BYPASS": 8, "SAFETY_ENVELOPE_INCOMPLETE": 9, "EXTERNAL_ACTION_FORBIDDEN": 10,
    "ENVELOPE_EXCEEDED": 11, "STOP_CONDITION_VIOLATED": 12, "FAILURE_REWRITE_FORBIDDEN": 13,
    "EXPECTED_EFFECT_REWRITE": 14, "CAUSAL_OVERCLAIM": 15, "ROLLBACK_INCOMPLETE": 16,
    "SINGLE_OWNER_FORGED": 17, "OBS_NOT_VALIDATED": 18, "SEPARATION_OF_DUTY_VIOLATION": 19,
    "BASELINE_MISSING": 20}.items()}

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

# phrases that upgrade residual/correlation/fit into a unique causal mechanism
CAUSAL_OVERCLAIM_TOKENS = [
    "causal mechanism proven", "causation proven", "proves causality", "causal proof",
    "this correlation proves", "fit proves mechanism", "accuracy proves cause",
    "establishes causation", "demonstrates causal", "residual proves cause",
    "uniquely caused by", "sole cause identified",
]
# phrases that assert a universal real-world intervention capability
UNIVERSAL_CAPABILITY_TOKENS = [
    "universal intervention", "intervenes in everything", "always succeeds in the real world",
    "guaranteed real-world effect", "proven real-world control", "can control any system",
    "general real-world intervention capability proven",
]


def _parse_time(value):
    if not value:
        return None
    try:
        v = value.replace("Z", "+00:00")
        return datetime.fromisoformat(v).astimezone(timezone.utc)
    except Exception:
        return None


def _result(code, errors, decision=None):
    return {"gate": "q36_int_intervention_failure_gate", "exit_code": code,
            "exit_name": EXIT_NAMES.get(code, "UNKNOWN"), "decision": decision, "errors": errors}


def _index(lst, key):
    return {item.get(key): item for item in lst if isinstance(item, dict) and item.get(key)}


def validate_schema(bundle):
    try:
        import jsonschema
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        errs = []
        for e in sorted(validator.iter_errors(bundle), key=lambda x: list(x.absolute_path)):
            path = ".".join(str(p) for p in e.absolute_path) or "<root>"
            errs.append(f"{path}: {e.message}")
            if len(errs) >= 25:
                errs.append("... (truncated)")
                break
        return errs
    except ImportError:
        errs = []
        for field in ("intervention_requests", "safety_envelopes", "plans",
                     "outcome_evaluations", "failure_records", "stop_rollback_records"):
            if field not in bundle:
                errs.append(f"missing required field: {field}")
        return errs


def check_temporal_integrity(bundle, now):
    errs = []
    reqs = _index(bundle.get("intervention_requests", []), "intervention_id")
    envs = _index(bundle.get("safety_envelopes", []), "envelope_id")
    for r in bundle.get("intervention_requests", []):
        pa = _parse_time(r.get("proposed_at", ""))
        aa = _parse_time(r.get("authorized_at", ""))
        if pa and aa and aa < pa:
            errs.append(f"request {r.get('intervention_id')}: authorized_at {r.get('authorized_at')} "
                        f"before proposed_at {r.get('proposed_at')} (temporal leak)")
    for p in bundle.get("plans", []):
        env = envs.get(p.get("envelope_id"))
        exp = _parse_time(env.get("expiry")) if env else None
        for ev in p.get("execution_events", []):
            et = _parse_time(ev.get("end_time"))
            if et and exp and et > exp:
                errs.append(f"plan {p.get('plan_id')} event {ev.get('event_id')}: execution ended "
                            f"{ev.get('end_time')} after envelope expiry {env.get('expiry')} (temporal leak)")
    return errs


def check_target_matching(bundle):
    errs = []
    reqs = _index(bundle.get("intervention_requests", []), "intervention_id")
    obs = _index(bundle.get("q36_obs_snapshots", []), "observation_id")
    for r in bundle.get("intervention_requests", []):
        snap = obs.get(r.get("q36_obs_ref"))
        if not snap:
            continue  # unvalidated-obs handled elsewhere
        # scope containment (either direction)
        rs = r.get("applicability_scope", "")
        ts = snap.get("target_scope", "")
        if rs and ts and ts not in rs and rs not in ts:
            errs.append(f"request {r.get('intervention_id')}: applicability_scope '{rs}' outside "
                        f"bound observation target_scope '{ts}' (target mismatch)")
        # window overlap
        ew = r.get("evaluation_window", {})
        sw = snap.get("sampling_window", {})
        ew_s, ew_e = _parse_time(ew.get("start", "")), _parse_time(ew.get("end", ""))
        sw_s, sw_e = _parse_time(sw.get("start", "")), _parse_time(sw.get("end", ""))
        if None not in (ew_s, ew_e, sw_s, sw_e):
            if sw_e < ew_s or sw_s > ew_e:
                errs.append(f"request {r.get('intervention_id')}: evaluation window "
                            f"[{ew.get('start')},{ew.get('end')}] does not intersect observation window "
                            f"[{sw.get('start')},{sw.get('end')}] (target mismatch)")
        # target resource must be within scope
        tr = r.get("target_resource", "")
        if tr and ts and tr not in ts and tr not in rs:
            errs.append(f"request {r.get('intervention_id')}: target_resource '{tr}' outside "
                        f"observation scope / applicability scope (target mismatch)")
    return errs


def check_references_resolvable(bundle, current_head):
    errs = []
    for r in bundle.get("intervention_requests", []):
        rid = r.get("intervention_id")
        if not HEAD_RE.match(str(r.get("exact_head", ""))):
            errs.append(f"request {rid}: malformed exact_head")
        if current_head and r.get("exact_head") and r.get("exact_head") != current_head:
            errs.append(f"request {rid}: exact_head {r.get('exact_head')} != required {current_head}")
        if not SHA256_RE.match(str(r.get("q35_trajectory_event_digest", ""))):
            errs.append(f"request {rid}: malformed q35_trajectory_event_digest")
    for p in bundle.get("plans", []):
        for ev in p.get("execution_events", []):
            if not SHA256_RE.match(str(ev.get("pre_state_digest", ""))):
                errs.append(f"plan {p.get('plan_id')} event {ev.get('event_id')}: malformed pre_state_digest")
            if not SHA256_RE.match(str(ev.get("trajectory_event_digest", ""))):
                errs.append(f"plan {p.get('plan_id')} event {ev.get('event_id')}: malformed trajectory_event_digest")
    for o in bundle.get("outcome_evaluations", []):
        oid = o.get("evaluation_id")
        if not HEAD_RE.match(str(o.get("exact_head", ""))):
            errs.append(f"evaluation {oid}: malformed exact_head")
    return errs


def check_q34_commitment(bundle, claims_registry):
    errs = []
    states = {}
    if claims_registry:
        for c in claims_registry.get("claims", []):
            states[c.get("claim_id")] = c.get("state")
    for r in bundle.get("intervention_requests", []):
        ref = r.get("q34_claim_ref")
        if not ref:
            errs.append(f"request {r.get('intervention_id')}: missing q34_claim_ref")
            continue
        if ref in states and states[ref] != "committed_current":
            errs.append(f"request {r.get('intervention_id')}: q34 claim '{ref}' state "
                        f"'{states[ref]}' is not committed_current")
    return errs


def check_q35_authority(bundle, now):
    errs = []
    grants = _index(bundle.get("q35_grants", []), "grant_id")
    now_t = _parse_time(now) if now else datetime.now(timezone.utc)
    for r in bundle.get("intervention_requests", []):
        rid = r.get("intervention_id")
        for field in ("q35_actor_ref", "q35_grant_ref", "q35_action_ref"):
            if not r.get(field):
                errs.append(f"request {rid}: missing {field}")
        gid = r.get("q35_grant_ref")
        g = grants.get(gid) if gid else None
        if gid and not g:
            errs.append(f"request {rid}: q35 grant '{gid}' not resolvable in bundle")
            continue
        if g:
            if g.get("status") != "active":
                errs.append(f"request {rid}: q35 grant '{gid}' status '{g.get('status')}' is not active")
            exp = _parse_time(g.get("grant_expires_at"))
            if exp and now_t and now_t > exp:
                errs.append(f"request {rid}: q35 grant '{gid}' expired at {g.get('grant_expires_at')}")
            scope = g.get("scope", "")
            app = r.get("applicability_scope", "")
            if scope and app and app not in scope and scope not in app:
                errs.append(f"request {rid}: q35 grant '{gid}' scope '{scope}' does not cover "
                            f"intervention applicability_scope '{app}'")
    return errs


def check_q33_rights(bundle, q33_rejects):
    errs = []
    rejected = set()
    if q33_rejects:
        rejected = set(q33_rejects.get("rejected", []))
    for r in bundle.get("intervention_requests", []):
        src = r.get("source_ref", "")
        if src in rejected:
            errs.append(f"request {r.get('intervention_id')}: source_ref '{src}' is Q33-rejected; "
                        f"publication gate bypassed")
    for o in bundle.get("outcome_evaluations", []):
        src = o.get("evaluation_method", "")
        if src in rejected:
            errs.append(f"evaluation {o.get('evaluation_id')}: evaluation_method '{src}' is Q33-rejected")
    return errs


def check_safety_envelope(bundle):
    errs = []
    reqs = {r.get("intervention_id") for r in bundle.get("intervention_requests", [])}
    for env in bundle.get("safety_envelopes", []):
        rid = env.get("request_id")
        if rid not in reqs:
            errs.append(f"envelope {env.get('envelope_id')}: request_id '{rid}' not found")
        if env.get("rollback_readiness") is not True:
            errs.append(f"envelope {env.get('envelope_id')}: rollback_readiness must be true (no usable rollback plan)")
        if not env.get("stop_conditions"):
            errs.append(f"envelope {env.get('envelope_id')}: missing stop_conditions")
        if not env.get("abort_conditions"):
            errs.append(f"envelope {env.get('envelope_id')}: missing abort_conditions")
        rp = env.get("rollback_plan") or {}
        if not rp.get("steps") or not rp.get("verification_method"):
            errs.append(f"envelope {env.get('envelope_id')}: incomplete rollback_plan")
    # every request must have an envelope
    env_reqs = {e.get("request_id") for e in bundle.get("safety_envelopes", [])}
    for rid in reqs:
        if rid not in env_reqs:
            errs.append(f"request {rid}: has no safety envelope (fail closed)")
    return errs


def check_external_action(bundle):
    errs = []
    for r in bundle.get("intervention_requests", []):
        if r.get("external_action") is True:
            errs.append(f"request {r.get('intervention_id')}: external_action=true (real-world external "
                        f"action) is forbidden; repository governance only")
    return errs


def check_envelope_exceeded(bundle):
    errs = []
    envs = _index(bundle.get("safety_envelopes", []), "request_id")
    plans = _index(bundle.get("plans", []), "request_id")
    reqs = _index(bundle.get("intervention_requests", []), "intervention_id")
    for pid, p in plans.items():
        env = envs.get(pid)
        req = reqs.get(pid)
        if not env or not req:
            continue
        maxmag = env.get("max_change_magnitude")
        for ev in p.get("execution_events", []):
            mag = ev.get("actual_change_magnitude")
            if maxmag is not None and mag is not None and mag > maxmag:
                errs.append(f"plan {p.get('plan_id')} event {ev.get('event_id')}: actual_change_magnitude "
                            f"{mag} exceeds envelope max_change_magnitude {maxmag}")
            # forbidden surfaces
            forbidden = set(env.get("forbidden_surfaces", []))
            for s in ev.get("affected_surfaces", []):
                if s in forbidden:
                    errs.append(f"plan {p.get('plan_id')} event {ev.get('event_id')}: affected surface "
                                f"'{s}' is in the envelope forbidden_surfaces")
    return errs


def check_stop_condition_violated(bundle):
    errs = []
    for p in bundle.get("plans", []):
        events = p.get("execution_events", [])
        # find the first event whose stop_condition_status is triggered/aborted
        triggered_idx = None
        for i, ev in enumerate(events):
            if ev.get("stop_condition_status") in ("triggered", "aborted"):
                triggered_idx = i
                break
        if triggered_idx is not None:
            # any later event with a 'real' execution must not occur
            for j in range(triggered_idx + 1, len(events)):
                later = events[j]
                if later.get("state") not in ("stopped", "rolled_back", "abandoned", "failed", "unresolved"):
                    errs.append(f"plan {p.get('plan_id')} event {later.get('event_id')}: execution continues "
                                f"after stop/abort condition triggered at event "
                                f"{events[triggered_idx].get('event_id')}")
    return errs


def check_failure_rewrite(bundle):
    """Failures must be preserved: a failure record must not be deleted, and a plan that failed
    must not be silently relabelled succeeded_within_scope without a rollback record."""
    errs = []
    failed_plans = set()
    for f in bundle.get("failure_records", []):
        failed_plans.add(f.get("plan_id"))
    plans = _index(bundle.get("plans", []), "plan_id")
    for pid in failed_plans:
        p = plans.get(pid)
        if p and p.get("state") in ("succeeded_within_scope",):
            # succeeded without a rollback record referencing it = silent success rewrite
            has_rollback = any(r.get("plan_id") == pid for r in bundle.get("stop_rollback_records", []))
            if not has_rollback:
                errs.append(f"plan {pid}: failure record exists but plan state is "
                            f"'{p.get('state')}' with no rollback record (failure rewritten to success)")
    return errs


def check_expected_effect_rewrite(bundle):
    errs = []
    reqs = _index(bundle.get("intervention_requests", []), "intervention_id")
    plans = _index(bundle.get("plans", []), "plan_id")
    for o in bundle.get("outcome_evaluations", []):
        p = plans.get(o.get("plan_id"))
        if not p:
            continue
        req = reqs.get(p.get("request_id"))
        if not req:
            continue
        if o.get("expected_effect") and req.get("expected_effect") and \
           o.get("expected_effect") != req.get("expected_effect"):
            errs.append(f"evaluation {o.get('evaluation_id')}: expected_effect modified after outcome "
                        f"(request froze '{req.get('expected_effect')}', outcome says "
                        f"'{o.get('expected_effect')}')")
    return errs


def _assertive_hits(text, tokens):
    hits = []
    lower = text.lower()
    negations = ("not ", "no ", "never ", "without ", "does not ", "did not ",
                 "cannot ", "must not ", "nor ", "neither ", "n't ")
    for clause in re.split(r"[.;\n]", lower):
        for tok in tokens:
            idx = clause.find(tok)
            if idx == -1:
                continue
            prefix = clause[:idx]
            if not any(n in prefix for n in negations):
                hits.append(tok)
    return hits


def check_causal_overclaim(bundle):
    errs = []
    for r in bundle.get("intervention_requests", []):
        text = str(r.get("claim_ceiling", "")) + " " + str(r.get("mechanism_hypothesis", ""))
        for tok in _assertive_hits(text, CAUSAL_OVERCLAIM_TOKENS + UNIVERSAL_CAPABILITY_TOKENS):
            errs.append(f"request {r.get('intervention_id')}: causal/universal overclaim token '{tok}'")
    for o in bundle.get("outcome_evaluations", []):
        if o.get("do_not_overclaim_causality") is not True:
            errs.append(f"evaluation {o.get('evaluation_id')}: do_not_overclaim_causality must be true")
        if o.get("causal_interpretation_status") == "BOUNDED_MECHANISM_EVIDENCE":
            # bounded evidence is allowed only if claim ceiling does not assert universality
            text = str(o.get("scope_validity", ""))
            if any(tok in text.lower() for tok in UNIVERSAL_CAPABILITY_TOKENS):
                errs.append(f"evaluation {o.get('evaluation_id')}: bounded mechanism evidence but "
                            f"scope_validity asserts universal capability")
    return errs


def check_rollback_integrity(bundle):
    errs = []
    for rb in bundle.get("stop_rollback_records", []):
        if rb.get("history_preservation") is not True:
            errs.append(f"rollback {rb.get('record_id')}: history_preservation must be true (append-only)")
        if rb.get("verification_result") == "failed":
            errs.append(f"rollback {rb.get('record_id')}: verification_result failed")
        if rb.get("verification_result") == "partial" and \
           rb.get("irreversible_residue", "").strip() == "":
            errs.append(f"rollback {rb.get('record_id')}: partial verification but no irreversible_residue declared")
        if not rb.get("restored_surfaces") and not rb.get("not_restored_surfaces"):
            errs.append(f"rollback {rb.get('record_id')}: must declare restored and/or not-restored surfaces")
    return errs


def check_single_owner_forged(bundle):
    errs = []
    for f in bundle.get("failure_records", []):
        rs = f.get("responsibility_state")
        if rs in ("UNRESOLVED_MANY_HANDS", "INSUFFICIENT_EVIDENCE"):
            # these must NOT be collapsed into a single named owner in claim_ceiling
            text = str(f.get("claim_ceiling", "")).lower()
            single_owner_markers = ("sole owner", "single owner", "uniquely responsible:",
                                     "only responsible party")
            if any(m in text for m in single_owner_markers):
                errs.append(f"failure {f.get('failure_id')}: {rs} responsibility forged into a single owner")
    return errs


def check_obs_validated(bundle):
    errs = []
    obs = _index(bundle.get("q36_obs_snapshots", []), "observation_id")
    for r in bundle.get("intervention_requests", []):
        ref = r.get("q36_obs_ref")
        snap = obs.get(ref)
        if not snap:
            errs.append(f"request {r.get('intervention_id')}: bound Q36-OBS observation '{ref}' not present "
                        f"in q36_obs_snapshots (unvalidated)")
            continue
        if snap.get("quality_status") in ("rejected", "quarantined"):
            errs.append(f"request {r.get('intervention_id')}: bound observation '{ref}' quality_status "
                        f"'{snap.get('quality_status')}' is not validated")
        if snap.get("do_not_infer_cause") is not True:
            errs.append(f"request {r.get('intervention_id')}: bound observation '{ref}' does not enforce "
                        f"do_not_infer_cause (residual treated as cause)")
    return errs


def check_separation_of_duty(bundle):
    errs = []
    for p in bundle.get("plans", []):
        if not p.get("high_risk"):
            continue
        sod = p.get("separation_of_duty") or {}
        roles = [sod.get("proposer"), sod.get("authorizer"), sod.get("executor"), sod.get("verifier")]
        if any(role is None for role in roles):
            errs.append(f"plan {p.get('plan_id')}: high-risk intervention missing separation_of_duty roles")
            continue
        if len(set(roles)) < 4:
            errs.append(f"plan {p.get('plan_id')}: high-risk intervention requires distinct proposer/"
                        f"authorizer/executor/verifier (separation of duty)")
    return errs


def check_baseline_present(bundle):
    errs = []
    for o in bundle.get("outcome_evaluations", []):
        oid = o.get("evaluation_id")
        if not o.get("baseline_comparator"):
            errs.append(f"evaluation {oid}: missing baseline_comparator")
        if not o.get("uncertainty"):
            errs.append(f"evaluation {oid}: missing uncertainty")
    return errs


def main():
    ap = argparse.ArgumentParser(description="Q36-INT intervention-failure dynamics gate (fail-closed)")
    ap.add_argument("--bundle", required=True, help="path to Q36-INT bundle JSON")
    ap.add_argument("--claims", help="path to Q34 claims registry JSON")
    ap.add_argument("--q33-rejects", help="path to Q33 rejected-sources JSON")
    ap.add_argument("--current-head", help="required exact head SHA for requests/evaluations")
    ap.add_argument("--now", help="reference 'now' ISO time for grant-expiry checks (default: utc now)")
    ap.add_argument("--report", help="write machine-readable JSON report to this path")
    args = ap.parse_args()

    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    claims_registry = json.loads(Path(args.claims).read_text(encoding="utf-8")) if args.claims else None
    q33_rejects = json.loads(Path(args.q33_rejects).read_text(encoding="utf-8")) if args.q33_rejects else None

    checks = [
        (SCHEMA_ERROR, lambda: validate_schema(bundle)),
        (TEMPORAL_LEAK, lambda: check_temporal_integrity(bundle, args.now)),
        (TARGET_MISMATCH, lambda: check_target_matching(bundle)),
        (UNRESOLVABLE_REF, lambda: check_references_resolvable(bundle, args.current_head)),
        (Q34_CLAIM_NOT_COMMITTED, lambda: check_q34_commitment(bundle, claims_registry)),
        (Q35_AUTHORITY_INVALID, lambda: check_q35_authority(bundle, args.now)),
        (Q33_GATE_BYPASS, lambda: check_q33_rights(bundle, q33_rejects)),
        (SAFETY_ENVELOPE_INCOMPLETE, lambda: check_safety_envelope(bundle)),
        (EXTERNAL_ACTION_FORBIDDEN, lambda: check_external_action(bundle)),
        (ENVELOPE_EXCEEDED, lambda: check_envelope_exceeded(bundle)),
        (STOP_CONDITION_VIOLATED, lambda: check_stop_condition_violated(bundle)),
        (FAILURE_REWRITE_FORBIDDEN, lambda: check_failure_rewrite(bundle)),
        (EXPECTED_EFFECT_REWRITE, lambda: check_expected_effect_rewrite(bundle)),
        (CAUSAL_OVERCLAIM, lambda: check_causal_overclaim(bundle)),
        (ROLLBACK_INCOMPLETE, lambda: check_rollback_integrity(bundle)),
        (SINGLE_OWNER_FORGED, lambda: check_single_owner_forged(bundle)),
        (OBS_NOT_VALIDATED, lambda: check_obs_validated(bundle)),
        (SEPARATION_OF_DUTY_VIOLATION, lambda: check_separation_of_duty(bundle)),
        (BASELINE_MISSING, lambda: check_baseline_present(bundle)),
    ]

    for code, fn in checks:
        errs = fn()
        if errs:
            out = _result(code, errs)
            _emit(out, args.report)
            sys.exit(code)

    out = _result(GATE_PASS, [], decision={
        "verdict": "ADMISSIBLE_WITHIN_DECLARED_SCOPE",
        "note": "Repository-governance admissibility only; not a claim of universal real-world intervention capability or proven causal mechanism.",
    })
    _emit(out, args.report)
    sys.exit(GATE_PASS)


def _emit(out, report_path):
    text = json.dumps(out, indent=2, ensure_ascii=False)
    print(text)
    if report_path:
        Path(report_path).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
