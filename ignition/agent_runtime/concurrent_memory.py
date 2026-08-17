"""Concurrent operational memory R2 with CAS, lineage and bounded capsules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from agent_kernel.contracts import _id, sha256_json

from .control import FileLock, _atomic_json, utc_now


MEMORY_R2_SCHEMA = "operational-memory-r2"
MEMORY_R2_STATES = frozenset({"ACTIVE", "SUPERSEDED", "TOMBSTONED"})
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "reasoning", "api_key", "access_token", "token", "cookie", "authorization", "secret"})


class MemoryR2Error(ValueError):
    """A concurrent-memory contract or integrity error."""


class MemoryCASConflict(MemoryR2Error):
    """The caller used a stale operational-memory generation."""


class MemoryDuplicateConflict(MemoryR2Error):
    """An event or semantic identity is bound to different content."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise MemoryR2Error(f"{field} must be a non-empty public value")
    return value


def _refs(values: Iterable[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise MemoryR2Error(f"{field} must be a string collection")
    return tuple(sorted({_text(value, f"{field}[]") for value in values}))


def _timestamp(value: Any, field: str) -> str:
    _text(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MemoryR2Error(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise MemoryR2Error(f"{field} must include a timezone")
    return value


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    semantic_key: str
    event_ref: str
    source_run_id: str
    created_at: str
    summary: str
    tags: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    version: int = 0
    state: str = "ACTIVE"
    supersedes: str | None = None
    superseded_by: str | None = None
    integrity_sha256: str | None = None

    def __post_init__(self) -> None:
        for value, field in ((self.memory_id, "memory_id"), (self.semantic_key, "semantic_key"), (self.event_ref, "event_ref"), (self.source_run_id, "source_run_id")):
            _id(value, field)
        _timestamp(self.created_at, "created_at")
        _text(self.summary, "summary")
        object.__setattr__(self, "tags", _refs(self.tags, "tags"))
        object.__setattr__(self, "provenance_refs", _refs(self.provenance_refs, "provenance_refs"))
        if not isinstance(self.version, int) or self.version < 0:
            raise MemoryR2Error("version must be non-negative")
        if self.state not in MEMORY_R2_STATES:
            raise MemoryR2Error(f"unknown memory state: {self.state}")
        if self.supersedes is not None:
            _id(self.supersedes, "supersedes")
        if self.superseded_by is not None:
            _id(self.superseded_by, "superseded_by")
        expected = sha256_json(self._body())
        if self.integrity_sha256 is not None and self.integrity_sha256 != expected:
            raise MemoryR2Error("memory record integrity mismatch")
        object.__setattr__(self, "integrity_sha256", expected)

    def _body(self) -> dict[str, Any]:
        return {"memory_id": self.memory_id, "semantic_key": self.semantic_key, "event_ref": self.event_ref, "source_run_id": self.source_run_id, "created_at": self.created_at, "summary": self.summary, "tags": list(self.tags), "provenance_refs": list(self.provenance_refs), "version": self.version, "state": self.state, "supersedes": self.supersedes, "superseded_by": self.superseded_by}

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "integrity_sha256": self.integrity_sha256}

    def with_integrity(self) -> "MemoryRecord":
        return MemoryRecord(**{**self._body(), "integrity_sha256": None})

    @classmethod
    def create(cls, *, memory_id: str, semantic_key: str, event_ref: str, source_run_id: str, summary: str, tags: Sequence[str] = (), provenance_refs: Sequence[str] = (), created_at: str | None = None, supersedes: str | None = None) -> "MemoryRecord":
        return cls(memory_id, semantic_key, event_ref, source_run_id, created_at or utc_now(), summary, tuple(tags), tuple(provenance_refs), supersedes=supersedes)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MemoryRecord":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise MemoryR2Error("memory record keys mismatch")
        return cls(**dict(data))


def _tombstone(data: Mapping[str, Any]) -> dict[str, Any]:
    required = {"memory_id", "generation", "reason", "original_integrity_sha256", "tombstone_sha256"}
    if set(data) != required:
        raise MemoryR2Error("memory tombstone keys mismatch")
    _id(data["memory_id"], "tombstone.memory_id")
    if not isinstance(data["generation"], int) or data["generation"] <= 0:
        raise MemoryR2Error("tombstone generation is invalid")
    _text(data["reason"], "tombstone.reason")
    for field in ("original_integrity_sha256", "tombstone_sha256"):
        value = data[field]
        if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise MemoryR2Error(f"{field} is not a digest")
    expected = sha256_json({key: data[key] for key in required if key != "tombstone_sha256"})
    if expected != data["tombstone_sha256"]:
        raise MemoryR2Error("tombstone integrity mismatch")
    return dict(data)


class ConcurrentOperationalMemoryStore:
    """Atomic multi-writer operational memory; knowledge authority is excluded."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _read(self) -> tuple[int, int, list[MemoryRecord], list[dict[str, Any]], dict[str, Any] | None]:
        if not self.path.exists():
            return 0, 0, [], [], None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != MEMORY_R2_SCHEMA or not isinstance(data.get("records"), list) or not isinstance(data.get("tombstones"), list):
                raise MemoryR2Error("memory R2 schema mismatch")
            generation = int(data.get("generation", 0))
            next_version = int(data.get("next_version", 0))
            if generation < 0 or next_version < 0:
                raise MemoryR2Error("memory generation/version is invalid")
            records = [MemoryRecord.from_dict(item) for item in data["records"]]
            if len({item.memory_id for item in records}) != len(records) or len({item.event_ref for item in records}) != len(records):
                raise MemoryR2Error("memory R2 contains duplicate ids or event refs")
            tombstones = [_tombstone(item) for item in data["tombstones"]]
            compaction = data.get("compaction")
            if compaction is not None and not isinstance(compaction, dict):
                raise MemoryR2Error("memory compaction metadata is invalid")
            return generation, next_version, records, tombstones, compaction
        except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
            if isinstance(exc, MemoryR2Error):
                raise
            raise MemoryR2Error("memory R2 state is malformed") from exc

    def _write(self, generation: int, next_version: int, records: Sequence[MemoryRecord], tombstones: Sequence[Mapping[str, Any]], compaction: Mapping[str, Any] | None) -> None:
        _atomic_json(self.path, {"schema": MEMORY_R2_SCHEMA, "generation": generation, "next_version": next_version, "records": [item.to_dict() for item in records], "tombstones": [dict(item) for item in tombstones], "compaction": dict(compaction) if compaction else None})

    @staticmethod
    def _cas(generation: int, expected_generation: int | None) -> None:
        if expected_generation is not None and expected_generation != generation:
            raise MemoryCASConflict(f"stale memory generation: expected {expected_generation}, current {generation}")

    def append(self, record: MemoryRecord, *, expected_generation: int | None = None) -> MemoryRecord:
        if not isinstance(record, MemoryRecord) or record.state != "ACTIVE" or record.supersedes is not None:
            raise MemoryR2Error("append accepts a fresh ACTIVE MemoryRecord without supersedes")
        with FileLock(self.lock_path):
            generation, next_version, records, tombstones, compaction = self._read()
            self._cas(generation, expected_generation)
            same_event = next((item for item in records if item.event_ref == record.event_ref), None)
            if same_event is not None:
                if same_event.semantic_key == record.semantic_key and same_event.summary == record.summary and same_event.tags == record.tags:
                    return same_event
                raise MemoryDuplicateConflict("event_ref is bound to different memory content")
            same_semantic = next((item for item in records if item.semantic_key == record.semantic_key and item.state == "ACTIVE"), None)
            if same_semantic is not None:
                if same_semantic.summary == record.summary and same_semantic.tags == record.tags:
                    return same_semantic
                raise MemoryDuplicateConflict("active semantic_key is already represented")
            stored = replace(record, version=next_version + 1, integrity_sha256=None).with_integrity()
            self._write(generation + 1, next_version + 1, (*records, stored), tombstones, compaction)
            return stored

    def supersede(self, memory_id: str, replacement: MemoryRecord, *, expected_generation: int | None = None) -> MemoryRecord:
        _id(memory_id, "memory_id")
        if not isinstance(replacement, MemoryRecord) or replacement.state != "ACTIVE" or replacement.supersedes != memory_id:
            raise MemoryR2Error("replacement must be an ACTIVE record naming the old memory")
        with FileLock(self.lock_path):
            generation, next_version, records, tombstones, compaction = self._read()
            self._cas(generation, expected_generation)
            old = next((item for item in records if item.memory_id == memory_id), None)
            if old is None or old.state != "ACTIVE":
                raise MemoryR2Error("only an active memory may be superseded")
            if any(item.memory_id == replacement.memory_id or item.event_ref == replacement.event_ref for item in records):
                raise MemoryDuplicateConflict("replacement identity already exists")
            if any(item.semantic_key == replacement.semantic_key and item.state == "ACTIVE" and item.memory_id != memory_id for item in records):
                raise MemoryDuplicateConflict("replacement semantic_key is already active")
            retired = replace(old, state="SUPERSEDED", superseded_by=replacement.memory_id, integrity_sha256=None).with_integrity()
            stored = replace(replacement, version=next_version + 1, integrity_sha256=None).with_integrity()
            updated = tuple(retired if item.memory_id == memory_id else item for item in records) + (stored,)
            self._write(generation + 1, next_version + 1, updated, tombstones, compaction)
            return stored

    def tombstone(self, memory_id: str, *, reason: str, expected_generation: int | None = None) -> MemoryRecord:
        _id(memory_id, "memory_id")
        _text(reason, "reason")
        with FileLock(self.lock_path):
            generation, next_version, records, tombstones, compaction = self._read()
            self._cas(generation, expected_generation)
            old = next((item for item in records if item.memory_id == memory_id), None)
            if old is None:
                raise MemoryR2Error("memory does not exist")
            if old.state == "TOMBSTONED":
                return old
            redacted = replace(old, state="TOMBSTONED", summary="[REDACTED_OPERATIONAL_MEMORY]", tags=(), provenance_refs=(), integrity_sha256=None).with_integrity()
            generation_next = generation + 1
            tombstone = {"memory_id": memory_id, "generation": generation_next, "reason": reason, "original_integrity_sha256": old.integrity_sha256, "tombstone_sha256": ""}
            tombstone["tombstone_sha256"] = sha256_json({key: tombstone[key] for key in tombstone if key != "tombstone_sha256"})
            updated = tuple(redacted if item.memory_id == memory_id else item for item in records)
            self._write(generation_next, next_version, updated, (*tombstones, tombstone), compaction)
            return redacted

    def show(self, memory_id: str) -> MemoryRecord:
        _id(memory_id, "memory_id")
        with FileLock(self.lock_path):
            _, _, records, _, _ = self._read()
        for record in records:
            if record.memory_id == memory_id:
                return record
        raise MemoryR2Error("memory does not exist")

    def query(self, *, semantic_key: str | None = None, active_only: bool = True) -> list[MemoryRecord]:
        if semantic_key is not None:
            _id(semantic_key, "semantic_key")
        with FileLock(self.lock_path):
            _, _, records, _, _ = self._read()
        result = [item for item in records if (not active_only or item.state == "ACTIVE") and (semantic_key is None or item.semantic_key == semantic_key)]
        return sorted(result, key=lambda item: (item.semantic_key, item.version, item.memory_id))

    def export_capsule(self, *, max_entries: int = 16, max_chars: int = 4000) -> dict[str, Any]:
        if not isinstance(max_entries, int) or not 0 < max_entries <= 256 or not isinstance(max_chars, int) or not 0 < max_chars <= 100_000:
            raise MemoryR2Error("capsule bounds are invalid")
        with FileLock(self.lock_path):
            generation, _, records, _, _ = self._read()
        selected: list[dict[str, Any]] = []
        used = 0
        for record in sorted((item for item in records if item.state == "ACTIVE"), key=lambda item: (item.semantic_key, item.version, item.memory_id)):
            item = {"memory_id": record.memory_id, "semantic_key": record.semantic_key, "source_run_id": record.source_run_id, "summary": record.summary, "tags": list(record.tags), "provenance_refs": list(record.provenance_refs), "version": record.version, "integrity_sha256": record.integrity_sha256}
            size = len(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            if len(selected) >= max_entries or used + size > max_chars:
                break
            selected.append(item)
            used += size
        capsule: dict[str, Any] = {"schema": "operational-memory-context-capsule-r2", "source": "concurrent-operational-memory", "source_generation": generation, "bounded": True, "entries": selected, "entry_count": len(selected), "char_count": used, "claim_ceiling": "Operational recall only; not knowledge truth, evidence, proof, permission or Owner authority."}
        capsule["capsule_sha256"] = sha256_json(capsule)
        return capsule

    def capsule_is_stale(self, capsule: Mapping[str, Any]) -> bool:
        if not isinstance(capsule, Mapping) or capsule.get("schema") != "operational-memory-context-capsule-r2":
            raise MemoryR2Error("unknown capsule schema")
        digest = capsule.get("capsule_sha256")
        if not isinstance(digest, str) or digest != sha256_json({key: capsule[key] for key in capsule if key != "capsule_sha256"}):
            raise MemoryR2Error("capsule digest mismatch")
        with FileLock(self.lock_path):
            generation, _, _, _, _ = self._read()
        return generation != capsule.get("source_generation")

    def compact(self) -> dict[str, Any]:
        """Return a deterministic projection without rewriting append-only history."""

        with FileLock(self.lock_path):
            generation, _, records, _, _ = self._read()
        latest: dict[str, MemoryRecord] = {}
        for record in sorted(records, key=lambda item: (item.semantic_key, item.version, item.memory_id)):
            latest[record.semantic_key] = record
        kept = sorted((item for item in latest.values() if item.state in {"ACTIVE", "TOMBSTONED"}), key=lambda item: (item.semantic_key, item.version, item.memory_id))
        kept_ids = {item.memory_id for item in kept}
        dropped = sorted((item.memory_id for item in records if item.memory_id not in kept_ids), key=str)
        projection: dict[str, Any] = {"schema": "operational-memory-compaction-r2", "source_generation": generation, "records": [item.to_dict() for item in kept], "dropped_memory_ids": dropped, "claim_ceiling": "Deterministic operational-memory projection only; source history remains the durable record."}
        projection["compaction_sha256"] = sha256_json(projection)
        return projection

    def audit(self) -> dict[str, Any]:
        with FileLock(self.lock_path):
            generation, next_version, records, tombstones, compaction = self._read()
        return {"status": "PASS", "schema": MEMORY_R2_SCHEMA, "generation": generation, "next_version": next_version, "record_count": len(records), "active_count": sum(item.state == "ACTIVE" for item in records), "tombstone_count": len(tombstones), "compaction_present": compaction is not None, "claim_ceiling": "Concurrent operational recall only; not Knowledge truth or authority."}


__all__ = ["ConcurrentOperationalMemoryStore", "MemoryCASConflict", "MemoryDuplicateConflict", "MemoryR2Error", "MemoryRecord", "MEMORY_R2_SCHEMA"]
