"""N1 Safe Expression DSL — evaluates expressions from a restricted AST whitelist.

v0.2: unchanged from v0.1 core logic, symbolic-only, AST whitelist.
No eval/exec/compile of arbitrary code. No os/subprocess/attribute access.
"""
import ast, operator

class SafeExpressionDSL:
    VERSION = "0.2.1-candidate"

    ALLOWED_NODES = {
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Compare,
        ast.BoolOp, ast.Name, ast.Constant, ast.Load,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Not,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.And, ast.Or,
        ast.IfExp
    }

    OPERATORS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
        ast.Not: operator.not_,
        ast.Eq: operator.eq, ast.NotEq: operator.ne,
        ast.Lt: operator.lt, ast.LtE: operator.le,
        ast.Gt: operator.gt, ast.GtE: operator.ge,
        ast.And: lambda a, b: a and b, ast.Or: lambda a, b: a or b
    }

    def evaluate(self, expression: str, context: dict):
        """Safely evaluate an expression against a context dict."""
        tree = ast.parse(expression.strip(), mode='eval')
        self._validate(tree)
        return self._eval_node(tree.body, context)

    def _validate(self, tree):
        """Validate that only allowed AST nodes are present."""
        for node in ast.walk(tree):
            if type(node) not in self.ALLOWED_NODES:
                raise ValueError(f"Forbidden node: {type(node).__name__} in expression")

    def _eval_node(self, node, context):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise ValueError(f"Undefined variable: {node.id}")
            return context[node.id]
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_func = self.OPERATORS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op_func(left, right)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op_func = self.OPERATORS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op_func(operand)
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            for op_node, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_func = self.OPERATORS.get(type(op_node))
                if op_func is None:
                    raise ValueError(f"Unsupported comparison: {type(op_node).__name__}")
                if not op_func(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.BoolOp):
            op_func = self.OPERATORS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported bool op: {type(node.op).__name__}")
            result = self._eval_node(node.values[0], context)
            for val in node.values[1:]:
                result = op_func(result, self._eval_node(val, context))
            return result
        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, context)
            if test:
                return self._eval_node(node.body, context)
            return self._eval_node(node.orelse, context)
        raise ValueError(f"Unsupported node: {type(node).__name__}")
