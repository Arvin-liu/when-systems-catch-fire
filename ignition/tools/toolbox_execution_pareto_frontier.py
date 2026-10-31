#!/usr/bin/env python3
"""Summarize a caller-supplied paired performance/resource comparison.

This offline tool reports the observed nondominated candidates above the
baseline pass-rate floor. It does not authenticate measurements or select,
install, modify, route, or authorize a candidate.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import re
from pathlib import Path
import sys
from typing import Any


MAX_INPUT_BYTES = 512 * 1024
MAX_CANDIDATES = 20
MAX_OBSERVATIONS_PER_CANDIDATE = 500
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ParetoInputError(ValueError):
    """Raised when an evaluation snapshot is malformed or incomparable."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ParetoInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ParetoInputError(f"non-standard JSON number is not allowed: {value}")


def _object(value: Any, path: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ParetoInputError(f"{path} must be an object")
    if set(value) != keys:
        missing = sorted(keys - set(value))
        extra = sorted(set(value) - keys)
        raise ParetoInputError(f"{path} keys mismatch (missing={missing}, extra={extra})")
    return value


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ParetoInputError(f"{path} must be a nonblank string")
    return value


def _identifier(value: Any, path: str) -> str:
    result = _nonblank(value, path)
    if not ID_RE.fullmatch(result):
        raise ParetoInputError(f"{path} must be a bounded identifier using letters, digits, . _ : or -")
    return result


def _digest(value: Any, path: str) -> str:
    result = _nonblank(value, path)
    if not SHA256_RE.fullmatch(result):
        raise ParetoInputError(f"{path} must be a lowercase SHA-256 digest")
    return result


def _cost(value: Any, path: str) -> Fraction | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ParetoInputError(f"{path} must be a non-negative JSON number or null when not measured")
    if isinstance(value, Decimal):
        if not value.is_finite() or value < 0 or value > Decimal("1000000000000000"):
            raise ParetoInputError(f"{path} must be finite and between 0 and 1e15")
        digits = value.as_tuple().digits
        exponent = value.as_tuple().exponent
        if len(digits) > 32 or not isinstance(exponent, int) or abs(exponent) > 30:
            raise ParetoInputError(f"{path} has excessive numeric precision")
        return Fraction(value)
    if value < 0 or value > 10**15:
        raise ParetoInputError(f"{path} must be between 0 and 1e15")
    return Fraction(value)


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _parse(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise ParetoInputError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except ParetoInputError:
        raise
    except UnicodeDecodeError as exc:
        raise ParetoInputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise ParetoInputError("input must be valid JSON") from exc
    return _object(parsed, "root", {"schema_version", "evaluation_context", "resource_metric", "baseline_candidate_id", "candidates"})


def analyze(raw: bytes) -> dict[str, Any]:
    """Return exact observed rates and resource-cost Pareto status for paired rows."""
    document = _parse(raw)
    if document["schema_version"] != "execution-candidate-pareto-input-r0":
        raise ParetoInputError("schema_version must be execution-candidate-pareto-input-r0")

    context = _object(
        document["evaluation_context"],
        "evaluation_context",
        {"evaluation_id", "task_set_sha256", "evaluator_sha256", "environment_ref"},
    )
    evaluation_id = _identifier(context["evaluation_id"], "evaluation_context.evaluation_id")
    task_set_sha256 = _digest(context["task_set_sha256"], "evaluation_context.task_set_sha256")
    evaluator_sha256 = _digest(context["evaluator_sha256"], "evaluation_context.evaluator_sha256")
    environment_ref = _nonblank(context["environment_ref"], "evaluation_context.environment_ref")

    metric = _object(document["resource_metric"], "resource_metric", {"metric_id", "unit"})
    metric_id = _identifier(metric["metric_id"], "resource_metric.metric_id")
    metric_unit = _nonblank(metric["unit"], "resource_metric.unit")
    baseline_candidate_id = _identifier(document["baseline_candidate_id"], "baseline_candidate_id")

    candidates_raw = document["candidates"]
    if not isinstance(candidates_raw, list) or not 2 <= len(candidates_raw) <= MAX_CANDIDATES:
        raise ParetoInputError(f"candidates must contain between 2 and {MAX_CANDIDATES} candidates")

    candidates: list[dict[str, Any]] = []
    candidate_ids: set[str] = set()
    paired_keys: set[tuple[str, str]] | None = None
    total_observations = 0
    any_missing_cost = False

    for index, candidate_raw in enumerate(candidates_raw):
        path = f"candidates[{index}]"
        candidate = _object(candidate_raw, path, {"candidate_id", "candidate_ref", "observations"})
        candidate_id = _identifier(candidate["candidate_id"], f"{path}.candidate_id")
        if candidate_id in candidate_ids:
            raise ParetoInputError(f"duplicate candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        candidate_ref = _nonblank(candidate["candidate_ref"], f"{path}.candidate_ref")
        observations_raw = candidate["observations"]
        if not isinstance(observations_raw, list) or not 1 <= len(observations_raw) <= MAX_OBSERVATIONS_PER_CANDIDATE:
            raise ParetoInputError(f"{path}.observations must contain 1 to {MAX_OBSERVATIONS_PER_CANDIDATE} rows")

        observations: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str]] = set()
        passed = 0
        resource_cost_sum = Fraction(0)
        candidate_cost_complete = True
        for row_index, observation_raw in enumerate(observations_raw):
            row_path = f"{path}.observations[{row_index}]"
            row = _object(observation_raw, row_path, {"case_id", "trial_id", "outcome", "resource_cost", "evidence_ref"})
            case_id = _identifier(row["case_id"], f"{row_path}.case_id")
            trial_id = _identifier(row["trial_id"], f"{row_path}.trial_id")
            key = (case_id, trial_id)
            if key in seen_keys:
                raise ParetoInputError(f"{row_path} duplicates paired case/trial {case_id}/{trial_id}")
            seen_keys.add(key)
            outcome = row["outcome"]
            if not isinstance(outcome, str) or outcome not in {"PASS", "FAIL"}:
                raise ParetoInputError(f"{row_path}.outcome must be PASS or FAIL; unknown results cannot be scored")
            if outcome == "PASS":
                passed += 1
            cost = _cost(row["resource_cost"], f"{row_path}.resource_cost")
            if cost is None:
                candidate_cost_complete = False
            else:
                resource_cost_sum += cost
            observations.append({
                "case_id": case_id,
                "trial_id": trial_id,
                "outcome": outcome,
                "resource_cost": _fraction_text(cost) if cost is not None else None,
                "evidence_ref": _nonblank(row["evidence_ref"], f"{row_path}.evidence_ref"),
            })

        if paired_keys is None:
            paired_keys = seen_keys
        elif seen_keys != paired_keys:
            raise ParetoInputError(f"{path}.observations do not match the paired case/trial set of candidates[0]")
        total_observations += len(observations)
        if total_observations > MAX_CANDIDATES * MAX_OBSERVATIONS_PER_CANDIDATE:
            raise ParetoInputError("total observations exceed the bounded comparison size")
        any_missing_cost = any_missing_cost or not candidate_cost_complete
        candidates.append({
            "candidate_id": candidate_id,
            "candidate_ref": candidate_ref,
            "observations": observations,
            "pass_count": passed,
            "trial_count": len(observations),
            "pass_rate": Fraction(passed, len(observations)),
            "resource_cost_sum": resource_cost_sum if candidate_cost_complete else None,
            "resource_cost_complete": candidate_cost_complete,
        })

    if baseline_candidate_id not in candidate_ids:
        raise ParetoInputError("baseline_candidate_id must identify one supplied candidate")
    if paired_keys is None:
        raise ParetoInputError("no paired case/trial rows were supplied")

    baseline = next(item for item in candidates if item["candidate_id"] == baseline_candidate_id)
    quality_floor = baseline["pass_rate"]
    complete_costs = not any_missing_cost
    analysis_status = (
        "COMPARABLE_CALLER_DECLARED_MEASUREMENTS_NOT_AUTHENTICATED"
        if complete_costs
        else "COMPARISON_UNDETERMINED_COST_MISSING"
    )

    summaries: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    for candidate in candidates:
        pass_rate = candidate["pass_rate"]
        status = "COST_INCOMPLETE" if not candidate["resource_cost_complete"] else "ABOVE_BASELINE_PASS_RATE"
        if pass_rate < quality_floor:
            status = "BELOW_BASELINE_PASS_RATE"
        elif complete_costs:
            eligible.append(candidate)
        summaries.append({
            "candidate_id": candidate["candidate_id"],
            "candidate_ref": candidate["candidate_ref"],
            "pass_count": candidate["pass_count"],
            "trial_count": candidate["trial_count"],
            "pass_rate_fraction": _fraction_text(pass_rate),
            "resource_metric_id": metric_id,
            "resource_metric_unit": metric_unit,
            "mean_resource_cost_fraction": (
                _fraction_text(candidate["resource_cost_sum"] / candidate["trial_count"])
                if candidate["resource_cost_complete"]
                else None
            ),
            "status": status,
            "dominated_by": [],
        })

    frontier_ids: list[str] = []
    if complete_costs:
        for candidate in eligible:
            dominators = []
            for other in eligible:
                if other["candidate_id"] == candidate["candidate_id"]:
                    continue
                no_worse = other["pass_rate"] >= candidate["pass_rate"] and other["resource_cost_sum"] <= candidate["resource_cost_sum"]
                strictly_better = other["pass_rate"] > candidate["pass_rate"] or other["resource_cost_sum"] < candidate["resource_cost_sum"]
                if no_worse and strictly_better:
                    dominators.append(other["candidate_id"])
            summary = next(row for row in summaries if row["candidate_id"] == candidate["candidate_id"])
            if dominators:
                summary["status"] = "DOMINATED"
                summary["dominated_by"] = sorted(dominators)
            else:
                summary["status"] = "ON_FRONTIER"
                frontier_ids.append(candidate["candidate_id"])

    source_path = Path(__file__).resolve()
    return {
        "schema_version": "execution-candidate-pareto-output-r0",
        "analysis_status": analysis_status,
        "evaluation_context": {
            "evaluation_id": evaluation_id,
            "task_set_sha256": task_set_sha256,
            "evaluator_sha256": evaluator_sha256,
            "environment_ref": environment_ref,
            "paired_case_trial_count": len(paired_keys),
        },
        "resource_metric": {"metric_id": metric_id, "unit": metric_unit, "direction": "MINIMIZE"},
        "baseline_candidate_id": baseline_candidate_id,
        "quality_floor_pass_rate_fraction": _fraction_text(quality_floor),
        "candidates": summaries,
        "frontier_candidate_ids": frontier_ids,
        "frontier_status": "OBSERVED_FRONTIER" if complete_costs else "NOT_COMPUTED_MISSING_COST",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "execution_authorized": False,
        "non_claims": {
            "measurements_authenticated": False,
            "statistical_significance_established": False,
            "task_generalization_established": False,
            "causal_improvement_established": False,
            "route_or_candidate_selected": False,
            "tool_or_harness_modified": False,
            "permission_changed": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON comparison from stdin")
    args = parser.parse_args(argv)
    if not args.stdin:
        return 2
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = analyze(raw)
    except ParetoInputError as exc:
        print(f"EXECUTION_PARETO_INPUT_REJECTED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
