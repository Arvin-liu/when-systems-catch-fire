#!/usr/bin/env python3
"""Q36-OBS Observation-Prediction Calibration Gate — fail-closed deterministic validator/CLI.

Decides whether an observation-prediction calibration bundle is admissible:
predictions frozen before outcome reveal, outcomes independently bound,
calibration deterministic and scope-bound, residuals preserved, no causal
overclaim, no silent history rewrite, no future-information leakage.

Repository governance only. Does NOT execute interventions (Q36-INT), does NOT
adjudicate causal mechanisms, does NOT assert universal real-world predictive
capability.

Stable exit codes (machine-consumable, never free-text PASS):
  0  GATE_PASS
  2  SCHEMA_ERROR              - bundle failed JSON schema
  3  TEMPORAL_LEAK             - issued_at >= outcome available_at, or input cutoff after outcome available
  4  TARGET_MISMATCH           - prediction target/window/scope/unit does not match outcome
  5  UNRESOLVABLE_REF          - model/version/snapshot/exact-head/digest unresolvable or malformed
  6  Q34_CLAIM_NOT_COMMITTED   - prediction relies on a non-committed Q34 claim
  7  Q35_AUTHORITY_INVALID     - Q35 actor/grant/trajectory reference missing or malformed
  8  Q33_GATE_BYPASS           - observation source is on the Q33 rejected list
  9  ILLEGAL_PROBABILITY       - probability/interval out of legal range or interval inverted
  10 SELF_GENERATED_OUTCOME    - outcome sole evidence produced by the predictor itself
  11 SILENT_PREDICTION_REWRITE - post-reveal in-place prediction modification
  12 SELECTIVE_OUTCOME_DELETION- excluded/abstained/missing outcomes dropped without record
  13 TARGET_DRIFT_UNVERSIONED  - target/definition drift not explicitly versioned
  14 CLAIM_CEILING_BREACH      - finite-scope performance expanded to universal capability
  15 CORRELATION_AS_CAUSATION  - correlation/fit/accuracy upgraded to causal mechanism
  16 CALIBRATION_UNBOUND       - calibration summary lacking sample size/scope/method
  17 FAILURE_DROPPED           - negative result / residual not preserved

Usage:
  python tools/observation/validate_observation_prediction_gate.py --bundle <bundle.json> \
      [--claims <q34-claims.json>] [--q33-rejects <path>] \
      [--current-main-head <sha>] [--report <out.json>]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT / "schemas" / "observation" / "observation-prediction-contract.schema.json"

GATE_PASS = 0
SCHEMA_ERROR = 2
TEMPORAL_LEAK = 3
TARGET_MISMATCH = 4
UNRESOLVABLE_REF = 5
Q34_CLAIM_NOT_COMMITTED = 6
Q35_AUTHORITY_INVALID = 7
Q33_GATE_BYPASS = 8
ILLEGAL_PROBABILITY = 9
SELF_GENERATED_OUTCOME = 10
SILENT_PREDICTION_REWRITE = 11
SELECTIVE_OUTCOME_DELETION = 12
TARGET_DRIFT_UNVERSIONED = 13
CLAIM_CEILING_BREACH = 14
CORRELATION_AS_CAUSATION = 15
CALIBRATION_UNBOUND = 16
FAILURE_DROPPED = 17

EXIT_NAMES = {v: k for k, v in {
    "GATE_PASS": 0, "SCHEMA_ERROR": 2, "TEMPORAL_LEAK": 3, "TARGET_MISMATCH": 4,
    "UNRESOLVABLE_REF": 5, "Q34_CLAIM_NOT_COMMITTED": 6, "Q35_AUTHORITY_INVALID": 7,
    "Q33_GATE_BYPASS": 8, "ILLEGAL_PROBABILITY": 9, "SELF_GENERATED_OUTCOME": 10,
    "SILENT_PREDICTION_REWRITE": 11, "SELECTIVE_OUTCOME_DELETION": 12,
    "TARGET_DRIFT_UNVERSIONED": 13, "CLAIM_CEILING_BREACH": 14,
    "CORRELATION_AS_CAUSATION": 15, "CALIBRATION_UNBOUND": 16, "FAILURE_DROPPED": 17}.items()}

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

# Phrases that expand finite-scope performance into universal predictive capability
UNIVERSAL_CAPABILITY_TOKENS = [
    "universal predictive", "predicts everything", "always predicts", "universally valid prediction",
    "general predictive capability proven", "can predict any", "predicts all", "guaranteed prediction",
    "proven predictive power", "unbounded applicability",
]
# Phrases that upgrade correlation/fit/accuracy into causal mechanism
CAUSAL_OVERCLAIM_TOKENS = [
    "causal mechanism proven", "causation proven", "proves causality", "causal proof",
    "this correlation proves", "fit proves mechanism", "accuracy proves cause",
    "establishes causation", "demonstrates causal",
]


def _parse_time(value):
    try:
        v = value.replace("Z", "+00:00")
        return datetime.fromisoformat(v).astimezone(timezone.utc)
    except Exception:
        return None


def _result(code, errors, decision=None):
    return {"gate": "q36_obs_observation_prediction_gate", "exit_code": code,
            "exit_name": EXIT_NAMES.get(code, "UNKNOWN"), "decision": decision, "errors": errors}


def _index(lst, key):
    return {item.get(key): item for item in lst if isinstance(item, dict) and item.get(key)}


def validate_schema(bundle):
    """Structural validation against the Q36-OBS contract schema."""
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
        # Minimal fallback: required top-level fields only
        errs = []
        for field in ("observations", "predictions", "outcome_bindings", "evaluations", "residuals"):
            if field not in bundle:
                errs.append(f"missing required field: {field}")
        return errs


def check_temporal_integrity(bundle):
    """issued_at < outcome available_at; input_cutoff <= outcome available_at."""
    errs = []
    preds = _index(bundle.get("predictions", []), "prediction_id")
    obs = _index(bundle.get("observations", []), "observation_id")
    for b in bundle.get("outcome_bindings", []):
        if b.get("inclusion_status") not in ("included",):
            continue
        p = preds.get(b.get("prediction_id"))
        o = obs.get(b.get("outcome_observation_id"))
        if not p or not o:
            continue  # unresolved refs handled elsewhere
        issued = _parse_time(p.get("issued_at", ""))
        avail = _parse_time(b.get("outcome_available_at", "") or o.get("available_at", ""))
        cutoff = _parse_time(p.get("input_cutoff_time", ""))
        if issued is None or avail is None:
            errs.append(f"binding {b.get('binding_id')}: unparseable issued_at/outcome_available_at")
            continue
        if issued >= avail:
            errs.append(f"binding {b.get('binding_id')}: prediction {p.get('prediction_id')} issued_at "
                        f"{p.get('issued_at')} not strictly before outcome available_at {b.get('outcome_available_at')}")
        if cutoff is not None and cutoff > avail:
            errs.append(f"binding {b.get('binding_id')}: prediction {p.get('prediction_id')} input_cutoff_time "
                        f"after outcome available_at (future information leak)")
    # observation itself: available_at >= observed_at
    for o in bundle.get("observations", []):
        oa = _parse_time(o.get("available_at", ""))
        ob = _parse_time(o.get("observed_at", ""))
        if oa is not None and ob is not None and oa < ob:
            errs.append(f"observation {o.get('observation_id')}: available_at before observed_at")
    return errs


def check_target_matching(bundle):
    """Prediction normalized_target/evaluation_window/scope must match outcome construct/window/scope."""
    errs = []
    preds = _index(bundle.get("predictions", []), "prediction_id")
    obs = _index(bundle.get("observations", []), "observation_id")
    for b in bundle.get("outcome_bindings", []):
        if b.get("inclusion_status") != "included":
            continue
        p = preds.get(b.get("prediction_id"))
        o = obs.get(b.get("outcome_observation_id"))
        if not p or not o:
            continue
        # The matching rule must reference the normalized target and the outcome construct.
        rule = str(b.get("matching_rule", ""))
        if p.get("normalized_target") and o.get("construct"):
            if p["normalized_target"] not in rule or o["construct"] not in rule:
                errs.append(f"binding {b.get('binding_id')}: matching_rule must cover prediction "
                            f"normalized_target '{p['normalized_target']}' and outcome construct '{o['construct']}'")
        # window overlap: outcome sampling window must intersect the prediction evaluation window
        ew = p.get("evaluation_window", {})
        sw = o.get("sampling_window", {})
        ew_s, ew_e = _parse_time(ew.get("start", "")), _parse_time(ew.get("end", ""))
        sw_s, sw_e = _parse_time(sw.get("start", "")), _parse_time(sw.get("end", ""))
        if None not in (ew_s, ew_e, sw_s, sw_e):
            if sw_e < ew_s or sw_s > ew_e:
                errs.append(f"binding {b.get('binding_id')}: outcome sampling window "
                            f"[{sw.get('start')},{sw.get('end')}] does not intersect prediction evaluation window "
                            f"[{ew.get('start')},{ew.get('end')}] (window drift)")
        # scope: outcome target_scope must be within the prediction applicability scope (string containment)
        if o.get("target_scope") and p.get("applicability_scope"):
            if o["target_scope"] not in p["applicability_scope"] and p["applicability_scope"] not in o["target_scope"]:
                errs.append(f"binding {b.get('binding_id')}: outcome scope '{o['target_scope']}' outside prediction "
                            f"applicability scope '{p['applicability_scope']}'")
    return errs


def check_references_resolvable(bundle, current_main_head):
    errs = []
    for p in bundle.get("predictions", []):
        pid = p.get("prediction_id")
        if not SHA256_RE.match(str(p.get("input_snapshot_digest", ""))):
            errs.append(f"prediction {pid}: malformed input_snapshot_digest")
        if not HEAD_RE.match(str(p.get("exact_head", ""))):
            errs.append(f"prediction {pid}: malformed exact_head")
        if current_main_head and p.get("exact_head") and p.get("exact_head") != current_main_head:
            # exact head pinning: predictions must bind to the declared working head
            errs.append(f"prediction {pid}: exact_head {p.get('exact_head')} != required {current_main_head}")
        if not SHA256_RE.match(str(p.get("q35_trajectory_event_digest", ""))):
            errs.append(f"prediction {pid}: malformed q35_trajectory_event_digest")
        mv = str(p.get("model_rule_version", "")).strip().lower()
        if not mv or mv in ("gpt", "claude", "kimi", "hy3", "unknown"):
            errs.append(f"prediction {pid}: model_rule_version '{p.get('model_rule_version')}' not resolvable")
    for o in bundle.get("observations", []):
        oid = o.get("observation_id")
        if not HEAD_RE.match(str(o.get("exact_head", ""))):
            errs.append(f"observation {oid}: malformed exact_head")
    return errs


def check_q34_commitment(bundle, claims_registry):
    errs = []
    states = {}
    if claims_registry:
        for c in claims_registry.get("claims", []):
            states[c.get("claim_id")] = c.get("state")
    for p in bundle.get("predictions", []):
        ref = p.get("q34_claim_ref")
        if not ref:
            errs.append(f"prediction {p.get('prediction_id')}: missing q34_claim_ref")
            continue
        if ref in states and states[ref] != "committed_current":
            errs.append(f"prediction {p.get('prediction_id')}: q34 claim '{ref}' state "
                        f"'{states[ref]}' is not committed_current")
    return errs


def check_q35_authority(bundle):
    errs = []
    for p in bundle.get("predictions", []):
        pid = p.get("prediction_id")
        for field in ("q35_actor_ref", "q35_grant_ref", "q35_trajectory_event_digest"):
            if not p.get(field):
                errs.append(f"prediction {pid}: missing {field}")
    for b in bundle.get("outcome_bindings", []):
        if not b.get("evaluator_ref"):
            errs.append(f"binding {b.get('binding_id')}: missing evaluator_ref")
    return errs


def check_q33_rights(bundle, q33_rejects):
    errs = []
    rejected = set()
    if q33_rejects:
        rejected = set(q33_rejects.get("rejected", []))
    for o in bundle.get("observations", []):
        src = o.get("source_ref", "")
        if src in rejected:
            errs.append(f"observation {o.get('observation_id')}: source_ref '{src}' is Q33-rejected; "
                        f"publication gate bypassed")
    return errs


def check_probability_legality(bundle):
    errs = []
    for p in bundle.get("predictions", []):
        v = p.get("prediction_value", {})
        pid = p.get("prediction_id")
        kind = v.get("kind")
        if kind != p.get("prediction_type"):
            errs.append(f"prediction {pid}: prediction_value.kind '{kind}' != prediction_type "
                            f"'{p.get('prediction_type')}'")
        if kind == "interval":
            lo, hi = v.get("interval_lower"), v.get("interval_upper")
            if lo is not None and hi is not None and lo > hi:
                errs.append(f"prediction {pid}: interval inverted (lower {lo} > upper {hi})")
            conf = v.get("interval_confidence")
            if conf is not None and not (0 <= conf <= 1):
                errs.append(f"prediction {pid}: interval_confidence {conf} out of [0,1]")
        if kind == "class":
            pr = v.get("class_probability")
            if pr is not None and not (0 <= pr <= 1):
                errs.append(f"prediction {pid}: class_probability {pr} out of [0,1]")
    for e in bundle.get("evaluations", []):
        m = e.get("metrics", {})
        for key in ("interval_coverage", "brier_score", "accuracy"):
            if key in m and not (0 <= m[key] <= 1):
                errs.append(f"evaluation {e.get('evaluation_id')}: metric {key}={m[key]} out of [0,1]")
    return errs


def check_outcome_independence(bundle):
    errs = []
    preds = _index(bundle.get("predictions", []), "prediction_id")
    for b in bundle.get("outcome_bindings", []):
        if b.get("independent_evidence_status") == "self_generated_forbidden":
            p = preds.get(b.get("prediction_id"), {})
            errs.append(f"binding {b.get('binding_id')}: outcome for prediction "
                        f"{b.get('prediction_id')} is self-generated by the predictor "
                        f"(model_rule_version '{p.get('model_rule_version')}') as sole evidence — forbidden")
    return errs


def check_no_silent_rewrite(bundle):
    """A superseded prediction must keep its original record and link via superseded_by;
    two predictions with the same id but different digests = silent in-place rewrite."""
    errs = []
    seen = {}
    for p in bundle.get("predictions", []):
        pid = p.get("prediction_id")
        if pid in seen:
            prev = seen[pid]
            # same id appearing twice is only legal as an explicit supersession chain
            if not (p.get("status") == "superseded" or prev.get("superseded_by") == pid
                    or p.get("superseded_by") or prev.get("status") == "superseded"):
                errs.append(f"prediction {pid}: duplicate id without explicit supersession chain "
                            f"(silent rewrite suspected)")
        seen[pid] = p
    for p in bundle.get("predictions", []):
        if p.get("status") == "superseded" and not p.get("superseded_by"):
            errs.append(f"prediction {p.get('prediction_id')}: status superseded but no superseded_by link")
    return errs


def check_outcome_preservation(bundle):
    errs = []
    for b in bundle.get("outcome_bindings", []):
        st = b.get("inclusion_status")
        if st == "excluded_with_reason" and not b.get("exclusion_reason"):
            errs.append(f"binding {b.get('binding_id')}: excluded_with_reason but no exclusion_reason")
    # every prediction that is frozen must have some binding or an explicit abstain/defer status
    bound_preds = {b.get("prediction_id") for b in bundle.get("outcome_bindings", [])}
    for p in bundle.get("predictions", []):
        if p.get("status") == "frozen" and p.get("prediction_id") not in bound_preds:
            errs.append(f"prediction {p.get('prediction_id')}: frozen but has no outcome binding record "
                        f"(outcome silently dropped?)")
    return errs


def check_target_drift_versioning(bundle):
    """If two predictions share a prediction family (same prefix before last segment) but
    declare different normalized_target strings, drift must be versioned via '::vN' suffix."""
    errs = []
    families = {}
    for p in bundle.get("predictions", []):
        pid = p.get("prediction_id", "")
        fam = pid.rsplit("-", 1)[0] if "-" in pid else pid
        families.setdefault(fam, set()).add(p.get("normalized_target", ""))
    for fam, targets in families.items():
        if len(targets) > 1:
            # drift present: each target must carry an explicit version marker
            for t in targets:
                if "::v" not in t:
                    errs.append(f"prediction family '{fam}': target drift '{t}' not explicitly versioned "
                                f"(expected '::vN' marker)")
    return errs


def _assertive_hits(text, tokens):
    """Return tokens that appear in an ASSERTIVE (non-negated) context.

    Negation is scoped to the same clause: we split the text on sentence/clause
    boundaries ('.', ';', newline) and only treat a token as disclaimed when a
    negation marker appears in the SAME clause before the token. This prevents a
    disclaimer in one clause ('not a universal predictive capability') from
    masking an overclaim in the next clause ('the high fit establishes causation').
    """
    hits = []
    lower = text.lower()
    negations = ("not ", "no ", "never ", "without ", "does not ", "did not ",
                 "cannot ", "must not ", "nor ", "neither ", "n't ")
    clauses = re.split(r"[.;\n]", lower)
    for clause in clauses:
        for tok in tokens:
            idx = clause.find(tok)
            if idx == -1:
                continue
            prefix = clause[:idx]
            if not any(n in prefix for n in negations):
                hits.append(tok)
    return hits


def check_claim_ceiling(bundle):
    errs = []
    for p in bundle.get("predictions", []):
        text = str(p.get("claim_ceiling", "")) + " " + str(p.get("applicability_scope", ""))
        for tok in _assertive_hits(text, UNIVERSAL_CAPABILITY_TOKENS):
            errs.append(f"prediction {p.get('prediction_id')}: universal-capability overclaim token '{tok}'")
    for e in bundle.get("evaluations", []):
        text = str(e.get("scope_summary", ""))
        for tok in _assertive_hits(text, UNIVERSAL_CAPABILITY_TOKENS):
            errs.append(f"evaluation {e.get('evaluation_id')}: universal-capability overclaim token '{tok}'")
    return errs


def check_no_causal_overclaim(bundle):
    errs = []
    for p in bundle.get("predictions", []):
        text = str(p.get("claim_ceiling", "")) + " " + str(p.get("uncertainty", ""))
        for tok in _assertive_hits(text, CAUSAL_OVERCLAIM_TOKENS):
            errs.append(f"prediction {p.get('prediction_id')}: causal overclaim token '{tok}'")
    for r in bundle.get("residuals", []):
        if r.get("do_not_infer_cause") is not True:
            errs.append(f"residual {r.get('residual_id')}: do_not_infer_cause must be true")
    return errs


def check_calibration_binding(bundle):
    errs = []
    for e in bundle.get("evaluations", []):
        eid = e.get("evaluation_id")
        if not e.get("sample_size"):
            errs.append(f"evaluation {eid}: missing sample_size")
        if not e.get("scope_summary"):
            errs.append(f"evaluation {eid}: missing scope_summary")
        if not e.get("computation_method"):
            errs.append(f"evaluation {eid}: missing computation_method")
        if not e.get("baseline_comparison"):
            errs.append(f"evaluation {eid}: missing baseline_comparison")
    return errs


def check_failure_preservation(bundle):
    """Negative results must be preserved: any binding that is missing/deferred or any
    evaluation with large residual must have a residual record."""
    errs = []
    residual_preds = {r.get("prediction_id") for r in bundle.get("residuals", [])}
    residual_bindings = {r.get("binding_id") for r in bundle.get("residuals", [])}
    preds = _index(bundle.get("predictions", []), "prediction_id")
    for b in bundle.get("outcome_bindings", []):
        if b.get("inclusion_status") in ("missing", "deferred") and b.get("binding_id") not in residual_bindings:
            errs.append(f"binding {b.get('binding_id')}: {b.get('inclusion_status')} outcome has no residual record")
    for e in bundle.get("evaluations", []):
        m = e.get("metrics", {})
        # a clear miss (interval_coverage == 0 with an interval prediction, or accuracy == 0)
        # without a residual record = dropped failure
        if m.get("accuracy") == 0 or m.get("interval_coverage") == 0:
            # find the binding -> prediction
            b = next((x for x in bundle.get("outcome_bindings", []) if x.get("binding_id") == e.get("binding_id")), None)
            if b and b.get("prediction_id") not in residual_preds:
                errs.append(f"evaluation {e.get('evaluation_id')}: clear miss (accuracy/coverage 0) has no residual record")
    return errs


def main():
    ap = argparse.ArgumentParser(description="Q36-OBS observation-prediction calibration gate (fail-closed)")
    ap.add_argument("--bundle", required=True, help="path to Q36-OBS bundle JSON")
    ap.add_argument("--claims", help="path to Q34 claims registry JSON")
    ap.add_argument("--q33-rejects", help="path to Q33 rejected-sources JSON")
    ap.add_argument("--current-main-head", help="required exact head SHA for predictions/observations")
    ap.add_argument("--report", help="write machine-readable JSON report to this path")
    args = ap.parse_args()

    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    claims_registry = json.loads(Path(args.claims).read_text(encoding="utf-8")) if args.claims else None
    q33_rejects = json.loads(Path(args.q33_rejects).read_text(encoding="utf-8")) if args.q33_rejects else None

    checks = [
        (SCHEMA_ERROR, lambda: validate_schema(bundle)),
        (TEMPORAL_LEAK, lambda: check_temporal_integrity(bundle)),
        (TARGET_MISMATCH, lambda: check_target_matching(bundle)),
        (UNRESOLVABLE_REF, lambda: check_references_resolvable(bundle, args.current_main_head)),
        (Q34_CLAIM_NOT_COMMITTED, lambda: check_q34_commitment(bundle, claims_registry)),
        (Q35_AUTHORITY_INVALID, lambda: check_q35_authority(bundle)),
        (Q33_GATE_BYPASS, lambda: check_q33_rights(bundle, q33_rejects)),
        (ILLEGAL_PROBABILITY, lambda: check_probability_legality(bundle)),
        (SELF_GENERATED_OUTCOME, lambda: check_outcome_independence(bundle)),
        (SILENT_PREDICTION_REWRITE, lambda: check_no_silent_rewrite(bundle)),
        (SELECTIVE_OUTCOME_DELETION, lambda: check_outcome_preservation(bundle)),
        (TARGET_DRIFT_UNVERSIONED, lambda: check_target_drift_versioning(bundle)),
        (CLAIM_CEILING_BREACH, lambda: check_claim_ceiling(bundle)),
        (CORRELATION_AS_CAUSATION, lambda: check_no_causal_overclaim(bundle)),
        (CALIBRATION_UNBOUND, lambda: check_calibration_binding(bundle)),
        (FAILURE_DROPPED, lambda: check_failure_preservation(bundle)),
    ]

    for code, fn in checks:
        errs = fn()
        if errs:
            out = _result(code, errs)
            _emit(out, args.report)
            sys.exit(code)

    out = _result(GATE_PASS, [], decision={
        "verdict": "ADMISSIBLE_WITHIN_DECLARED_SCOPE",
        "note": "Repository-governance admissibility only; not a claim of universal real-world predictive capability.",
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
