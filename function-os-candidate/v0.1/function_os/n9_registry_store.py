"""Function OS v0.1 — N9 VersionedRegistry Store

Append-only local filesystem JSON registry. No network, no database, no SQL.
Atomic writes via tempfile + os.replace(). No silent overwrites.
"""
import json, os, hashlib, tempfile
from datetime import datetime, timezone
from typing import Optional

class N9RegistryStore:
    def __init__(self, store_path: str):
        self.store_path = store_path
        self._index: dict[str, list[dict]] = {}
        os.makedirs(store_path, exist_ok=True)
        self._load_index()

    def _canonical_json(self, obj: dict) -> bytes:
        """Sorted-keys JSON, utf-8, no trailing newline."""
        return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    def _compute_hash(self, *parts: str) -> str:
        return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()

    def _atomic_write(self, path: str, content: bytes) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.store_path, suffix='.tmp')
        try:
            os.write(fd, content)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, path)

    def _reg_file(self, function_id: str) -> str:
        safe = function_id.replace('/', '_').replace('..', '_')
        return os.path.join(self.store_path, f"{safe}.json")

    def _load_index(self) -> None:
        self._index = {}
        if not os.path.isdir(self.store_path):
            return
        for fn in os.listdir(self.store_path):
            if fn.endswith('.json') and not fn.endswith('.tmp'):
                try:
                    with open(os.path.join(self.store_path, fn)) as f:
                        records = json.load(f)
                    if isinstance(records, list) and records:
                        fid = records[0].get('function_id', '')
                        self._index[fid] = records
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    def _validate_record(self, record: dict) -> list[str]:
        """Validate a registry record against the N9 schema. Returns errors."""
        errors = []
        required = ['function_id', 'revision', 'spec_hash', 'artifact_hash',
                     'compiler_version', 'status', 'created_at', 'content_hash']
        for fld in required:
            if fld not in record:
                errors.append(f"Missing required field: {fld}")
        if errors:
            return errors
        
        import re
        if not re.match(r'^FN-\d{8}-\d{4}$', record.get('function_id', '')):
            errors.append("Invalid function_id format")
        if not isinstance(record.get('revision'), int) or record['revision'] < 1:
            errors.append("Invalid revision (must be int >= 1)")
        if record.get('status') not in ('active', 'deprecated', 'superseded'):
            errors.append("Invalid status")
        if not re.match(r'^[a-f0-9]{64}$', record.get('content_hash', '')):
            errors.append("Invalid content_hash")
        return errors

    def create(self, record: dict) -> dict:
        """Register a new function. Fails if function_id already exists."""
        errors = self._validate_record(record)
        if errors:
            return {"ok": False, "error": "VALIDATION_FAILED", "details": errors}
        
        fid = record['function_id']
        if fid in self._index:
            return {"ok": False, "error": "DUPLICATE_ID", "function_id": fid}
        
        # Verify content_hash
        expected = self._compute_hash(
            fid,
            record.get('spec_hash', ''),
            record.get('artifact_hash', ''),
            str(record['revision'])
        )
        if record['content_hash'] != expected:
            return {"ok": False, "error": "HASH_MISMATCH", 
                    "expected": expected, "got": record['content_hash']}
        
        # Verify created_at is reasonable
        record['revision'] = 1  # Force revision=1 for new functions
        record['superseded_by'] = None
        
        self._index[fid] = [record]
        content = self._canonical_json(self._index[fid])
        self._atomic_write(self._reg_file(fid), content)
        
        return {"ok": True, "function_id": fid, "revision": 1}

    def read(self, function_id: str, revision: Optional[int] = None) -> dict:
        """Read a function record. If revision is None, returns latest."""
        if function_id not in self._index:
            return {"ok": False, "error": "NOT_FOUND", "function_id": function_id}
        
        records = self._index[function_id]
        if revision is None:
            record = records[-1]  # Latest
        else:
            found = [r for r in records if r['revision'] == revision]
            if not found:
                return {"ok": False, "error": "REVISION_NOT_FOUND", 
                        "function_id": function_id, "revision": revision}
            record = found[0]
        
        return {"ok": True, "record": dict(record)}

    def list(self) -> dict:
        """List all registered functions with latest revision info."""
        result = []
        for fid, records in self._index.items():
            latest = records[-1]
            result.append({
                "function_id": fid,
                "latest_revision": latest['revision'],
                "status": latest['status'],
                "name": latest.get('spec', {}).get('name', ''),
                "created_at": latest['created_at']
            })
        return {"ok": True, "count": len(result), "functions": result}

    def history(self, function_id: str) -> dict:
        """Get all revisions for a function."""
        if function_id not in self._index:
            return {"ok": False, "error": "NOT_FOUND", "function_id": function_id}
        records = self._index[function_id]
        summary = [{"revision": r['revision'], "status": r['status'],
                     "created_at": r['created_at'], "spec_version": r.get('spec', {}).get('spec_version', '')}
                   for r in records]
        return {"ok": True, "function_id": function_id, "count": len(records), "revisions": summary}

    def _internal_update(self, function_id: str, new_record: dict) -> dict:
        """Internal: append a new revision."""
        errors = self._validate_record(new_record)
        if errors:
            return {"ok": False, "error": "VALIDATION_FAILED", "details": errors}
        
        records = self._index[function_id]
        expected_revision = records[-1]['revision'] + 1
        if new_record['revision'] != expected_revision:
            return {"ok": False, "error": "REVISION_SEQUENCE_ERROR",
                    "expected": expected_revision, "got": new_record['revision']}
        
        records.append(new_record)
        records[-2]['superseded_by'] = new_record['revision']
        new_record['superseded_by'] = None
        
        content = self._canonical_json(records)
        self._atomic_write(self._reg_file(function_id), content)
        
        return {"ok": True, "function_id": function_id, "revision": new_record['revision']}

