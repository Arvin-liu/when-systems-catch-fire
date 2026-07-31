"""Independent reference oracle for Task 105 benchmark (contract §5.2).

IMPORTANT (contract §5.2): this module MUST NOT import any `function_os` module,
the compiler, the validator or the registry under test. It is a SEPARATE
implementation of the reference semantics, so agreement with Function OS is
meaningful evidence rather than two views of the same code.

DESIGN DECISION (preregistered, see PREREGISTRATION.md §oracle):
The oracle's allowed-node whitelist is intentionally IDENTICAL to
`function_os/n1_safe_expression_dsl.py::SafeExpressionDSL.ALLOWED_NODES` (v0.2).
Rationale: Function OS v0.2 explicitly and repeatedly claims ONLY this restricted
AST (README "限制是什么", v0.2-scope-contract.json, canonical-node-contract.json,
and the DSL source). A broader "true math" oracle (e.g. one that also permits
`abs()`, `len()`, or `min()`) would classify those as valid inputs, but Function
OS documents and implements them as FORBIDDEN (`ast.Call` is absent from
ALLOWED_NODES, and the README lists "禁止任意函数调用"). Measuring fidelity with a
superset oracle would manufacture false fidelity failures on inputs that are
out of claimed scope — a violation of contract §3 ("do not test or imply
capabilities the current implementation does not claim"). Therefore:

  - Within the shared allowed node set, oracle value == Function OS value
    (this is the SUPPORTED_SEMANTIC_FIDELITY signal);
  - Outside the allowed node set, the oracle REJECTS (OracleError) AND Function
    OS rejects (RUNTIME_ERROR / TYPE_ERROR), which is the
    FAIL_CLOSED_LANGUAGE_BOUNDARY signal.

Independence is preserved because the evaluation code, constant handling,
extraction logic and error taxonomy are written from scratch, not imported.
Agreement between two implementations sharing the same bug is not asserted as
proof of correctness (contract §5.2); the oracle's limits are recorded in the
preregistration and the receipt.
"""
import ast
import hashlib
import json

# Exact mirror of function_os/n1_safe_expression_dsl.py ALLOWED_NODES (v0.2.1-candidate).
ALLOWED_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Compare,
    ast.BoolOp, ast.Name, ast.Constant, ast.Load,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.And, ast.Or,
    ast.IfExp,
}

# Node types that, if present, represent a FORBIDDEN construct for Function OS v0.2.
# Used by the boundary stratum to enumerate adversarial expressions that must be
# rejected rather than silently executed.
FORBIDDEN_NODE_KINDS = {
    "Call": "function call (e.g. os.system, eval, abs, len)",
    "Attribute": "attribute access (e.g. x.__class__)",
    "Subscript": "indexing (e.g. x[0])",
    "Lambda": "lambda expression",
    "List": "list literal",
    "Tuple": "tuple literal",
    "Dict": "dict literal",
    "Set": "set literal",
    "Comprehension": "comprehension",
    "Import": "import statement",
    "ImportFrom": "import-from statement",
    "Assign": "assignment",
    "AugAssign": "augmented assignment",
    "Delete": "delete statement",
    "Starred": "starred expression",
    "NamedExpr": "walrus expression",
    "Yield": "yield expression",
    "Await": "await expression",
    "GeneratorExp": "generator expression",
    "FormattedValue": "f-string value",
    "JoinedStr": "f-string",
}


class OracleError(Exception):
    """Raised when an expression is outside the allowed reference semantics."""
    pass


def _is_allowed(node) -> bool:
    return type(node) in ALLOWED_NODES


def expression_allowed(expr: str):
    """Static check used by the boundary stratum.

    Returns (allowed: bool, reason: str). `allowed` is True only when every AST
    node is in ALLOWED_NODES. `reason` describes the first forbidden node kind.
    """
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        return False, f"syntax_error:{e}"
    for n in ast.walk(tree):
        if not _is_allowed(n):
            return False, f"forbidden_node:{type(n).__name__}"
    return True, ""


def evaluate(expr: str, env: dict):
    """Independently evaluate a compute expression under the reference semantics."""
    tree = ast.parse(expr.strip(), mode="eval")
    for n in ast.walk(tree):
        if not _is_allowed(n):
            raise OracleError(f"disallowed AST node type: {type(n).__name__}")
    return _eval(tree.body, dict(env))


def _eval(node, env):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise OracleError(f"unsupported constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise OracleError(f"unbound name: {node.id}")
    if isinstance(node, ast.UnaryOp):
        v = _eval(node.operand, env)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return +v
        if isinstance(node.op, ast.Not):
            return not v
        raise OracleError("unsupported unary op")
    if isinstance(node, ast.BinOp):
        a = _eval(node.left, env)
        b = _eval(node.right, env)
        op = node.op
        if isinstance(op, ast.Add):
            return a + b
        if isinstance(op, ast.Sub):
            return a - b
        if isinstance(op, ast.Mult):
            return a * b
        if isinstance(op, ast.Div):
            if b == 0:
                raise OracleError("division by zero")
            return a / b
        if isinstance(op, ast.FloorDiv):
            if b == 0:
                raise OracleError("division by zero")
            return a // b
        if isinstance(op, ast.Mod):
            if b == 0:
                raise OracleError("division by zero")
            return a % b
        if isinstance(op, ast.Pow):
            return a ** b
        raise OracleError("unsupported binary op")
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(_eval(v, env) for v in node.values)
        if isinstance(node.op, ast.Or):
            return any(_eval(v, env) for v in node.values)
        raise OracleError("unsupported bool op")
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval(comp, env)
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            else:
                raise OracleError("unsupported compare op")
            if not ok:
                return False
            left = right
        return True
    if isinstance(node, ast.IfExp):
        return _eval(node.body, env) if _eval(node.test, env) else _eval(node.orelse, env)
    raise OracleError(f"disallowed AST node: {type(node).__name__}")


def extract_outputs(spec: dict) -> dict:
    """Mirror N2RepresentationEncoder._extract_expressions.

    For each output variable, find a postcondition of the form `o == e` (or
    `e == o`) and return the compute expression `e`. Resolution direction is
    resolved by matching the output variable, exactly as N2 does.
    """
    outputs = spec.get("outputs", {})
    postconds = spec.get("postconditions", [])
    exprs = {}
    for out_var in outputs:
        chosen = None
        for pc in postconds:
            e = pc.get("expression", "")
            if "==" in e:
                left, right = e.split("==", 1)
                if out_var in left:
                    chosen = right.strip()
                elif out_var in right:
                    chosen = left.strip()
        if chosen is None:
            # Fallback: use the raw postcondition expression (likely to be
            # rejected by the evaluator, which is the correct behaviour for a
            # malformed spec rather than silent acceptance).
            chosen = postconds[-1].get("expression", "") if postconds else ""
        exprs[out_var] = chosen
    return exprs


def compute_reference(spec: dict, inputs: dict):
    """Return (status, outputs, error).

    status is 'OK' when every output expression evaluates under the reference
    semantics; otherwise 'RUNTIME_ERROR' (mirrors Function OS N5 RUNTIME_ERROR
    outcome for forbidden/unsupported constructs and runtime exceptions).
    """
    try:
        exprs = extract_outputs(spec)
        env = dict(inputs)
        outputs = {}
        for out_var, expr in exprs.items():
            val = evaluate(expr, env)
            outputs[out_var] = val
            env[out_var] = val
        return "OK", outputs, None
    except OracleError as e:
        return "RUNTIME_ERROR", {}, str(e)
    except Exception as e:  # defensive: any unexpected evaluation fault
        return "RUNTIME_ERROR", {}, f"{type(e).__name__}:{e}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
