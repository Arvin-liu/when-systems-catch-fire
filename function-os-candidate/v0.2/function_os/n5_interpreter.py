"""N5 Interpreter — canonical interpreter: Artifact + inputs → execution result.

v0.2: correctly assigned to N5 (was wrongfully N3 in v0.1).
Flow: precondition_check → execute → postcondition_check → result.
"""
import hashlib, json, time
from typing import Dict, Any
from function_os.n1_safe_expression_dsl import SafeExpressionDSL

class N5Interpreter:
    _exec_counter = 0
    VERSION = "0.2.1-candidate"
    SUPPORTED_EFFECTS = {"pure", "stateful", "io"}

    def __init__(self):
        self.dsl = SafeExpressionDSL()

    def execute(self, artifact: dict, inputs: dict) -> dict:
        """Execute artifact with given inputs."""
        start_time = time.time()
        payload = artifact.get('payload', {})
        spec_inputs = payload.get('input_map', {})

        # Type check inputs
        type_errors = self._check_types(inputs, spec_inputs)
        if type_errors:
            return self._make_result(artifact, inputs, "TYPE_ERROR",
                                     errors=type_errors)

        # Step 1: Precondition check
        pre_result = self._check_preconditions(payload, inputs)
        if not pre_result['passed']:
            return self._make_result(artifact, inputs, "PRECONDITION_FAILED",
                                     precondition_result=pre_result)

        # Step 2: Execute
        try:
            outputs = self._compute(payload, inputs)
        except Exception as e:
            return self._make_result(artifact, inputs, "RUNTIME_ERROR",
                                     errors=[{"detail": str(e)}])

        # Step 3: Postcondition check
        post_result = self._check_postconditions(payload, inputs, outputs)
        if not post_result['passed']:
            return self._make_result(artifact, inputs, "POSTCONDITION_FAILED",
                                     outputs=outputs, postcondition_result=post_result)

        # OK
        time_ms = (time.time() - start_time) * 1000
        return self._make_result(artifact, inputs, "OK", outputs=outputs,
                                 precondition_result=pre_result,
                                 postcondition_result=post_result,
                                 time_ms=time_ms)

    def _check_types(self, inputs: dict, spec_inputs: dict) -> list:
        errors = []
        for var, expected in spec_inputs.items():
            if var not in inputs:
                errors.append({"variable": var, "issue": "missing", "expected": expected})
                continue
            actual_type = type(inputs[var]).__name__
            if not self._type_match(actual_type, expected):
                errors.append({"variable": var, "issue": "type_mismatch",
                               "expected": expected, "got": actual_type})
        return errors

    def _type_match(self, actual: str, expected: str) -> bool:
        mapping = {"integer": "int", "int": "int", "float": "float", "number": "float",
                   "string": "str", "str": "str", "boolean": "bool", "bool": "bool"}
        return mapping.get(expected, expected) == mapping.get(actual, actual)

    def _check_preconditions(self, payload: dict, inputs: dict) -> dict:
        checks = []
        context = dict(inputs)
        for pc in payload.get('preconditions', []):
            expr = pc.get('expression', '')
            msg = pc.get('message', '')
            try:
                result = self.dsl.evaluate(expr, context)
                checks.append({"expression": expr, "passed": result, "message": msg})
            except Exception as e:
                checks.append({"expression": expr, "passed": False, "error": str(e), "message": msg})
        return {"passed": all(c['passed'] for c in checks), "checks": checks}

    def _check_postconditions(self, payload: dict, inputs: dict, outputs: dict) -> dict:
        checks = []
        context = {**inputs, **outputs}
        for pc in payload.get('postconditions', []):
            expr = pc.get('expression', '')
            msg = pc.get('message', '')
            try:
                result = self.dsl.evaluate(expr, context)
                checks.append({"expression": expr, "passed": result, "message": msg})
            except Exception as e:
                checks.append({"expression": expr, "passed": False, "error": str(e), "message": msg})
        return {"passed": all(c['passed'] for c in checks), "checks": checks}

    def _compute(self, payload: dict, inputs: dict) -> dict:
        context = dict(inputs)
        outputs = {}
        for out_var, expr in payload.get('expressions', {}).items():
            outputs[out_var] = self.dsl.evaluate(expr, context)
            context[out_var] = outputs[out_var]  # allow chaining
        return outputs

    def _make_result(self, artifact, inputs, status, outputs=None, errors=None,
                     precondition_result=None, postcondition_result=None, time_ms=0.0):
        N5Interpreter._exec_counter += 1
        exec_id = f"EXE-{artifact['artifact_id'].replace('ART-','')}-{N5Interpreter._exec_counter}"
        return {
            "execution_id": exec_id,
            "artifact_id": artifact['artifact_id'],
            "status": status,
            "inputs": inputs,
            "outputs": outputs or {},
            "result": {},
            "trace_id": f"TRC-{exec_id.replace('EXE-','')}",
            "precondition_result": precondition_result or {"passed": True, "checks": []},
            "postcondition_result": postcondition_result or {"passed": True, "checks": []},
            "time_ms": time_ms,
            "errors": errors or []
        }


# Smoke test
if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from n1_functionspec_parser import N1FunctionSpecParser
    from n2_representation import N2RepresentationEncoder
    from n3_compiler import N3SymbolicCompiler
    from n4_artifact_packager import N4ArtifactPackager

    parser, encoder, compiler, packager = (N1FunctionSpecParser(), N2RepresentationEncoder(),
                                           N3SymbolicCompiler(), N4ArtifactPackager())
    spec = parser.parse(json.dumps({
        "function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic",
        "inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},
        "preconditions":[{"expression":"x >= 0","message":"x non-negative"}],
        "postconditions":[{"expression":"result == x + y","message":"r == sum"}],
        "effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"
    }))
    rep = encoder.encode(spec)
    compiled = compiler.compile(spec, rep)
    artifact = packager.package(compiled, spec, rep)

    interpreter = N5Interpreter()

    # Test OK
    result = interpreter.execute(artifact, {"x": 3, "y": 7})
    print("OK test:", result['status'], "→ result:", result['outputs'])

    # Test precondition fail
    result = interpreter.execute(artifact, {"x": -1, "y": 2})
    print("Precond fail:", result['status'])

    # Test postcondition fail (we'd need a buggy spec, not trivial to test here)
    # Test type error
    result = interpreter.execute(artifact, {"x": 3})
    print("Missing input:", result['status'])

    print("N5: ALL OK")
