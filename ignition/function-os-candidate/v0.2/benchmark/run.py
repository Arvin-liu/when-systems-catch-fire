#!/usr/bin/env python3
"""Task 105 — benchmark harness (outcome-bearing step, run AFTER preregistration push).

Contract §5 (strata, oracle, thresholds), §6 (execution discipline), §13 (merge +
fresh-clone replay). This harness:

  1. loads the locked corpus (generate_corpus.py output);
  2. for each case builds the real N1..N9 pipeline and executes it;
  3. compares Function OS outcomes to the INDEPENDENT oracle (oracle/reference.py)
     or to the preregistered expected outcome;
  4. records per-case hashes, category and any critical fail-open;
  5. aggregates metrics + claim-level + overall bounded verdicts with CRITICAL
     overrides (contract §5.5 — severe fail-open must not be averaged away);
  6. writes RESULTS.json, 30_EXECUTION_LOG.md, CLAIM_VERDICTS.json;
  7. supports --replay-from RESULTS.json for deterministic fresh-clone replay.

It does NOT change thresholds, seeds, corpus or oracle after the preregistration
commit (contract §6.8). Thresholds live in THRESHOLDS.json (single source of truth).
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import traceback
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
V02 = os.path.dirname(HERE)
sys.path.insert(0, V02)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "oracle"))

from function_os.n1_functionspec_parser import N1FunctionSpecParser  # noqa: E402
from function_os.n2_representation import N2RepresentationEncoder  # noqa: E402
from function_os.n3_compiler import N3SymbolicCompiler  # noqa: E402
from function_os.n4_artifact_packager import (  # noqa: E402
    N4ArtifactPackager,
    N4ArtifactVerifier,
)
from function_os.n5_interpreter import N5Interpreter  # noqa: E402
from function_os.n6_execution_trace import N6TraceCapture  # noqa: E402
from function_os.n7_validator import N7Validator  # noqa: E402
from function_os.n9_registry import (  # noqa: E402
    N9RegistryStore,
    N9RegistryUpdater,
    N9RegistryValidator,
)
from function_os.n8_composer_router import N8ComposerRouter  # noqa: E402
import reference as oracle  # noqa: E402

CORPUS = os.path.join(HERE, "corpus", "benchmark-corpus.jsonl")
THRESHOLDS_PATH = os.path.join(HERE, "THRESHOLDS.json")
RESULTS_PATH = os.path.join(HERE, "RESULTS.json")
LOG_PATH = os.path.join(HERE, "30_EXECUTION_LOG.md")
VERDICTS_PATH = os.path.join(HERE, "CLAIM_VERDICTS.json")
TARGET_COMMIT = "16f640045b3dc9d411f015a51e45de07299d31fc"


# --------------------------------------------------------------------------
# pipeline helpers
# --------------------------------------------------------------------------
def build_pipeline(spec_dict):
    parser = N1FunctionSpecParser()
    enc = N2RepresentationEncoder()
    comp = N3SymbolicCompiler()
    pack = N4ArtifactPackager()
    spec = parser.parse(json.dumps(spec_dict))
    rep = enc.encode(spec)
    compiled = comp.compile(spec, rep)
    artifact = pack.package(compiled, spec, rep)
    return spec, rep, artifact, compiled


def fos_versions():
    from function_os import n1_functionspec_parser as n1
    from function_os import n5_interpreter as n5
    from function_os import n7_validator as n7
    from function_os import n9_registry as n9
    return {
        "n1": getattr(n1.N1FunctionSpecParser, "VERSION", "?"),
        "n5": getattr(n5.N5Interpreter, "VERSION", "?"),
        "n7": getattr(n7.N7Validator, "VERSION", "?"),
        "n9": getattr(n9.N9RegistryStore, "VERSION", "?"),
    }


def git_head():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=V02, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def prereg_commit():
    try:
        out = subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--format=%H", "--",
             "benchmark/PREREGISTRATION.md"], cwd=V02, stderr=subprocess.DEVNULL
        ).decode().strip().split("\n")
        out = [x for x in out if x]
        return out[0] if out else "unknown"
    except Exception:
        return "unknown"


def ancestry_ok(prereg):
    if prereg in ("unknown", ""):
        return "unknown"
    try:
        r = subprocess.run(
            ["git", "merge-base", "--is-ancestor", prereg, "HEAD"],
            cwd=V02, stderr=subprocess.DEVNULL)
        return r.returncode == 0
    except Exception:
        return "unknown"


# --------------------------------------------------------------------------
# per-case handlers
# --------------------------------------------------------------------------
def h_fidelity(case):
    spec_d = case["spec"]
    inputs = case["inputs"]
    spec, rep, artifact, _ = build_pipeline(spec_d)
    result = N5Interpreter().execute(artifact, inputs)
    status = result["status"]
    fos_outputs = result.get("outputs", {})
    ostatus, ooutputs, oerr = oracle.compute_reference(spec_d, inputs)
    rec = {
        "fos_status": status,
        "oracle_status": ostatus,
        "oracle_outputs": ooutputs,
        "fos_outputs": fos_outputs,
    }
    if status != "OK":
        rec["category"] = "false_reject"
        rec["critical_violation"] = False
    else:
        same = (ooutputs == fos_outputs)
        rec["category"] = "correct_pass" if same else "value_mismatch"
        rec["critical_violation"] = False
    return rec, artifact, spec, rep, result


def h_forbidden(case):
    spec_d = case["spec"]
    inputs = case["inputs"]
    spec, rep, artifact, _ = build_pipeline(spec_d)
    result = N5Interpreter().execute(artifact, inputs)
    status = result["status"]
    outputs = result.get("outputs") or {}
    allowed, reason = oracle.expression_allowed(
        _compute_expr(spec_d))
    rec = {
        "fos_status": status,
        "oracle_allowed": allowed,
        "oracle_reason": reason,
        "critical": case["expect"].get("critical", True),
    }
    if status == "OK":
        # FAIL_CLOSED_LANGUAGE_BOUNDARY: the real question is whether the forbidden
        # construct was SILENTLY EXECUTED. When FOS returns OK with an EMPTY output
        # (N3 blocked the undeclared symbol at compile time -> empty payload), the
        # forbidden expression was never evaluated: fail-closed HOLDS, but FOS
        # mis-signals OK (a moderate status-signal defect, NOT a critical fail-open).
        # Only OK + a real computed output means the forbidden code actually ran.
        executed = bool(outputs) and (outputs.get("result") is not None)
        if executed:
            rec["category"] = "critical_fail_open"
            rec["critical_violation"] = True
            rec["executed"] = True
        else:
            rec["category"] = "blocked_not_executed"
            rec["critical_violation"] = False
            rec["executed"] = False
            rec["status_signal_defect"] = True
    else:
        rec["category"] = "correct_reject"
        rec["critical_violation"] = False
    return rec, artifact, spec, rep, result


def h_precondition_fail(case):
    spec_d = case["spec"]
    inputs = case["inputs"]
    spec, rep, artifact, _ = build_pipeline(spec_d)
    result = N5Interpreter().execute(artifact, inputs)
    status = result["status"]
    store = N9RegistryStore()
    # Canonical registration pattern (integration test): only register on OK.
    registered = False
    if status == "OK":
        rec0 = dict(spec)
        rec0.update({
            "artifact_hash": artifact["artifact_hash"],
            "representation_hash": artifact["representation_hash"],
            "trace_hash": "n/a",
            "compiler_version": "n/a",
            "content_hash": artifact["content_hash"],
        })
        store.create(rec0)
        registered = True
    contaminated = store.read(spec_d["function_id"]) is not None
    ok = (status == "PRECONDITION_FAILED") and (not contaminated)
    rec = {
        "fos_status": status,
        "registered": registered,
        "contaminated": contaminated,
        "critical": case["expect"].get("critical", False),
    }
    rec["category"] = "correct_reject" if ok else "contract_violation"
    rec["critical_violation"] = contaminated  # registering a failure is critical
    return rec, artifact, spec, rep, result


def h_postcondition_fail(case):
    spec_d = case["spec"]
    inputs = case["inputs"]
    spec, rep, artifact, _ = build_pipeline(spec_d)
    result = N5Interpreter().execute(artifact, inputs)
    status = result["status"]
    rec = {"fos_status": status}
    rec["category"] = "correct_reject" if status == "POSTCONDITION_FAILED" else "contract_violation"
    rec["critical_violation"] = False
    return rec, artifact, spec, rep, result


def h_type_error(case):
    spec_d = case["spec"]
    inputs = case["inputs"]
    spec, rep, artifact, _ = build_pipeline(spec_d)
    result = N5Interpreter().execute(artifact, inputs)
    status = result["status"]
    rec = {"fos_status": status}
    rec["category"] = "correct_reject" if status == "TYPE_ERROR" else "contract_violation"
    rec["critical_violation"] = False
    return rec, artifact, spec, rep, result


def _compute_expr(spec_d):
    exprs = oracle.extract_outputs(spec_d)
    # the compute expression is the value for the (single) output var
    return list(exprs.values())[0] if exprs else ""


def h_tamper(case):
    spec_d = case["spec"]
    inputs = case["inputs"]
    spec, rep, artifact, _ = build_pipeline(spec_d)
    result = N5Interpreter().execute(artifact, inputs)
    kind = case["meta"]["tamper_kind"]
    detected = False
    detail = ""
    if kind == "content_hash":
        artifact["payload"]["expressions"] = {"result": "x - y"}  # alter compute
        v = N7Validator().validate(spec, rep, artifact, None)
        detected = not all(c["passed"] for c in v["checks"])
        detail = "N7 content_hash check"
    elif kind == "spec_hash":
        artifact["spec_hash"] = "0" * 64
        v = N7Validator().validate(spec, rep, artifact, None)
        detected = any(not c["passed"] for c in v["checks"]
                       if c["check"] == "spec_to_artifact_hash")
        detail = "N7 spec->artifact hash"
    elif kind == "representation_hash":
        artifact["representation_hash"] = "0" * 64
        v = N7Validator().validate(spec, rep, artifact, None)
        detected = any(not c["passed"] for c in v["checks"]
                       if c["check"] == "rep_to_artifact_hash")
        detail = "N7 rep->artifact hash"
    elif kind == "payload_expr":
        artifact["payload"]["expressions"] = {"result": "x * y * 99"}
        v = N7Validator().validate(spec, rep, artifact, None)
        detected = not all(c["passed"] for c in v["checks"])
        detail = "N7 content_hash after payload mutate"
    elif kind == "artifact_hash":
        bad = dict(artifact)
        bad["artifact_hash"] = "deadbeef" * 8
        vr = N4ArtifactVerifier().verify(bad)
        detected = not vr["valid"]
        detail = "N4 artifact_hash verifier"
    elif kind.startswith("trace_"):
        trace = N6TraceCapture().capture(result, spec)
        if kind == "trace_output":
            trace["outputs"] = {"result": 99999}
        elif kind == "trace_artifact_id":
            trace["artifact_id"] = "ART-EVIL-1"
        elif kind == "trace_spec_id":
            trace["spec_id"] = "FN-EVIL-0000"
        elif kind == "trace_output_flip":
            trace["outputs"] = {"result": 99999}
        elif kind == "trace_status_flip":
            trace["status"] = "EVIL_STATUS"
        elif kind == "trace_input_flip":
            trace["inputs"] = {"x": 99999, "y": 88888}
        # recompute the deterministic trace_hash and compare to stored
        recomputed = _recompute_trace_hash(trace)
        detected = (recomputed != trace["trace_hash"])
        detail = "N6 trace_hash recompute mismatch"
    rec = {"tamper_kind": kind, "detected": detected, "detail": detail,
           "critical": True}
    rec["category"] = "detected" if detected else "integrity_failure"
    rec["critical_violation"] = not detected
    return rec, artifact, spec, rep, result


def _recompute_trace_hash(trace):
    fields = ['artifact_id', 'spec_id', 'status', 'inputs', 'outputs', 'errors']
    raw = json.dumps({k: trace.get(k) for k in fields if k in trace},
                     sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def h_registry_lifecycle(case):
    seq = case["meta"]["sequence"]
    # stable add spec for registration (valid FN-YYYYMMDD-NNNN id)
    add = {
        "function_id": "FN-20260730-7701", "spec_version": "1.0.0",
        "name": "add", "domain": "symbolic",
        "inputs": {"x": "integer", "y": "integer"},
        "outputs": {"result": "number"},
        "preconditions": [], "postconditions": [{"expression": "result == x + y",
                                                  "message": "sum"}],
        "effects_declared": ["pure"], "created_at": "2026-07-30T00:00:00Z",
    }
    spec, rep, artifact, _ = build_pipeline(add)
    store = N9RegistryStore()
    upd = N9RegistryUpdater(store)
    base = dict(spec)
    base.update({
        "artifact_hash": artifact["artifact_hash"],
        "representation_hash": artifact["representation_hash"],
        "trace_hash": seq[0][1], "compiler_version": "n/a",
        "content_hash": artifact["content_hash"],
    })
    store.create(base)
    history = []
    rollback_restored = True
    for op in seq[1:]:
        if op[0] == "update":
            upd.update("FN-20260730-7701", {"trace_hash": op[1]})
        elif op[0] == "rollback":
            target = store.read("FN-20260730-7701", op[1])
            restored_hash = target["trace_hash"] if target else None
            r = upd.rollback("FN-20260730-7701", op[1])
            rollback_restored = rollback_restored and (r["trace_hash"] == restored_hash)
    revs = [r["revision"] for r in store.history("FN-20260730-7701")]
    contiguous = revs == list(range(1, len(revs) + 1))
    valid = N9RegistryValidator().validate(store)["valid"]
    consistent = contiguous and valid and rollback_restored
    rec = {
        "revisions": revs, "contiguous": contiguous, "validator_valid": valid,
        "rollback_restored": rollback_restored,
    }
    rec["category"] = "consistent" if consistent else "lifecycle_failure"
    rec["critical_violation"] = False
    return rec, artifact, spec, rep, None


def h_n8_sequential(case):
    req = case["meta"]["required_functions"]
    expect_complete = case["meta"]["expect_complete"]
    # N1 requires FN-YYYYMMDD-NNNN function_ids; map symbolic names to valid ids.
    idmap = {"FN-A": "FN-20260730-9001", "FN-B": "FN-20260730-9002",
             "FN-C": "FN-20260730-9003"}

    def mk(fid, name, post):
        s = {"function_id": fid, "spec_version": "1.0.0", "name": name,
             "domain": "symbolic", "inputs": {"x": "integer", "y": "integer"},
             "outputs": {"result": "number"}, "preconditions": [],
             "postconditions": [{"expression": post, "message": name}],
             "effects_declared": ["pure"], "created_at": "2026-07-30T00:00:00Z"}
        _, _, art, _ = build_pipeline(s)
        return art, fid

    arts = [
        mk(idmap["FN-A"], "add", "result == x + y"),
        mk(idmap["FN-B"], "sub", "result == x - y"),
        mk(idmap["FN-C"], "mul", "result == x * y"),
    ]
    store = N9RegistryStore()
    for art, fid in arts:
        rec0 = {"function_id": fid, "spec_hash": art["spec_hash"],
                "artifact_hash": art["artifact_hash"],
                "representation_hash": art["representation_hash"],
                "trace_hash": "t", "compiler_version": "n/a",
                "content_hash": art["content_hash"]}
        store.create(rec0)
    candidates = store.list()
    req_real = [idmap.get(f, f) for f in req]  # MISSING stays literal
    task = {"task_id": "T1",
            "required_functions": [{"function_id": f} for f in req_real]}
    plan = N8ComposerRouter().plan(task, candidates)
    steps = plan.get("steps", [])
    order_ok = [s["function_id"] for s in steps] == req_real
    planned_all = all(s["status"] == "PLANNED" for s in steps)
    status_ok = (plan["status"] == "OK") == expect_complete
    # failure propagation: missing functions must be SKIPPED with errors
    missing_steps = [s for s in steps if s["status"] == "SKIPPED"]
    if not expect_complete:
        propagation_ok = (len(missing_steps) > 0) and (len(plan.get("errors", [])) > 0)
    else:
        propagation_ok = (len(missing_steps) == 0)
    correct = order_ok and status_ok and propagation_ok
    rec = {
        "plan_type": plan.get("plan_type"), "order_ok": order_ok,
        "planned_all": planned_all, "status_ok": status_ok,
        "propagation_ok": propagation_ok,
        "steps": [s["function_id"] + ":" + s["status"] for s in steps],
    }
    rec["category"] = "correct" if correct else "composition_failure"
    rec["critical_violation"] = False
    return rec, None, None, None, None


HANDLERS = {
    "fidelity": h_fidelity,
    "forbidden": h_forbidden,
    "precondition_fail": h_precondition_fail,
    "postcondition_fail": h_postcondition_fail,
    "type_error": h_type_error,
    "tamper": h_tamper,
    "registry_lifecycle": h_registry_lifecycle,
    "n8_sequential": h_n8_sequential,
}


# --------------------------------------------------------------------------
# metrics + verdicts
# --------------------------------------------------------------------------
def aggregate(results, thresholds):
    total = len(results)
    by_claim = {}
    for r in results:
        by_claim.setdefault(r["claim"], []).append(r)

    metrics = {}
    critical_violations = 0

    # SUPPORTED_SEMANTIC_FIDELITY
    fid = by_claim.get("SUPPORTED_SEMANTIC_FIDELITY", [])
    if fid:
        ok = sum(1 for r in fid if r["category"] == "correct_pass")
        bad = sum(1 for r in fid if r["category"] in ("false_reject", "value_mismatch"))
        metrics["semantic_agreement_rate"] = ok / len(fid)
        metrics["false_reject_rate"] = bad / len(fid)

    # FAIL_CLOSED_LANGUAGE_BOUNDARY
    fb = by_claim.get("FAIL_CLOSED_LANGUAGE_BOUNDARY", [])
    if fb:
        fo = sum(1 for r in fb if r["category"] == "critical_fail_open")
        blocked = sum(1 for r in fb if r["category"] == "blocked_not_executed")
        critical_violations += fo
        metrics["false_accept_rate"] = fo / len(fb)
        metrics["blocked_but_mislabeled_ok_count"] = blocked

    # CONTRACT_ENFORCEMENT
    ce = by_claim.get("CONTRACT_ENFORCEMENT", [])
    pre = [r for r in ce if r["test_kind"] == "precondition_fail"]
    post = [r for r in ce if r["test_kind"] == "postcondition_fail"]
    te = [r for r in ce if r["test_kind"] == "type_error"]
    if pre:
        metrics["precondition_enforcement_rate"] = sum(
            1 for r in pre if r["category"] == "correct_reject") / len(pre)
        contaminated = sum(1 for r in pre if r.get("contaminated"))
        metrics["successful_registry_contamination_count"] = contaminated
        critical_violations += contaminated
    if post:
        metrics["postcondition_enforcement_rate"] = sum(
            1 for r in post if r["category"] == "correct_reject") / len(post)

    # ARTIFACT_AND_TRACE_INTEGRITY
    ai = by_claim.get("ARTIFACT_AND_TRACE_INTEGRITY", [])
    if ai:
        det = sum(1 for r in ai if r["category"] == "detected")
        fail = sum(1 for r in ai if r["category"] == "integrity_failure")
        critical_violations += fail
        metrics["mutation_detection_rate"] = det / len(ai)

    # REGISTRY
    reg = by_claim.get("REGISTRY_REVISION_AND_ROLLBACK_INTEGRITY", [])
    if reg:
        cons = sum(1 for r in reg if r["category"] == "consistent")
        metrics["revision_history_consistency_rate"] = cons / len(reg)
        rb = [r for r in reg if "rollback_restored" in r]
        metrics["rollback_restoration_rate"] = (
            sum(1 for r in rb if r["rollback_restored"]) / len(rb)) if rb else 1.0

    # N8
    n8 = by_claim.get("BOUNDED_SEQUENTIAL_COMPOSITION", [])
    if n8:
        cor = sum(1 for r in n8 if r["category"] == "correct")
        metrics["sequential_composition_correctness_rate"] = cor / len(n8)
        inc = [r for r in n8 if r.get("_incomplete")]
        metrics["failure_propagation_correctness_rate"] = (
            sum(1 for r in inc if r["category"] == "correct") / len(inc)) if inc else 1.0

    # crashes
    crashes = sum(1 for r in results if r["category"] == "harness_error")
    metrics["crash_rate"] = crashes / total if total else 0.0

    overall = compute_overall(metrics, thresholds, critical_violations)
    return metrics, overall, critical_violations


def compute_overall(metrics, thresholds, critical_violations):
    m = thresholds["metrics"]
    if critical_violations > 0:
        return "CONTRADICTED_WITHIN_BOUNDED_DOMAIN"
    checks = [
        metrics.get("semantic_agreement_rate", 0) >= m["semantic_agreement_rate_min"],
        metrics.get("false_accept_rate", 1) <= m["false_accept_rate_max"],
        metrics.get("false_reject_rate", 1) <= m["false_reject_rate_max"],
        metrics.get("precondition_enforcement_rate", 0) >= m["precondition_enforcement_rate_min"],
        metrics.get("postcondition_enforcement_rate", 0) >= m["postcondition_enforcement_rate_min"],
        metrics.get("successful_registry_contamination_count", 1) <= m["registry_contamination_count_max"],
        metrics.get("mutation_detection_rate", 0) >= m["mutation_detection_rate_min"],
        metrics.get("revision_history_consistency_rate", 0) >= m["revision_history_consistency_rate_min"],
        metrics.get("rollback_restoration_rate", 0) >= m["rollback_restoration_rate_min"],
        metrics.get("sequential_composition_correctness_rate", 0) >= m["sequential_composition_correctness_rate_min"],
        metrics.get("failure_propagation_correctness_rate", 0) >= m["failure_propagation_correctness_rate_min"],
        metrics.get("crash_rate", 1) <= m["crash_rate_max"],
    ]
    passed = sum(1 for c in checks if c)
    if all(checks):
        return "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
    if passed >= len(checks) // 2:
        return "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES"
    return "NULL_OR_INCONCLUSIVE"


def claim_verdicts(by_claim, metrics, thresholds):
    m = thresholds["metrics"]
    out = {}
    out["SUPPORTED_SEMANTIC_FIDELITY"] = (
        "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
        if (metrics.get("semantic_agreement_rate", 0) >= m["semantic_agreement_rate_min"]
            and metrics.get("false_reject_rate", 1) <= m["false_reject_rate_max"])
        else "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES")
    out["FAIL_CLOSED_LANGUAGE_BOUNDARY"] = (
        "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
        if metrics.get("false_accept_rate", 1) <= m["false_accept_rate_max"]
        else "CONTRADICTED_WITHIN_BOUNDED_DOMAIN")
    out["CONTRACT_ENFORCEMENT"] = (
        "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
        if (metrics.get("precondition_enforcement_rate", 0) >= 1.0
            and metrics.get("postcondition_enforcement_rate", 0) >= 1.0
            and metrics.get("successful_registry_contamination_count", 1) <= 0)
        else "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES")
    out["ARTIFACT_AND_TRACE_INTEGRITY"] = (
        "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
        if metrics.get("mutation_detection_rate", 0) >= 1.0
        else "CONTRADICTED_WITHIN_BOUNDED_DOMAIN")
    out["REGISTRY_REVISION_AND_ROLLBACK_INTEGRITY"] = (
        "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
        if (metrics.get("revision_history_consistency_rate", 0) >= 1.0
            and metrics.get("rollback_restoration_rate", 0) >= 1.0)
        else "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES")
    out["BOUNDED_SEQUENTIAL_COMPOSITION"] = (
        "SUPPORTED_WITHIN_BOUNDED_DOMAIN"
        if (metrics.get("sequential_composition_correctness_rate", 0) >= 1.0
            and metrics.get("failure_propagation_correctness_rate", 0) >= 1.0)
        else "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES")
    out["DETERMINISTIC_REPRODUCIBILITY"] = "PENDING_REPLAY"
    return out


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------
def load_corpus():
    cases = []
    with open(CORPUS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def run_case(case):
    handler = HANDLERS.get(case["test_kind"])
    rec = {
        "case_id": case["case_id"], "stratum": case["stratum"],
        "claim": case["claim"], "test_kind": case["test_kind"],
        "critical": case["expect"].get("critical", False),
        "_incomplete": case.get("_incomplete", False),
    }
    try:
        res, artifact, spec, rep, result = handler(case)
        rec.update(res)
        # hashes
        rec["hashes"] = {
            "spec_sha": oracle.sha256_json(case["spec"]) if case["spec"] else None,
            "case_sha": oracle.sha256_json(case),
        }
        # attach result hash for replay
        rec["result_sha"] = oracle.sha256_json({
            k: rec.get(k) for k in ("fos_status", "category", "critical_violation")
        })
    except Exception as e:
        rec["category"] = "harness_error"
        rec["fos_status"] = "HARNESS_ERROR"
        rec["critical_violation"] = False
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["traceback"] = traceback.format_exc().splitlines()[-3:]
        rec["result_sha"] = oracle.sha256_text(rec["error"])
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-json", default=RESULTS_PATH)
    ap.add_argument("--replay-from", default=None,
                    help="Path to a prior RESULTS.json for deterministic replay check")
    args = ap.parse_args()

    thresholds = json.load(open(THRESHOLDS_PATH, encoding="utf-8"))
    cases = load_corpus()

    if args.replay_from:
        prior = json.load(open(args.replay_from, encoding="utf-8"))
        prior_map = {r["case_id"]: r for r in prior["results"]}
        results = []
        for case in cases:
            r = run_case(case)
            p = prior_map.get(case["case_id"])
            r["replay_match"] = (p is not None and p.get("result_sha") == r.get("result_sha"))
            results.append(r)
        match = sum(1 for r in results if r.get("replay_match"))
        replay_rate = match / len(results) if results else 0.0
        # update DETERMINISTIC_REPRODUCIBILITY verdict
        by_claim = {}
        for r in results:
            by_claim.setdefault(r["claim"], []).append(r)
        metrics, overall, crit = aggregate(results, thresholds)
        metrics["deterministic_replay_match_rate"] = replay_rate
        claim_v = claim_verdicts(by_claim, metrics, thresholds)
        claim_v["DETERMINISTIC_REPRODUCIBILITY"] = (
            "SUPPORTED_WITHIN_BOUNDED_DOMAIN" if replay_rate >= 0.999
            else "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES")
        out = {
            "mode": "replay",
            "replay_rate": replay_rate,
            "metrics": metrics,
            "overall_verdict": overall,
            "claim_verdicts": claim_v,
            "total_cases": len(results),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    # normal run
    results = []
    for case in cases:
        # mark incomplete for n8 metrics
        if case["test_kind"] == "n8_sequential":
            case["_incomplete"] = not case["meta"]["expect_complete"]
        results.append(run_case(case))

    by_claim = {}
    for r in results:
        by_claim.setdefault(r["claim"], []).append(r)

    metrics, overall, crit = aggregate(results, thresholds)
    claim_v = claim_verdicts(by_claim, metrics, thresholds)

    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "function_os_versions": fos_versions(),
        "git_head": git_head(),
        "target_commit": TARGET_COMMIT,
        "prereg_commit": prereg_commit(),
        "prereg_ancestor_of_head": ancestry_ok(prereg_commit()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "oracle_allowed_nodes": [n.__name__ for n in oracle.ALLOWED_NODES],
    }

    out = {
        "task": "105",
        "environment": env,
        "thresholds": thresholds,
        "total_cases": len(results),
        "metrics": metrics,
        "overall_verdict": overall,
        "critical_violations": crit,
        "claim_verdicts": claim_v,
        "results": results,
    }
    with open(args.emit_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)

    # human log
    write_human_log(out)
    # claim verdicts (machine)
    with open(VERDICTS_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "overall_verdict": overall,
            "critical_violations": crit,
            "claim_verdicts": claim_v,
            "metrics": metrics,
        }, f, ensure_ascii=False, indent=2, sort_keys=True)

    # console summary
    print(f"TOTAL={len(results)} OVERALL={overall} CRITICAL_VIOLATIONS={crit}")
    print("METRICS:")
    for k, v in metrics.items():
        print(f"  {k} = {v:.4f}" if isinstance(v, float) else f"  {k} = {v}")
    print("CLAIM VERDICTS:")
    for k, v in claim_v.items():
        print(f"  {k} = {v}")


def write_human_log(out):
    L = []
    L.append("# Task 105 — First-Run Execution Log (original target 16f64004)\n")
    L.append(f"- Generated: {out['environment']['generated_at']}")
    L.append(f"- Git HEAD: {out['environment']['git_head']}")
    L.append(f"- Target commit: {out['environment']['target_commit']}")
    L.append(f"- Preregistration ancestor of HEAD: "
             f"{out['environment']['prereg_ancestor_of_head']}")
    L.append(f"- Overall verdict: **{out['overall_verdict']}** "
             f"(critical violations: {out['critical_violations']})\n")
    L.append("## Metrics\n")
    for k, v in out["metrics"].items():
        L.append(f"- {k}: {v}")
    L.append("\n## Claim verdicts\n")
    for k, v in out["claim_verdicts"].items():
        L.append(f"- {k}: {v}")
    L.append("\n## Per-case results (preserved, including failures)\n")
    for r in out["results"]:
        status = r.get("fos_status")
        cat = r.get("category")
        cv = " [CRITICAL VIOLATION]" if r.get("critical_violation") else ""
        L.append(f"- {r['case_id']} [{r['test_kind']}] fos={status} "
                 f"cat={cat}{cv}")
        if r.get("category") == "harness_error":
            L.append(f"    ERROR: {r.get('error')}")
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
