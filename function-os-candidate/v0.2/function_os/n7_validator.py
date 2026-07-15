"""N7 Validator — canonical validator: artifact/spec/trace consistency validation.

v0.2: correctly assigned to N7 (merged from v0.1 n5/n6 feedback paths).
Validates FunctionSpec, Representation, Artifact, ExecutionTrace against each other.
"""
import hashlib, json
from typing import Dict, Any, List

class N7Validator:
    VERSION = "0.2.1-candidate"

    def validate(self, spec: dict, representation: dict, artifact: dict,
                 trace: dict = None, evidence: list = None) -> dict:
        """Validate artifact against spec, representation, and trace."""
        checks = []
        feedback = []

        # Check 1: Spec hash chain
        if spec.get('spec_hash') != artifact.get('spec_hash'):
            feedback.append({"severity": "ERROR", "chain": "spec→artifact",
                             "detail": "spec_hash mismatch"})
            checks.append({"check": "spec_to_artifact_hash", "passed": False})
        else:
            checks.append({"check": "spec_to_artifact_hash", "passed": True})

        # Check 2: Representation hash chain
        rep_hash = representation.get('ir_hash', '')
        art_rep_hash = artifact.get('representation_hash', '')
        if rep_hash and art_rep_hash and rep_hash != art_rep_hash:
            feedback.append({"severity": "ERROR", "chain": "rep→artifact",
                             "detail": "representation_hash mismatch"})
            checks.append({"check": "rep_to_artifact_hash", "passed": False})
        else:
            checks.append({"check": "rep_to_artifact_hash", "passed": True})

        # Check 3: Artifact content integrity
        payload_bytes = json.dumps(artifact.get('payload', {}), sort_keys=True, ensure_ascii=False).encode('utf-8')
        actual_hash = hashlib.sha256(payload_bytes).hexdigest()
        passed = actual_hash == artifact.get('content_hash', '')
        if not passed:
            feedback.append({"severity": "ERROR", "chain": "artifact",
                             "detail": "content_hash broken — possible tampering"})
        checks.append({"check": "artifact_content_integrity", "passed": passed})

        # Check 4: Input/output completeness (spec vs artifact payload)
        payload = artifact.get('payload', {})
        spec_inputs = set(spec.get('inputs', {}).keys())
        payload_inputs = set(payload.get('input_map', {}).keys())
        if spec_inputs != payload_inputs:
            feedback.append({"severity": "WARNING", "chain": "spec→artifact",
                             "detail": f"input mismatch: spec={spec_inputs}, artifact={payload_inputs}"})
            checks.append({"check": "input_completeness", "passed": False})
        else:
            checks.append({"check": "input_completeness", "passed": True})

        spec_outputs = set(spec.get('outputs', {}).keys())
        payload_outputs = set(payload.get('output_map', {}).keys())
        if spec_outputs != payload_outputs:
            feedback.append({"severity": "WARNING", "chain": "spec→artifact",
                             "detail": f"output mismatch: spec={spec_outputs}, artifact={payload_outputs}"})
            checks.append({"check": "output_completeness", "passed": False})
        else:
            checks.append({"check": "output_completeness", "passed": True})

        # Check 5: Trace consistency
        if trace:
            if trace.get('artifact_id') != artifact.get('artifact_id'):
                feedback.append({"severity": "WARNING", "chain": "artifact→trace",
                                 "detail": "trace.artifact_id != artifact.artifact_id"})
                checks.append({"check": "trace_artifact_consistency", "passed": False})
            else:
                checks.append({"check": "trace_artifact_consistency", "passed": True})

            if trace.get('spec_id') != spec.get('function_id'):
                feedback.append({"severity": "WARNING", "chain": "spec→trace",
                                 "detail": "trace.spec_id != spec.function_id"})
                checks.append({"check": "trace_spec_consistency", "passed": False})
            else:
                checks.append({"check": "trace_spec_consistency", "passed": True})

        # Check 6: Evidence relevance
        if evidence:
            for i, ev in enumerate(evidence):
                if ev.get('source_id') and ev.get('source_id') == spec.get('function_id'):
                    checks.append({"check": f"evidence_{i}_self_reference",
                                   "passed": False})
                    feedback.append({"severity": "WARNING", "chain": "evidence",
                                     "detail": "evidence references self — circular"})

        # Determine overall status
        all_passed = all(c['passed'] for c in checks)
        return {
            "validation_id": f"VAL-{spec['function_id']}-1",
            "artifact_id": artifact.get('artifact_id', ''),
            "status": "PASS" if all_passed else ("FAIL" if feedback else "WARNING"),
            "checks": checks,
            "feedback": feedback,
            "validator_version": self.VERSION
        }


class N7Feedback:
    """Generate feedback for N1 spec revision suggestions."""

    def suggest(self, validation_result: dict, spec: dict) -> list:
        suggestions = []
        for fb in validation_result.get('feedback', []):
            if fb.get('severity') == 'ERROR':
                suggestions.append({
                    "target": "N1 FunctionSpec revision",
                    "issue": fb.get('detail', ''),
                    "chain": fb.get('chain', ''),
                    "recommended_action": self._recommend(fb)
                })
        return suggestions

    def _recommend(self, feedback: dict) -> str:
        chain = feedback.get('chain', '')
        detail = feedback.get('detail', '')
        if 'hash mismatch' in chain or 'content_hash broken' in detail:
            return "REBUILD from N1 spec: recompute all downstream hashes"
        if 'missing' in detail or 'mismatch' in detail:
            return "REVIEW spec: align inputs/outputs/preconditions"
        return "INVESTIGATE"
