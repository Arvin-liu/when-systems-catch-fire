"""N1 Safe Expression DSL — minimal arithmetic/comparison/boolean subset.

Allowed: + - * / ** // % == != > >= < <= and or not if-then-else
Not allowed: eval, exec, import, open, os, subprocess, __, ., ( ), any I/O

Grammar (strict subset):
  expr     = comparison | bool_expr | conditional
  comparison = term (('==' | '!=' | '>' | '>=' | '<' | '<=') term)*
  bool_expr = atom (('and' | 'or') atom)*
  term     = factor (('+' | '-') factor)*
  factor   = power (('*' | '/' | '//' | '%') power)*
  power    = primary ('**' primary)*
  unary    = ('not' | '-')? atom
  atom     = NUMBER | identifier | '(' expr ')' | conditional
  conditional = expr 'if' comparison 'else' expr
  identifier = [a-zA-Z_][a-zA-Z0-9_]*

Forbidden: . (attribute access), __ (dunder), (), [] (beyond grouping), any keyword except if/else/and/or/not
"""
import ast
import operator
import math
from typing import Any, Dict, Set

BUILTINS = {'true': True, 'false': False, 'null': None, 'pi': math.pi, 'e': math.e}

class SafeExpressionError(Exception):
    pass

class SafeExpressionDSL:
    def evaluate(self, expr: str, variables: Dict[str, Any]) -> Any:
        """Parse and evaluate a safe expression with given variable bindings."""
        expr = expr.strip()
        if not expr:
            raise SafeExpressionError("Empty expression")
        self._safety_scan(expr)
        tree = self._parse(expr)
        return self._eval_node(tree, variables)

    def _safety_scan(self, expr: str):
        """Reject unsafe patterns before parsing."""
        # Reject attribute access
        if '.' in expr:
            raise SafeExpressionError("Dot (attribute access) is forbidden")
        # Reject double underscore
        if '__' in expr:
            raise SafeExpressionError("Double underscore is forbidden")
        # Reject function call syntax (x(y))
        import re
        if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(', expr):
            raise SafeExpressionError("Function calls are forbidden")
        # Reject index/slice
        if '[' in expr or ']' in expr:
            raise SafeExpressionError("Indexing/slicing is forbidden")
        # Reject known dangerous tokens
        dangerous = ['import', 'exec', 'eval', 'open', '__', 'os.', 'subprocess', 'system', 'popen']
        for d in dangerous:
            if d in expr:
                raise SafeExpressionError(f"Forbidden token: {d}")

    def _parse(self, expr: str) -> ast.AST:
        """Parse expression using Python's ast with strict node whitelist."""
        try:
            tree = ast.parse(expr.strip(), mode='eval')
        except SyntaxError as e:
            raise SafeExpressionError(f"Syntax error: {e}")
        self._validate_ast(tree)
        return tree

    def _validate_ast(self, node: ast.AST):
        """Ensure AST only contains allowed node types."""
        ALLOWED = {
            ast.Expression, ast.BoolOp, ast.Compare, ast.BinOp, ast.UnaryOp,
            ast.IfExp, ast.Name, ast.Constant,
            ast.And, ast.Or, ast.Not, ast.Eq, ast.NotEq, ast.Lt, ast.LtE,
            ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
            ast.USub, ast.UAdd, ast.Load,
        }
        for child in ast.walk(node):
            if type(child) not in ALLOWED:
                raise SafeExpressionError(f"Forbidden AST node: {type(child).__name__}")

    def _eval_node(self, node: ast.AST, variables: Dict[str, Any]) -> Any:
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body, variables)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            name = node.id
            if name in BUILTINS:
                return BUILTINS[name]
            if name not in variables:
                raise SafeExpressionError(f"Undefined variable: {name}")
            return variables[name]
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, variables)
            right = self._eval_node(node.right, variables)
            ops = {
                ast.Add: operator.add, ast.Sub: operator.sub,
                ast.Mult: operator.mul, ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
                ast.Pow: operator.pow,
            }
            op_type = type(node.op)
            if op_type in ops:
                try:
                    return ops[op_type](left, right)
                except ZeroDivisionError:
                    raise SafeExpressionError("Division by zero")
            raise SafeExpressionError(f"Unknown binary operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, variables)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.Not):
                return not operand
            raise SafeExpressionError(f"Unknown unary operator: {type(node.op).__name__}")
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, variables)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, variables)
                cmp_ops = {
                    ast.Eq: operator.eq, ast.NotEq: operator.ne,
                    ast.Lt: operator.lt, ast.LtE: operator.le,
                    ast.Gt: operator.gt, ast.GtE: operator.ge,
                }
                op_type = type(op)
                if op_type in cmp_ops:
                    if not cmp_ops[op_type](left, right):
                        return False
                    left = right
                else:
                    raise SafeExpressionError(f"Unknown comparison: {op_type.__name__}")
            return True
        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, variables) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
            raise SafeExpressionError(f"Unknown bool op: {type(node.op).__name__}")
        elif isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, variables)
            if test:
                return self._eval_node(node.body, variables)
            else:
                return self._eval_node(node.orelse, variables)
        else:
            raise SafeExpressionError(f"Unsupported node: {type(node).__name__}")
