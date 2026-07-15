"""N9 Registry Validator — schema, hash, and structural integrity checks."""
import re, hashlib
from typing import List, Dict

class N9RegistryValidator:
    def __init__(self, store):
        self.store = store

    def validate_all(self) -> List[Dict]:
        issues = []
        for fid in self.store._index:
            issues.extend(self._validate_function(fid))
        return issues

    def _validate_function(self, fid: str) -> List[Dict]:
        issues = []
        records = self.store._index[fid]
        
        prev = 0
        for r in records:
            if r['revision'] != prev + 1:
                issues.append({"severity": "ERROR", "function_id": fid,
                    "revision": r['revision'],
                    "issue": f"Non-monotonic revision (expected {prev+1})"})
            prev = r['revision']
        
        for i, r in enumerate(records):
            if r.get('supersedes') and i > 0:
                expected = records[i-1]['revision']
                if r['supersedes'] != expected:
                    issues.append({"severity": "ERROR", "function_id": fid,
                        "revision": r['revision'],
                        "issue": f"supersedes={r['supersedes']} expected={expected}"})
            if i < len(records) - 1:
                expected_sb = records[i+1]['revision']
                if r.get('superseded_by') != expected_sb:
                    issues.append({"severity": "ERROR", "function_id": fid,
                        "revision": r['revision'],
                        "issue": f"superseded_by={r.get('superseded_by')} expected={expected_sb}"})
        
        for r in records:
            expected = self.store._compute_hash(
                fid, r.get('spec_hash', ''), r.get('artifact_hash', ''), str(r['revision'])
            )
            if r['content_hash'] != expected:
                issues.append({"severity": "ERROR", "function_id": fid,
                    "revision": r['revision'],
                    "issue": f"Content hash mismatch"})
        
        for r in records:
            for hf in ['spec_hash', 'artifact_hash', 'content_hash']:
                if not re.match(r'^[a-f0-9]{64}$', r.get(hf, '')):
                    issues.append({"severity": "ERROR", "function_id": fid,
                        "revision": r['revision'],
                        "issue": f"Invalid {hf} format"})
        
        seen = set()
        for r in records:
            if r.get('supersedes') and r['supersedes'] in seen:
                issues.append({"severity": "ERROR", "function_id": fid,
                    "revision": r['revision'], "issue": "Circular supersede"})
            seen.add(r['revision'])
        
        return issues
