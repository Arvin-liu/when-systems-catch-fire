#!/usr/bin/env python3
"""Summarize caller-declared evidence for one governed improvement transition.

This is a bounded, offline preflight. It never edits, deploys, merges, or
authorizes a successor system. All hashes, measurements, and scope declarations
remain caller-supplied and unauthenticated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from typing import Any


MAX_INPUT_BYTES = 131072
MAX_LIST_ITEMS = 128
HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
INPUT_KEYS = {
    "schema_version", "transition_id", "predecessor", "successor_candidate",
    "changed_mechanisms", "preregistration", "evaluation_bindings",
    "quality_metrics", "cost_metrics", "failure_deltas", "authority_scopes",
    "rollback", "next_round_rnd_gain",
}
FINDING_ORDER = (
    "EVALUATION_ANCHOR_CHANGED",
    "PREDECESSOR_ANCHOR_REPLAY_MISSING",
    "PREDECESSOR_ANCHOR_REPLAY_BINDING_MISMATCH",
    "QUALITY_REGRESSION",
    "QUALITY_GAIN_NOT_POSITIVE",
    "COST_GUARDRAIL_EXCEEDED",
    "FAILURE_GUARDRAIL_EXCEEDED",
    "AUTHORITY_SCOPE_ADDED",
    "ROLLBACK_TARGET_MISMATCH",
    "ROLLBACK_NOT_VERIFIED",
    "NEXT_ROUND_GAIN_NOT_MEASURED",
    "NEXT_ROUND_GAIN_NOT_POSITIVE",
)


class InputError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise InputError("DUPLICATE_JSON_KEY")
        value[key] = item
    return value


def _reject_constant(_: str) -> None:
    raise InputError("NONFINITE_JSON_NUMBER")


def _require_object(value: Any, required: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(code)
    if set(value) != required:
        raise InputError(code)
    return value


def _text(value: Any, code: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise InputError(code)
    return value


def _digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or HEX_64.fullmatch(value) is None:
        raise InputError(code)
    return value


def _number(value: Any, code: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(code)
    try:
        result = float(value)
    except OverflowError as exc:
        raise InputError(code) from exc
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        raise InputError(code)
    return result


def _items(value: Any, code: str, *, minimum: int = 1) -> list[Any]:
    if not isinstance(value, list) or not minimum <= len(value) <= MAX_LIST_ITEMS:
        raise InputError(code)
    return value


def _string_set(value: Any, code: str) -> list[str]:
    rows = _items(value, code, minimum=0)
    result = [_text(item, code) for item in rows]
    if len(set(result)) != len(result):
        raise InputError(code)
    return result


def _direction(value: Any) -> str:
    if not isinstance(value, str) or value not in {"HIGHER_IS_BETTER", "LOWER_IS_BETTER"}:
        raise InputError("METRIC_DIRECTION_INVALID")
    return value


def _system(value: Any, code: str) -> dict[str, str]:
    row = _require_object(value, {"system_ref", "system_sha256"}, code)
    return {
        "system_ref": _text(row["system_ref"], code),
        "system_sha256": _digest(row["system_sha256"], code),
    }


def _metric_rows(value: Any, code: str, *, quality: bool) -> list[dict[str, Any]]:
    rows = _items(value, code)
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        if quality:
            required = {"metric_id", "unit", "direction", "predecessor_value", "successor_value"}
        else:
            required = {"metric_id", "unit", "predecessor_value", "successor_value", "max_allowed_increase"}
        row = _require_object(raw, required, code)
        metric_id = _text(row["metric_id"], code, maximum=128)
        if metric_id in seen:
            raise InputError("DUPLICATE_METRIC_ID")
        seen.add(metric_id)
        item: dict[str, Any] = {
            "metric_id": metric_id,
            "unit": _text(row["unit"], code, maximum=128),
            "predecessor_value": _number(row["predecessor_value"], code),
            "successor_value": _number(row["successor_value"], code),
        }
        if quality:
            item["direction"] = _direction(row["direction"])
        else:
            item["max_allowed_increase"] = _number(row["max_allowed_increase"], code, minimum=0)
        result.append(item)
    return result


def _failure_rows(value: Any) -> list[dict[str, Any]]:
    rows = _items(value, "FAILURE_DELTAS_INVALID")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        row = _require_object(
            raw,
            {"failure_class", "predecessor_count", "successor_count", "max_allowed_increase"},
            "FAILURE_DELTAS_INVALID",
        )
        name = _text(row["failure_class"], "FAILURE_DELTAS_INVALID", maximum=128)
        if name in seen:
            raise InputError("DUPLICATE_FAILURE_CLASS")
        seen.add(name)
        counts = []
        for key in ("predecessor_count", "successor_count", "max_allowed_increase"):
            value_int = row[key]
            if type(value_int) is not int or value_int < 0:
                raise InputError("FAILURE_DELTAS_INVALID")
            counts.append(value_int)
        result.append({
            "failure_class": name,
            "predecessor_count": counts[0],
            "successor_count": counts[1],
            "max_allowed_increase": counts[2],
        })
    return result


def _evaluate_binding(value: Any, code: str) -> dict[str, str]:
    row = _require_object(value, {"evaluator_sha256", "benchmark_sha256", "heldout_sha256"}, code)
    return {key: _digest(row[key], code) for key in ("evaluator_sha256", "benchmark_sha256", "heldout_sha256")}


def _replay(
    value: Any,
    quality: list[dict[str, Any]],
    predecessor_binding: dict[str, str],
) -> tuple[str, dict[str, str] | None, bool | None, list[dict[str, Any]]]:
    row = _require_object(
        value,
        {"status", "evaluation_binding", "metrics"},
        "PREDECESSOR_ANCHOR_REPLAY_INVALID",
    )
    status = row["status"]
    if not isinstance(status, str) or status not in {"MEASURED", "NOT_RUN"}:
        raise InputError("PREDECESSOR_ANCHOR_REPLAY_INVALID")
    metrics = _items(row["metrics"], "PREDECESSOR_ANCHOR_REPLAY_INVALID", minimum=0)
    if status == "NOT_RUN":
        if row["evaluation_binding"] is not None or metrics:
            raise InputError("PREDECESSOR_ANCHOR_REPLAY_INVALID")
        return status, None, None, []
    evaluation_binding = _evaluate_binding(row["evaluation_binding"], "PREDECESSOR_ANCHOR_REPLAY_INVALID")
    binding_matches_predecessor = evaluation_binding == predecessor_binding
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in metrics:
        item = _require_object(
            raw, {"metric_id", "unit", "direction", "value"},
            "PREDECESSOR_ANCHOR_REPLAY_INVALID",
        )
        metric_id = _text(item["metric_id"], "PREDECESSOR_ANCHOR_REPLAY_INVALID", maximum=128)
        if metric_id in seen:
            raise InputError("DUPLICATE_REPLAY_METRIC_ID")
        seen.add(metric_id)
        result.append({
            "metric_id": metric_id,
            "unit": _text(item["unit"], "PREDECESSOR_ANCHOR_REPLAY_INVALID", maximum=128),
            "direction": _direction(item["direction"]),
            "value": _number(item["value"], "PREDECESSOR_ANCHOR_REPLAY_INVALID"),
        })
    if status == "MEASURED":
        expected = {item["metric_id"]: (item["unit"], item["direction"]) for item in quality}
        observed = {item["metric_id"]: (item["unit"], item["direction"]) for item in result}
        if observed != expected:
            raise InputError("PREDECESSOR_ANCHOR_REPLAY_METRICS_MISMATCH")
    return status, evaluation_binding, binding_matches_predecessor, result


def _next_round(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or "status" not in value:
        raise InputError("NEXT_ROUND_GAIN_INVALID")
    status = value["status"]
    if status == "NOT_MEASURED":
        row = _require_object(value, {"status", "metric"}, "NEXT_ROUND_GAIN_INVALID")
        if row["metric"] is not None:
            raise InputError("NEXT_ROUND_GAIN_INVALID")
        return {"status": status, "metric": None}
    if status == "MEASURED":
        row = _require_object(value, {"status", "metric"}, "NEXT_ROUND_GAIN_INVALID")
        metric = _require_object(
            row["metric"],
            {"metric_id", "unit", "direction", "predecessor_value", "successor_value", "evaluator_sha256", "benchmark_sha256"},
            "NEXT_ROUND_GAIN_INVALID",
        )
        return {
            "status": status,
            "metric": {
                "metric_id": _text(metric["metric_id"], "NEXT_ROUND_GAIN_INVALID", maximum=128),
                "unit": _text(metric["unit"], "NEXT_ROUND_GAIN_INVALID", maximum=128),
                "direction": _direction(metric["direction"]),
                "predecessor_value": _number(metric["predecessor_value"], "NEXT_ROUND_GAIN_INVALID"),
                "successor_value": _number(metric["successor_value"], "NEXT_ROUND_GAIN_INVALID"),
                "evaluator_sha256": _digest(metric["evaluator_sha256"], "NEXT_ROUND_GAIN_INVALID"),
                "benchmark_sha256": _digest(metric["benchmark_sha256"], "NEXT_ROUND_GAIN_INVALID"),
            },
        }
    raise InputError("NEXT_ROUND_GAIN_INVALID")


def _directional_delta(before: float, after: float, direction: str) -> float:
    delta = after - before
    if not math.isfinite(delta):
        raise InputError("ARITHMETIC_OVERFLOW")
    return delta if direction == "HIGHER_IS_BETTER" else -delta


def analyze_bytes(raw: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) > MAX_INPUT_BYTES:
        return _invalid(digest, "INPUT_LIMIT_EXCEEDED")
    try:
        text = raw.decode("utf-8", errors="strict")
        request = json.loads(text, object_pairs_hook=_object_pairs, parse_constant=_reject_constant)
        normalized = _validate(request)
        return _report(normalized, digest)
    except InputError as exc:
        return _invalid(digest, exc.code)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        return _invalid(digest, "JSON_INVALID")


def _validate(value: Any) -> dict[str, Any]:
    row = _require_object(value, INPUT_KEYS, "TOP_LEVEL_FIELDS_INVALID")
    if row["schema_version"] != "governed-improvement-transition-r0":
        raise InputError("SCHEMA_VERSION_UNSUPPORTED")
    transition_id = _text(row["transition_id"], "TRANSITION_ID_INVALID", maximum=128)
    predecessor = _system(row["predecessor"], "PREDECESSOR_INVALID")
    successor = _system(row["successor_candidate"], "SUCCESSOR_INVALID")
    if predecessor == successor:
        raise InputError("PREDECESSOR_SUCCESSOR_IDENTICAL")
    changes = _string_set(row["changed_mechanisms"], "CHANGED_MECHANISMS_INVALID")
    if not changes:
        raise InputError("CHANGED_MECHANISMS_INVALID")
    prereg = _require_object(row["preregistration"], {"ref", "sha256"}, "PREREGISTRATION_INVALID")
    preregistration = {"ref": _text(prereg["ref"], "PREREGISTRATION_INVALID"), "sha256": _digest(prereg["sha256"], "PREREGISTRATION_INVALID")}

    bindings = _require_object(row["evaluation_bindings"], {"predecessor", "successor", "successor_on_predecessor_anchor"}, "EVALUATION_BINDINGS_INVALID")
    predecessor_binding = _evaluate_binding(bindings["predecessor"], "EVALUATION_BINDINGS_INVALID")
    successor_binding = _evaluate_binding(bindings["successor"], "EVALUATION_BINDINGS_INVALID")
    quality = _metric_rows(row["quality_metrics"], "QUALITY_METRICS_INVALID", quality=True)
    replay_status, replay_binding, replay_binding_matches, replay_metrics = _replay(
        bindings["successor_on_predecessor_anchor"], quality, predecessor_binding,
    )
    cost = _metric_rows(row["cost_metrics"], "COST_METRICS_INVALID", quality=False)
    failures = _failure_rows(row["failure_deltas"])
    authority = _require_object(row["authority_scopes"], {"predecessor", "successor"}, "AUTHORITY_SCOPES_INVALID")
    authority_before = _string_set(authority["predecessor"], "AUTHORITY_SCOPES_INVALID")
    authority_after = _string_set(authority["successor"], "AUTHORITY_SCOPES_INVALID")
    rollback = _require_object(row["rollback"], {"target_system_ref", "target_system_sha256", "exercise_status"}, "ROLLBACK_INVALID")
    rollback_value = {
        "target_system_ref": _text(rollback["target_system_ref"], "ROLLBACK_INVALID"),
        "target_system_sha256": _digest(rollback["target_system_sha256"], "ROLLBACK_INVALID"),
        "exercise_status": rollback["exercise_status"],
    }
    if not isinstance(rollback_value["exercise_status"], str) or rollback_value["exercise_status"] not in {"PASS", "FAIL", "NOT_RUN"}:
        raise InputError("ROLLBACK_INVALID")
    next_gain = _next_round(row["next_round_rnd_gain"])
    return {
        "transition_id": transition_id,
        "predecessor": predecessor,
        "successor_candidate": successor,
        "changed_mechanisms": changes,
        "preregistration": preregistration,
        "evaluation_bindings": {
            "predecessor": predecessor_binding,
            "successor": successor_binding,
            "successor_on_predecessor_anchor": {
                "status": replay_status,
                "evaluation_binding": replay_binding,
                "binding_matches_predecessor": replay_binding_matches,
                "metrics": replay_metrics,
            },
        },
        "quality_metrics": quality,
        "cost_metrics": cost,
        "failure_deltas": failures,
        "authority_scopes": {"predecessor": authority_before, "successor": authority_after},
        "rollback": rollback_value,
        "next_round_rnd_gain": next_gain,
    }


def _report(data: dict[str, Any], input_sha256: str) -> dict[str, Any]:
    before_binding = data["evaluation_bindings"]["predecessor"]
    after_binding = data["evaluation_bindings"]["successor"]
    changed = {
        "evaluator": before_binding["evaluator_sha256"] != after_binding["evaluator_sha256"],
        "benchmark": before_binding["benchmark_sha256"] != after_binding["benchmark_sha256"],
        "heldout": before_binding["heldout_sha256"] != after_binding["heldout_sha256"],
    }
    anchor_changed = any(changed.values())
    replay = data["evaluation_bindings"]["successor_on_predecessor_anchor"]
    replay_by_id = {item["metric_id"]: item for item in replay["metrics"]}
    findings: set[str] = set()
    if replay["status"] == "MEASURED" and replay["binding_matches_predecessor"] is False:
        findings.add("PREDECESSOR_ANCHOR_REPLAY_BINDING_MISMATCH")
    if anchor_changed:
        findings.add("EVALUATION_ANCHOR_CHANGED")
        if replay["status"] != "MEASURED":
            findings.add("PREDECESSOR_ANCHOR_REPLAY_MISSING")

    quality_deltas = []
    quality_gain_values: list[float] = []
    for metric in data["quality_metrics"]:
        primary_delta = _directional_delta(metric["predecessor_value"], metric["successor_value"], metric["direction"])
        replay_row = replay_by_id.get(metric["metric_id"])
        replay_is_comparable = replay["binding_matches_predecessor"] is True
        comparable_value = replay_row["value"] if anchor_changed and replay_is_comparable and replay_row is not None else metric["successor_value"] if not anchor_changed else None
        comparable_delta = None if comparable_value is None else _directional_delta(metric["predecessor_value"], comparable_value, metric["direction"])
        basis = "SUCCESSOR_REPLAYED_ON_PREDECESSOR_ANCHOR" if anchor_changed and replay_is_comparable and replay_row is not None else "SAME_DECLARED_EVALUATION_ANCHOR" if not anchor_changed else "NOT_COMPARABLE"
        if comparable_delta is not None:
            quality_gain_values.append(comparable_delta)
            if comparable_delta < 0:
                findings.add("QUALITY_REGRESSION")
        quality_deltas.append({
            "metric_id": metric["metric_id"],
            "unit": metric["unit"],
            "direction": metric["direction"],
            "primary_directional_delta": primary_delta,
            "comparable_directional_delta": comparable_delta,
            "comparison_basis": basis,
        })
    if quality_gain_values and not any(value > 0 for value in quality_gain_values):
        findings.add("QUALITY_GAIN_NOT_POSITIVE")

    cost_deltas = []
    for metric in data["cost_metrics"]:
        delta = metric["successor_value"] - metric["predecessor_value"]
        if not math.isfinite(delta):
            raise InputError("ARITHMETIC_OVERFLOW")
        within = delta <= metric["max_allowed_increase"]
        if not within:
            findings.add("COST_GUARDRAIL_EXCEEDED")
        cost_deltas.append({
            "metric_id": metric["metric_id"],
            "unit": metric["unit"],
            "delta": delta,
            "max_allowed_increase": metric["max_allowed_increase"],
            "within_declared_guardrail": within,
        })

    failure_deltas = []
    for metric in data["failure_deltas"]:
        delta = metric["successor_count"] - metric["predecessor_count"]
        within = delta <= metric["max_allowed_increase"]
        if not within:
            findings.add("FAILURE_GUARDRAIL_EXCEEDED")
        failure_deltas.append({
            "failure_class": metric["failure_class"],
            "delta": delta,
            "max_allowed_increase": metric["max_allowed_increase"],
            "within_declared_guardrail": within,
        })

    before_scopes = set(data["authority_scopes"]["predecessor"])
    after_scopes = set(data["authority_scopes"]["successor"])
    added_scopes = sorted(after_scopes - before_scopes)
    removed_scopes = sorted(before_scopes - after_scopes)
    if added_scopes:
        findings.add("AUTHORITY_SCOPE_ADDED")

    rollback = data["rollback"]
    rollback_matches = (
        rollback["target_system_ref"] == data["predecessor"]["system_ref"]
        and rollback["target_system_sha256"] == data["predecessor"]["system_sha256"]
    )
    if not rollback_matches:
        findings.add("ROLLBACK_TARGET_MISMATCH")
    if rollback["exercise_status"] != "PASS":
        findings.add("ROLLBACK_NOT_VERIFIED")

    gain = data["next_round_rnd_gain"]
    gain_report: dict[str, Any]
    if gain["status"] == "NOT_MEASURED":
        findings.add("NEXT_ROUND_GAIN_NOT_MEASURED")
        gain_report = {"status": "NOT_MEASURED", "directional_delta": None, "positive": None}
    else:
        metric = gain["metric"]
        delta = _directional_delta(metric["predecessor_value"], metric["successor_value"], metric["direction"])
        positive = delta > 0
        if not positive:
            findings.add("NEXT_ROUND_GAIN_NOT_POSITIVE")
        gain_report = {
            "status": "MEASURED",
            "metric_id": metric["metric_id"],
            "unit": metric["unit"],
            "directional_delta": delta,
            "positive": positive,
            "evaluation_binding_sha256": {
                "evaluator": metric["evaluator_sha256"],
                "benchmark": metric["benchmark_sha256"],
            },
        }

    ordered_findings = [code for code in FINDING_ORDER if code in findings]
    return {
        "schema_version": "governed-improvement-transition-result-r0",
        "status": "REVIEW_REQUIRED",
        "transition_id": data["transition_id"],
        "input_sha256": input_sha256,
        "evaluation_anchor": {
            "same_evaluator": not changed["evaluator"],
            "same_benchmark": not changed["benchmark"],
            "same_heldout_set": not changed["heldout"],
            "successor_replay_on_predecessor_anchor": replay["status"],
            "successor_replay_binding_matches_predecessor": replay["binding_matches_predecessor"],
        },
        "quality_deltas": quality_deltas,
        "cost_deltas": cost_deltas,
        "failure_deltas": failure_deltas,
        "authority_delta": {"added_scopes": added_scopes, "removed_scopes": removed_scopes},
        "rollback": {"target_matches_predecessor": rollback_matches, "exercise_status": rollback["exercise_status"]},
        "next_round_rnd_gain": gain_report,
        "finding_codes": ordered_findings,
        "source_authenticity": "NOT_VERIFIED",
        "measurement_authenticity": "NOT_VERIFIED",
        "improvement_accepted": False,
        "successor_promoted": False,
        "execution_authorized": False,
        "claim_ceiling": "Deterministic structure and arithmetic over caller-declared transition data only; no source, evaluator, benchmark, measurement, rollback, improvement, generalization, authority, or successor state is authenticated.",
    }


def _invalid(input_sha256: str, code: str) -> dict[str, Any]:
    return {
        "schema_version": "governed-improvement-transition-result-r0",
        "status": "INPUT_INVALID",
        "input_sha256": input_sha256,
        "finding_codes": [code],
        "improvement_accepted": False,
        "successor_promoted": False,
        "execution_authorized": False,
        "claim_ceiling": "Input validation only; no source, evaluator, benchmark, measurement, rollback, improvement, generalization, authority, or successor state is authenticated.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded UTF-8 JSON transition from stdin")
    args = parser.parse_args(argv)
    if not args.stdin:
        parser.error("--stdin is required")
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    report = analyze_bytes(raw)
    sys.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0 if report["status"] == "REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
