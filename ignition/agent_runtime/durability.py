"""Canonical snapshot contracts for OS Durability & Lifecycle R1.

Snapshots are verified replay checkpoints.  The append-only Event Ledger stays
the only canonical operational authority; this module never replaces event
lineage with a mutable snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json

from .control import _atomic_json
from .event_ledger import CanonicalEvent, EventLedger, LedgerCorruptionError, ZERO_HASH


SNAPSHOT_SCHEMA = "ignition-durability-snapshot-r1"
SNAPSHOT_SCHEMA_EPOCH = "os-durability-r1"
_HEX = set("0123456789abcdef")
_FORBIDDEN = ("access_token", "api_key", "client_secret", "password", "hidden reasoning", "chain-of-thought", "raw_prompt", "prompt_body")


class DurabilityError(RuntimeError):
    """Base error for fail-closed durability operations."""


class SnapshotIntegrityError(DurabilityError):
    """A snapshot is partial, tampered, stale at its claimed prefix, or invalid."""


class SnapshotNamespaceError(SnapshotIntegrityError):
    """A snapshot is used outside its declared namespace scope."""


COMPACTION_SCHEMA = "ignition-durability-compaction-receipt-r1"


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in _HEX for char in value):
        raise SnapshotIntegrityError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _public(value: Any, field: str = "value") -> Any:
    if isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in _FORBIDDEN) or "secret" in lowered or "token" in lowered:
            raise SnapshotIntegrityError(f"{field} contains prohibited private material")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _public(value[key], f"{field}.{key}") for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_public(item, f"{field}[]") for item in value]
    raise SnapshotIntegrityError(f"{field} is not JSON-safe")


def _event_hash_chain(events: Sequence[CanonicalEvent]) -> str:
    return sha256_json([event.event_hash for event in events])


@dataclass(frozen=True)
class CanonicalSnapshot:
    snapshot_id: str
    schema_epoch: str
    namespace_scope: str
    ledger_start_sequence: int
    ledger_end_sequence: int
    captured_head_hash: str
    event_hash_chain_sha256: str
    state: Mapping[str, Any]
    state_sha256: str
    active_pack_versions: tuple[str, ...]
    outstanding_reconciliation_refs: tuple[str, ...]
    advisory_soft_governance_versions: tuple[str, ...]
    creation_tool: str
    provenance_refs: tuple[str, ...] = ()
    snapshot_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_id, str) or not self.snapshot_id.strip():
            raise SnapshotIntegrityError("snapshot_id must be non-empty")
        if self.schema_epoch != SNAPSHOT_SCHEMA_EPOCH:
            raise SnapshotIntegrityError(f"unsupported snapshot schema epoch: {self.schema_epoch}")
        if not isinstance(self.namespace_scope, str) or not self.namespace_scope.strip() or "/" in self.namespace_scope:
            raise SnapshotIntegrityError("namespace_scope must be a portable non-empty identifier")
        if self.ledger_start_sequence != 0 or not isinstance(self.ledger_end_sequence, int) or self.ledger_end_sequence < 0:
            raise SnapshotIntegrityError("snapshot sequence range must start at genesis and end at a non-negative exclusive sequence")
        _digest(self.captured_head_hash, "captured_head_hash")
        _digest(self.event_hash_chain_sha256, "event_hash_chain_sha256")
        state = _public(self.state, "state")
        object.__setattr__(self, "state", state)
        if self.state_sha256 != sha256_json(state):
            raise SnapshotIntegrityError("snapshot state digest mismatch")
        for field, values in (("active_pack_versions", self.active_pack_versions), ("outstanding_reconciliation_refs", self.outstanding_reconciliation_refs), ("advisory_soft_governance_versions", self.advisory_soft_governance_versions), ("provenance_refs", self.provenance_refs)):
            if isinstance(values, str) or any(not isinstance(item, str) or not item.strip() for item in values):
                raise SnapshotIntegrityError(f"{field} must contain non-empty strings")
            if len(values) != len(set(values)):
                raise SnapshotIntegrityError(f"{field} must not contain duplicates")
        if not isinstance(self.creation_tool, str) or not self.creation_tool.strip():
            raise SnapshotIntegrityError("creation_tool must be non-empty")
        expected = sha256_json(self._unsigned_dict())
        if self.snapshot_sha256 is not None and self.snapshot_sha256 != expected:
            raise SnapshotIntegrityError("snapshot digest mismatch")
        object.__setattr__(self, "snapshot_sha256", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "snapshot_id": self.snapshot_id,
            "schema_epoch": self.schema_epoch,
            "namespace_scope": self.namespace_scope,
            "ledger_start_sequence": self.ledger_start_sequence,
            "ledger_end_sequence": self.ledger_end_sequence,
            "captured_head_hash": self.captured_head_hash,
            "event_hash_chain_sha256": self.event_hash_chain_sha256,
            "state": self.state,
            "state_sha256": self.state_sha256,
            "active_pack_versions": list(self.active_pack_versions),
            "outstanding_reconciliation_refs": list(self.outstanding_reconciliation_refs),
            "advisory_soft_governance_versions": list(self.advisory_soft_governance_versions),
            "creation_tool": self.creation_tool,
            "provenance_refs": list(self.provenance_refs),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "snapshot_sha256": self.snapshot_sha256}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CanonicalSnapshot":
        required = {"schema", "snapshot_id", "schema_epoch", "namespace_scope", "ledger_start_sequence", "ledger_end_sequence", "captured_head_hash", "event_hash_chain_sha256", "state", "state_sha256", "active_pack_versions", "outstanding_reconciliation_refs", "advisory_soft_governance_versions", "creation_tool", "provenance_refs", "snapshot_sha256"}
        if not isinstance(data, Mapping) or set(data) != required or data.get("schema") != SNAPSHOT_SCHEMA:
            raise SnapshotIntegrityError("snapshot schema or keys mismatch")
        return cls(
            snapshot_id=data["snapshot_id"], schema_epoch=data["schema_epoch"], namespace_scope=data["namespace_scope"],
            ledger_start_sequence=data["ledger_start_sequence"], ledger_end_sequence=data["ledger_end_sequence"],
            captured_head_hash=data["captured_head_hash"], event_hash_chain_sha256=data["event_hash_chain_sha256"],
            state=data["state"], state_sha256=data["state_sha256"], active_pack_versions=tuple(data["active_pack_versions"]),
            outstanding_reconciliation_refs=tuple(data["outstanding_reconciliation_refs"]),
            advisory_soft_governance_versions=tuple(data["advisory_soft_governance_versions"]),
            creation_tool=data["creation_tool"], provenance_refs=tuple(data["provenance_refs"]), snapshot_sha256=data["snapshot_sha256"],
        )


class CanonicalSnapshotStore:
    """Create, persist and restore verified snapshots against an EventLedger."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def create(
        self,
        ledger: EventLedger,
        *,
        snapshot_id: str,
        namespace_scope: str = "global",
        active_pack_versions: Sequence[str] = (),
        outstanding_reconciliation_refs: Sequence[str] = (),
        advisory_soft_governance_versions: Sequence[str] = (),
        creation_tool: str = "ignition.durability.snapshot-r1",
        provenance_refs: Sequence[str] = (),
    ) -> CanonicalSnapshot:
        events = ledger.events()
        state = ledger.replay()
        snapshot = CanonicalSnapshot(
            snapshot_id=snapshot_id, schema_epoch=SNAPSHOT_SCHEMA_EPOCH, namespace_scope=namespace_scope,
            ledger_start_sequence=0, ledger_end_sequence=len(events),
            captured_head_hash=events[-1].event_hash if events else ZERO_HASH,
            event_hash_chain_sha256=_event_hash_chain(events), state=state,
            state_sha256=sha256_json(state), active_pack_versions=tuple(sorted(active_pack_versions)),
            outstanding_reconciliation_refs=tuple(sorted(outstanding_reconciliation_refs)),
            advisory_soft_governance_versions=tuple(sorted(advisory_soft_governance_versions)),
            creation_tool=creation_tool, provenance_refs=tuple(sorted(provenance_refs)),
        )
        return snapshot

    def write(self, snapshot: CanonicalSnapshot) -> CanonicalSnapshot:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_json(self.path, snapshot.to_dict())
        return snapshot

    def read(self, path: str | Path | None = None) -> CanonicalSnapshot:
        target = Path(path) if path is not None else self.path
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            return CanonicalSnapshot.from_dict(data)
        except SnapshotIntegrityError:
            raise
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise SnapshotIntegrityError("snapshot is unreadable") from exc

    @staticmethod
    def _validate_prefix(ledger: EventLedger, snapshot: CanonicalSnapshot, *, namespace_scope: str | None = None) -> list[CanonicalEvent]:
        if namespace_scope is not None and namespace_scope != snapshot.namespace_scope:
            raise SnapshotNamespaceError("snapshot namespace does not match restore namespace")
        events = ledger.events()
        end = snapshot.ledger_end_sequence
        if end > len(events):
            raise SnapshotIntegrityError("snapshot claims events not present in the ledger")
        prefix = events[:end]
        expected_head = prefix[-1].event_hash if prefix else ZERO_HASH
        if expected_head != snapshot.captured_head_hash:
            raise SnapshotIntegrityError("snapshot head is not a ledger prefix")
        if _event_hash_chain(prefix) != snapshot.event_hash_chain_sha256:
            raise SnapshotIntegrityError("snapshot event hash-chain digest mismatch")
        return events[end:]

    def restore(self, ledger: EventLedger, snapshot: CanonicalSnapshot | None = None, *, namespace_scope: str | None = None) -> dict[str, Any]:
        snapshot = snapshot or self.read()
        tail = self._validate_prefix(ledger, snapshot, namespace_scope=namespace_scope)
        rebuilt: dict[str, Any] = json.loads(json.dumps(snapshot.state, ensure_ascii=False))
        rebuilt.pop("event_count", None)
        rebuilt.pop("head_hash", None)
        for event in tail:
            EventLedger._default_reduce(rebuilt, event)
        rebuilt["event_count"] = len(ledger.events())
        current = ledger.events()
        rebuilt["head_hash"] = current[-1].event_hash if current else ZERO_HASH
        full = ledger.replay()
        if rebuilt != full:
            raise SnapshotIntegrityError("snapshot plus tail replay differs from full genesis replay")
        return rebuilt

    def audit(self, ledger: EventLedger, snapshot: CanonicalSnapshot | None = None, *, namespace_scope: str | None = None) -> dict[str, Any]:
        snapshot = snapshot or self.read()
        tail = self._validate_prefix(ledger, snapshot, namespace_scope=namespace_scope)
        restored = self.restore(ledger, snapshot, namespace_scope=namespace_scope)
        return {
            "status": "PASS",
            "schema": SNAPSHOT_SCHEMA,
            "snapshot_id": snapshot.snapshot_id,
            "captured_events": snapshot.ledger_end_sequence,
            "tail_events": len(tail),
            "full_event_count": len(ledger.events()),
            "snapshot_state_sha256": snapshot.state_sha256,
            "restored_state_sha256": sha256_json(restored),
            "replay_equivalent": restored == ledger.replay(),
            "namespace_scope": snapshot.namespace_scope,
            "authority": "event-ledger-only; snapshot-is-recovery-accelerator",
        }


@dataclass(frozen=True)
class CompactionPolicy:
    """A bounded policy that never permits canonical lineage deletion."""

    snapshot_interval_events: int = 100
    derived_cache_keep: int = 2
    advisory_artifact_keep: int = 2
    preserve_event_lineage: bool = True
    preserve_unresolved_reconciliation: bool = True
    preserve_external_pointer_digests: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_interval_events, int) or self.snapshot_interval_events <= 0:
            raise DurabilityError("snapshot_interval_events must be positive")
        if not isinstance(self.derived_cache_keep, int) or self.derived_cache_keep < 0:
            raise DurabilityError("derived_cache_keep must be non-negative")
        if not isinstance(self.advisory_artifact_keep, int) or self.advisory_artifact_keep < 0:
            raise DurabilityError("advisory_artifact_keep must be non-negative")
        if not self.preserve_event_lineage:
            raise DurabilityError("canonical event lineage deletion is forbidden")
        if not self.preserve_unresolved_reconciliation:
            raise DurabilityError("unresolved reconciliation deletion is forbidden")
        if not self.preserve_external_pointer_digests:
            raise DurabilityError("external pointer digest deletion is forbidden")

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_interval_events": self.snapshot_interval_events,
            "derived_cache_keep": self.derived_cache_keep,
            "advisory_artifact_keep": self.advisory_artifact_keep,
            "preserve_event_lineage": self.preserve_event_lineage,
            "preserve_unresolved_reconciliation": self.preserve_unresolved_reconciliation,
            "preserve_external_pointer_digests": self.preserve_external_pointer_digests,
        }


@dataclass(frozen=True)
class CompactionReceipt:
    compaction_id: str
    source_event_count: int
    source_head_hash: str
    snapshot_id: str
    policy_sha256: str
    derived_cache_prune_candidates: int
    advisory_artifact_prune_candidates: int
    unresolved_reconciliation_refs_preserved: tuple[str, ...]
    external_pointer_digests_preserved: tuple[str, ...]
    event_lineage_preserved: bool = True
    status: str = "COMPLETED_WITH_LINEAGE_PRESERVED"
    receipt_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.compaction_id or not self.snapshot_id:
            raise DurabilityError("compaction and snapshot IDs must be non-empty")
        if not isinstance(self.source_event_count, int) or self.source_event_count < 0:
            raise DurabilityError("source_event_count must be non-negative")
        _digest(self.source_head_hash, "source_head_hash")
        _digest(self.policy_sha256, "policy_sha256")
        if self.derived_cache_prune_candidates < 0 or self.advisory_artifact_prune_candidates < 0:
            raise DurabilityError("prune candidate counts must be non-negative")
        if not self.event_lineage_preserved or self.status != "COMPLETED_WITH_LINEAGE_PRESERVED":
            raise DurabilityError("compaction receipt must preserve lineage")
        for values in (self.unresolved_reconciliation_refs_preserved, self.external_pointer_digests_preserved):
            if len(values) != len(set(values)):
                raise DurabilityError("preserved references must be unique")
        expected = sha256_json(self._unsigned_dict())
        if self.receipt_sha256 is not None and self.receipt_sha256 != expected:
            raise DurabilityError("compaction receipt digest mismatch")
        object.__setattr__(self, "receipt_sha256", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": COMPACTION_SCHEMA,
            "compaction_id": self.compaction_id,
            "source_event_count": self.source_event_count,
            "source_head_hash": self.source_head_hash,
            "snapshot_id": self.snapshot_id,
            "policy_sha256": self.policy_sha256,
            "derived_cache_prune_candidates": self.derived_cache_prune_candidates,
            "advisory_artifact_prune_candidates": self.advisory_artifact_prune_candidates,
            "unresolved_reconciliation_refs_preserved": list(self.unresolved_reconciliation_refs_preserved),
            "external_pointer_digests_preserved": list(self.external_pointer_digests_preserved),
            "event_lineage_preserved": self.event_lineage_preserved,
            "status": self.status,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "receipt_sha256": self.receipt_sha256}


class SnapshotChainStore:
    """Keep multiple immutable checkpoints and choose a trusted prefix."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def write(self, snapshot: CanonicalSnapshot) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{snapshot.snapshot_id}.json"
        _atomic_json(path, snapshot.to_dict())
        return path

    def paths(self) -> list[Path]:
        return sorted(self.directory.glob("*.json"))

    def read_all(self) -> list[CanonicalSnapshot]:
        snapshots: list[CanonicalSnapshot] = []
        for path in self.paths():
            snapshots.append(CanonicalSnapshotStore(path).read())
        return snapshots

    def select_trusted(self, ledger: EventLedger, *, namespace_scope: str | None = None) -> tuple[CanonicalSnapshot, Path]:
        candidates: list[tuple[CanonicalSnapshot, Path]] = []
        for path in self.paths():
            try:
                snapshot = CanonicalSnapshotStore(path).read()
                CanonicalSnapshotStore._validate_prefix(ledger, snapshot, namespace_scope=namespace_scope)
                candidates.append((snapshot, path))
            except (SnapshotIntegrityError, OSError, json.JSONDecodeError):
                continue
        if not candidates:
            raise SnapshotIntegrityError("no trusted snapshot prefix is available")
        return max(candidates, key=lambda item: (item[0].ledger_end_sequence, item[0].snapshot_id))

    def restore_with_fallback(self, ledger: EventLedger, *, namespace_scope: str | None = None) -> tuple[dict[str, Any], CanonicalSnapshot, Path]:
        snapshot, path = self.select_trusted(ledger, namespace_scope=namespace_scope)
        restored = CanonicalSnapshotStore(path).restore(ledger, snapshot, namespace_scope=namespace_scope)
        return restored, snapshot, path


class DurabilityCompactor:
    """Create bounded checkpoints and receipts without mutating canonical events."""

    def __init__(self, chain: SnapshotChainStore) -> None:
        self.chain = chain

    def compact(
        self,
        ledger: EventLedger,
        *,
        compaction_id: str,
        snapshot_id: str,
        policy: CompactionPolicy | None = None,
        namespace_scope: str = "global",
        active_pack_versions: Sequence[str] = (),
        outstanding_reconciliation_refs: Sequence[str] = (),
        advisory_soft_governance_versions: Sequence[str] = (),
        external_pointer_digests: Sequence[str] = (),
        derived_cache_entries: Sequence[str] = (),
        advisory_artifacts: Sequence[str] = (),
    ) -> tuple[CanonicalSnapshot, CompactionReceipt]:
        policy = policy or CompactionPolicy()
        before = ledger.events()
        snapshot = CanonicalSnapshotStore(self.chain.directory / f"{snapshot_id}.json").create(
            ledger, snapshot_id=snapshot_id, namespace_scope=namespace_scope,
            active_pack_versions=active_pack_versions,
            outstanding_reconciliation_refs=outstanding_reconciliation_refs,
            advisory_soft_governance_versions=advisory_soft_governance_versions,
        )
        self.chain.write(snapshot)
        after = ledger.events()
        if [event.event_hash for event in before] != [event.event_hash for event in after]:
            raise DurabilityError("compaction changed canonical event lineage")
        receipt = CompactionReceipt(
            compaction_id=compaction_id, source_event_count=len(before),
            source_head_hash=before[-1].event_hash if before else ZERO_HASH,
            snapshot_id=snapshot_id, policy_sha256=sha256_json(policy.to_dict()),
            derived_cache_prune_candidates=max(0, len(derived_cache_entries) - policy.derived_cache_keep),
            advisory_artifact_prune_candidates=max(0, len(advisory_artifacts) - policy.advisory_artifact_keep),
            unresolved_reconciliation_refs_preserved=tuple(sorted(set(outstanding_reconciliation_refs))),
            external_pointer_digests_preserved=tuple(sorted(set(external_pointer_digests))),
        )
        return snapshot, receipt


__all__ = [
    "CanonicalSnapshot", "CanonicalSnapshotStore", "CompactionPolicy", "CompactionReceipt",
    "COMPACTION_SCHEMA", "DurabilityCompactor", "DurabilityError", "SNAPSHOT_SCHEMA",
    "SNAPSHOT_SCHEMA_EPOCH", "SnapshotChainStore", "SnapshotIntegrityError", "SnapshotNamespaceError",
]
