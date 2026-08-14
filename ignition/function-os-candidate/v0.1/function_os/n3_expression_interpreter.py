"""N3 Expression Interpreter — evaluates compiled expressions with precondition enforcement."""
import json, time
from typing import Dict, Any, List, Optional

class ExecutionTrace:
    def __init__(self):
        self.events: List[Dict] = []
        self.start_time = None
        self.end_time = None

    def record(self, event_type: str, data: dict):
        self.events.append({
            "type": event_type,
            "timestamp": time.time(),
            **data
        })

    def start(self):
        self.start_time = time.time()
        self.record("EXECUTION_START", {})

    def finish(self, result: dict):
        self.end_time = time.time()
        self.record("EXECUTION_END", {
            "duration_ms": (self.end_time - self.start_time) * 1000,
            "result": "ok" if result.get('ok') else "error"
        })

    def to_dict(self) -> dict:
        return {
            "events": self.events,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": (self.end_time - self.start_time) * 1000 if self.start_time and self.end_time else 0
        }


class N3ExpressionInterpreter:
    """Interprets compiled N2 output via the N1 safe expression DSL."""

    def __init__(self, expression_dsl):
        self.dsl = expression_dsl

    def execute(self, compiled: dict, inputs: dict,
                trace: Optional[ExecutionTrace] = None) -> Dict[str, Any]:
        if trace is None:
            trace = ExecutionTrace()

        trace.start()

        try:
            # Step 1: Validate inputs
            result = self._validate_inputs(compiled, inputs, trace)
            if not result.get('ok', True):
                trace.finish(result)
                return result

            # Step 2: Check preconditions
            result = self._check_preconditions(compiled, inputs, trace)
            if not result.get('ok', True):
                trace.finish(result)
                return result

            # Step 3: Compute
            result = self._compute(compiled, inputs, trace)
            if not result.get('ok', True):
                trace.finish(result)
                return result

            outputs = result['outputs']

            # Step 4: Check postconditions
            result = self._check_postconditions(compiled, inputs, outputs, trace)
            if not result.get('ok', True):
                trace.finish(result)
                return result

            # Step 5: Check invariants
            result = self._check_invariants(compiled, inputs, outputs, trace)
            if not result.get('ok', True):
                trace.finish(result)
                return result

            trace.record("OUTPUT_PRODUCED", {"outputs": outputs})
            trace.finish({"ok": True, "outputs": outputs})

            return {
                "ok": True,
                "outputs": outputs,
                "trace": trace.to_dict(),
                "entrypoint": compiled.get('entrypoint', ''),
                "effects_applied": compiled.get('effects', [])
            }

        except Exception as e:
            trace.record("EXECUTION_ERROR", {"error": str(e)})
            trace.finish({"ok": False, "error": str(e)})
            return {
                "ok": False,
                "error": "EXECUTION_ERROR",
                "details": str(e),
                "trace": trace.to_dict()
            }

    def _validate_inputs(self, compiled: dict, inputs: dict, trace: ExecutionTrace) -> dict:
        expected = compiled.get('input_schema', {})
        trace.record("VALIDATE_INPUTS", {"expected": list(expected.keys()), "received": list(inputs.keys())})

        for var_name, var_type in expected.items():
            if var_name not in inputs:
                return {
                    "ok": False,
                    "error": "PRECONDITION_FAILED",
                    "details": f"Missing input variable: {var_name}",
                    "expected": var_name
                }
        return {"ok": True}

    def _check_preconditions(self, compiled: dict, inputs: dict, trace: ExecutionTrace) -> dict:
        preconds = compiled.get('preconditions', [])
        for i, expr in enumerate(preconds):
            try:
                result = self.dsl.evaluate(expr, inputs)
                trace.record("PRECONDITION_CHECK", {"expression": expr, "variables": inputs, "result": result})
                if not result:
                    return {
                        "ok": False,
                        "error": "PRECONDITION_FAILED",
                        "details": f"Precondition #{i+1} failed: {expr}",
                        "expression": expr,
                        "inputs": inputs
                    }
            except Exception as e:
                return {
                    "ok": False,
                    "error": "PRECONDITION_ERROR",
                    "details": f"Error evaluating precondition '{expr}': {e}"
                }
        return {"ok": True}

    def _compute(self, compiled: dict, inputs: dict, trace: ExecutionTrace) -> dict:
        expressions = compiled.get('expressions', {})
        outputs = {}

        for out_var, expr in expressions.items():
            try:
                # Build evaluation context: inputs + computed so far
                eval_context = {**inputs, **outputs}
                trace.record("COMPUTE_STEP", {"output_var": out_var, "expression": expr, "context": eval_context})

                # For expressions like "result == x + y", extract right-hand side
                clean_expr = expr
                # Try to extract compute part from postcondition-style expressions
                if '==' in expr and out_var in expr:
                    parts = expr.split('==')
                    # Find which side computes the output
                    if out_var in parts[0]:
                        clean_expr = parts[1].strip()
                    else:
                        clean_expr = parts[0].strip()

                value = self.dsl.evaluate(clean_expr, eval_context)
                outputs[out_var] = value
                trace.record("COMPUTE_RESULT", {"output_var": out_var, "value": value})

            except Exception as e:
                return {
                    "ok": False,
                    "error": "COMPUTE_ERROR",
                    "details": f"Failed to compute '{out_var}': {e}",
                    "expression": expr
                }

        return {"ok": True, "outputs": outputs}

    def _check_postconditions(self, compiled: dict, inputs: dict, outputs: dict, trace: ExecutionTrace) -> dict:
        postconds = compiled.get('postconditions', [])
        eval_context = {**inputs, **outputs}
        for i, expr in enumerate(postconds):
            try:
                result = self.dsl.evaluate(expr, eval_context)
                trace.record("POSTCONDITION_CHECK", {"expression": expr, "result": result})
                if not result:
                    return {
                        "ok": False,
                        "error": "POSTCONDITION_FAILED",
                        "details": f"Postcondition #{i+1} failed: {expr}",
                        "expression": expr,
                        "inputs": inputs,
                        "outputs": outputs
                    }
            except Exception as e:
                return {
                    "ok": False,
                    "error": "POSTCONDITION_ERROR",
                    "details": f"Error evaluating postcondition '{expr}': {e}"
                }
        return {"ok": True}

    def _check_invariants(self, compiled: dict, inputs: dict, outputs: dict, trace: ExecutionTrace) -> dict:
        invariants = compiled.get('invariants', [])
        if not invariants:
            return {"ok": True}
        eval_context = {**inputs, **outputs}
        for i, expr in enumerate(invariants):
            try:
                result = self.dsl.evaluate(expr, eval_context)
                trace.record("INVARIANT_CHECK", {"expression": expr, "result": result})
                if not result:
                    return {
                        "ok": False,
                        "error": "INVARIANT_FAILED",
                        "details": f"Invariant #{i+1} failed: {expr}"
                    }
            except Exception as e:
                return {
                    "ok": False,
                    "error": "INVARIANT_ERROR",
                    "details": f"Error evaluating invariant '{expr}': {e}"
                }
        return {"ok": True}
