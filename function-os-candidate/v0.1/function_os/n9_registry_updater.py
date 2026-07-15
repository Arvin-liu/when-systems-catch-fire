"""N9 RegistryStore — Update & Rollback extension

Append-only: new revision created on update, rollback creates new revision.
Historical records never deleted.
"""
import json, os, hashlib
from datetime import datetime, timezone
from typing import Optional

# Import from same package
from function_os_candidate.v0_1.function_os.n9_registry_store import N9RegistryStore

class N9RegistryUpdater:
    """Extends N9RegistryStore with update/rollback/supersede operations."""
    
    def __init__(self, store: N9RegistryStore):
        self.store = store
    
    def update(self, function_id: str, updated_record: dict) -> dict:
        """Register a new revision. Fails if function_id not found or revision mismatch."""
        if function_id not in self.store._index:
            return {"ok": False, "error": "NOT_FOUND", "function_id": function_id}
        
        current = self.store._index[function_id][-1]
        
        required = ['function_id', 'spec_hash', 'artifact_hash', 'compiler_version', 
                     'status', 'created_at', 'content_hash']
        for fld in required:
            if fld not in updated_record:
                return {"ok": False, "error": "MISSING_FIELD", "field": fld}
        
        if updated_record['function_id'] != function_id:
            return {"ok": False, "error": "FUNCTION_ID_MISMATCH"}
        
        new_revision = current['revision'] + 1
        updated_record['revision'] = new_revision
        
        expected_hash = self.store._compute_hash(
            function_id,
            updated_record.get('spec_hash', ''),
            updated_record.get('artifact_hash', ''),
            str(new_revision)
        )
        if updated_record['content_hash'] != expected_hash:
            return {"ok": False, "error": "HASH_MISMATCH",
                    "expected": expected_hash, "got": updated_record['content_hash']}
        
        records = list(self.store._index[function_id])
        records.append(updated_record)
        records[-2]['superseded_by'] = new_revision
        updated_record['superseded_by'] = None
        
        content = self.store._canonical_json(records)
        self.store._atomic_write(self.store._reg_file(function_id), content)
        self.store._index[function_id] = records
        
        return {"ok": True, "function_id": function_id, 
                "previous_revision": current['revision'], "new_revision": new_revision}
    
    def rollback(self, function_id: str, target_revision: int, reason: str = "") -> dict:
        """Rollback to a previous revision by creating a NEW revision pointing to target."""
        if function_id not in self.store._index:
            return {"ok": False, "error": "NOT_FOUND", "function_id": function_id}
        
        records = self.store._index[function_id]
        target = None
        for r in records:
            if r['revision'] == target_revision:
                target = r
                break
        
        if target is None:
            return {"ok": False, "error": "TARGET_REVISION_NOT_FOUND",
                    "function_id": function_id, "revision": target_revision,
                    "available": [r['revision'] for r in records]}
        
        if target_revision == records[-1]['revision']:
            return {"ok": False, "error": "ALREADY_LATEST",
                    "function_id": function_id, "revision": target_revision}
        
        new_revision = records[-1]['revision'] + 1
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        rollback_record = {
            "function_id": function_id,
            "revision": new_revision,
            "spec_hash": target['spec_hash'],
            "artifact_hash": target['artifact_hash'],
            "compiler_version": target.get('compiler_version', '0.1.0'),
            "status": "active",
            "created_at": now,
            "content_hash": self.store._compute_hash(
                function_id, target['spec_hash'], target['artifact_hash'], str(new_revision)
            ),
            "spec": target.get('spec', {}),
            "artifact": target.get('artifact', {}),
            "supersedes": records[-1]['revision'],
            "notes": f"ROLLBACK to revision {target_revision}. Reason: {reason}",
            "provenance": {
                "provenance_id": f"PROV-{function_id}-rollback-{target_revision}",
                "rollback_from": records[-1]['revision'],
                "rollback_to": target_revision,
                "reason": reason
            }
        }
        
        records = list(records)
        records.append(rollback_record)
        records[-2]['superseded_by'] = new_revision
        rollback_record['superseded_by'] = None
        
        content = self.store._canonical_json(records)
        self.store._atomic_write(self.store._reg_file(function_id), content)
        self.store._index[function_id] = records
        
        return {"ok": True, "function_id": function_id,
                "rollback_from": records[-2]['revision'], 
                "rollback_to": target_revision,
                "new_revision": new_revision}
    
    def supersede(self, function_id: str, superseded_by_id: str) -> dict:
        """Mark a function as superseded by another function."""
        if function_id not in self.store._index:
            return {"ok": False, "error": "NOT_FOUND", "function_id": function_id}
        
        records = self.store._index[function_id]
        latest = records[-1]
        
        updated = dict(latest)
        updated['status'] = 'superseded'
        new_revision = latest['revision'] + 1
        updated['revision'] = new_revision
        updated['superseded_by'] = None
        updated['notes'] = f"Superseded by {superseded_by_id}"
        updated['content_hash'] = self.store._compute_hash(
            function_id, latest['spec_hash'], latest['artifact_hash'], str(new_revision)
        )
        updated['created_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        records = list(records)
        records.append(updated)
        records[-2]['superseded_by'] = new_revision
        
        content = self.store._canonical_json(records)
        self.store._atomic_write(self.store._reg_file(function_id), content)
        self.store._index[function_id] = records
        
        return {"ok": True, "function_id": function_id, "superseded_by": superseded_by_id,
                "new_revision": new_revision, "previous_status": latest['status']}
