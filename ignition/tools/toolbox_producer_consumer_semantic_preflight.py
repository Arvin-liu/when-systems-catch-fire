#!/usr/bin/env python3
"""Statically compare bounded producer text with constant consumer regex checks.

The consumer source is parsed with ``ast`` and is never imported, compiled, or
executed. Only direct ``re.search(constant_pattern, text_name)`` calls assigned
to names and jointly guarded by a simple fail-closed ``if not a or not b:
raise`` are supported. This is a narrow static preflight, not a proof that an
arbitrary consumer accepts or interprets the producer's semantics correctly.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-producer-consumer-semantic-input-r0.schema.json"
TOOL_ID = "maintenance.preflight_producer_consumer_semantics"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "producer-consumer-semantic-preflight-input-r0"
OUTPUT_SCHEMA_VERSION = "producer-consumer-semantic-preflight-output-r0"
MAX_INPUT_BYTES = 262_144
MAX_CONSUMER_SOURCE_BYTES = 131_072
MAX_PRODUCER_TEXT_BYTES = 65_536
MAX_PATTERN_LENGTH = 512
MAX_PATTERN_CHECKS = 16
MAX_PATTERN_GROUPS = 32
MAX_FINDINGS = 16
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FIELD_KEY_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(?:`)?\(")


class DuplicateJSONKey(ValueError):
    """Raised when a JSON object repeats a key."""


class InputError(ValueError):
    """Raised for malformed or out-of-contract input."""


class NotEvaluable(ValueError):
    """Raised when the supplied parser is outside the conservative subset."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _text_sha256(value: str) -> str:
    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputError("text contains an invalid Unicode surrogate") from exc
    return _sha256(raw)


def _pointer(path: Any) -> str:
    parts = [str(item).replace("~", "~0").replace("/", "~1") for item in path]
    return "$" + ("/" + "/".join(parts) if parts else "")


def _validate_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        problems = sorted(
            Draft202012Validator(schema).iter_errors(payload),
            key=lambda item: (_pointer(item.absolute_path), item.validator or ""),
        )
    except OSError as exc:
        raise InputError("input schema is unavailable") from exc
    except json.JSONDecodeError as exc:
        raise InputError("input schema is invalid JSON") from exc
    if problems:
        detail = "; ".join(
            f"{_pointer(problem.absolute_path)}:{problem.validator or 'invalid'}"
            for problem in problems[:MAX_FINDINGS]
        )
        raise InputError("input schema validation failed: " + detail)

    consumer = payload["consumer_source"]
    producer = payload["producer_text"]
    try:
        source_size = len(consumer["python_source"].encode("utf-8"))
        producer_size = len(producer["text"].encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise InputError("text contains an invalid Unicode surrogate") from exc
    if source_size > MAX_CONSUMER_SOURCE_BYTES:
        raise InputError("consumer source exceeds the byte limit")
    if producer_size > MAX_PRODUCER_TEXT_BYTES:
        raise InputError("producer text exceeds the byte limit")


def _assigned_name(node: ast.AST, parent_by_node: dict[ast.AST, ast.AST]) -> str | None:
    parent = parent_by_node.get(node)
    if isinstance(parent, ast.Assign) and parent.value is node and len(parent.targets) == 1:
        target = parent.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(parent, ast.AnnAssign) and parent.value is node and isinstance(parent.target, ast.Name):
        return parent.target.id
    return None


def _is_utf8_decode(value: ast.AST) -> str | None:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Attribute):
        return None
    if value.func.attr != "decode" or not isinstance(value.func.value, ast.Name):
        return None
    if len(value.args) > 1 or value.keywords:
        return None
    if value.args and not (
        isinstance(value.args[0], ast.Constant)
        and isinstance(value.args[0].value, str)
        and value.args[0].value.lower().replace("_", "-") == "utf-8"
    ):
        return None
    return value.func.value.id


def _module_and_function_constants(module: ast.Module, function: ast.FunctionDef) -> dict[str, str]:
    constants: dict[str, str] = {}
    for statement in module.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                constants[statement.targets[0].id] = statement.value.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                constants[statement.target.id] = statement.value.value
    for statement in function.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                constants[statement.targets[0].id] = statement.value.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                constants[statement.target.id] = statement.value.value
    return constants


def _import_aliases(module: ast.Module, function: ast.FunctionDef) -> tuple[set[str], set[str]]:
    re_modules: set[str] = set()
    search_names: set[str] = set()
    for statement in [*module.body, *function.body]:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "re":
                    re_modules.add(alias.asname or "re")
        elif isinstance(statement, ast.ImportFrom) and statement.module == "re":
            for alias in statement.names:
                if alias.name == "search":
                    search_names.add(alias.asname or alias.name)
    return re_modules, search_names


def _regex_call_kind(node: ast.Call, re_modules: set[str], search_names: set[str]) -> str | None:
    if isinstance(node.func, ast.Attribute) and node.func.attr == "search":
        if isinstance(node.func.value, ast.Name) and node.func.value.id in re_modules:
            return "re.search"
    if isinstance(node.func, ast.Name) and node.func.id in search_names:
        return "search"
    return None


def _guarded_match_names(node: ast.AST) -> set[str] | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not) and isinstance(node.operand, ast.Name):
        return {node.operand.id}
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        names: set[str] = set()
        for value in node.values:
            found = _guarded_match_names(value)
            if found is None or names.intersection(found):
                return None
            names.update(found)
        return names
    return None


def _safe_regex_subset(pattern: str) -> None:
    if not pattern or len(pattern) > MAX_PATTERN_LENGTH:
        raise NotEvaluable("REGEX_PATTERN_LENGTH_UNSUPPORTED")
    if pattern.startswith("(?m)"):
        body = pattern[4:]
    else:
        body = pattern
    if "(?" in body or re.search(r"\\[1-9]", body):
        raise NotEvaluable("REGEX_GROUP_EXTENSION_OR_BACKREFERENCE_UNSUPPORTED")

    in_class = False
    escaped = False
    plus_count = 0
    index = 0
    while index < len(body):
        char = body[index]
        if escaped:
            if char not in "dDsSwWtnr\\.^$|()[]+-":
                raise NotEvaluable("REGEX_ESCAPE_UNSUPPORTED")
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if in_class:
            if char == "]":
                in_class = False
            index += 1
            continue
        if char == "[":
            in_class = True
        elif char in "*?{}.":
            raise NotEvaluable("REGEX_QUANTIFIER_OR_WILDCARD_UNSUPPORTED")
        elif char == "+":
            plus_count += 1
            previous_is_class = index > 0 and body[index - 1] == "]"
            previous_is_short_class = index > 1 and body[index - 2:index] in {r"\d", r"\D", r"\s", r"\S", r"\w", r"\W"}
            if not (previous_is_class or previous_is_short_class):
                raise NotEvaluable("REGEX_REPEAT_MUST_FOLLOW_A_CHARACTER_CLASS")
            if index + 1 < len(body) and body[index + 1] in "+*?{":
                raise NotEvaluable("REGEX_NESTED_OR_ADJACENT_REPEAT_UNSUPPORTED")
        elif char == ")" and index + 1 < len(body) and body[index + 1] in "+*?{":
            raise NotEvaluable("REGEX_REPEATED_GROUP_UNSUPPORTED")
        index += 1
    if escaped or in_class:
        raise NotEvaluable("REGEX_UNCLOSED_ESCAPE_OR_CHARACTER_CLASS")
    if plus_count > MAX_PATTERN_GROUPS:
        raise NotEvaluable("REGEX_REPEAT_COUNT_LIMIT_EXCEEDED")
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise NotEvaluable("REGEX_SYNTAX_INVALID") from exc
    if compiled.groups > MAX_PATTERN_GROUPS:
        raise NotEvaluable("REGEX_CAPTURE_GROUP_LIMIT_EXCEEDED")


def _capture_labels(pattern: str, group_count: int) -> list[str]:
    labels = [match.group(1) for match in FIELD_KEY_RE.finditer(pattern)]
    if len(labels) != group_count:
        return [f"capture_{index}" for index in range(1, group_count + 1)]
    return labels


def _extract_contract(module_source: str, function_name: str) -> list[dict[str, Any]]:
    try:
        module = ast.parse(module_source)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise NotEvaluable("CONSUMER_SOURCE_AST_PARSE_FAILED") from exc
    functions = [
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    ]
    if len(functions) != 1:
        raise NotEvaluable("CONSUMER_FUNCTION_MISSING_OR_AMBIGUOUS")
    function = functions[0]
    body_nodes = [node for statement in function.body for node in ast.walk(statement)]
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)) for node in body_nodes):
        raise NotEvaluable("NESTED_CONSUMER_CODE_UNSUPPORTED")

    positional = [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]
    string_names = {
        argument.arg for argument in positional
        if isinstance(argument.annotation, ast.Name) and argument.annotation.id == "str"
    }
    byte_names = {argument.arg for argument in positional} - string_names
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(function):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    if any(
        isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in string_names
        for node in body_nodes
    ):
        raise NotEvaluable("CONSUMER_TEXT_ARGUMENT_REASSIGNED")

    decode_aliases: dict[str, str] = {}
    assignment_counts: dict[str, int] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            assignment_counts[name] = assignment_counts.get(name, 0) + 1
            source_name = _is_utf8_decode(node.value)
            if source_name in byte_names and parents.get(node) is function:
                decode_aliases[name] = source_name
    string_names.update(name for name in decode_aliases if assignment_counts.get(name) == 1)

    local_constants = _module_and_function_constants(module, function)
    re_modules, search_names = _import_aliases(module, function)
    if any(
        isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in re_modules
        for node in body_nodes
    ):
        raise NotEvaluable("CONSUMER_REGEX_MODULE_SHADOWED")
    calls: list[dict[str, Any]] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        kind = _regex_call_kind(node, re_modules, search_names)
        if kind is None:
            continue
        if kind != "re.search" or len(node.args) != 2 or node.keywords:
            raise NotEvaluable("CONSUMER_REGEX_CALL_SHAPE_UNSUPPORTED")
        target_name = _assigned_name(node, parents)
        if target_name is None:
            raise NotEvaluable("CONSUMER_REGEX_RESULT_NOT_ASSIGNED_TO_NAME")
        assignment = parents.get(node)
        if parents.get(assignment) is not function:
            raise NotEvaluable("CONSUMER_REGEX_CHECK_NOT_TOP_LEVEL")
        pattern_node, text_node = node.args
        if isinstance(pattern_node, ast.Constant) and isinstance(pattern_node.value, str):
            pattern = pattern_node.value
        elif isinstance(pattern_node, ast.Name) and pattern_node.id in local_constants:
            pattern = local_constants[pattern_node.id]
        else:
            raise NotEvaluable("CONSUMER_REGEX_PATTERN_NOT_CONSTANT")
        if not isinstance(text_node, ast.Name) or text_node.id not in string_names:
            raise NotEvaluable("CONSUMER_REGEX_TEXT_SOURCE_UNSUPPORTED")
        _safe_regex_subset(pattern)
        compiled = re.compile(pattern)
        calls.append({
            "consumer_variable": target_name,
            "source_line": node.lineno,
            "pattern": pattern,
            "pattern_sha256": _text_sha256(pattern),
            "capture_labels": _capture_labels(pattern, compiled.groups),
            "capture_count": compiled.groups,
        })

    calls.sort(key=lambda row: row["source_line"])

    if not calls or len(calls) > MAX_PATTERN_CHECKS:
        raise NotEvaluable("CONSUMER_REQUIRED_PATTERN_COUNT_OUT_OF_RANGE")
    variables = [row["consumer_variable"] for row in calls]
    if len(variables) != len(set(variables)):
        raise NotEvaluable("CONSUMER_REGEX_RESULT_VARIABLE_REUSED")

    call_lines = [row["source_line"] for row in calls]
    guards: list[tuple[int, set[str]]] = []
    for node in function.body:
        if not isinstance(node, ast.If):
            continue
        names = _guarded_match_names(node.test)
        if names is not None and not node.orelse and any(isinstance(statement, ast.Raise) for statement in node.body):
            guards.append((node.lineno, names))
    required = set(variables)
    if not any(line > max(call_lines) and names == required for line, names in guards):
        raise NotEvaluable("CONSUMER_CHECKS_NOT_JOINTLY_FAIL_CLOSED")
    return calls


def _literal_prefix(pattern: str) -> str:
    body = pattern[4:] if pattern.startswith("(?m)") else pattern
    prefix: list[str] = []
    index = 0
    while index < len(body):
        char = body[index]
        if char == "\\" and index + 1 < len(body):
            escaped = body[index + 1]
            if escaped in "dDsSwWbBAZ":
                break
            prefix.append(escaped)
            index += 2
            continue
        if char in ".^$*+?{[()|":
            break
        prefix.append(char)
        index += 1
    return "".join(prefix)


def _line_sha256_at(text: str, position: int) -> str:
    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    if end < 0:
        end = len(text)
    return _text_sha256(text[start:end].rstrip("\r"))


def _record_marker_prefix(pattern: str) -> str:
    body = pattern[4:] if pattern.startswith("(?m)") else pattern
    field = FIELD_KEY_RE.search(body)
    if field is None:
        return _literal_prefix(pattern)
    return _literal_prefix(body[:field.start(1)])


def _field_occurrences(text: str, field_id: str) -> list[int]:
    token = re.escape(field_id) + "="
    positions: list[int] = []
    for match in re.finditer(token, text):
        start = match.start()
        if start == 0 or not (text[start - 1].isalnum() or text[start - 1] == "_"):
            positions.append(start)
    return positions


def _field_rows(pattern: str, labels: list[str], matches: list[re.Match[str]], producer: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    marker = _record_marker_prefix(pattern).casefold()
    casefolded = "\n".join(
        line for line in producer.splitlines()
        if not marker or marker in line.casefold()
    ).casefold()
    for index, label in enumerate(labels, start=1):
        positions = []
        for position in _field_occurrences(producer, label):
            start = producer.rfind("\n", 0, position) + 1
            end = producer.find("\n", position)
            if end < 0:
                end = len(producer)
            if not marker or marker in producer[start:end].casefold():
                positions.append(position)
        hashes = [_line_sha256_at(producer, position) for position in positions]
        row: dict[str, Any] = {"field_id": label, "occurrence_count": len(positions)}
        if len(positions) == 0:
            if f"{label}=".casefold() in casefolded:
                row["status"] = "CASE_VARIANT"
            elif matches:
                row["status"] = "PRESENT"
            else:
                row["status"] = "ABSENT"
        elif len(positions) > 1:
            row["status"] = "AMBIGUOUS" if len(set(hashes)) == 1 else "CONTRADICTORY"
            row["occurrence_line_sha256"] = hashes
        elif matches and index <= len(matches[0].groups()):
            captured = matches[0].group(index)
            row["status"] = "PRESENT"
            row["value_sha256"] = _text_sha256(captured) if captured is not None else None
        else:
            row["status"] = "PRESENT_UNVALIDATED"
            row["occurrence_line_sha256"] = hashes
        rows.append(row)
    return rows


def _evaluate_check(contract: dict[str, Any], producer: str) -> dict[str, Any]:
    pattern = contract["pattern"]
    compiled = re.compile(pattern)
    matches = list(compiled.finditer(producer))
    labels = contract["capture_labels"]
    prefix = _record_marker_prefix(pattern)
    exact_prefix = bool(prefix and prefix in producer)
    case_variant_prefix = bool(prefix and prefix.casefold() in producer.casefold() and not exact_prefix)

    if len(matches) == 1:
        status = "PRESENT"
    elif len(matches) > 1:
        capture_tuples = [match.groups() for match in matches]
        status = "AMBIGUOUS" if all(row == capture_tuples[0] for row in capture_tuples[1:]) else "CONTRADICTORY"
    elif exact_prefix:
        status = "MALFORMED_OR_REORDERED"
    elif case_variant_prefix:
        status = "CASE_VARIANT"
    else:
        status = "ABSENT"

    return {
        "consumer_variable": contract["consumer_variable"],
        "method": "re.search",
        "source_line": contract["source_line"],
        "pattern_sha256": contract["pattern_sha256"],
        "status": status,
        "match_count": len(matches),
        "capture_fields": _field_rows(pattern, labels, matches, producer),
    }


def _result_base(input_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "input_sha256": input_sha256,
        "source_bindings": {
            "consumer_source": {"expected_sha256": None, "observed_sha256": None, "status": "NOT_CHECKED"},
            "producer_text": {"expected_sha256": None, "observed_sha256": None, "status": "NOT_CHECKED"},
        },
        "analysis_status": "NOT_RUN",
        "contract_status": "NOT_EVALUABLE",
        "checks": [],
        "unsupported_reasons": [],
        "claim_flags": {
            "consumer_code_executed": False,
            "source_provenance_authenticated": False,
            "consumer_acceptance_proven": False,
            "semantic_equivalence_proven": False,
            "external_truth_verified": False,
            "execution_authorized": False,
        },
    }


def evaluate(payload: Any, *, input_sha256: str | None = None) -> dict[str, Any]:
    _validate_payload(payload)
    consumer = payload["consumer_source"]
    producer = payload["producer_text"]
    observed_consumer = _text_sha256(consumer["python_source"])
    observed_producer = _text_sha256(producer["text"])
    result = _result_base(input_sha256 or _text_sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))))
    result["source_bindings"]["consumer_source"] = {
        "expected_sha256": consumer["expected_sha256"],
        "observed_sha256": observed_consumer,
        "status": "MATCH" if observed_consumer == consumer["expected_sha256"] else "MISMATCH",
    }
    result["source_bindings"]["producer_text"] = {
        "expected_sha256": producer["expected_sha256"],
        "observed_sha256": observed_producer,
        "status": "MATCH" if observed_producer == producer["expected_sha256"] else "MISMATCH",
    }
    if observed_consumer != consumer["expected_sha256"] or observed_producer != producer["expected_sha256"]:
        result["contract_status"] = "SOURCE_BINDING_MISMATCH"
        result["unsupported_reasons"] = ["CALLER_SUPPLIED_EXPECTED_DIGEST_MISMATCH"]
        return result

    try:
        contract = _extract_contract(consumer["python_source"], consumer["function_name"])
        result["checks"] = [_evaluate_check(row, producer["text"]) for row in contract]
    except NotEvaluable as exc:
        result["analysis_status"] = "NOT_EVALUABLE"
        result["contract_status"] = "NOT_EVALUABLE"
        result["unsupported_reasons"] = [str(exc)]
        return result

    result["analysis_status"] = "EVALUATED"
    result["contract_status"] = (
        "STATIC_REQUIRED_PATTERNS_MATCHED"
        if all(row["status"] == "PRESENT" for row in result["checks"])
        else "STATIC_REQUIRED_PATTERN_MISMATCH"
    )
    return result


def _error_result(code: str, input_sha256: str) -> dict[str, Any]:
    result = _result_base(input_sha256)
    result["analysis_status"] = "NOT_EVALUABLE"
    result["contract_status"] = "INPUT_INVALID"
    result["unsupported_reasons"] = [code]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True)
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    input_sha256 = _sha256(raw)
    if len(raw) > MAX_INPUT_BYTES:
        print(json.dumps(_error_result("INPUT_BYTE_LIMIT_EXCEEDED", input_sha256), sort_keys=True))
        return 2
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        result = evaluate(payload, input_sha256=input_sha256)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJSONKey, InputError, RecursionError) as exc:
        code = "DUPLICATE_JSON_KEY" if isinstance(exc, DuplicateJSONKey) else "INPUT_INVALID"
        print(json.dumps(_error_result(code, input_sha256), sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if result["contract_status"] == "STATIC_REQUIRED_PATTERNS_MATCHED":
        return 0
    if result["contract_status"] == "STATIC_REQUIRED_PATTERN_MISMATCH":
        return 1
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
