"""N3 Compiler — canonical compiler: N1 FunctionSpec + N2 Representation → compiled payload.

v0.2: correctly assigned to N3 (was wrongfully N2 in v0.1).
Input validation, type checking, resolution, payload generation.
"""
import hashlib, json
from typing import Dict, Any, Tuple

class N3SymbolicCompiler:
    VERSION = "0.2.1-candidate"

    def compile(self, spec: dict, representation: dict) -> dict:
        """Compile FunctionSpec + Representation → compiled payload."""
        errors, warnings = self._validate_inputs(spec, representation)

        status = "ERROR" if errors else ("WARNING" if warnings else "OK")

        # Generate payload
        payload = self._generate_payload(spec, representation) if not errors else {}

        compiled = {
            "compiled_id": f"CMP-{spec['function_id']}-1",
            "spec_hash": spec['spec_hash'],
            "representation_hash": representation.get('ir_hash', ''),
            "compiler_version": self.VERSION,
            "status": status,
            "target": "n5_interpreter_v0.2",
            "errors": errors,
            "warnings": warnings,
            "payload": payload
        }

        return compiled

    def _validate_inputs(self, spec: dict, rep: dict) -> Tuple[list, list]:
        errors = []
        warnings = []

        # Check hash consistency
        if spec.get('spec_hash') != rep.get('spec_hash'):
            errors.append({
                "category": "HASH_MISMATCH",
                "detail": "spec.spec_hash != representation.spec_hash"
            })

        # Check domain
        if spec.get('domain') != 'symbolic':
            errors.append({
                "category": "DOMAIN_UNSUPPORTED",
                "detail": f"domain '{spec.get('domain')}' not supported"
            })

        # Check representation type
        if rep.get('representation_type') != 'symbolic_ast':
            errors.append({
                "category": "DOMAIN_UNSUPPORTED",
                "detail": f"representation_type '{rep.get('representation_type')}' not supported"
            })

        # Check IR completeness
        ir = rep.get('canonical_ir', {})
        spec_inputs = set(spec.get('inputs', {}).keys())
        ir_inputs = set(ir.get('input_map', {}).keys())
        if spec_inputs != ir_inputs:
            errors.append({
                "category": "TYPE_MISMATCH",
                "detail": f"input mismatch: spec={spec_inputs}, ir={ir_inputs}"
            })

        # Check for undeclared symbols in expressions
        all_declared = spec_inputs | set(spec.get('outputs', {}).keys())
        for out_var, expr in ir.get('expressions', {}).items():
            import re
            tokens = set(re.findall(r'[a-zA-Z_]\w*', expr))
            keywords = {'True', 'False', 'None', 'and', 'or', 'not', 'if', 'else'}
            refs = tokens - keywords - {'int', 'float', 'str', 'bool'}
            undeclared = refs - all_declared
            if undeclared:
                errors.append({
                    "category": "UNDECLARED_SYMBOL",
                    "detail": f"expression '{expr}' references undeclared: {undeclared}"
                })

        # Check effects declared
        effects = spec.get('effects_declared', [])
        if not effects:
            warnings.append({"category": "NO_EFFECTS", "detail": "no effects declared"})

        return errors, warnings

    def _generate_payload(self, spec: dict, rep: dict) -> dict:
        ir = rep['canonical_ir']
        return {
            "function_id": spec['function_id'],
            "entrypoint": ir['entrypoint'],
            "expressions": ir['expressions'],
            "input_map": ir['input_map'],
            "output_map": ir['output_map'],
            "preconditions": spec.get('preconditions', []),
            "postconditions": spec.get('postconditions', []),
            "effects": spec.get('effects_declared', []),
            "uncertainty": spec.get('uncertainty', {"model": "deterministic", "confidence": 1.0})
        }


