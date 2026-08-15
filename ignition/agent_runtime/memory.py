"""Bounded cross-run operational memory for Agent Runtime R1.

This store is operational recall, not a truth registry.  It accepts only
public structured summaries and references, keeps an integrity digest, and
supports explicit supersession and redacting forget/expire tombstones.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import _id, _string, _tuple_strings, sha256_json

from .control import FileLock, _atomic_json, utc_now


MEMORY_SCHEMA = "operational-memory-r1"
MEMORY_TYPES = frozenset({
    "EPISODIC",
    "PROCEDURAL",
    "OWNER_FEEDBACK",
    "FAILURE",
    "ROLLBACK",
    "APPROVAL",
    "PACK_USAGE",
    "UNRESOLVED_CONTINUATION",
})
RETENTION_CLASSES = frozenset({"RUN", "SHORT", "LONG", "UNTIL_FORGOTTEN"})
VISIBILITIES = frozenset({"RUN_SCOPED", "OWNER_VISIBLE", "SHARED_OPERATIONAL"})
SENSITIVITY_CLASSES = frozenset({"PUBLIC_OPERATIONAL", "INTERNAL_OPERATIONAL", "SENSITIVE_REFERENCE"})
FORGET_POLICIES = frozenset({"MANUAL", "EXPIRES_AT", "OWNER_REQUEST", "RUN_END"})
SUPERSESSION_STATES = frozenset({"ACTIVE", "SUPERSEDED", "FORGOTTEN", "EXPIRED"})
SENSITIVE_MARKERS = (
    "api_key",
    "access_token",
    "bearer ",
    "client_secret",
    "password",
    "private model reasoning",
    "hidden reasoning",
    "chain-of-thought",
    "chain of thought",
)
PROMPT_FIELD_MARKERS = ("full_prompt", "raw_prompt", "prompt_text", "prompt_body", "completion_text")


class MemoryStoreError(ValueError):
    """Raised when operational memory cannot be safely validated or changed."""


def _public_string(value: Any, field: str) -> str:
    value = _string(value, field)
    lowered = value.casefold()
    if "prompt" in lowered or any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise MemoryStoreError(f"{field} contains a forbidden secret or hidden-reasoning marker")
    return value


def _public_strings(value: Any, field: str) -> tuple[str, ...]:
    values = _tuple_strings(value, field)
    return tuple(_public_string(item, f"{field}[]") for item in values)


def _iso_timestamp(value: Any, field: str) -> str:
    value = _public_string(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MemoryStoreError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise MemoryStoreError(f"{field} must include a timezone")
    return value


def _optional_timestamp(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _iso_timestamp(value, field)


def _entry_digest(data: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "integrity_sha256"}
    return sha256_json(unsigned)


@dataclass(frozen=True)
class MemoryEntry:
    memory_id: str
    memory_type: str
    source_run_id: str
    created_at: str
    retention_class: str
    visibility: str
    sensitivity_class: str
    provenance_refs: tuple[str, ...]
    owner_feedback_refs: tuple[str, ...]
    summary: str
    tags: tuple[str, ...]
    forget_policy: str
    expires_at: str | None = None
    supersession_state: str = "ACTIVE"
    supersedes: str | None = None
    superseded_by: str | None = None
    related_refs: tuple[str, ...] = ()
    integrity_sha256: str = ""

    def __post_init__(self) -> None:
        _id(self.memory_id, "memory_id")
        if self.memory_type not in MEMORY_TYPES:
            raise MemoryStoreError(f"unknown memory_type: {self.memory_type}")
        _id(self.source_run_id, "source_run_id")
        _iso_timestamp(self.created_at, "created_at")
        if self.retention_class not in RETENTION_CLASSES:
            raise MemoryStoreError(f"unknown retention_class: {self.retention_class}")
        if self.visibility not in VISIBILITIES:
            raise MemoryStoreError(f"unknown visibility: {self.visibility}")
        if self.sensitivity_class not in SENSITIVITY_CLASSES:
            raise MemoryStoreError(f"unknown sensitivity_class: {self.sensitivity_class}")
        object.__setattr__(self, "provenance_refs", _public_strings(self.provenance_refs, "provenance_refs"))
        object.__setattr__(self, "owner_feedback_refs", _public_strings(self.owner_feedback_refs, "owner_feedback_refs"))
        object.__setattr__(self, "related_refs", _public_strings(self.related_refs, "related_refs"))
        _public_string(self.summary, "summary")
        object.__setattr__(self, "tags", _public_strings(self.tags, "tags"))
        if self.forget_policy not in FORGET_POLICIES:
            raise MemoryStoreError(f"unknown forget_policy: {self.forget_policy}")
        object.__setattr__(self, "expires_at", _optional_timestamp(self.expires_at, "expires_at"))
        if self.supersession_state not in SUPERSESSION_STATES:
            raise MemoryStoreError(f"unknown supersession_state: {self.supersession_state}")
        if self.supersedes is not None:
            _id(self.supersedes, "supersedes")
        if self.superseded_by is not None:
            _id(self.superseded_by, "superseded_by")
        if self.integrity_sha256 and not re.fullmatch(r"[0-9a-f]{64}", self.integrity_sha256):
            raise MemoryStoreError("integrity_sha256 must be a lowercase SHA-256 digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "source_run_id": self.source_run_id,
            "created_at": self.created_at,
            "retention_class": self.retention_class,
            "visibility": self.visibility,
            "sensitivity_class": self.sensitivity_class,
            "provenance_refs": list(self.provenance_refs),
            "owner_feedback_refs": list(self.owner_feedback_refs),
            "summary": self.summary,
            "tags": list(self.tags),
            "forget_policy": self.forget_policy,
            "expires_at": self.expires_at,
            "supersession_state": self.supersession_state,
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
            "related_refs": list(self.related_refs),
            "integrity_sha256": self.integrity_sha256,
        }

    def with_integrity(self) -> "MemoryEntry":
        data = self.to_dict()
        data["integrity_sha256"] = _entry_digest(data)
        return MemoryEntry.from_dict(data, verify_integrity=False)

    @classmethod
    def create(
        cls,
        *,
        memory_id: str,
        memory_type: str,
        source_run_id: str,
        summary: str,
        provenance_refs: Sequence[str] = (),
        owner_feedback_refs: Sequence[str] = (),
        tags: Sequence[str] = (),
        retention_class: str = "LONG",
        visibility: str = "SHARED_OPERATIONAL",
        sensitivity_class: str = "INTERNAL_OPERATIONAL",
        forget_policy: str = "MANUAL",
        expires_at: str | None = None,
        supersedes: str | None = None,
        related_refs: Sequence[str] = (),
        created_at: str | None = None,
    ) -> "MemoryEntry":
        entry = cls(
            memory_id=memory_id,
            memory_type=memory_type,
            source_run_id=source_run_id,
            created_at=created_at or utc_now(),
            retention_class=retention_class,
            visibility=visibility,
            sensitivity_class=sensitivity_class,
            provenance_refs=tuple(provenance_refs),
            owner_feedback_refs=tuple(owner_feedback_refs),
            summary=summary,
            tags=tuple(tags),
            forget_policy=forget_policy,
            expires_at=expires_at,
            supersedes=supersedes,
            related_refs=tuple(related_refs),
        )
        return entry.with_integrity()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], *, verify_integrity: bool = True) -> "MemoryEntry":
        required = {
            "memory_id", "memory_type", "source_run_id", "created_at", "retention_class", "visibility",
            "sensitivity_class", "provenance_refs", "owner_feedback_refs", "summary", "tags", "forget_policy",
            "expires_at", "supersession_state", "supersedes", "superseded_by", "related_refs", "integrity_sha256",
        }
        if set(data) != required:
            raise MemoryStoreError("MemoryEntry keys mismatch")
        entry = cls(**data)
        if verify_integrity and entry.integrity_sha256 != _entry_digest(entry.to_dict()):
            raise MemoryStoreError(f"memory integrity mismatch: {entry.memory_id}")
        return entry


class OperationalMemoryStore:
    """Locked JSON store with bounded operational recall and redacting forget."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _read(self) -> tuple[list[MemoryEntry], list[dict[str, Any]]]:
        if not self.path.exists():
            return [], []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != MEMORY_SCHEMA or not isinstance(data.get("entries"), list) or not isinstance(data.get("tombstones"), list):
                raise MemoryStoreError("operational memory store schema mismatch")
            entries = [MemoryEntry.from_dict(item) for item in data["entries"]]
            tombstones = [dict(item) for item in data["tombstones"]]
            return entries, tombstones
        except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
            raise MemoryStoreError("operational memory store is malformed") from exc

    def _write(self, entries: Sequence[MemoryEntry], tombstones: Sequence[Mapping[str, Any]]) -> None:
        _atomic_json(self.path, {"schema": MEMORY_SCHEMA, "entries": [entry.to_dict() for entry in entries], "tombstones": [dict(item) for item in tombstones]})

    def audit(self) -> dict[str, Any]:
        with FileLock(self.lock_path):
            entries, tombstones = self._read()
        return {
            "status": "PASS",
            "schema": MEMORY_SCHEMA,
            "entry_count": len(entries),
            "tombstone_count": len(tombstones),
            "active_count": sum(entry.supersession_state == "ACTIVE" for entry in entries),
        }

    def append(self, entry: MemoryEntry) -> MemoryEntry:
        entry = entry.with_integrity()
        with FileLock(self.lock_path):
            entries, tombstones = self._read()
            if any(existing.memory_id == entry.memory_id for existing in entries):
                raise MemoryStoreError(f"memory_id already exists: {entry.memory_id}")
            entries.append(entry)
            self._write(entries, tombstones)
        return entry

    def show(self, memory_id: str) -> MemoryEntry:
        _id(memory_id, "memory_id")
        with FileLock(self.lock_path):
            entries, _ = self._read()
        for entry in entries:
            if entry.memory_id == memory_id:
                return entry
        raise MemoryStoreError(f"unknown memory_id: {memory_id}")

    def query(
        self,
        *,
        memory_type: str | None = None,
        source_run_id: str | None = None,
        tag: str | None = None,
        visibility: str | None = None,
        active_only: bool = True,
    ) -> list[MemoryEntry]:
        with FileLock(self.lock_path):
            entries, _ = self._read()
        if memory_type is not None and memory_type not in MEMORY_TYPES:
            raise MemoryStoreError(f"unknown memory_type: {memory_type}")
        if source_run_id is not None:
            _id(source_run_id, "source_run_id")
        if visibility is not None and visibility not in VISIBILITIES:
            raise MemoryStoreError(f"unknown visibility: {visibility}")
        result = []
        for entry in entries:
            if active_only and entry.supersession_state != "ACTIVE":
                continue
            if memory_type is not None and entry.memory_type != memory_type:
                continue
            if source_run_id is not None and entry.source_run_id != source_run_id:
                continue
            if tag is not None and tag not in entry.tags:
                continue
            if visibility is not None and entry.visibility != visibility:
                continue
            result.append(entry)
        return sorted(result, key=lambda item: (item.created_at, item.memory_id))

    def supersede(self, memory_id: str, replacement: MemoryEntry) -> MemoryEntry:
        if replacement.supersedes != memory_id:
            raise MemoryStoreError("replacement must name the memory it supersedes")
        replacement = replacement.with_integrity()
        with FileLock(self.lock_path):
            entries, tombstones = self._read()
            index = next((index for index, item in enumerate(entries) if item.memory_id == memory_id), None)
            if index is None:
                raise MemoryStoreError(f"unknown memory_id: {memory_id}")
            if any(item.memory_id == replacement.memory_id for item in entries):
                raise MemoryStoreError(f"memory_id already exists: {replacement.memory_id}")
            old = entries[index]
            if old.supersession_state != "ACTIVE":
                raise MemoryStoreError(f"memory is not active: {memory_id}")
            entries[index] = replace(old, supersession_state="SUPERSEDED", superseded_by=replacement.memory_id).with_integrity()
            entries.append(replacement)
            self._write(entries, tombstones)
        return replacement

    def _redact(self, memory_id: str, state: str, reason: str) -> dict[str, Any]:
        _id(memory_id, "memory_id")
        _public_string(reason, "reason")
        now = utc_now()
        with FileLock(self.lock_path):
            entries, tombstones = self._read()
            index = next((index for index, item in enumerate(entries) if item.memory_id == memory_id), None)
            if index is None:
                raise MemoryStoreError(f"unknown memory_id: {memory_id}")
            old = entries[index]
            if old.supersession_state in {"FORGOTTEN", "EXPIRED"}:
                return {"memory_id": memory_id, "status": old.supersession_state}
            redacted = replace(
                old,
                summary="[REDACTED_OPERATIONAL_MEMORY]",
                provenance_refs=(),
                owner_feedback_refs=(),
                tags=(),
                related_refs=(),
                supersession_state=state,
            ).with_integrity()
            entries[index] = redacted
            tombstone = {
                "memory_id": memory_id,
                "action": state,
                "reason": reason,
                "at": now,
                "original_integrity_sha256": old.integrity_sha256,
                "tombstone_sha256": hashlib.sha256(f"{memory_id}:{state}:{now}:{reason}".encode("utf-8")).hexdigest(),
            }
            tombstones.append(tombstone)
            self._write(entries, tombstones)
        return {"memory_id": memory_id, "status": state, "tombstone_sha256": tombstone["tombstone_sha256"]}

    def forget(self, memory_id: str, *, reason: str = "explicit forget request") -> dict[str, Any]:
        return self._redact(memory_id, "FORGOTTEN", reason)

    def expire(self, *, now: str | None = None) -> list[dict[str, Any]]:
        current = datetime.fromisoformat((now or utc_now()).replace("Z", "+00:00"))
        with FileLock(self.lock_path):
            entries, _ = self._read()
            due = [entry.memory_id for entry in entries if entry.supersession_state == "ACTIVE" and entry.expires_at is not None and datetime.fromisoformat(entry.expires_at.replace("Z", "+00:00")) <= current]
        return [self._redact(memory_id, "EXPIRED", "expiry policy reached") for memory_id in due]

    def export_capsule(
        self,
        *,
        max_entries: int = 16,
        max_chars: int = 4000,
        source_run_id: str | None = None,
        tags: Sequence[str] = (),
    ) -> dict[str, Any]:
        if not isinstance(max_entries, int) or max_entries <= 0 or max_entries > 256:
            raise MemoryStoreError("max_entries must be between 1 and 256")
        if not isinstance(max_chars, int) or max_chars <= 0 or max_chars > 100_000:
            raise MemoryStoreError("max_chars must be between 1 and 100000")
        entries = self.query(source_run_id=source_run_id, active_only=True)
        tag_set = set(_public_strings(tuple(tags), "tags"))
        if tag_set:
            entries = [entry for entry in entries if tag_set.intersection(entry.tags)]
        selected: list[dict[str, Any]] = []
        used = 0
        for entry in entries:
            item = {
                "memory_id": entry.memory_id,
                "memory_type": entry.memory_type,
                "source_run_id": entry.source_run_id,
                "summary": entry.summary,
                "tags": list(entry.tags),
                "provenance_refs": list(entry.provenance_refs),
                "integrity_sha256": entry.integrity_sha256,
            }
            size = len(json.dumps(item, ensure_ascii=False, sort_keys=True))
            if len(selected) >= max_entries or used + size > max_chars:
                break
            selected.append(item)
            used += size
        capsule = {
            "schema": "operational-memory-context-capsule-r1",
            "source": "operational-memory",
            "claim_ceiling": "Operational recall only; not knowledge truth, evidence, proof, or permission authority.",
            "bounded": True,
            "entries": selected,
            "entry_count": len(selected),
            "char_count": used,
        }
        capsule["capsule_sha256"] = sha256_json(capsule)
        return capsule
