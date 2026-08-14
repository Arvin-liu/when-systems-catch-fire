"""N2 Symbolic Compiler — compiles FunctionSpec into executable artifact.

Input: parsed/validated FunctionSpec (from N1)
Output: compiled_output dict (for N4 packaging)

Flow:
  1. Validate domain is symbolic
  2. Extract and normalize expressions
  3. Generate entrypoint
  4. Collect execution plan
  5. Produce compiled output
"""
import re
from typing import Dict, Any, List

class N2SymbolicCompiler:
    VERSION = "0.1.0"

    def compile(self, spec: dict) -> Dict[str, Any]:
        """Compile a validated FunctionSpec into executable output."""
        errors = self._validate_compilable(spec)
        if errors:
            return {"ok": False, "error": "COMPILE_ERROR", "details": errors}

        name = spec['name']
        inputs = spec.get('inputs', {})
        outputs = spec.get('outputs', {})
        preconditions = spec.get('preconditions', [])
        postconditions = spec.get('postconditions', [])
        invariants = spec.get('invariants', [])
        effects = spec.get('effects_declared', [])

        # Build expression mapping
        output_exprs = {}
        for out_var in outputs:
            # For symbolic functions, the spec defines the mapping via postconditions
            # We extract compute expressions from postconditions
            for pc in postconditions:
                expr = pc.get('expression', '')
                if out_var in expr:
                    output_exprs[out_var] = expr

        # Fallback: use name-based entrypoint
        if not output_exprs:
            output_exprs = {k: f"{name}({', '.join(inputs.keys())})" for k in outputs}

        # Build execution plan
        plan = {
            "validate_inputs": list(inputs.keys()),
            "check_preconditions": [pc['expression'] for pc in preconditions],
            "compute": output_exprs,
            "check_postconditions": [pc['expression'] for pc in postconditions],
            "check_invariants": [inv['expression'] for inv in invariants],
            "produce_outputs": list(outputs.keys()),
            "effects": effects
        }

        compiled = {
            "entrypoint": name,
            "function_id": spec['function_id'],
            "spec_version": spec.get('spec_version', '1.0.0'),
            "input_schema": inputs,
            "output_schema": outputs,
            "expressions": output_exprs,
            "preconditions": [pc['expression'] for pc in preconditions],
            "postconditions": [pc['expression'] for pc in postconditions],
            "invariants": [inv['expression'] for inv in invariants],
            "effects": effects,
            "plan": plan,
            "source_spec_hash": spec.get('spec_hash', ''),
            "compiler": {
                "name": "N2SymbolicCompiler",
                "version": self.VERSION
            }
        }

        return {"ok": True, "compiled": compiled}

    def _validate_compilable(self, spec: dict) -> List[str]:
        errors = []
        domain = spec.get('domain', 'symbolic')
        if domain != 'symbolic':
            errors.append(f"Domain '{domain}' not compilable (v0.1 symbolic only)")

        outputs = spec.get('outputs', {})
        if not outputs:
            errors.append("FunctionSpec has no outputs (nothing to compile)")

        # Check cyclic dependencies (simple self-reference)
        deps = spec.get('dependencies', [])
        for d in deps:
            if d.get('function_id') == spec.get('function_id'):
                errors.append(f"Self-referential dependency: {d['function_id']}")

        return errors

    def get_signature(self, spec: dict) -> Dict[str, Any]:
        """Extract type signature without full compilation."""
        return {
            "function_id": spec['function_id'],
            "name": spec['name'],
            "inputs": spec.get('inputs', {}),
            "outputs": spec.get('outputs', {}),
            "spec_version": spec.get('spec_version', '1.0.0'),
            "domain": spec.get('domain', 'symbolic')
        }
