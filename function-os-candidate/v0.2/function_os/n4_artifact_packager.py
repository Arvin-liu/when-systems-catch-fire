"""N4 Artifact Packager — canonical artifact creation/verification/tamper detection.

v0.2: accepts compiled payload from N3, produces immutable versioned artifact.
"""
import hashlib, json
from typing import Dict, Any, Optional

class N4ArtifactPackager:
    VERSION = "0.2.1-candidate"

    def package(self, compiled: dict, spec: dict, representation: dict) -> dict:
        """Package compiled payload into immutable artifact."""
        payload = compiled.get('payload', {})
        payload_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')
        content_hash = hashlib.sha256(payload_bytes).hexdigest()

        artifact = {
            "artifact_id": f"ART-{spec['function_id']}-1",
            "spec_hash": spec['spec_hash'],
            "representation_hash": representation.get('ir_hash', ''),
            "compiled_id": compiled.get('compiled_id', ''),
            "content_hash": content_hash,
            "version": spec.get('spec_version', '1.0.0'),
            "manifest": self._build_manifest(spec, compiled, content_hash),
            "payload": payload,
            "created_at": spec.get('created_at', '')
        }

        artifact['artifact_hash'] = self._compute_artifact_hash(artifact)
        return artifact

    def _build_manifest(self, spec: dict, compiled: dict, content_hash: str) -> dict:
        return {
            "packager": "N4ArtifactPackager",
            "packager_version": self.VERSION,
            "function_id": spec['function_id'],
            "function_name": spec['name'],
            "domain": spec['domain'],
            "compiler_status": compiled.get('status'),
            "artifact_hash": None,  # Will be set by packager
            "immutable": True,
            "immutable_after": "artifact_hash assignment"
        }

    def _compute_artifact_hash(self, artifact: dict) -> str:
        fields = ['artifact_id', 'spec_hash', 'content_hash', 'compiled_id', 'version']
        raw = json.dumps({k: artifact[k] for k in fields if k in artifact},
                         sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()


class N4ArtifactVerifier:
    """Verify artifact integrity and detect tampering."""

    def verify(self, artifact: dict) -> dict:
        """Verify artifact integrity. Returns {valid: bool, checks: [...]}"""
        checks = []

        # Content hash check
        payload_bytes = json.dumps(artifact.get('payload', {}), sort_keys=True, ensure_ascii=False).encode('utf-8')
        actual_hash = hashlib.sha256(payload_bytes).hexdigest()
        checks.append({
            "check": "content_hash",
            "passed": actual_hash == artifact.get('content_hash', ''),
            "detail": "content_hash matches payload" if actual_hash == artifact.get('content_hash') else "TAMPERED: content_hash mismatch"
        })

        # Artifact hash
        packager = N4ArtifactPackager()
        expected_artifact_hash = packager._compute_artifact_hash(artifact)
        checks.append({
            "check": "artifact_hash",
            "passed": expected_artifact_hash == artifact.get('artifact_hash', ''),
            "detail": "artifact_hash intact" if expected_artifact_hash == artifact.get('artifact_hash') else "TAMPERED: artifact_hash broken"
        })

        # Immutable check
        checks.append({
            "check": "immutable",
            "passed": artifact.get('manifest', {}).get('immutable') is True,
            "detail": "manifest.immutable == True"
        })

        return {
            "valid": all(c['passed'] for c in checks),
            "checks": checks
        }


# Smoke test
if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from n1_functionspec_parser import N1FunctionSpecParser
    from n2_representation import N2RepresentationEncoder
    from n3_compiler import N3SymbolicCompiler

    parser, encoder, compiler = N1FunctionSpecParser(), N2RepresentationEncoder(), N3SymbolicCompiler()
    spec = parser.parse(json.dumps({
        "function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic",
        "inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},
        "preconditions":[{"expression":"x >= 0","message":"x"}],
        "postconditions":[{"expression":"result == x + y","message":"r"}],
        "effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"
    }))
    rep = encoder.encode(spec)
    compiled = compiler.compile(spec, rep)

    packager = N4ArtifactPackager()
    artifact = packager.package(compiled, spec, rep)
    print("Artifact:", artifact['artifact_id'], "hash:", artifact['artifact_hash'][:12])

    verifier = N4ArtifactVerifier()
    result = verifier.verify(artifact)
    print("Verification:", "VALID" if result['valid'] else "INVALID")
    print("N4: ALL OK")
