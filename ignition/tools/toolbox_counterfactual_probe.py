#!/usr/bin/env python3
"""Run bounded, caller-declared counterfactual probes against one pure model."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import toolbox_function_os_evaluator as function_os_runner  # noqa: E402


TOOL_ID = "research.probe_counterfactual_fragility"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "toolbox-counterfactual-probe-input-r0"
OUTPUT_SCHEMA_VERSION = "toolbox-counterfactual-probe-output-r0"
MAX_REQUEST_BYTES = 65536
MAX_OUTPUT_BYTES = 262144
MAX_FUNCTION_SPEC_BYTES = 16384
MAX_ASSUMPTIONS = 16
MAX_PROBES = 8
MAX_TEXT_CHARS = 512
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
TYPE_MAP = {
    "integer": int,
    "int": int,
    "float": float,
    "number": float,
    "boolean": bool,
    "bool": bool,
}
BOOLEAN_DIRECTIONS = {"ANY_CHANGE", "NO_CHANGE", "TRUE_TO_FALSE", "FALSE_TO_TRUE"}
NUMERIC_DIRECTIONS = {"ANY_CHANGE", "NO_CHANGE", "INCREASE", "DECREASE"}
INVARIANTS = [
    "COUNTERFACTUAL_EDIT_IS_NOT_EVIDENCE_OF_ACTUAL_WORLD",
    "COUNTERFACTUAL_CHANGE_MUST_BIND_TARGET_ASSUMPTION",
    "DISCONFIRMATION_HAS_PRIORITY_OVER_SELF_CONFIRMING_REPETITION",
    "FAILED_COUNTERFACTUAL_DOES_NOT_REWRITE_SOURCE_EVIDENCE",
]


class CounterfactualProbeError(ValueError):
    """Raised when the bounded probe contract is malformed."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CounterfactualProbeError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _exact_fields(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CounterfactualProbeError(where + " must be an object")
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise CounterfactualProbeError(f"{where} fields mismatch; missing={missing}, extra={extra}")
    return value


def _text(value: Any, where: str, *, maximum: int = MAX_TEXT_CHARS) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise CounterfactualProbeError(f"{where} must be nonblank text of at most {maximum} characters")
    return value


def _identifier(value: Any, where: str) -> str:
    text = _text(value, where, maximum=128)
    if ID_PATTERN.fullmatch(text) is None:
        raise CounterfactualProbeError(where + " must be a bounded identifier")
    return text


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_finite_scalar(value: Any) -> bool:
    return type(value) in {bool, int} or (type(value) is float and math.isfinite(value))


def _validate_request(request: Any) -> dict[str, Any]:
    data = _exact_fields(
        request,
        {"schema_version", "target_conclusion", "function_spec", "baseline_inputs", "assumptions", "probes"},
        "request",
    )
    if data["schema_version"] != INPUT_SCHEMA_VERSION:
        raise CounterfactualProbeError("schema_version must be " + INPUT_SCHEMA_VERSION)
    target = _exact_fields(data["target_conclusion"], {"conclusion_id", "statement"}, "target_conclusion")
    _identifier(target["conclusion_id"], "target_conclusion.conclusion_id")
    _text(target["statement"], "target_conclusion.statement")

    spec = data["function_spec"]
    if not isinstance(spec, dict):
        raise CounterfactualProbeError("function_spec must be an object")
    try:
        spec_bytes = _canonical_json(spec).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CounterfactualProbeError("function_spec must contain finite JSON values only") from exc
    if len(spec_bytes) > MAX_FUNCTION_SPEC_BYTES:
        raise CounterfactualProbeError("function_spec exceeds 16 KiB")
    input_contract = spec.get("inputs")
    output_contract = spec.get("outputs")
    if not isinstance(input_contract, dict) or not 1 <= len(input_contract) <= 16:
        raise CounterfactualProbeError("function_spec.inputs must declare 1 to 16 inputs")
    if not isinstance(output_contract, dict) or len(output_contract) != 1:
        raise CounterfactualProbeError("function_spec.outputs must declare exactly one output")
    output_type_name = next(iter(output_contract.values()))
    if output_type_name not in TYPE_MAP:
        raise CounterfactualProbeError("function_spec output type must be numeric or boolean")
    output_type = TYPE_MAP[output_type_name]
    if output_type is bool:
        allowed_directions = BOOLEAN_DIRECTIONS
    else:
        allowed_directions = NUMERIC_DIRECTIONS

    baseline = data["baseline_inputs"]
    if not isinstance(baseline, dict):
        raise CounterfactualProbeError("baseline_inputs must be an object")

    raw_assumptions = data["assumptions"]
    if not isinstance(raw_assumptions, list) or not 1 <= len(raw_assumptions) <= MAX_ASSUMPTIONS:
        raise CounterfactualProbeError(f"assumptions must contain 1 to {MAX_ASSUMPTIONS} entries")
    assumptions: dict[str, dict[str, Any]] = {}
    bound_inputs: set[str] = set()
    for index, raw in enumerate(raw_assumptions):
        where = f"assumptions[{index}]"
        item = _exact_fields(raw, {"assumption_id", "statement", "input_names"}, where)
        assumption_id = _identifier(item["assumption_id"], where + ".assumption_id")
        if assumption_id in assumptions:
            raise CounterfactualProbeError("assumption_id values must be unique")
        statement = _text(item["statement"], where + ".statement")
        input_names = item["input_names"]
        if (
            not isinstance(input_names, list)
            or not input_names
            or any(not isinstance(name, str) or name not in input_contract for name in input_names)
            or len(input_names) != len(set(input_names))
        ):
            raise CounterfactualProbeError(where + ".input_names must uniquely name declared FunctionSpec inputs")
        if bound_inputs.intersection(input_names):
            raise CounterfactualProbeError("each FunctionSpec input may bind to only one declared assumption")
        bound_inputs.update(input_names)
        assumptions[assumption_id] = {
            "assumption_id": assumption_id,
            "statement": statement,
            "input_names": list(input_names),
        }

    raw_probes = data["probes"]
    if not isinstance(raw_probes, list) or not 1 <= len(raw_probes) <= MAX_PROBES:
        raise CounterfactualProbeError(f"probes must contain 1 to {MAX_PROBES} entries")
    probe_ids: set[str] = set()
    for index, raw in enumerate(raw_probes):
        where = f"probes[{index}]"
        item = _exact_fields(
            raw,
            {"probe_id", "assumption_id", "input_name", "replacement_value", "expected_direction", "admissibility_note"},
            where,
        )
        probe_id = _identifier(item["probe_id"], where + ".probe_id")
        if probe_id in probe_ids:
            raise CounterfactualProbeError("probe_id values must be unique")
        probe_ids.add(probe_id)
        assumption_id = item["assumption_id"]
        if assumption_id not in assumptions:
            raise CounterfactualProbeError(where + ".assumption_id must name a declared load-bearing assumption")
        input_name = item["input_name"]
        if input_name not in assumptions[assumption_id]["input_names"]:
            raise CounterfactualProbeError(where + ".input_name must bind the declared assumption")
        declared_type = input_contract.get(input_name)
        expected_python_type = TYPE_MAP.get(declared_type)
        replacement = item["replacement_value"]
        if expected_python_type is None or type(replacement) is not expected_python_type or not _is_finite_scalar(replacement):
            raise CounterfactualProbeError(where + ".replacement_value must match the declared finite input type")
        if input_name in baseline and type(baseline[input_name]) is expected_python_type and replacement == baseline[input_name]:
            raise CounterfactualProbeError(where + ".replacement_value must differ from the baseline value")
        direction = item["expected_direction"]
        if direction not in allowed_directions:
            raise CounterfactualProbeError(where + ".expected_direction is incompatible with the FunctionSpec output type")
        _text(item["admissibility_note"], where + ".admissibility_note", maximum=400)
    return data


def _evaluate_case(spec: dict[str, Any], inputs: dict[str, Any], case_id: str) -> tuple[dict[str, Any], Any]:
    binding = {"function_spec": spec, "inputs": inputs}
    result: dict[str, Any] | None = None
    error: str | None = None
    try:
        result = function_os_runner.build_evaluation_result(spec, inputs)
    except Exception as exc:  # Preserve each failed probe as a result instead of dropping it.
        error = (type(exc).__name__ + ": " + str(exc))[:512]
    if result is None:
        return ({
            "case_id": case_id,
            "case_input_sha256": _sha256(binding),
            "execution_status": "NOT_COMPLETED",
            "policy_status": "EVALUATION_ERROR",
            "n7_status": "NOT_AVAILABLE",
            "artifact_integrity_valid": False,
            "evaluable": False,
            "output_name": next(iter(spec.get("outputs", {"unknown": None}))),
            "output_value": None,
            "trace_sha256": None,
            "evaluation_error": error,
        }, None)

    output_name = next(iter(spec["outputs"]))
    n7_status = result.get("n7_validation", {}).get("status", "UNKNOWN")
    artifact_valid = result.get("artifact_integrity", {}).get("valid") is True
    output_value = result.get("outputs", {}).get(output_name)
    evaluable = (
        result.get("policy_status") == "OK"
        and result.get("execution_status") == "OK"
        and n7_status == "PASS"
        and artifact_valid
        and _is_finite_scalar(output_value)
    )
    return ({
        "case_id": case_id,
        "case_input_sha256": _sha256(binding),
        "execution_status": result.get("execution_status", "UNKNOWN"),
        "policy_status": result.get("policy_status", "UNKNOWN"),
        "n7_status": n7_status,
        "artifact_integrity_valid": artifact_valid,
        "evaluable": evaluable,
        "output_name": output_name,
        "output_value": output_value if evaluable else None,
        "trace_sha256": _sha256(result.get("trace", {})),
        "evaluation_error": None,
    }, result)


def _observed_direction(before: Any, after: Any, output_type: type) -> str:
    if before == after:
        return "NO_CHANGE"
    if output_type is bool:
        return "TRUE_TO_FALSE" if before is True else "FALSE_TO_TRUE"
    return "INCREASE" if after > before else "DECREASE"


def probe_counterfactual_fragility(request: Any) -> dict[str, Any]:
    """Evaluate independent one-input edits; return only model-conditional results."""
    data = _validate_request(request)
    spec = data["function_spec"]
    baseline_inputs = data["baseline_inputs"]
    baseline_case, baseline_raw = _evaluate_case(spec, baseline_inputs, "BASELINE")
    assumptions = {item["assumption_id"]: item for item in data["assumptions"]}
    output_name, output_type_name = next(iter(spec["outputs"].items()))
    output_type = TYPE_MAP[output_type_name]
    probe_results: list[dict[str, Any]] = []
    for probe in data["probes"]:
        edited_inputs = dict(baseline_inputs)
        input_name = probe["input_name"]
        original_value = baseline_inputs.get(input_name)
        replacement_value = probe["replacement_value"]
        edited_inputs[input_name] = replacement_value
        evaluated_case, _ = _evaluate_case(spec, edited_inputs, probe["probe_id"])
        comparable = baseline_case["evaluable"] and evaluated_case["evaluable"]
        if comparable:
            observed = _observed_direction(baseline_case["output_value"], evaluated_case["output_value"], output_type)
            expected = probe["expected_direction"]
            expectation_match = observed != "NO_CHANGE" if expected == "ANY_CHANGE" else observed == expected
            stability = "STABLE_WITHIN_DECLARED_MODEL" if observed == "NO_CHANGE" else "FRAGILE_WITHIN_DECLARED_MODEL"
            disconfirmation_status = (
                "EXPECTED_DIRECTION_OBSERVED_NOT_CONFIRMATORY"
                if expectation_match
                else "EXPECTED_DIRECTION_NOT_OBSERVED_PRESERVE_AS_DISCONFIRMING_RESULT"
            )
        else:
            observed = None
            expectation_match = None
            stability = "NOT_ASSESSABLE"
            disconfirmation_status = "NOT_ASSESSABLE_FAILURE_PRESERVED"
        probe_results.append({
            "probe_id": probe["probe_id"],
            "target_conclusion_id": data["target_conclusion"]["conclusion_id"],
            "assumption_id": probe["assumption_id"],
            "assumption_statement": assumptions[probe["assumption_id"]]["statement"],
            "intervention": {
                "input_name": input_name,
                "baseline_value": original_value,
                "replacement_value": replacement_value,
            },
            "expected_direction": probe["expected_direction"],
            "observed_direction": observed,
            "expected_direction_match": expectation_match,
            "disconfirmation_status": disconfirmation_status,
            "admissibility": {
                "status": "CALLER_DECLARED_NOT_VERIFIED",
                "note": probe["admissibility_note"],
            },
            "observed_or_simulated_result": evaluated_case,
            "conclusion_stability": stability,
        })

    successful = baseline_case["evaluable"] and all(item["observed_or_simulated_result"]["evaluable"] for item in probe_results)
    wrapper_path = "ignition/tools/toolbox_counterfactual_probe.py"
    wrapper_sha = hashlib.sha256(HERE.read_bytes()).hexdigest()
    result = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": "COUNTERFACTUAL_PROBE_REPORTED" if successful else "COUNTERFACTUAL_PROBE_WITH_FAILURES_RETAINED",
        "request_sha256": _sha256(data),
        "target_conclusion": data["target_conclusion"],
        "model_binding": {
            "function_id": spec.get("function_id"),
            "function_spec_sha256": _sha256(spec),
            "output_name": output_name,
            "output_type": output_type_name,
            "function_os_version": "0.2.1rc0-candidate",
        },
        "baseline": baseline_case,
        "probes": probe_results,
        "evaluation_count": 1 + len(probe_results),
        "each_probe_starts_from_baseline": True,
        "counterfactual_edit_is_actual_world_evidence": False,
        "source_evidence_mutated": False,
        "external_action_taken": False,
        "admissibility_ceiling": "Caller-declared model admissibility note; the tool does not verify real-world admissibility.",
        "invariants_applied": INVARIANTS,
        "wrapper_source": {"path": wrapper_path, "sha256": wrapper_sha},
        "function_os_source_refs": baseline_raw.get("source_refs", []) if baseline_raw else [],
        "claim_ceiling": (
            "Sensitivity of a caller-declared bounded pure symbolic model under independent caller-declared input edits. "
            "Results do not establish actual-world evidence, causal identification, model validity, scientific truth, "
            "admissible real-world interventions, or a proof. Matching a predicted direction is not confirmation; "
            "a mismatched or failed probe remains visible as a disconfirming or unassessable model result."
        ),
    }
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise CounterfactualProbeError("output exceeds 256 KiB")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON probe request from stdin")
    parser.parse_args(argv)
    if sys.version_info < (3, 10):
        print("COUNTERFACTUAL_PROBE_REQUIRES_PYTHON_3_10_OR_NEWER", file=sys.stderr)
        return 2
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise CounterfactualProbeError("stdin request exceeds 64 KiB")
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        result = probe_counterfactual_fragility(request)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, CounterfactualProbeError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print("COUNTERFACTUAL_PROBE_NOT_AVAILABLE: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
