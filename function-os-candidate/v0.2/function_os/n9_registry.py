"""N9 VersionedRegistry — canonical append-only, versioned, auditable registry.

v0.2: adapted from v0.1 n9_registry_store/updater/validator.
"""
import hashlib, json
from typing import Dict, Any, List, Optional
from datetime import datetime

class N9RegistryStore:
    VERSION = "0.2.1-candidate"

    def __init__(self):
        self._records = {}  # function_id → list of revisions

    def create(self, record: dict) -> dict:
        """Add initial record for a function."""
        fn_id = record['function_id']
        if fn_id in self._records:
            raise ValueError(f"function_id {fn_id} already exists — use update()")

        record['revision'] = 1
        record['status'] = 'active'
        record['created_at'] = datetime.utcnow().isoformat() + 'Z'
        record['supersedes'] = None

        self._records[fn_id] = [dict(record)]
        return dict(record)

    def read(self, function_id: str, revision: int = None) -> Optional[dict]:
        """Read record by function_id, optionally at specific revision."""
        records = self._records.get(function_id, [])
        if not records:
            return None
        if revision is not None:
            for r in records:
                if r['revision'] == revision:
                    return dict(r)
            return None
        return dict(records[-1])

    def list(self) -> list:
        """List all active records (latest revision only)."""
        return [dict(records[-1]) for records in self._records.values()
                if records]

    def history(self, function_id: str) -> list:
        """Get full revision history for a function."""
        return [dict(r) for r in self._records.get(function_id, [])]


class N9RegistryUpdater:
    VERSION = "0.2.1-candidate"

    def __init__(self, store: N9RegistryStore):
        self._store = store

    def update(self, function_id: str, new_record: dict) -> dict:
        """Append a new revision to an existing function."""
        current = self._store.read(function_id)
        if current is None:
            raise ValueError(f"function_id {function_id} not found")

        new_record['function_id'] = function_id
        new_record['revision'] = current['revision'] + 1
        new_record['status'] = 'active'
        new_record['supersedes'] = current['revision']
        new_record['created_at'] = datetime.utcnow().isoformat() + 'Z'
        new_record['spec_hash'] = new_record.get('spec_hash', current.get('spec_hash'))
        new_record['artifact_hash'] = new_record.get('artifact_hash', current.get('artifact_hash'))
        new_record['representation_hash'] = new_record.get('representation_hash', current.get('representation_hash'))
        new_record['trace_hash'] = new_record.get('trace_hash', current.get('trace_hash'))
        new_record['compiler_version'] = new_record.get('compiler_version', current.get('compiler_version'))
        new_record['content_hash'] = new_record.get('content_hash', current.get('content_hash'))

        self._store._records[function_id].append(dict(new_record))
        return dict(new_record)

    def rollback(self, function_id: str, target_revision: int) -> dict:
        """Rollback to a previous revision (restores it as a new revision)."""
        target = self._store.read(function_id, target_revision)
        if target is None:
            raise ValueError(f"revision {target_revision} not found for {function_id}")
        return self.update(function_id, target)

    def supersede(self, function_id: str, new_record: dict) -> dict:
        """Supersede and deactivate old record, create new."""
        new_record = self.update(function_id, new_record)
        return new_record


class N9RegistryValidator:
    VERSION = "0.2.1-candidate"

    def validate(self, store: N9RegistryStore) -> dict:
        """Validate registry integrity."""
        checks = []
        records = store.list()

        # Check for duplicate function_ids
        ids = [r['function_id'] for r in records]
        if len(ids) != len(set(ids)):
            checks.append({"check": "unique_function_ids", "passed": False,
                           "detail": "duplicate function_ids in active records"})
        else:
            checks.append({"check": "unique_function_ids", "passed": True})

        # Check for revision gaps
        for fn_id, revisions in store._records.items():
            revs = [r['revision'] for r in revisions]
            if revs != sorted(revs):
                checks.append({"check": f"revision_order_{fn_id}", "passed": False,
                               "detail": "revisions not in order"})
            if revs != list(range(1, len(revs) + 1)):
                checks.append({"check": f"revision_contiguous_{fn_id}", "passed": False,
                               "detail": f"gap in revisions: {revs}"})

        # Check required fields in all records
        required = ['function_id', 'revision', 'spec_hash', 'artifact_hash',
                    'representation_hash', 'trace_hash', 'compiler_version',
                    'status', 'supersedes', 'content_hash', 'created_at']
        for i, record in enumerate(records):
            missing = [f for f in required if f not in record]
            if missing:
                checks.append({"check": f"required_fields_record_{i}", "passed": False,
                               "detail": f"missing: {missing}"})

        # Check no empty required fields in active records
        for i, record in enumerate(records):
            empty_fields = [f for f in required if f in record and not record[f] and record[f] != 0 and f != 'supersedes']
            if empty_fields:
                checks.append({"check": f"non_empty_fields_{record['function_id']}", "passed": False,
                               "detail": f"empty: {empty_fields}"})

        return {"valid": all(c.get('passed', True) for c in checks), "checks": checks}


# Smoke test
if __name__ == '__main__':
    store = N9RegistryStore()
    updater = N9RegistryUpdater(store)
    validator = N9RegistryValidator()

    record = {
        "function_id": "FN-20260715-0001",
        "spec_hash": "abc123", "artifact_hash": "def456",
        "representation_hash": "ghi789", "trace_hash": "jkl012",
        "compiler_version": "0.2.0", "content_hash": "abc123"
    }
    r1 = store.create(record)
    print("Created:", r1['function_id'], "rev:", r1['revision'])

    r2 = updater.update("FN-20260715-0001", {"spec_hash": "new_hash"})
    print("Updated: rev:", r2['revision'])

    history = store.history("FN-20260715-0001")
    print("History:", len(history), "revisions")

    r3 = updater.rollback("FN-20260715-0001", 1)
    print("Rollback: rev:", r3['revision'])

    vresult = validator.validate(store)
    print("Validation:", vresult['valid'])
    print("N9: ALL OK")
