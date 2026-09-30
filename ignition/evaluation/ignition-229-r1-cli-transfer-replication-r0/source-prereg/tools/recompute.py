#!/usr/bin/env python3
"""Deterministic Task229 outcome recomputation and synthetic preflight."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import pathlib
import sys
import tempfile

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover - hard failure on the fixed analysis runtime
    raise SystemExit("TASK229_ANALYSIS_RUNTIME=INVALID jsonschema is unavailable") from exc


HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE.parent
REPO = PREREG.parents[3]
CASES = ("A", "B", "C")
POLICY_DIR = pathlib.Path("ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies")


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validator(path: pathlib.Path):
    schema = read_json(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema), schema


def condition_matches(conditions, values):
    for condition in conditions:
        if condition.get("operator") != "eq":
            return False
        input_id = condition.get("input_id")
        if input_id not in values or values[input_id] != condition.get("value"):
            return False
    return True


def baseline_action_ids(policy):
    return sorted({entry["baseline_action"] for entry in policy.get("preserved_rules", [])})


def verify_trace(response, policy, case_values):
    trace = response.get("route_trace")
    if not isinstance(trace, dict) or trace.get("policy_id") != policy.get("policy_id"):
        return False
    expected_baseline = baseline_action_ids(policy)
    if sorted(response.get("preserved_baseline_action_ids", [])) != expected_baseline:
        return False
    if sorted(trace.get("preserved_baseline_action_ids", [])) != expected_baseline:
        return False
    input_ids = trace.get("input_ids")
    if not isinstance(input_ids, list) or len(input_ids) != len(set(input_ids)):
        return False
    if any(input_id not in case_values for input_id in input_ids):
        return False

    stops = [item for item in policy.get("stop_conditions", []) if condition_matches(item.get("when", []), case_values)]
    rules = [item for item in policy.get("selector", {}).get("rule", []) if condition_matches(item.get("when", []), case_values)]
    if len(stops) > 1 or (stops and rules) or len(rules) > 1:
        return False
    if stops:
        chosen = stops[0]
        needed = {condition["input_id"] for condition in chosen.get("when", [])}
        return (
            set(needed).issubset(input_ids)
            and trace.get("route_type") == "stop"
            and trace.get("selected_rule_id") == chosen.get("stop_id")
            and trace.get("selected_action_id") is None
        )
    if rules:
        chosen = rules[0]
        needed = {condition["input_id"] for condition in chosen.get("when", [])}
        return (
            set(needed).issubset(input_ids)
            and trace.get("route_type") == "selector"
            and trace.get("selected_rule_id") == chosen.get("rule_id")
            and trace.get("selected_action_id") == chosen.get("action_ref")
        )
    return (
        trace.get("route_type") == "fallback"
        and trace.get("selected_rule_id") is None
        and trace.get("selected_action_id") is None
    )


def load_scores(evaluator, dataset_path, expected_sessions):
    base = dataset_path.parent
    scores_path = base / evaluator["scores_file"]
    key_path = base / evaluator["response_key_file"]
    scores = {session_id: {case: False for case in CASES} for session_id in expected_sessions}
    if not scores_path.is_file() or not key_path.is_file():
        return scores, {"valid_rows": 0, "invalid_rows": 0, "unmapped_rows": 0}

    try:
        score_doc = read_json(scores_path)
        key_doc = read_json(key_path)
    except (OSError, json.JSONDecodeError):
        return scores, {"valid_rows": 0, "invalid_rows": 0, "unmapped_rows": 0}
    if score_doc.get("schema_version") != "task229-blind-evaluation-r0" or not isinstance(score_doc.get("rows"), list):
        return scores, {"valid_rows": 0, "invalid_rows": 0, "unmapped_rows": 0}
    key_validator, _ = validator(PREREG / "blind-key-schema.json")
    score_validator, score_schema = validator(PREREG / "blind-evaluation-schema.json")
    if list(key_validator.iter_errors(key_doc)):
        return scores, {"valid_rows": 0, "invalid_rows": len(score_doc["rows"]), "unmapped_rows": 0}

    response_map = {}
    ambiguous = set()
    for item in key_doc["items"]:
        rid = item["response_id"]
        if rid in response_map:
            ambiguous.add(rid)
        response_map[rid] = (item["session_id"], item["case_id"])
    row_schema = score_schema["properties"]["rows"]["items"]
    row_validator = jsonschema.Draft202012Validator(row_schema)
    row_values = {}
    valid_rows = invalid_rows = unmapped_rows = 0
    for row in score_doc["rows"]:
        if list(row_validator.iter_errors(row)):
            invalid_rows += 1
            continue
        rid = row["response_id"]
        if rid not in response_map or rid in ambiguous:
            unmapped_rows += 1
            continue
        session_id, case_id = response_map[rid]
        if session_id not in expected_sessions:
            unmapped_rows += 1
            continue
        row_values.setdefault((session_id, case_id), []).append(row["success"])
        valid_rows += 1
    for (session_id, case_id), values in row_values.items():
        # Duplicate score rows are invalidated rather than resolved by order.
        scores[session_id][case_id] = len(values) == 1 and values[0] is True
    return scores, {"valid_rows": valid_rows, "invalid_rows": invalid_rows, "unmapped_rows": unmapped_rows}


def validate_response(record, dataset_path, response_validator, condition):
    if record.get("status") != "semantic" or not record.get("response_file"):
        return None, False
    try:
        value = json.loads((dataset_path.parent / record["response_file"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, False
    if list(response_validator.iter_errors(value)):
        return value, False
    responses = value.get("responses", [])
    if {item["case_id"] for item in responses} != set(CASES) or len(responses) != 3:
        return value, False
    has_trace = ["route_trace" in item for item in responses]
    if condition == "REFERENCE_M1" and not all(has_trace):
        return value, False
    if condition != "REFERENCE_M1" and any(has_trace):
        return value, False
    return value, True


def recompute(dataset_path: pathlib.Path, prereg_root: pathlib.Path = PREREG, repo_root: pathlib.Path = REPO):
    dataset = read_json(dataset_path)
    input_validator, _ = validator(prereg_root / "analysis-input-schema.json")
    errors = list(input_validator.iter_errors(dataset))
    if errors:
        first = errors[0]
        raise ValueError(f"analysis input schema invalid at {list(first.absolute_path)}: {first.message}")
    manifest = read_json(prereg_root / "condition-manifest.json")
    order_doc = read_json(prereg_root / "session-order.json")
    lineages = manifest["lineages"]
    all_sessions = [condition["session_id"] for lineage in lineages for condition in lineage["conditions"]]
    if len(all_sessions) != 18 or len(set(all_sessions)) != 18:
        raise ValueError("condition manifest must bind 18 unique sessions")
    if set(dataset["session_records"]) != set(all_sessions):
        raise ValueError("analysis input must contain one record per preregistered session")
    if set(order_doc["order"]) != set(all_sessions) or len(order_doc["order"]) != 18:
        raise ValueError("session order does not match condition manifest")

    response_validator, _ = validator(prereg_root / "response-schema.json")
    session_binding = {}
    policy_docs = {}
    for lineage in lineages:
        policy_path = repo_root / lineage["policy_path"]
        policy = read_json(policy_path)
        policy_docs[lineage["policy_id"]] = policy
        for item in lineage["conditions"]:
            session_binding[item["session_id"]] = {"condition": item["condition"], "lineage": lineage, "entry": item}

    outputs = {}
    for session_id in all_sessions:
        binding = session_binding[session_id]
        response, valid = validate_response(dataset["session_records"][session_id], dataset_path, response_validator, binding["condition"])
        trace_ok = False
        if valid and binding["condition"] == "REFERENCE_M1":
            inputs_by_case = dataset["case_inputs_by_lineage"].get(binding["lineage"]["lineage_id"], {})
            response_by_case = {item["case_id"]: item for item in response["responses"]}
            policy = policy_docs[binding["lineage"]["policy_id"]]
            trace_ok = all(
                case in inputs_by_case
                and verify_trace(response_by_case[case], policy, inputs_by_case[case])
                for case in CASES
            )
        outputs[session_id] = {"response_valid": valid, "trace_valid": trace_ok, "condition": binding["condition"], "lineage_id": binding["lineage"]["lineage_id"]}

    eval_docs = []
    evaluator_scores = {}
    evaluator_file_stats = {}
    evaluator_keys = set()
    for evaluator in dataset["evaluators"]:
        key = evaluator["evaluator_key"]
        if key in evaluator_keys:
            raise ValueError("evaluator_key values must be distinct")
        evaluator_keys.add(key)
        scores, stats = load_scores(evaluator, dataset_path, all_sessions)
        evaluator_scores[key] = scores
        evaluator_file_stats[key] = stats
        eval_docs.append(key)

    interface_success = {}
    for lineage in lineages:
        ref_session = next(item["session_id"] for item in lineage["conditions"] if item["condition"] == "REFERENCE_M1")
        interface_success[lineage["lineage_id"]] = outputs[ref_session]["response_valid"] and outputs[ref_session]["trace_valid"]
    interface_count = sum(interface_success.values())
    if interface_count >= 5:
        interface_marker = "INTERFACE_EXECUTION_WORKING"
    elif interface_count >= 3:
        interface_marker = "INTERFACE_EXECUTION_PARTIAL"
    else:
        interface_marker = "INTERFACE_EXECUTION_NOT_ESTABLISHED"

    ref_scores = {}
    compat_working = True
    compat_partial = True
    for evaluator_key in eval_docs:
        counts = {case: 0 for case in CASES}
        for lineage in lineages:
            session_id = next(item["session_id"] for item in lineage["conditions"] if item["condition"] == "REFERENCE_M1")
            usable = outputs[session_id]["response_valid"]
            for case in CASES:
                counts[case] += int(usable and evaluator_scores[evaluator_key][session_id][case])
        ref_scores[evaluator_key] = counts
        compat_working = compat_working and all(counts[case] >= 5 for case in CASES)
        compat_partial = compat_partial and counts["A"] >= 3 and sum(counts[case] >= 3 for case in CASES) >= 2
    if compat_working:
        compatibility_marker = "REFERENCE_TARGET_COMPATIBILITY_WORKING"
    elif compat_partial:
        compatibility_marker = "REFERENCE_TARGET_COMPATIBILITY_PARTIAL"
    else:
        compatibility_marker = "REFERENCE_TARGET_COMPATIBILITY_NOT_ESTABLISHED"

    control_by_lineage = {}
    condition_sessions = {}
    for lineage in lineages:
        for condition in ("M0_ONLY", "M0_PLUS_E1", "REFERENCE_M1"):
            item = next(entry for entry in lineage["conditions"] if entry["condition"] == condition)
            condition_sessions[(lineage["lineage_id"], condition)] = item["session_id"]
        sid = condition_sessions[(lineage["lineage_id"], "M0_ONLY")]
        control_by_lineage[lineage["lineage_id"]] = outputs[sid]["response_valid"]
    control_count = sum(control_by_lineage.values())
    incremental_counts = {}
    for evaluator_key in eval_docs:
        m0_a = 0
        chain = 0
        chain_observed = 0
        for lineage in lineages:
            lineage_id = lineage["lineage_id"]
            m0_sid = condition_sessions[(lineage_id, "M0_ONLY")]
            ref_sid = condition_sessions[(lineage_id, "REFERENCE_M1")]
            if not control_by_lineage[lineage_id]:
                continue
            m0_a += int(evaluator_scores[evaluator_key][m0_sid]["A"] and outputs[m0_sid]["response_valid"])
            ref_a = evaluator_scores[evaluator_key][ref_sid]["A"] and outputs[ref_sid]["response_valid"]
            ref_b = evaluator_scores[evaluator_key][ref_sid]["B"] and outputs[ref_sid]["response_valid"]
            ref_c = evaluator_scores[evaluator_key][ref_sid]["C"] and outputs[ref_sid]["response_valid"]
            m0_only_a = evaluator_scores[evaluator_key][m0_sid]["A"] and outputs[m0_sid]["response_valid"]
            chain += int(ref_a and not m0_only_a and ref_b and ref_c)
            chain_observed += 1
        incremental_counts[evaluator_key] = {"m0_only_A_successes": m0_a, "chain_successes_among_observed_controls": chain, "observed_controls": chain_observed}
    if control_count <= 4:
        incremental_marker = "INCREMENTAL_POLICY_EFFECT_NOT_ESTABLISHED_CONTROL_FAILURE"
    elif control_count == 5:
        incremental_marker = "INCREMENTAL_POLICY_EFFECT_PARTIAL_OBSERVABILITY"
    else:
        supported = all(
            incremental_counts[key]["observed_controls"] == 6
            and incremental_counts[key]["m0_only_A_successes"] <= 1
            and incremental_counts[key]["chain_successes_among_observed_controls"] >= 5
            for key in eval_docs
        )
        incremental_marker = "INCREMENTAL_POLICY_EFFECT_SUPPORTED" if supported else None

    descriptive = {}
    for evaluator_key in eval_docs:
        descriptive[evaluator_key] = {}
        for condition in ("M0_ONLY", "M0_PLUS_E1", "REFERENCE_M1"):
            counts = {case: 0 for case in CASES}
            for lineage in lineages:
                sid = condition_sessions[(lineage["lineage_id"], condition)]
                usable = outputs[sid]["response_valid"]
                for case in CASES:
                    counts[case] += int(usable and evaluator_scores[evaluator_key][sid][case])
            descriptive[evaluator_key][condition] = counts

    if interface_marker == "INTERFACE_EXECUTION_WORKING" and compatibility_marker == "REFERENCE_TARGET_COMPATIBILITY_WORKING":
        direction = "PROCEED_TO_ISOLATED_REVISION_GENERATION_TASK230"
    elif interface_marker == "INTERFACE_EXECUTION_WORKING":
        direction = "REFERENCE_TARGET_COMPATIBILITY_REPAIR"
    else:
        direction = "TRANSFER_INTERFACE_REPAIR"
    if control_count <= 4:
        direction += "+INCREMENTAL_EFFECT_UNINTERPRETABLE_CONTROL_FAILURE"

    return {
        "schema_version": "task229-recomputed-results-r0",
        "result_markers": {
            "interface_execution": interface_marker,
            "reference_target_compatibility": compatibility_marker,
            "incremental_policy_effect": incremental_marker
        },
        "interface_execution": {"success_count": interface_count, "denominator": 6, "lineage_success": interface_success},
        "reference_target_compatibility": {"success_counts_by_evaluator": ref_scores, "denominator_per_target": 6},
        "incremental_policy_effect": {
            "m0_only_controls_observed": control_count,
            "control_denominator": 6,
            "control_observed_by_lineage": control_by_lineage,
            "evaluator_counts": incremental_counts,
            "support_threshold_met": incremental_marker == "INCREMENTAL_POLICY_EFFECT_SUPPORTED",
            "when_all_controls_observed_threshold_not_met": "no conclusion marker; do not infer causality" if control_count == 6 and incremental_marker is None else None
        },
        "descriptive_condition_counts": descriptive,
        "response_validity": outputs,
        "evaluator_file_stats": evaluator_file_stats,
        "next_direction": direction
    }


def synthetic_dataset(root: pathlib.Path, scenario: str):
    manifest = read_json(PREREG / "condition-manifest.json")
    root.mkdir(parents=True, exist_ok=True)
    raw_dir = root / "raw"
    eval_dir = root / "eval"
    raw_dir.mkdir(exist_ok=True)
    eval_dir.mkdir(exist_ok=True)
    data = {"schema_version": "task229-analysis-input-r0", "case_inputs_by_lineage": {}, "session_records": {}, "evaluators": []}
    score_truth = {"blind-A": {}, "blind-B": {}}
    keys = {"blind-A": [], "blind-B": []}
    missing_controls = {"five_controls": 1, "control_failure": 2}.get(scenario, 0)
    no_support_m0_a = 2 if scenario == "thresholds_not_met" else 0
    for lineage_index, lineage in enumerate(manifest["lineages"]):
        policy = read_json(REPO / lineage["policy_path"])
        rule = policy["selector"]["rule"][0]
        values = {item["input_id"]: item["value"] for item in rule["when"]}
        data["case_inputs_by_lineage"][lineage["lineage_id"]] = {case: dict(values) for case in CASES}
        baseline = baseline_action_ids(policy)
        for condition in ("M0_ONLY", "M0_PLUS_E1", "REFERENCE_M1"):
            entry = next(item for item in lineage["conditions"] if item["condition"] == condition)
            sid = entry["session_id"]
            is_missing_control = condition == "M0_ONLY" and lineage_index >= 6 - missing_controls
            if is_missing_control:
                data["session_records"][sid] = {"status": "missing"}
                continue
            responses = []
            for case in CASES:
                response = {
                    "case_id": case,
                    "primary_action": "synthetic action",
                    "additional_actions": [],
                    "reported_values": [],
                    "preserved_baseline_action_ids": baseline,
                    "fallback": None,
                    "scope": "synthetic scope",
                    "rationale": "synthetic fixture"
                }
                if condition == "REFERENCE_M1":
                    response["route_trace"] = {
                        "policy_id": policy["policy_id"],
                        "route_type": "selector",
                        "selected_rule_id": rule["rule_id"],
                        "selected_action_id": rule["action_ref"],
                        "input_ids": sorted(values),
                        "preserved_baseline_action_ids": baseline
                    }
                responses.append(response)
            out_path = raw_dir / f"{sid}.json"
            out_path.write_bytes(canonical_bytes({"schema_version": "task229-successor-output-r0", "responses": responses}))
            data["session_records"][sid] = {"status": "semantic", "response_file": str(out_path.relative_to(root))}
    for evaluator_key in ("blind-A", "blind-B"):
        rows = []
        key_items = []
        for lineage_index, lineage in enumerate(manifest["lineages"]):
            for condition in ("M0_ONLY", "M0_PLUS_E1", "REFERENCE_M1"):
                entry = next(item for item in lineage["conditions"] if item["condition"] == condition)
                sid = entry["session_id"]
                for case in CASES:
                    rid = f"{evaluator_key}-{len(rows):03d}"
                    key_items.append({"response_id": rid, "session_id": sid, "case_id": case})
                    if case == "A" and condition == "M0_ONLY":
                        success = lineage_index < no_support_m0_a
                    elif condition == "REFERENCE_M1":
                        success = True
                    else:
                        success = case in ("B", "C")
                    if data["session_records"][sid]["status"] != "semantic":
                        success = False
                    rows.append({"response_id": rid, "case_id": case, "success": success, "criterion_reference": "synthetic fixture"})
        score_name = f"{evaluator_key}-scores.json"
        key_name = f"{evaluator_key}-key.json"
        (eval_dir / score_name).write_bytes(canonical_bytes({"schema_version": "task229-blind-evaluation-r0", "rows": rows}))
        (eval_dir / key_name).write_bytes(canonical_bytes({"schema_version": "task229-blind-key-r0", "items": key_items}))
        data["evaluators"].append({"evaluator_key": evaluator_key, "scores_file": f"eval/{score_name}", "response_key_file": f"eval/{key_name}"})
    dataset_path = root / "analysis-input.json"
    dataset_path.write_bytes(canonical_bytes(data))
    return dataset_path


def self_test():
    expected = {
        "supported": "INCREMENTAL_POLICY_EFFECT_SUPPORTED",
        "thresholds_not_met": None,
        "five_controls": "INCREMENTAL_POLICY_EFFECT_PARTIAL_OBSERVABILITY",
        "control_failure": "INCREMENTAL_POLICY_EFFECT_NOT_ESTABLISHED_CONTROL_FAILURE"
    }
    with tempfile.TemporaryDirectory(prefix="task229-synthetic-") as temp:
        for scenario, marker in expected.items():
            dataset_path = synthetic_dataset(pathlib.Path(temp) / scenario, scenario)
            first = canonical_bytes(recompute(dataset_path))
            second = canonical_bytes(recompute(dataset_path))
            if first != second:
                raise AssertionError(f"{scenario}: recomputation output is not byte-identical")
            result = json.loads(first)
            if result["result_markers"]["interface_execution"] != "INTERFACE_EXECUTION_WORKING":
                raise AssertionError(f"{scenario}: synthetic interface trace did not validate")
            if result["result_markers"]["reference_target_compatibility"] != "REFERENCE_TARGET_COMPATIBILITY_WORKING":
                raise AssertionError(f"{scenario}: synthetic evaluator scores did not validate")
            if result["result_markers"]["incremental_policy_effect"] != marker:
                raise AssertionError(f"{scenario}: unexpected incremental marker {result['result_markers']['incremental_policy_effect']!r}")
            if scenario == "thresholds_not_met" and result["incremental_policy_effect"]["when_all_controls_observed_threshold_not_met"] is None:
                raise AssertionError("thresholds_not_met: failed support threshold was not recorded")
    print("TASK229_SYNTHETIC_SCHEMA_OBSERVABILITY=PASS")
    print("TASK229_SYNTHETIC_RECOMPUTE_DETERMINISM=BYTE_IDENTICAL")
    print("TASK229_SYNTHETIC_OUTCOME_BOUNDARIES=PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.input is None or args.output is None:
        parser.error("--input and --output are required unless --self-test is used")
    result = recompute(args.input.resolve())
    args.output.write_bytes(canonical_bytes(result))
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    print(f"TASK229_RECOMPUTE=PASS SHA256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
