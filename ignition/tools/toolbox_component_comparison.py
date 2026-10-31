#!/usr/bin/env python3
"""Compare a toolbox incumbent and successor against declared valuable use cases.

This offline analyzer checks caller-supplied scope and matched-result records. It
never changes a registry, retires runtime code, selects a route, or authorizes a
tool invocation.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


MAX_INPUT_BYTES = 512 * 1024
MAX_USE_CASES = 100
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TOOL_VERSION = "0.1.0"


class ComparisonInputError(ValueError):
    """Raised when caller-supplied component comparison data is malformed."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ComparisonInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ComparisonInputError(f"non-standard JSON number is not allowed: {value}")


def _object(value: Any, path: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ComparisonInputError(f"{path} must be an object")
    if set(value) != keys:
        missing = sorted(keys - set(value))
        extra = sorted(set(value) - keys)
        raise ComparisonInputError(f"{path} keys mismatch (missing={missing}, extra={extra})")
    return value


def _text(value: Any, path: str, *, maximum: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ComparisonInputError(f"{path} must be a nonblank string of at most {maximum} characters")
    return value.strip()


def _id(value: Any, path: str) -> str:
    result = _text(value, path, maximum=96)
    if not ID_RE.fullmatch(result):
        raise ComparisonInputError(f"{path} must be a bounded identifier")
    return result


def _digest(value: Any, path: str) -> str:
    result = _text(value, path, maximum=64)
    if not SHA256_RE.fullmatch(result):
        raise ComparisonInputError(f"{path} must be a lowercase SHA-256 digest")
    return result


def _score(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000:
        raise ComparisonInputError(f"{path} must be an integer from 0 to 1000")
    return value


def _rank(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise ComparisonInputError(f"{path} must be an integer from 0 to 100")
    return value


def _cost(value: Any, path: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ComparisonInputError(f"{path} must be a non-negative number or null when unmeasured")
    result = Decimal(value)
    if not result.is_finite() or result < 0 or result > Decimal("1000000000000000"):
        raise ComparisonInputError(f"{path} must be finite and between 0 and 1e15")
    return result


def _string_ids(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_USE_CASES:
        raise ComparisonInputError(f"{path} must be an array of at most {MAX_USE_CASES} identifiers")
    result = [_id(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise ComparisonInputError(f"{path} must not contain duplicates")
    return result


def _parse(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise ComparisonInputError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except ComparisonInputError:
        raise
    except UnicodeDecodeError as exc:
        raise ComparisonInputError("input must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise ComparisonInputError("input must be valid JSON") from exc
    return _object(parsed, "root", {
        "schema_version", "comparison_id", "incumbent", "proposed_successor",
        "evaluation_context", "incumbent_use_cases", "successor_use_cases", "paired_results",
    })


def _use_cases(value: Any, path: str) -> dict[str, dict[str, str]]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_USE_CASES:
        raise ComparisonInputError(f"{path} must contain 1 to {MAX_USE_CASES} use cases")
    cases: dict[str, dict[str, str]] = {}
    for index, raw in enumerate(value):
        row_path = f"{path}[{index}]"
        row = _object(raw, row_path, {
            "use_case_id", "value_basis", "input_contract_sha256", "output_contract_sha256", "evidence_ref",
        })
        case_id = _id(row["use_case_id"], f"{row_path}.use_case_id")
        if case_id in cases:
            raise ComparisonInputError(f"{path} contains duplicate use_case_id {case_id}")
        cases[case_id] = {
            "value_basis": _text(row["value_basis"], f"{row_path}.value_basis"),
            "input_contract_sha256": _digest(row["input_contract_sha256"], f"{row_path}.input_contract_sha256"),
            "output_contract_sha256": _digest(row["output_contract_sha256"], f"{row_path}.output_contract_sha256"),
            "evidence_ref": _text(row["evidence_ref"], f"{row_path}.evidence_ref"),
        }
    return cases


def _result(value: Any, path: str, metric_id: str) -> dict[str, Any]:
    row = _object(value, path, {
        "outcome", "quality_score", "resource_cost", "permission_rank", "adverse_effect_ids",
    })
    outcome = row["outcome"]
    if not isinstance(outcome, str) or outcome not in {"PASS", "FAIL", "UNKNOWN"}:
        raise ComparisonInputError(f"{path}.outcome must be PASS, FAIL, or UNKNOWN")
    score = None if row["quality_score"] is None else _score(row["quality_score"], f"{path}.quality_score")
    if outcome == "UNKNOWN" and score is not None:
        raise ComparisonInputError(f"{path}.quality_score must be null when outcome is UNKNOWN")
    adverse = _string_ids(row["adverse_effect_ids"], f"{path}.adverse_effect_ids")
    return {
        "outcome": outcome,
        "quality_score": score,
        "resource_cost": _cost(row["resource_cost"], f"{path}.resource_cost"),
        "permission_rank": _rank(row["permission_rank"], f"{path}.permission_rank"),
        "adverse_effect_ids": sorted(adverse),
        "resource_metric_id": metric_id,
    }


def compare(raw: bytes) -> dict[str, Any]:
    """Compare explicit valuable-use-case inventories and matched results."""
    document = _parse(raw)
    if document["schema_version"] != "toolbox-component-comparison-input-r0":
        raise ComparisonInputError("schema_version must be toolbox-component-comparison-input-r0")
    comparison_id = _id(document["comparison_id"], "comparison_id")
    incumbent = _object(document["incumbent"], "incumbent", {"tool_id", "version"})
    successor = _object(document["proposed_successor"], "proposed_successor", {"tool_id", "version"})
    incumbent_id = _id(incumbent["tool_id"], "incumbent.tool_id")
    successor_id = _id(successor["tool_id"], "proposed_successor.tool_id")
    incumbent_version = _text(incumbent["version"], "incumbent.version", maximum=64)
    successor_version = _text(successor["version"], "proposed_successor.version", maximum=64)
    if incumbent_id == successor_id:
        raise ComparisonInputError("incumbent and proposed successor must have different tool IDs")

    context = _object(document["evaluation_context"], "evaluation_context", {
        "environment_sha256", "evaluator_sha256", "resource_metric_id", "resource_metric_unit",
    })
    environment_sha256 = (
        None if context["environment_sha256"] is None
        else _digest(context["environment_sha256"], "evaluation_context.environment_sha256")
    )
    evaluator_sha256 = (
        None if context["evaluator_sha256"] is None
        else _digest(context["evaluator_sha256"], "evaluation_context.evaluator_sha256")
    )
    metric_id = _id(context["resource_metric_id"], "evaluation_context.resource_metric_id")
    metric_unit = _text(context["resource_metric_unit"], "evaluation_context.resource_metric_unit", maximum=64)

    old_cases = _use_cases(document["incumbent_use_cases"], "incumbent_use_cases")
    new_cases = _use_cases(document["successor_use_cases"], "successor_use_cases")
    shared_ids = sorted(
        case_id for case_id in old_cases.keys() & new_cases.keys()
        if old_cases[case_id]["input_contract_sha256"] == new_cases[case_id]["input_contract_sha256"]
        and old_cases[case_id]["output_contract_sha256"] == new_cases[case_id]["output_contract_sha256"]
    )
    old_unique = sorted(set(old_cases) - set(shared_ids))
    new_unique = sorted(set(new_cases) - set(shared_ids))
    contract_mismatch = sorted((old_cases.keys() & new_cases.keys()) - set(shared_ids))

    rows_raw = document["paired_results"]
    if not isinstance(rows_raw, list) or len(rows_raw) > MAX_USE_CASES:
        raise ComparisonInputError(f"paired_results must contain at most {MAX_USE_CASES} rows")
    paired: dict[str, dict[str, Any]] = {}
    mismatched_rows: list[str] = []
    for index, raw_row in enumerate(rows_raw):
        path = f"paired_results[{index}]"
        row = _object(raw_row, path, {
            "use_case_id", "input_sha256", "output_contract_sha256", "environment_sha256",
            "evaluator_sha256", "evidence_ref", "incumbent", "proposed_successor",
        })
        case_id = _id(row["use_case_id"], f"{path}.use_case_id")
        if case_id in paired:
            raise ComparisonInputError(f"paired_results contains duplicate use_case_id {case_id}")
        if case_id not in shared_ids:
            raise ComparisonInputError(f"{path}.use_case_id must name an identical declared use case")
        pair_hashes = {
            "input_sha256": _digest(row["input_sha256"], f"{path}.input_sha256"),
            "output_contract_sha256": _digest(row["output_contract_sha256"], f"{path}.output_contract_sha256"),
            "environment_sha256": None if row["environment_sha256"] is None else _digest(row["environment_sha256"], f"{path}.environment_sha256"),
            "evaluator_sha256": None if row["evaluator_sha256"] is None else _digest(row["evaluator_sha256"], f"{path}.evaluator_sha256"),
        }
        expected = old_cases[case_id]
        aligned = (
            pair_hashes["output_contract_sha256"] == expected["output_contract_sha256"]
            and environment_sha256 is not None
            and pair_hashes["environment_sha256"] is not None
            and pair_hashes["environment_sha256"] == environment_sha256
            and evaluator_sha256 is not None
            and pair_hashes["evaluator_sha256"] is not None
            and pair_hashes["evaluator_sha256"] == evaluator_sha256
        )
        old_result = _result(row["incumbent"], f"{path}.incumbent", metric_id)
        new_result = _result(row["proposed_successor"], f"{path}.proposed_successor", metric_id)
        paired[case_id] = {
            "input_sha256": pair_hashes["input_sha256"],
            "output_contract_sha256": pair_hashes["output_contract_sha256"],
            "environment_sha256": pair_hashes["environment_sha256"],
            "evaluator_sha256": pair_hashes["evaluator_sha256"],
            "evidence_ref": _text(row["evidence_ref"], f"{path}.evidence_ref"),
            "context_aligned": aligned,
            "incumbent": old_result,
            "proposed_successor": new_result,
        }
        if not aligned:
            mismatched_rows.append(case_id)

    missing_pairs = sorted(set(shared_ids) - set(paired))
    evaluated_pairs = [paired[case_id] for case_id in shared_ids if case_id in paired]
    unknown_pairs = sorted(
        case_id for case_id in shared_ids if case_id in paired and (
            not paired[case_id]["context_aligned"]
            or paired[case_id]["incumbent"]["outcome"] == "UNKNOWN"
            or paired[case_id]["proposed_successor"]["outcome"] == "UNKNOWN"
            or paired[case_id]["incumbent"]["quality_score"] is None
            or paired[case_id]["proposed_successor"]["quality_score"] is None
        )
    )
    missing_costs = sorted(
        case_id for case_id in shared_ids if case_id in paired and (
            paired[case_id]["incumbent"]["resource_cost"] is None
            or paired[case_id]["proposed_successor"]["resource_cost"] is None
        )
    )
    performance_complete = bool(shared_ids) and not missing_pairs and not unknown_pairs and not missing_costs
    old_advantages: list[str] = []
    new_advantages: list[str] = []
    per_case: list[dict[str, Any]] = []
    strict_improvement = False
    no_worse_all = performance_complete and all(
        paired[case_id]["proposed_successor"]["outcome"] == "PASS"
        for case_id in shared_ids if case_id in paired
    )
    for case_id in shared_ids:
        pair = paired.get(case_id)
        if pair is None:
            continue
        old = pair["incumbent"]
        new = pair["proposed_successor"]
        if not pair["context_aligned"] or old["outcome"] == "UNKNOWN" or new["outcome"] == "UNKNOWN" or old["quality_score"] is None or new["quality_score"] is None:
            status = "COMPARISON_UNKNOWN"
            no_worse_all = False
        else:
            old_pass = old["outcome"] == "PASS"
            new_pass = new["outcome"] == "PASS"
            new_effects = sorted(set(new["adverse_effect_ids"]) - set(old["adverse_effect_ids"]))
            old_effects_removed = bool(set(old["adverse_effect_ids"]) - set(new["adverse_effect_ids"]))
            worse = (
                (old_pass and not new_pass)
                or new["quality_score"] < old["quality_score"]
                or new["permission_rank"] > old["permission_rank"]
                or bool(new_effects)
                or (old["resource_cost"] is not None and new["resource_cost"] is not None and new["resource_cost"] > old["resource_cost"])
            )
            better = (
                (new_pass and not old_pass)
                or (new_pass and old_pass and new["quality_score"] > old["quality_score"])
                or new["permission_rank"] < old["permission_rank"]
                or old_effects_removed
                or (old["resource_cost"] is not None and new["resource_cost"] is not None and new["resource_cost"] < old["resource_cost"])
            )
            if not new_pass:
                no_worse_all = False
            if worse:
                status = "INCUMBENT_ADVANTAGE"
                old_advantages.append(case_id)
                no_worse_all = False
            elif better:
                status = "SUCCESSOR_ADVANTAGE"
                new_advantages.append(case_id)
                strict_improvement = True
            else:
                status = "NO_STRICT_DIFFERENCE"
        per_case.append({
            "use_case_id": case_id,
            "status": status,
            "evidence_ref": pair["evidence_ref"],
            "outcome_pair": [old["outcome"], new["outcome"]],
            "quality_score_pair": [old["quality_score"], new["quality_score"]],
            "resource_cost_pair": [
                str(old["resource_cost"]) if old["resource_cost"] is not None else None,
                str(new["resource_cost"]) if new["resource_cost"] is not None else None,
            ],
            "permission_rank_pair": [old["permission_rank"], new["permission_rank"]],
        })

    evidence_unknown = bool(missing_pairs or unknown_pairs or contract_mismatch)
    if contract_mismatch:
        scope_disposition = "COMPARISON_UNKNOWN"
        performance_status = "COMPARISON_UNKNOWN"
    elif old_unique or new_unique or old_advantages:
        scope_disposition = "COEXIST_DISTINCT_SCOPE"
        performance_status = "COMPARABLE_AS_DECLARED" if performance_complete else "COMPARISON_UNKNOWN"
    elif evidence_unknown:
        scope_disposition = "COMPARISON_UNKNOWN"
        performance_status = "COMPARISON_UNKNOWN"
    elif not performance_complete:
        scope_disposition = "COMPARISON_UNKNOWN"
        performance_status = "COMPARISON_UNKNOWN"
    elif no_worse_all and strict_improvement:
        scope_disposition = "REPLACEMENT_SUPPORTED_AS_DECLARED"
        performance_status = "COMPARABLE_AS_DECLARED"
    elif new_advantages:
        scope_disposition = "RETAIN_BOTH_NO_DOMINANCE"
        performance_status = "COMPARABLE_AS_DECLARED"
    else:
        scope_disposition = "RETAIN_INCUMBENT_NO_SUCCESSOR_ADVANTAGE"
        performance_status = "COMPARABLE_AS_DECLARED"

    if scope_disposition == "COMPARISON_UNKNOWN":
        next_comparison = "Run one matched, low-cost task for every shared declared use case with identical input, output contract, evaluator, environment, permission inventory, and resource unit."
    elif scope_disposition == "COEXIST_DISTINCT_SCOPE":
        next_comparison = "Keep both routes limited to their supported task ranges; compare any remaining shared use case only if a route decision needs it."
    elif scope_disposition == "REPLACEMENT_SUPPORTED_AS_DECLARED":
        next_comparison = "Review the cited evidence and migrate through the canonical candidate card and route projections; this tool does not retire code or change the registry."
    else:
        next_comparison = "Retain the incumbent; add the proposed tool only for a separately evidenced use case or after a new matched comparison."

    return {
        "schema_version": "toolbox-component-comparison-output-r0",
        "comparison_id": comparison_id,
        "tools": {
            "incumbent": {"tool_id": incumbent_id, "version": incumbent_version},
            "proposed_successor": {"tool_id": successor_id, "version": successor_version},
        },
        "scope_disposition": scope_disposition,
        "performance_comparison_status": performance_status,
        "scope": {
            "shared_use_case_ids": shared_ids,
            "incumbent_unique_use_case_ids": old_unique,
            "successor_unique_use_case_ids": new_unique,
            "same_id_contract_mismatch_use_case_ids": contract_mismatch,
        },
        "paired_result_summary": {
            "matched_pair_count": len(evaluated_pairs),
            "missing_pair_use_case_ids": missing_pairs,
            "incomparable_or_unknown_use_case_ids": unknown_pairs,
            "missing_cost_use_case_ids": missing_costs,
            "case_results": per_case,
            "incumbent_advantage_use_case_ids": sorted(old_advantages),
            "successor_advantage_use_case_ids": sorted(new_advantages),
            "resource_metric": {"metric_id": metric_id, "unit": metric_unit},
        },
        "evidence_refs": sorted({
            *[item["evidence_ref"] for item in old_cases.values()],
            *[item["evidence_ref"] for item in new_cases.values()],
            *[pair["evidence_ref"] for pair in paired.values()],
        }),
        "next_low_cost_comparison": next_comparison,
        "governance_boundary": {
            "caller_evidence_authenticated": False,
            "use_case_value_independently_verified": False,
            "tool_retired_or_registry_changed": False,
            "route_selected": False,
            "execution_authorized": False,
            "permission_changed": False,
        },
        "claim_ceiling": "Deterministic analysis of caller-declared use-case inventories and matched outcomes only; supplied evidence, value claims, measurements, risk lists, and tool sources are not authenticated or independently validated.",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded JSON request from stdin")
    args = parser.parse_args()
    if not args.stdin:
        parser.error("--stdin is required")
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = compare(raw)
    except ComparisonInputError as exc:
        print(json.dumps({"error": str(exc), "execution_authorized": False}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
