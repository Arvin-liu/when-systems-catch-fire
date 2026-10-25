#!/usr/bin/env python3
"""Run one bounded, pure symbolic FunctionSpec through Function OS N1-N7."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import operator
from pathlib import Path
import re
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
FUNCTION_OS_REL = "ignition/function-os-candidate/v0.2/function_os"
FUNCTION_OS_ROOT = REPO_ROOT / FUNCTION_OS_REL
sys.path.insert(0, str(FUNCTION_OS_ROOT.parent))

from function_os.n1_functionspec_parser import FunctionSpecParseError, N1FunctionSpecParser  # noqa: E402
from function_os.n1_semantic_checker import N1SemanticChecker  # noqa: E402
from function_os.n2_representation import N2RepresentationEncoder  # noqa: E402
from function_os.n3_compiler import N3SymbolicCompiler  # noqa: E402
from function_os.n4_artifact_packager import N4ArtifactPackager, N4ArtifactVerifier  # noqa: E402
from function_os.n5_interpreter import N5Interpreter  # noqa: E402
from function_os.n6_execution_trace import N6TraceCapture  # noqa: E402
from function_os.n7_validator import N7Validator  # noqa: E402


TOOL_SOURCE = "ignition/tools/toolbox_function_os_evaluator.py"
SCOPE_SOURCE = "ignition/function-os-candidate/v0.2/v0.2-scope-contract.json"
PROJECT_SOURCE = "ignition/function-os-candidate/v0.2/pyproject.toml"
MAX_REQUEST_BYTES = 16 * 1024
MAX_EXPRESSION_CHARS = 512
MAX_EXPRESSION_NODES = 64
MAX_EXPRESSION_DEPTH = 16
MAX_INPUTS = 16
MAX_INPUT_MAGNITUDE = 10**12
MAX_OUTPUT_MAGNITUDE = 10**100
MAX_COLLECTION_ITEMS = 16
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_TYPE_MAP = {
    "integer": int,
    "int": int,
    "float": float,
    "number": float,
    "boolean": bool,
    "bool": bool,
}
_ALLOWED_AST_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.Name,
    ast.Constant,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.And,
    ast.Or,
    ast.IfExp,
}
_BOUNDED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Not: operator.not_,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: lambda left, right: left and right,
    ast.Or: lambda left, right: left or right,
}


class FunctionOSRunError(ValueError):
    """Raised when a FunctionSpec is outside this CLI's bounded contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FunctionOSRunError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _safe_repo_path(relative_path: str, *, must_be_dir: bool = False) -> Path:
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        raise FunctionOSRunError("source paths must remain under ignition/")
    root = Path(REPO_ROOT)
    if root.is_symlink():
        raise FunctionOSRunError("repository root must not be a symlink")
    root = root.resolve()
    candidate = root
    for part in Path(relative_path).parts:
        if part in {".", ".."}:
            raise FunctionOSRunError("source path contains traversal")
        candidate = candidate / part
        if candidate.is_symlink():
            raise FunctionOSRunError("source path contains a symlink: " + relative_path)
    if must_be_dir and not candidate.is_dir():
        raise FunctionOSRunError("Function OS source directory is unavailable")
    if not must_be_dir and not candidate.is_file():
        raise FunctionOSRunError("Function OS source file is unavailable: " + relative_path)
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise FunctionOSRunError("source path escapes the repository: " + relative_path) from exc
    return candidate


def _tree_digest(relative_path: str) -> dict[str, Any]:
    root = Path(REPO_ROOT).resolve()
    directory = _safe_repo_path(relative_path, must_be_dir=True)
    entries = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise FunctionOSRunError("Function OS source tree contains a symlink")
        if path.is_file():
            entries.append({
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "path": relative_path,
        "hash_kind": "SHA256_FILE_TREE_R0",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "file_count": len(entries),
    }


def _source_refs() -> list[dict[str, Any]]:
    files = [TOOL_SOURCE, SCOPE_SOURCE, PROJECT_SOURCE]
    refs = [
        {"path": path, "sha256": hashlib.sha256(_safe_repo_path(path).read_bytes()).hexdigest()}
        for path in files
    ]
    refs.insert(1, _tree_digest(FUNCTION_OS_REL))
    return refs


def _bounded_expression(expression: Any, where: str) -> ast.Expression:
    if not isinstance(expression, str) or not expression.strip():
        raise FunctionOSRunError(where + " must be a nonblank expression")
    if len(expression) > MAX_EXPRESSION_CHARS:
        raise FunctionOSRunError(where + " exceeds the expression length limit")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError, ValueError) as exc:
        raise FunctionOSRunError(where + " is not a bounded expression") from exc
    stack: list[tuple[ast.AST, int]] = [(tree, 1)]
    node_count = 0
    while stack:
        node, depth = stack.pop()
        node_count += 1
        if node_count > MAX_EXPRESSION_NODES:
            raise FunctionOSRunError(where + " exceeds the expression node limit")
        if depth > MAX_EXPRESSION_DEPTH:
            raise FunctionOSRunError(where + " exceeds the expression depth limit")
        if type(node) not in _ALLOWED_AST_NODES:
            raise FunctionOSRunError(where + " uses an unsupported expression feature: " + type(node).__name__)
        if isinstance(node, ast.Name) and not _NAME_RE.fullmatch(node.id):
            raise FunctionOSRunError(where + " contains an invalid variable name")
        if isinstance(node, ast.Constant):
            value = node.value
            if type(value) not in {int, float, bool}:
                raise FunctionOSRunError(where + " accepts numeric and boolean literals only")
            if type(value) is int and abs(value) > MAX_INPUT_MAGNITUDE:
                raise FunctionOSRunError(where + " contains an oversized integer literal")
            if type(value) is float and (not math.isfinite(value) or abs(value) > MAX_INPUT_MAGNITUDE):
                raise FunctionOSRunError(where + " contains a non-finite or oversized float literal")
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    return tree


def _guard_bounded_value(value: Any, where: str) -> Any:
    if type(value) is bool:
        return value
    if type(value) is int and abs(value) <= MAX_OUTPUT_MAGNITUDE:
        return value
    if type(value) is float and math.isfinite(value) and abs(value) <= MAX_OUTPUT_MAGNITUDE:
        return value
    raise FunctionOSRunError(where + " produces a non-finite or oversized intermediate value")


def _preflight_node(node: ast.AST, context: dict[str, Any], where: str) -> Any:
    """Evaluate the whitelisted AST with an intermediate magnitude guard."""
    try:
        if isinstance(node, ast.Constant):
            return _guard_bounded_value(node.value, where)
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise FunctionOSRunError(where + " references an undeclared variable: " + node.id)
            return _guard_bounded_value(context[node.id], where)
        if isinstance(node, ast.BinOp):
            left = _preflight_node(node.left, context, where)
            right = _preflight_node(node.right, context, where)
            function = _BOUNDED_OPERATORS.get(type(node.op))
            if function is None:
                raise FunctionOSRunError(where + " uses an unsupported binary operator")
            return _guard_bounded_value(function(left, right), where)
        if isinstance(node, ast.UnaryOp):
            operand = _preflight_node(node.operand, context, where)
            function = _BOUNDED_OPERATORS.get(type(node.op))
            if function is None:
                raise FunctionOSRunError(where + " uses an unsupported unary operator")
            return _guard_bounded_value(function(operand), where)
        if isinstance(node, ast.Compare):
            left = _preflight_node(node.left, context, where)
            for operation, comparator in zip(node.ops, node.comparators):
                right = _preflight_node(comparator, context, where)
                function = _BOUNDED_OPERATORS.get(type(operation))
                if function is None:
                    raise FunctionOSRunError(where + " uses an unsupported comparison")
                if not function(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.BoolOp):
            function = _BOUNDED_OPERATORS.get(type(node.op))
            if function is None:
                raise FunctionOSRunError(where + " uses an unsupported boolean operator")
            result = _preflight_node(node.values[0], context, where)
            for item in node.values[1:]:
                result = function(result, _preflight_node(item, context, where))
            return _guard_bounded_value(result, where)
        if isinstance(node, ast.IfExp):
            test = _preflight_node(node.test, context, where)
            branch = node.body if test else node.orelse
            return _preflight_node(branch, context, where)
    except FunctionOSRunError:
        raise
    except (ArithmeticError, OverflowError, TypeError, ValueError) as exc:
        raise FunctionOSRunError(where + " cannot be evaluated within the bounded arithmetic contract") from exc
    raise FunctionOSRunError(where + " contains an unsupported expression node")


def _validate_function_spec_bounds(spec: Any, inputs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(spec, dict) or not isinstance(inputs, dict):
        raise FunctionOSRunError("function_spec and inputs must both be JSON objects")
    allowed_spec_keys = {
        "function_id", "spec_version", "name", "domain", "inputs", "outputs",
        "preconditions", "postconditions", "effects_declared", "created_at",
    }
    unknown = sorted(set(spec) - allowed_spec_keys)
    if unknown:
        raise FunctionOSRunError("FunctionSpec fields outside the bounded CLI contract: " + ", ".join(unknown))
    if spec.get("domain") != "symbolic":
        raise FunctionOSRunError("only symbolic FunctionSpecs are supported")
    if spec.get("effects_declared") != ["pure"]:
        raise FunctionOSRunError("the bounded evaluator accepts only effects_declared=[\"pure\"]")
    if not isinstance(spec.get("function_id"), str) or not isinstance(spec.get("spec_version"), str):
        raise FunctionOSRunError("function_id and spec_version must be strings")
    if not isinstance(spec.get("name"), str) or not _NAME_RE.fullmatch(spec["name"]):
        raise FunctionOSRunError("function name must be a bounded identifier")
    if not isinstance(spec.get("created_at"), str) or len(spec["created_at"]) > 128:
        raise FunctionOSRunError("created_at must be a string no longer than 128 characters")
    input_contract = spec.get("inputs")
    output_contract = spec.get("outputs")
    preconditions = spec.get("preconditions")
    postconditions = spec.get("postconditions")
    if not isinstance(input_contract, dict) or not 1 <= len(input_contract) <= MAX_INPUTS:
        raise FunctionOSRunError("FunctionSpec must declare 1 to 16 inputs")
    if any(not isinstance(name, str) or not _NAME_RE.fullmatch(name) for name in input_contract):
        raise FunctionOSRunError("input names must be bounded identifiers")
    if not isinstance(output_contract, dict) or len(output_contract) != 1:
        raise FunctionOSRunError("the bounded evaluator supports exactly one output variable")
    output_name, output_type = next(iter(output_contract.items()))
    if not isinstance(output_name, str) or not _NAME_RE.fullmatch(output_name):
        raise FunctionOSRunError("output name must be a bounded identifier")
    if not isinstance(output_type, str) or output_type not in _TYPE_MAP:
        raise FunctionOSRunError("output type must be integer, float/number, or boolean")
    if not isinstance(preconditions, list) or len(preconditions) > MAX_COLLECTION_ITEMS:
        raise FunctionOSRunError("preconditions must contain at most 16 entries")
    if not isinstance(postconditions, list) or len(postconditions) != 1:
        raise FunctionOSRunError("the bounded evaluator requires exactly one postcondition")
    for name, expected in input_contract.items():
        if not isinstance(expected, str) or expected not in _TYPE_MAP:
            raise FunctionOSRunError("input type must be integer, float/number, or boolean: " + name)
        if name not in inputs:
            raise FunctionOSRunError("input value is missing: " + name)
        value = inputs[name]
        expected_type = _TYPE_MAP[expected]
        if type(value) is not expected_type:
            raise FunctionOSRunError("input value has the wrong JSON type: " + name)
        if type(value) is int and abs(value) > MAX_INPUT_MAGNITUDE:
            raise FunctionOSRunError("input integer exceeds the magnitude limit: " + name)
        if type(value) is float and (not math.isfinite(value) or abs(value) > MAX_INPUT_MAGNITUDE):
            raise FunctionOSRunError("input float is non-finite or exceeds the magnitude limit: " + name)
    if set(inputs) != set(input_contract):
        raise FunctionOSRunError("inputs must contain exactly the declared input names")

    for index, condition in enumerate(preconditions):
        if not isinstance(condition, dict) or set(condition) != {"expression", "message"}:
            raise FunctionOSRunError("each precondition must contain exactly expression and message")
        tree = _bounded_expression(condition["expression"], "preconditions[%d]" % index)
        _preflight_node(tree.body, inputs, "preconditions[%d]" % index)
        if not isinstance(condition["message"], str) or len(condition["message"]) > MAX_EXPRESSION_CHARS:
            raise FunctionOSRunError("precondition messages must be bounded strings")

    postcondition = postconditions[0]
    if not isinstance(postcondition, dict) or set(postcondition) != {"expression", "message"}:
        raise FunctionOSRunError("postcondition must contain exactly expression and message")
    post_tree = _bounded_expression(postcondition["expression"], "postconditions[0]")
    body = post_tree.body
    if (
        not isinstance(body, ast.Compare)
        or len(body.ops) != 1
        or type(body.ops[0]) is not ast.Eq
        or not isinstance(body.left, ast.Name)
        or body.left.id != output_name
    ):
        raise FunctionOSRunError("postcondition must be one equality with the output variable on the left")
    if output_name in {node.id for node in ast.walk(body.comparators[0]) if isinstance(node, ast.Name)}:
        raise FunctionOSRunError("postcondition output cannot refer to itself")
    _preflight_node(body.comparators[0], inputs, "postconditions[0] right-hand side")
    if sum(len(condition["expression"]) for condition in preconditions) + len(postcondition["expression"]) > 4096:
        raise FunctionOSRunError("combined expression text exceeds the request limit")
    return spec, inputs


def _value_within_output_bound(value: Any) -> bool:
    if type(value) is bool:
        return True
    if type(value) is int:
        return abs(value) <= MAX_OUTPUT_MAGNITUDE
    if type(value) is float:
        return math.isfinite(value) and abs(value) <= MAX_OUTPUT_MAGNITUDE
    return False


def build_evaluation_result(function_spec: Any, inputs: Any) -> dict[str, Any]:
    """Build and execute one single-output, pure symbolic FunctionSpec through N1-N7."""
    spec_source, input_values = _validate_function_spec_bounds(function_spec, inputs)
    parser = N1FunctionSpecParser()
    spec = parser.parse(json.dumps(spec_source, ensure_ascii=False, separators=(",", ":")))
    semantic_issues = N1SemanticChecker().check(spec)
    errors = [item for item in semantic_issues if item.get("severity") == "ERROR"]
    if errors:
        raise FunctionOSRunError("N1 semantic checks failed: " + json.dumps(errors, ensure_ascii=False, sort_keys=True))

    representation = N2RepresentationEncoder().encode(spec)
    compiled = N3SymbolicCompiler().compile(spec, representation)
    if compiled.get("status") != "OK":
        raise FunctionOSRunError("N3 compilation did not return OK")
    artifact = N4ArtifactPackager().package(compiled, spec, representation)
    artifact_check = N4ArtifactVerifier().verify(artifact)
    if artifact_check.get("valid") is not True:
        raise FunctionOSRunError("N4 artifact integrity verification failed")
    execution = N5Interpreter().execute(artifact, input_values)
    trace = N6TraceCapture().capture(execution, spec)
    validation = N7Validator().validate(spec, representation, artifact, trace)

    output_name, output_type = next(iter(spec["outputs"].items()))
    outputs = execution.get("outputs", {})
    output_value = outputs.get(output_name)
    output_bound_ok = execution.get("status") != "OK" or _value_within_output_bound(output_value)
    output_type_ok = execution.get("status") != "OK" or type(output_value) is _TYPE_MAP[output_type]
    if not output_bound_ok:
        policy_status = "OUTPUT_OUT_OF_BOUNDS"
    elif not output_type_ok:
        policy_status = "OUTPUT_TYPE_MISMATCH"
    else:
        policy_status = execution.get("status", "UNKNOWN")

    return {
        "schema_version": "toolbox-function-os-evaluation-r0",
        "result_status": "FUNCTION_OS_RUN_REPORTED",
        "function_id": spec["function_id"],
        "function_os_version": "0.2.1rc0-candidate",
        "pipeline_nodes": ["N1", "N2", "N3", "N4", "N5", "N6", "N7"],
        "registry_write": "NOT_REQUESTED_N9_NOT_INVOKED",
        "execution_status": execution.get("status", "UNKNOWN"),
        "policy_status": policy_status,
        "outputs": outputs,
        "precondition_result": execution.get("precondition_result", {}),
        "postcondition_result": execution.get("postcondition_result", {}),
        "artifact_integrity": artifact_check,
        "artifact_hash": artifact.get("artifact_hash"),
        "artifact_content_hash": artifact.get("content_hash"),
        "trace": trace,
        "n7_validation": validation,
        "source_refs": _source_refs(),
        "claim_ceiling": (
            "Bounded pure symbolic FunctionSpec execution and internal N7 consistency checks only. A passing result "
            "does not establish that the specification models reality, that the function is scientifically correct, "
            "or that a proof, external validation, or registry admission exists. This is not a general code sandbox."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help='read {"function_spec":{},"inputs":{}} from stdin')
    parser.parse_args(argv)
    if sys.version_info < (3, 10):
        print("FUNCTION_OS_REQUIRES_PYTHON_3_10_OR_NEWER", file=sys.stderr)
        return 2
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise FunctionOSRunError("stdin request exceeds 16 KiB")
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        if not isinstance(request, dict) or set(request) != {"function_spec", "inputs"}:
            raise FunctionOSRunError("stdin object must contain exactly function_spec and inputs")
        result = build_evaluation_result(request["function_spec"], request["inputs"])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, FunctionSpecParseError, FunctionOSRunError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print("FUNCTION_OS_EVALUATION_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
