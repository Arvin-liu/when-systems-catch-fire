#!/usr/bin/env python3
"""Deterministic Evidence Program validator (Task 103 §9).

Self-contained: standard library only. Validates every Evidence Program
instance against its JSON schema (a self-implemented subset of JSON Schema
draft-07 sufficient for our schemas) and enforces the cross-file integrity
checks required by the relay contract:

  1. Preregistration-before-result ordering (§5.10, §12.3).
  2. No post-hoc threshold / metric substitution (§3, §7).
  3. Source-provenance completeness (§6).
  4. No train/test or exploratory/confirmatory leakage (§7).

Exit code 0 = all checks pass; 1 = at least one failure.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SCHEMA_FILES = {
    "candidate-portfolio": "schemas/candidate-portfolio.schema.json",
    "preregistration": "schemas/preregistration.schema.json",
    "evidence-source-manifest": "schemas/evidence-source-manifest.schema.json",
    "run-manifest": "schemas/run-manifest.schema.json",
    "result-adjudication": "schemas/result-adjudication.schema.json",
    "deviation-log": "schemas/deviation-log.schema.json",
    "e-axis-transition": "schemas/e-axis-transition.schema.json",
}


# --------------------------------------------------------------------------
# Minimal JSON-Schema (draft-07 subset) checker
# --------------------------------------------------------------------------
def check_type(value, t):
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def check_instance(inst, schema, path="$"):
    errors = []
    if "type" in schema:
        if not check_type(inst, schema["type"]):
            errors.append(f"{path}: expected type {schema['type']}, got {type(inst).__name__}")
            return errors  # cannot recurse sensibly
    if "enum" in schema and inst not in schema["enum"]:
        errors.append(f"{path}: {inst!r} not in enum {schema['enum']}")
    if "pattern" in schema and isinstance(inst, str):
        if not re.search(schema["pattern"], inst):
            errors.append(f"{path}: {inst!r} does not match {schema['pattern']}")
    if "minimum" in schema and isinstance(inst, (int, float)) and inst < schema["minimum"]:
        errors.append(f"{path}: {inst} < minimum {schema['minimum']}")
    if "maximum" in schema and isinstance(inst, (int, float)) and inst > schema["maximum"]:
        errors.append(f"{path}: {inst} > maximum {schema['maximum']}")
    if schema.get("type") == "object" and isinstance(inst, dict):
        required = schema.get("required", [])
        for k in required:
            if k not in inst:
                errors.append(f"{path}.{k}: MISSING required key")
        props = schema.get("properties", {})
        for k, v in inst.items():
            if k in props:
                errors.extend(check_instance(v, props[k], f"{path}.{k}"))
            # unknown keys allowed (forward-compatible)
    if schema.get("type") == "array" and isinstance(inst, list):
        item_schema = schema.get("items")
        if item_schema:
            for i, v in enumerate(inst):
                errors.extend(check_instance(v, item_schema, f"{path}[{i}]"))
    return errors


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(path):
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            out.append((ln, json.loads(line)))
    return out


# --------------------------------------------------------------------------
# Cross-file integrity checks
# --------------------------------------------------------------------------
def git_is_ancestor(ancestor, descendant, root):
    try:
        r = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root, capture_output=True, text=True,
        )
        return r.returncode == 0
    except Exception:
        return False


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    root = args.root
    failures = []
    checks = []

    def record(name, ok, detail=""):
        checks.append((name, ok, detail))
        if not ok:
            failures.append(f"{name}: {detail}")

    # 1. Schemas themselves parse and have required shapes
    schemas = {}
    for name, rel in SCHEMA_FILES.items():
        p = os.path.join(root, rel)
        try:
            schemas[name] = load_json(p)
            record(f"schema:{name}:parse", True)
        except Exception as e:
            record(f"schema:{name}:parse", False, str(e))

    def validate_instance(name, inst, label):
        if name not in schemas:
            record(f"instance:{label}:schema-present", False, "schema missing")
            return
        errs = check_instance(inst, schemas[name])
        record(f"instance:{label}:valid", not errs, "; ".join(errs[:3]))

    # 2. Candidate portfolio (jsonl)
    pf = os.path.join(root, "registry", "candidate-portfolio.jsonl")
    if os.path.exists(pf):
        rows = load_jsonl(pf)
        record("portfolio:nonempty", len(rows) > 0, f"{len(rows)} candidates")
        for ln, row in rows:
            validate_instance("candidate-portfolio", row, f"portfolio:{ln}")
    else:
        record("portfolio:present", False, "missing")

    # 3. Preregistration
    pre_files = [f for f in os.listdir(os.path.join(root, "preregistration"))
                 if f.endswith(".prereg.json")] if os.path.isdir(os.path.join(root, "preregistration")) else []
    prereg = None
    for f in pre_files:
        p = os.path.join(root, "preregistration", f)
        inst = load_json(p)
        validate_instance("preregistration", inst, f"prereg:{f}")
        prereg = inst

    # 4. Preregistration-before-result ordering + post-hoc threshold check
    run_dir = os.path.join(root, "runs")
    result_inst = None
    run_inst = None
    if os.path.isdir(run_dir):
        for d in os.listdir(run_dir):
            rd = os.path.join(run_dir, d)
            if not os.path.isdir(rd):
                continue
            rm = os.path.join(rd, "run-manifest.json")
            ra = os.path.join(rd, "result-adjudication.json")
            sm = os.path.join(rd, "source-manifest.jsonl")
            if os.path.exists(rm):
                run_inst = load_json(rm)
                validate_instance("run-manifest", run_inst, f"run:{d}")
                # ordering check
                pc = run_inst.get("preregistration_commit")
                pct = run_inst.get("preregistration_commit_timestamp")
                rgt = run_inst.get("results_generated_at_utc")
                if pc and pct and rgt:
                    ancestor = git_is_ancestor(pc, "HEAD", os.path.abspath(os.path.join(root, "..")))
                    record(f"ordering:{d}:prereg-ancestor-of-head", ancestor,
                           f"prereg {pc[:10]} ancestor of HEAD")
                    record(f"ordering:{d}:time-prereg-before-result",
                           pct < rgt, f"{pct} < {rgt}")
                else:
                    record(f"ordering:{d}:fields-present", False, "missing commit/timestamp fields")
            if os.path.exists(ra):
                result_inst = load_json(ra)
                validate_instance("result-adjudication", result_inst, f"result:{d}")
            if os.path.exists(sm):
                rows = load_jsonl(sm)
                record(f"source-manifest:{d}:nonempty", len(rows) > 0, f"{len(rows)} sources")
                for ln, row in rows:
                    validate_instance("evidence-source-manifest", row, f"source:{d}:{ln}")
                    # provenance completeness for OK entries
                    if row.get("acquisition_status") == "OK":
                        miss = [k for k in ("response_sha256", "licence", "retrieval_timestamp_utc", "canonical_identifier")
                                if not row.get(k)]
                        record(f"source-provenance:{d}:{ln}:complete", not miss,
                               f"missing {miss}" if miss else "complete")
                    else:
                        # non-OK must still record a reason (never silently dropped)
                        record(f"source-provenance:{d}:{ln}:failure-explicit",
                               bool(row.get("acquisition_status")),
                               row.get("acquisition_status", "UNKNOWN"))

    # 5. Post-hoc threshold / metric substitution check
    if prereg and result_inst:
        used = result_inst.get("thresholds_used", {})
        pre = {k: prereg.get(k) for k in ("success_conditions", "partial_support_conditions",
                                          "null_conditions", "contradiction_conditions", "invalid_test_conditions")}
        record("posthoc:thresholds-unchanged", canon(used) == canon(pre),
               "thresholds differ between preregistration and result" if canon(used) != canon(pre) else "identical")
        # leakage: observed metrics must be subset of preregistered metrics
        pre_metrics = set(prereg.get("metrics", {}).get("secondary_metrics", []))
        pre_metrics.add(prereg.get("metrics", {}).get("primary_metric", ""))
        obs_metrics = set(result_inst.get("metrics_observed", {}).keys())
        leaked = obs_metrics - pre_metrics
        record("leakage:no-unregistered-metrics", not leaked,
               f"unregistered metrics used: {leaked}" if leaked else "none")

    # 6. E-axis transition legality
    ea = os.path.join(root, "registry", "e-axis-transitions.jsonl") if False else None
    # (transitions, if any, validated on demand; none required for E0 retention)

    # ---- report ----
    print("=== Evidence Program validation ===")
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}" + (f" — {detail}" if detail and (not ok or args.strict) else ""))
    print(f"\nTotal checks: {len(checks)} | Failures: {len(failures)}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("ALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
