"""N2 Representation — canonical symbolic representation encoder/decoder/validator.

v0.2: maps FunctionSpec (N1) → symbolic IR (intermediate representation).
Not a compiler — N3 does compilation. N2 only encodes/decodes/validates.
"""
import hashlib, json
from typing import Dict, Any

class N2RepresentationEncoder:
    VERSION = "0.2.1-candidate"

    def encode(self, spec: dict) -> dict:
        """Encode FunctionSpec → symbolic representation."""
        # Build canonical IR
        ir = {
            "kind": "symbolic_ast",
            "entrypoint": spec['name'],
            "expressions": self._extract_expressions(spec),
            "input_map": dict(spec.get('inputs', {})),
            "output_map": dict(spec.get('outputs', {})),
            "preconditions": [pc['expression'] for pc in spec.get('preconditions', [])],
            "postconditions": [pc['expression'] for pc in spec.get('postconditions', [])],
            "effects": list(spec.get('effects_declared', []))
        }

        # Compute content hash of IR
        ir_bytes = json.dumps(ir, sort_keys=True, ensure_ascii=False).encode('utf-8')
        ir_hash = hashlib.sha256(ir_bytes).hexdigest()

        # Build representation ID
        rev = 1  # initial revision
        rep_id = f"REP-{spec['function_id']}-{rev}"

        representation = {
            "representation_id": rep_id,
            "spec_hash": spec['spec_hash'],
            "representation_type": "symbolic_ast",
            "canonical_ir": ir,
            "version": "1.0.0",
            "ir_hash": ir_hash,
            "provenance": {
                "encoder": "N2RepresentationEncoder",
                "encoder_version": self.VERSION,
                "spec_source": spec['function_id'],
                "created_at": spec.get('created_at', '')
            }
        }

        return representation

    def _extract_expressions(self, spec: dict) -> dict:
        """Extract output variable → expression mapping from spec."""
        outputs = spec.get('outputs', {})
        postconds = spec.get('postconditions', [])

        exprs = {}
        for out_var in outputs:
            # Search postconditions for expressions referencing this output
            for pc in postconds:
                expr = pc.get('expression', '')
                if out_var in expr:
                    # Extract compute expression (right side of ==)
                    if '==' in expr:
                        parts = expr.split('==')
                        if out_var in parts[0]:
                            exprs[out_var] = parts[1].strip()
                        else:
                            exprs[out_var] = parts[0].strip()
                    else:
                        exprs[out_var] = expr

        # Fallback
        if not exprs:
            exprs = {k: f"{spec['name']}({', '.join(outputs.keys())})" for k in outputs}

        return exprs


class N2RepresentationDecoder:
    """Decode representation back to structured data for downstream use."""

    def decode(self, representation: dict) -> dict:
        """Extract the canonical IR and metadata from a representation."""
        return {
            "entrypoint": representation['canonical_ir']['entrypoint'],
            "expressions": representation['canonical_ir']['expressions'],
            "input_map": representation['canonical_ir']['input_map'],
            "output_map": representation['canonical_ir']['output_map'],
            "preconditions": representation['canonical_ir']['preconditions'],
            "postconditions": representation['canonical_ir']['postconditions'],
            "effects": representation['canonical_ir']['effects'],
            "spec_hash": representation['spec_hash'],
            "representation_id": representation['representation_id']
        }


class N2RepresentationValidator:
    """Validate representation consistency against source spec."""

    def validate(self, representation: dict, spec: dict) -> list:
        issues = []

        # 1. Spec hash match
        if representation.get('spec_hash') != spec.get('spec_hash'):
            issues.append({
                "severity": "ERROR",
                "check": "spec_hash_match",
                "passed": False,
                "detail": "representation.spec_hash != spec.spec_hash"
            })

        # 2. IR completeness
        ir = representation.get('canonical_ir', {})
        spec_inputs = set(spec.get('inputs', {}).keys())
        ir_inputs = set(ir.get('input_map', {}).keys())
        if spec_inputs != ir_inputs:
            issues.append({
                "severity": "ERROR",
                "check": "ir_input_completeness",
                "passed": False,
                "detail": f"missing={spec_inputs-ir_inputs}, extra={ir_inputs-spec_inputs}"
            })

        spec_outputs = set(spec.get('outputs', {}).keys())
        ir_outputs = set(ir.get('output_map', {}).keys())
        if spec_outputs != ir_outputs:
            issues.append({
                "severity": "ERROR",
                "check": "ir_output_completeness",
                "passed": False,
                "detail": f"missing={spec_outputs-ir_outputs}, extra={ir_outputs-spec_outputs}"
            })

        # 3. Provenance
        prov = representation.get('provenance', {})
        if prov.get('encoder') != 'N2RepresentationEncoder':
            issues.append({
                "severity": "WARNING",
                "check": "provenance_encoder",
                "passed": False,
                "detail": f"unexpected encoder: {prov.get('encoder')}"
            })

        # 4. Type check
        if representation.get('representation_type') != 'symbolic_ast':
            issues.append({
                "severity": "ERROR",
                "check": "representation_type",
                "passed": False,
                "detail": f"unsupported type: {representation.get('representation_type')}"
            })

        return issues


