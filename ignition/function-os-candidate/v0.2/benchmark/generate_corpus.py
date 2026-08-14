#!/usr/bin/env python3
"""Task 105 — deterministic benchmark corpus generator (preregistration artifact).

Contract §5.1 (three strata), §5.3 (lock manifest + seed + generator version before
outcome-bearing runs), §6.1 (seal before running). This script ONLY enumerates
cases; it does NOT execute Function OS. The produced corpus is committed as the
locked benchmark input set; `run.py` executes it later as the outcome-bearing step.

Design notes (preregistered):
- Three strata: S1 reference-semantic, S2 boundary/adversarial, S3 stateful lifecycle.
- All input domains are exhaustive bounded enumerations over a fixed integer grid
  plus a fixed seed for any incidental ordering. No randomness affects case content.
- Forbidden constructs are enumerated from the SAME node set that Function OS v0.2
  documents as unsupported (see oracle/reference.py and PREREGISTRATION.md).
- POSTCONDITION_FAILED is reachable only with >=2 inconsistent postconditions,
  because N5 derives the compute expression from the (first) postcondition; this is
  encoded explicitly rather than relying on a single self-satisfying postcondition.
"""
import json
import os
import random

SEED = 20260730
GRID = [-2, -1, 0, 1, 2]          # 5-value integer grid for 2-input arithmetic
GRID3 = [-1, 0, 1]                 # 3-value grid for 3-input templates
BOOL = [True, False]
CREATED_AT = "2026-07-30T00:00:00Z"
SPEC_VERSION = "1.0.0"

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "corpus")
MANIFEST_PATH = os.path.join(HERE, "CORPUS_MANIFEST.json")


def make_spec(fid, name, inputs, outputs, preconditions, postconditions, effects):
    return {
        "function_id": fid,
        "spec_version": SPEC_VERSION,
        "name": name,
        "domain": "symbolic",
        "inputs": inputs,
        "outputs": outputs,
        "preconditions": preconditions,
        "postconditions": postconditions,
        "effects_declared": effects,
        "created_at": CREATED_AT,
    }


def pc(expression, message):
    return {"expression": expression, "message": message}


_counter = {"n": 0}


def next_id(prefix):
    # N1 requires function_id to match FN-YYYYMMDD-NNNN (4 digits). The stratum is
    # already encoded in case_id; the function_id is a unique numeric sequence.
    _counter["n"] += 1
    return f"FN-20260730-{_counter['n']:04d}"


def emit(cases, stratum, claim, test_kind, spec, inputs, expect, meta=None):
    cid = f"{stratum.split('_')[0].upper()}-{test_kind.upper()}-{len(cases)+1:04d}"
    cases.append({
        "case_id": cid,
        "stratum": stratum,
        "claim": claim,
        "test_kind": test_kind,
        "spec": spec,
        "inputs": inputs,
        "expect": expect,
        "meta": meta or {},
    })


def build_s1(cases):
    """Reference-semantic fidelity cases: every case must yield FOS status OK with
    outputs exactly matching the independent oracle."""
    # (name, inputs dict template, grid vars, output type, postcondition expr template)
    templates = [
        ("add", ["x", "y"], ["integer", "integer"], "number", "result == x + y"),
        ("sub", ["x", "y"], ["integer", "integer"], "number", "result == x - y"),
        ("mul", ["x", "y"], ["integer", "integer"], "number", "result == x * y"),
        ("truediv", ["x", "y"], ["integer", "integer"], "number", "result == x / y"),
        ("floordiv", ["x", "y"], ["integer", "integer"], "number", "result == x // y"),
        ("mod", ["x", "y"], ["integer", "integer"], "number", "result == x % y"),
        ("pow", ["x", "y"], ["integer", "integer"], "number", "result == x ** y"),
        ("negate", ["x"], ["integer"], "number", "result == -x"),
        ("eq", ["x", "y"], ["integer", "integer"], "boolean", "result == (x == y)"),
        ("lt", ["x", "y"], ["integer", "integer"], "boolean", "result == (x < y)"),
        ("lte", ["x", "y"], ["integer", "integer"], "boolean", "result == (x <= y)"),
        ("gt", ["x", "y"], ["integer", "integer"], "boolean", "result == (x > y)"),
        ("gte", ["x", "y"], ["integer", "integer"], "boolean", "result == (x >= y)"),
        ("and", ["a", "b"], ["boolean", "boolean"], "boolean", "result == (a and b)"),
        ("or", ["a", "b"], ["boolean", "boolean"], "boolean", "result == (a or b)"),
        ("not", ["a"], ["boolean"], "boolean", "result == (not a)"),
        ("ifexp", ["a", "b", "c"], ["integer", "integer", "integer"], "number",
         "result == (a if b > 0 else c)"),
        ("chain3", ["x", "y", "z"], ["integer", "integer", "integer"], "number",
         "result == x + y + z"),
        ("nested", ["x", "y", "z"], ["integer", "integer", "integer"], "number",
         "result == (x + y) * z"),
        ("mixed", ["x", "y", "z"], ["integer", "integer", "integer"], "number",
         "result == x * y + z"),
    ]
    for (name, vars_, types, otype, post) in templates:
        if all(t == "boolean" for t in types):
            grid = BOOL
        elif len(vars_) == 3:
            grid = GRID3
        else:
            grid = GRID
        combos = _combos(vars_, grid)
        for combo in combos:
            inputs = dict(zip(vars_, combo))
            # Skip divisor-zero for division-family templates (covered by S2 runtime).
            if name in ("truediv", "floordiv", "mod") and inputs[vars_[1]] == 0:
                continue
            if name == "pow" and inputs[vars_[1]] < 0:
                continue
            spec = make_spec(
                next_id("S1"), name,
                {v: t for v, t in zip(vars_, types)},
                {"result": otype},
                [], [pc(post, f"{name} semantics")], ["pure"],
            )
            emit(cases, "S1_reference_semantic", "SUPPORTED_SEMANTIC_FIDELITY",
                 "fidelity", spec, inputs,
                 {"fos_status": "OK", "oracle_basis": "fidelity_equal",
                  "critical": False})


def _combos(vars_, grid):
    import itertools
    return list(itertools.product(grid, repeat=len(vars_)))


def build_s2_forbidden(cases):
    """Boundary: forbidden AST forms that Function OS must reject (fail-closed).
    A forbidden construct that is silently executed is a CRITICAL fail-open."""
    forbidden = [
        ("call_os_system", 'result == os.system("x")', {"x": 5}),
        ("call_eval", 'result == eval("1+1")', {"x": 5}),
        ("call_abs", "result == abs(x)", {"x": 5}),
        ("call_len", "result == len(x)", {"x": [1, 2, 3]}),
        ("call_min", "result == min(x, y)", {"x": 5, "y": 7}),
        ("call_import", '__import__("os") == result', {"x": 5}),
        ("attribute_access", "result == x.__class__", {"x": 5}),
        ("subscript", "result == x[0]", {"x": [1, 2, 3]}),
        ("lambda", "(lambda a: a + 1)(x) == result", {"x": 5}),
        ("list_literal", "result == [x, y]", {"x": 1, "y": 2}),
        ("tuple_literal", "result == (x, y)", {"x": 1, "y": 2}),
        ("dict_literal", "result == {x: y}", {"x": 1, "y": 2}),
        ("set_literal", "result == {x}", {"x": 1}),
        ("comprehension", "result == [i for i in x]", {"x": [1, 2, 3]}),
        ("generator_expr", "result == (i for i in x)", {"x": [1, 2, 3]}),
        ("walrus", "(z := x + y) == result", {"x": 1, "y": 2}),
        ("fstring", 'result == f"{x}"', {"x": 5}),
        ("starred", "result == (*x,)", {"x": [1, 2]}),
    ]
    for (name, post, inputs) in forbidden:
        spec = make_spec(
            next_id("S2F"), name,
            {k: ("integer" if isinstance(v, int) else "list") for k, v in inputs.items()},
            {"result": "number"},
            [], [pc(post, "forbidden construct")], ["pure"],
        )
        emit(cases, "S2_boundary_adversarial", "FAIL_CLOSED_LANGUAGE_BOUNDARY",
             "forbidden", spec, inputs,
             {"fos_status": "non_OK", "oracle_basis": "both_reject", "critical": True},
             meta={"forbidden_kind": name})


def build_s2_runtime(cases):
    """Runtime-exception / malformed cases: must also fail closed (reject), not crash
    or silently accept. Both oracle and Function OS reject."""
    runtime = [
        ("div_by_zero", "result == x / y", {"x": 5, "y": 0}),
        ("floordiv_zero", "result == x // y", {"x": 5, "y": 0}),
        ("mod_zero", "result == x % y", {"x": 5, "y": 0}),
        ("pow_zero_neg", "result == 0 ** -1", {"x": 0}),
        ("malformed_expr", "result == x +", {"x": 5}),
        ("malformed_paren", "result == (x + y", {"x": 5, "y": 3}),
    ]
    for (name, post, inputs) in runtime:
        spec = make_spec(
            next_id("S2R"), name,
            {k: "integer" for k in inputs},
            {"result": "number"},
            [], [pc(post, "runtime/malformed")], ["pure"],
        )
        emit(cases, "S2_boundary_adversarial", "FAIL_CLOSED_LANGUAGE_BOUNDARY",
             "forbidden", spec, inputs,
             {"fos_status": "non_OK", "oracle_basis": "both_reject", "critical": False},
             meta={"runtime_kind": name})


def build_s2_precond(cases):
    """Precondition enforcement + registry non-contamination. A precondition failure
    must return PRECONDITION_FAILED and MUST NOT enter the successful registry."""
    # Single precondition, x negative grid
    for x in [-5, -4, -3, -2, -1]:
        spec = make_spec(
            next_id("S2P"), "precond_x_nonneg",
            {"x": "integer", "y": "integer"}, {"result": "number"},
            [pc("x >= 0", "x non-negative")],
            [pc("result == x + y", "sum")], ["pure"],
        )
        emit(cases, "S2_boundary_adversarial", "CONTRACT_ENFORCEMENT",
             "precondition_fail", spec, {"x": x, "y": 3},
             {"fos_status": "PRECONDITION_FAILED", "oracle_basis": "precondition_failure",
              "must_not_register": True, "critical": False})
    # Two preconditions, both must hold; enumerate one failing (y negative)
    for y in [-3, -2, -1]:
        spec = make_spec(
            next_id("S2P"), "precond_xy_nonneg",
            {"x": "integer", "y": "integer"}, {"result": "number"},
            [pc("x >= 0", "x non-negative"), pc("y >= 0", "y non-negative")],
            [pc("result == x + y", "sum")], ["pure"],
        )
        emit(cases, "S2_boundary_adversarial", "CONTRACT_ENFORCEMENT",
             "precondition_fail", spec, {"x": 2, "y": y},
             {"fos_status": "PRECONDITION_FAILED", "oracle_basis": "precondition_failure",
              "must_not_register": True, "critical": False})


def build_s2_postcond(cases):
    """Postcondition enforcement via two inconsistent postconditions. The first
    postcondition is the compute source (always self-satisfying); the second must
    fail for inputs where the two disagree -> POSTCONDITION_FAILED."""
    for y in [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]:  # y != 0
        spec = make_spec(
            next_id("S2C"), "postcond_inconsistent",
            {"x": "integer", "y": "integer"}, {"result": "number"},
            [],
            [pc("result == x + y", "compute sum"),
             pc("result == x - y", "must equal difference")],
            ["pure"],
        )
        emit(cases, "S2_boundary_adversarial", "CONTRACT_ENFORCEMENT",
             "postcondition_fail", spec, {"x": 3, "y": y},
             {"fos_status": "POSTCONDITION_FAILED", "oracle_basis": "postcondition_failure",
              "critical": False})
    # second postcondition asserts a constant that never holds for positive inputs
    for x in [1, 2, 3]:
        for y in [1, 2, 3]:
            spec = make_spec(
                next_id("S2C"), "postcond_const",
                {"x": "integer", "y": "integer"}, {"result": "number"},
                [],
                [pc("result == x + y", "compute sum"),
                 pc("result == 0", "must be zero")],
                ["pure"],
            )
            emit(cases, "S2_boundary_adversarial", "CONTRACT_ENFORCEMENT",
                 "postcondition_fail", spec, {"x": x, "y": y},
                 {"fos_status": "POSTCONDITION_FAILED", "oracle_basis": "postcondition_failure",
                  "critical": False})


def build_s2_type(cases):
    """Type/shape boundary: wrong or missing inputs must yield TYPE_ERROR."""
    base = make_spec(
        next_id("S2T"), "type_checks",
        {"x": "integer", "y": "integer"}, {"result": "number"},
        [], [pc("result == x + y", "sum")], ["pure"],
    )
    # wrong type: string instead of integer
    emit(cases, "S2_boundary_adversarial", "CONTRACT_ENFORCEMENT", "type_error",
         base, {"x": "5", "y": 3},
         {"fos_status": "TYPE_ERROR", "oracle_basis": "type_error", "critical": False})
    # missing input
    emit(cases, "S2_boundary_adversarial", "CONTRACT_ENFORCEMENT", "type_error",
         base, {"x": 5},
         {"fos_status": "TYPE_ERROR", "oracle_basis": "type_error", "critical": False})
    # bool where integer declared (mismatch)
    emit(cases, "S2_boundary_adversarial", "CONTRACT_ENFORCEMENT", "type_error",
         base, {"x": True, "y": 3},
         {"fos_status": "TYPE_ERROR", "oracle_basis": "type_error", "critical": False})


def build_s2_tamper(cases):
    """Artifact & trace integrity: specified mutations must be detected by the
    validation chain (N7Validator / N4ArtifactVerifier / N6 trace_hash)."""
    tamper_kinds = [
        ("content_hash", "flip payload content"),
        ("spec_hash", "artifact.spec_hash mismatch with spec"),
        ("representation_hash", "artifact.representation_hash mismatch with rep"),
        ("payload_expr", "mutate expression inside payload"),
        ("artifact_hash", "corrupt artifact_hash (N4 verifier)"),
    ]
    for (kind, desc) in tamper_kinds:
        spec = make_spec(
            next_id("S2M"), "tamper_target",
            {"x": "integer", "y": "integer"}, {"result": "number"},
            [], [pc("result == x + y", "sum")], ["pure"],
        )
        emit(cases, "S2_boundary_adversarial", "ARTIFACT_AND_TRACE_INTEGRITY",
             "tamper", spec, {"x": 3, "y": 4},
             {"fos_status": "DETECTED", "oracle_basis": "tamper_detected",
              "critical": True},
             meta={"tamper_kind": kind, "desc": desc})
    # trace mutation family
    for kind in ["trace_output", "trace_artifact_id", "trace_spec_id"]:
        spec = make_spec(
            next_id("S2M"), "trace_tamper_target",
            {"x": "integer", "y": "integer"}, {"result": "number"},
            [], [pc("result == x + y", "sum")], ["pure"],
        )
        emit(cases, "S2_boundary_adversarial", "ARTIFACT_AND_TRACE_INTEGRITY",
             "tamper", spec, {"x": 3, "y": 4},
             {"fos_status": "DETECTED", "oracle_basis": "tamper_detected",
              "critical": True},
             meta={"tamper_kind": kind})


def build_s3_registry(cases):
    """Stateful lifecycle: revision/update/rollback history must be auditable and
    internally consistent; rollback must restore prior trace_hash."""
    # Varied update/rollback sequences (lengths 1..6, varied rollback targets)
    sequences = [
        [("create", "t1"), ("update", "t2"), ("rollback", 1)],
        [("create", "t1"), ("update", "t2"), ("update", "t3"), ("rollback", 2)],
        [("create", "t1"), ("rollback", 1)],  # rollback to only revision
        [("create", "t1"), ("update", "t2"), ("update", "t3"),
         ("update", "t4"), ("rollback", 1)],
        [("create", "t1"), ("update", "t2"), ("rollback", 2)],
        [("create", "t1"), ("update", "t2"), ("update", "t3"),
         ("rollback", 3)],
        [("create", "t1"), ("update", "t2"), ("update", "t3"),
         ("update", "t4"), ("update", "t5"), ("rollback", 4)],
        [("create", "t1"), ("update", "t2"), ("update", "t3"),
         ("rollback", 1), ("update", "t4"), ("rollback", 2)],  # post-rollback update
    ]
    for i, seq in enumerate(sequences):
        spec = make_spec(
            next_id("S3R"), f"registry_seq_{i}",
            {"x": "integer", "y": "integer"}, {"result": "number"},
            [], [pc("result == x + y", "sum")], ["pure"],
        )
        emit(cases, "S3_stateful_lifecycle", "REGISTRY_REVISION_AND_ROLLBACK_INTEGRITY",
             "registry_lifecycle", spec, {"x": 1, "y": 2},
             {"fos_status": "CONSISTENT", "oracle_basis": "registry_consistent",
              "critical": False},
             meta={"sequence": seq})


def build_s3_n8(cases):
    """Bounded sequential composition: N8 produces an ordered sequential plan from
    required functions + registry candidates; missing functions are skipped with
    failure propagation (no auto-discovery)."""
    # A valid 3-step sequential plan referencing three registered functions
    plan_cases = [
        (["FN-A", "FN-B", "FN-C"], True, "ordered_plan"),
        (["FN-A", "FN-B"], True, "two_step_plan"),
        (["FN-A", "MISSING", "FN-C"], False, "failure_propagation"),
        (["MISSING"], False, "all_missing"),
        (["FN-A", "FN-A", "FN-B"], True, "repeat_function"),
        (["FN-C", "FN-B", "FN-A"], True, "reordered"),
        (["FN-A", "MISSING", "MISSING", "FN-B"], False, "partial_failure"),
        (["FN-B", "FN-A"], True, "two_step_reverse"),
    ]
    for (req, complete, name) in plan_cases:
        # candidate specs are built by the harness from these ids
        emit(cases, "S3_stateful_lifecycle", "BOUNDED_SEQUENTIAL_COMPOSITION",
             "n8_sequential", None, None,
             {"fos_status": "PLANNED" if complete else "PARTIAL",
              "oracle_basis": "plan_sequential", "critical": False},
             meta={"required_functions": req, "expect_complete": complete,
                   "name": name})


def build_s3_trace(cases):
    """Trace integrity within lifecycle: a mutated trace must change its
    deterministic trace_hash (tamper evidence)."""
    for kind in ["output_flip", "status_flip", "input_flip"]:
        spec = make_spec(
            next_id("S3T"), "trace_lifecycle",
            {"x": "integer", "y": "integer"}, {"result": "number"},
            [], [pc("result == x + y", "sum")], ["pure"],
        )
        emit(cases, "S3_stateful_lifecycle", "ARTIFACT_AND_TRACE_INTEGRITY",
             "tamper", spec, {"x": 3, "y": 4},
             {"fos_status": "DETECTED", "oracle_basis": "tamper_detected",
              "critical": True},
             meta={"tamper_kind": "trace_" + kind})


def main():
    random.seed(SEED)
    cases = []
    build_s1(cases)
    build_s2_forbidden(cases)
    build_s2_runtime(cases)
    build_s2_precond(cases)
    build_s2_postcond(cases)
    build_s2_type(cases)
    build_s2_tamper(cases)
    build_s3_registry(cases)
    build_s3_n8(cases)
    build_s3_trace(cases)

    os.makedirs(CORPUS_DIR, exist_ok=True)
    # combined corpus
    combined = os.path.join(CORPUS_DIR, "benchmark-corpus.jsonl")
    with open(combined, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    # per-stratum files
    strata = {}
    for c in cases:
        strata.setdefault(c["stratum"], []).append(c)
    for s, cs in strata.items():
        path = os.path.join(CORPUS_DIR, s + ".jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for c in cs:
                f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")

    # manifest
    counts = {}
    for c in cases:
        counts[c["stratum"]] = counts.get(c["stratum"], 0) + 1
    claim_counts = {}
    for c in cases:
        claim_counts[c["claim"]] = claim_counts.get(c["claim"], 0) + 1
    manifest = {
        "generator": "generate_corpus.py",
        "generator_version": "1.0.0-preregistered",
        "seed": SEED,
        "grid": GRID,
        "grid3": GRID3,
        "boolean_grid": BOOL,
        "created_at": CREATED_AT,
        "target_commit": "16f640045b3dc9d411f015a51e45de07299d31fc",
        "total_cases": len(cases),
        "strata_counts": counts,
        "claim_counts": claim_counts,
        "determinism": "exhaustive bounded enumeration; no case content depends on RNG",
        "notes": "POSTCONDITION_FAILED cases use >=2 inconsistent postconditions; "
                 "fidelity compares FOS computed value to independent oracle value.",
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"Generated {len(cases)} cases")
    print("By stratum:", json.dumps(counts, ensure_ascii=False))
    print("By claim:", json.dumps(claim_counts, ensure_ascii=False))
    print(f"Manifest -> {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
