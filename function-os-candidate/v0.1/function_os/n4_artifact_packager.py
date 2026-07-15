"""N4 Artifact Packager — compiles packaged artifact from N2 output.

Produces: {manifest, content, content_hash} → JSON artifact.
"""
import json, hashlib
from datetime import datetime, timezone
from typing import Dict, Any

class N4ArtifactPackager:
    VERSION = "0.1.0"

    def package(self, spec: dict, compiled_output: dict,
                 format_type: str = "json_artifact") -> Dict[str, Any]:
        """Package a compiled FunctionSpec into a full artifact."""
        function_id = spec['function_id']
        spec_version = spec.get('spec_version', '1.0.0')
        spec_hash = spec.get('spec_hash', '')

        artifact_id = f"ART-{function_id}-{spec_version}"

        # Content: the compiled output
        content_canonical = json.dumps(compiled_output, sort_keys=True, ensure_ascii=False,
                                        separators=(',', ':'))
        content_hash = hashlib.sha256(content_canonical.encode('utf-8')).hexdigest()

        created_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        deps = spec.get('dependencies', [])
        caps = self._derive_capabilities(spec)

        manifest = {
            "artifact_id": artifact_id,
            "spec_hash": spec_hash,
            "compiler_version": self.VERSION,
            "format": format_type,
            "entrypoint": compiled_output.get('entrypoint', spec.get('name', '')),
            "content_hash": content_hash,
            "dependencies": [{"function_id": d['function_id'],
                              "min_spec_version": d.get('min_spec_version', '1.0.0')}
                             for d in deps],
            "capabilities": caps,
            "provenance": {
                "provenance_id": f"PROV-{function_id}-{spec_version}-{int(datetime.now(timezone.utc).timestamp())}",
                "spec_created_at": spec.get('created_at', created_at),
                "compiled_at": created_at,
                "compiler_version": self.VERSION
            },
            "created_at": created_at
        }

        # Manifest hash
        manifest_canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                                         separators=(',', ':'))
        manifest_hash = hashlib.sha256(manifest_canonical.encode('utf-8')).hexdigest()
        manifest['artifact_hash'] = manifest_hash

        return {
            "ok": True,
            "artifact": {
                "manifest": manifest,
                "content": compiled_output,
                "artifact_path": f"artifacts/{artifact_id}.json"
            },
            "artifact_id": artifact_id,
            "content_hash": content_hash,
            "manifest_hash": manifest_hash
        }

    def verify(self, artifact: dict) -> Dict[str, Any]:
        """Verify artifact integrity: content hash, manifest hash."""
        manifest = artifact.get('manifest', {})
        content = artifact.get('content', {})

        # Verify content hash
        content_canonical = json.dumps(content, sort_keys=True, ensure_ascii=False,
                                        separators=(',', ':'))
        actual_content_hash = hashlib.sha256(content_canonical.encode('utf-8')).hexdigest()
        stated_content_hash = manifest.get('content_hash', '')

        results = []
        if actual_content_hash != stated_content_hash:
            results.append({"check": "content_hash", "status": "FAIL",
                            "expected": stated_content_hash, "actual": actual_content_hash})
        else:
            results.append({"check": "content_hash", "status": "PASS"})

        # Verify manifest hash
        manifest_copy = dict(manifest)
        stated_manifest_hash = manifest_copy.pop('artifact_hash', '')
        manifest_canonical = json.dumps(manifest_copy, sort_keys=True, ensure_ascii=False,
                                         separators=(',', ':'))
        actual_manifest_hash = hashlib.sha256(manifest_canonical.encode('utf-8')).hexdigest()
        if actual_manifest_hash != stated_manifest_hash:
            results.append({"check": "manifest_hash", "status": "FAIL",
                            "expected": stated_manifest_hash, "actual": actual_manifest_hash})
        else:
            results.append({"check": "manifest_hash", "status": "PASS"})

        # Verify artifact_id format
        import re
        aid = manifest.get('artifact_id', '')
        if not re.match(r'^ART-FN-\d{8}-\d{4}-\d+\.\d+\.\d+$', aid):
            results.append({"check": "artifact_id_format", "status": "FAIL",
                            "value": aid})
        else:
            results.append({"check": "artifact_id_format", "status": "PASS"})

        passed = all(r['status'] == 'PASS' for r in results)
        return {"ok": passed, "results": results,
                "passed": sum(1 for r in results if r['status'] == 'PASS'),
                "total": len(results)}

    def _derive_capabilities(self, spec: dict) -> list:
        """Derive capabilities from spec structure."""
        caps = []
        effects = spec.get('effects_declared', [])
        if 'pure' in effects or not effects:
            caps.append('pure')
        # Check expressions for operation types
        all_exprs = []
        for ct in ['preconditions', 'postconditions', 'invariants']:
            for c in spec.get(ct, []):
                all_exprs.append(c.get('expression', ''))
        combined = ' '.join(all_exprs)
        if any(op in combined for op in ['+', '-', '*', '/', '**', '//', '%']):
            caps.append('arithmetic')
        if any(op in combined for op in ['==', '!=', '>', '<', '>=', '<=']):
            caps.append('comparison')
        if any(op in combined for op in ['and', 'or', 'not']):
            caps.append('boolean')
        if 'if' in combined and 'else' in combined:
            caps.append('conditional')
        return caps if caps else ['pure']
