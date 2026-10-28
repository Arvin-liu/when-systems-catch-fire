"""Transactional, version-pinned lifecycle for Domain Packs."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json

from .control import _atomic_json
from .pack_registry import PackManifest, PackRegistryError


PACK_LIFECYCLE_SCHEMA = "ignition-durability-pack-lifecycle-r1"
PACK_STATES = frozenset({"DISCOVERED", "STAGED", "VALIDATED", "ACTIVATED", "DRAINING", "DEACTIVATED", "ROLLED_BACK", "QUARANTINED"})
ADVISORY_OVERLAY_ROLE = "ADVISORY_ONLY_CROSS_CUTTING_OVERLAY"


class PackLifecycleError(ValueError):
    """Raised when a Pack lifecycle transition is unsafe."""


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or ".." in value or "/" in value:
        raise PackLifecycleError(f"{field} must be a portable identifier")
    return value


@dataclass(frozen=True)
class PackLifecycleRecord:
    pack_id: str
    version: str
    state: str
    manifest_digest: str
    authority_ceiling: str = "DECLARED_PACK_SCOPE_ONLY"
    role: str = "DOMAIN_PACK"
    active_run_ids: tuple[str, ...] = ()
    validation_receipt_ref: str | None = None
    last_known_good_version: str | None = None

    def __post_init__(self) -> None:
        _id(self.pack_id, "pack_id")
        _id(self.version, "version")
        if self.state not in PACK_STATES:
            raise PackLifecycleError("unknown Pack lifecycle state")
        if not isinstance(self.manifest_digest, str) or len(self.manifest_digest) != 64 or any(char not in "0123456789abcdef" for char in self.manifest_digest):
            raise PackLifecycleError("manifest_digest must be a lowercase SHA-256 digest")
        if self.authority_ceiling != "DECLARED_PACK_SCOPE_ONLY":
            raise PackLifecycleError("Pack lifecycle cannot widen authority")
        if self.role not in {"DOMAIN_PACK", ADVISORY_OVERLAY_ROLE}:
            raise PackLifecycleError("unknown Pack lifecycle role")
        if len(self.active_run_ids) != len(set(self.active_run_ids)) or any(not isinstance(run_id, str) or not run_id.strip() for run_id in self.active_run_ids):
            raise PackLifecycleError("active run IDs must be unique public references")

    def to_dict(self) -> dict[str, Any]:
        return {"pack_id": self.pack_id, "version": self.version, "state": self.state, "manifest_digest": self.manifest_digest, "authority_ceiling": self.authority_ceiling, "role": self.role, "active_run_ids": list(self.active_run_ids), "validation_receipt_ref": self.validation_receipt_ref, "last_known_good_version": self.last_known_good_version}


@dataclass(frozen=True)
class PackRunPin:
    run_id: str
    pack_id: str
    version: str
    pin_digest: str | None = None

    def __post_init__(self) -> None:
        _id(self.run_id, "run_id")
        _id(self.pack_id, "pack_id")
        _id(self.version, "version")
        expected = sha256_json({"run_id": self.run_id, "pack_id": self.pack_id, "version": self.version})
        if self.pin_digest is not None and self.pin_digest != expected:
            raise PackLifecycleError("run pin digest mismatch")
        object.__setattr__(self, "pin_digest", expected)


@dataclass(frozen=True)
class PackLifecycleReceipt:
    sequence: int
    pack_id: str
    version: str
    from_state: str | None
    to_state: str
    reason: str
    active_run_ids: tuple[str, ...]
    receipt_digest: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0 or self.to_state not in PACK_STATES:
            raise PackLifecycleError("invalid lifecycle receipt")
        if self.from_state is not None and self.from_state not in PACK_STATES:
            raise PackLifecycleError("invalid lifecycle receipt source state")
        if not self.reason.strip():
            raise PackLifecycleError("lifecycle receipt reason is required")
        expected = sha256_json(self._unsigned_dict())
        if self.receipt_digest is not None and self.receipt_digest != expected:
            raise PackLifecycleError("lifecycle receipt digest mismatch")
        object.__setattr__(self, "receipt_digest", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {"schema": PACK_LIFECYCLE_SCHEMA, "sequence": self.sequence, "pack_id": self.pack_id, "version": self.version, "from_state": self.from_state, "to_state": self.to_state, "reason": self.reason, "active_run_ids": list(self.active_run_ids)}

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "receipt_digest": self.receipt_digest}


class PackLifecycleManager:
    """A small atomic state store around declarative Pack manifests."""

    def __init__(self, state_path: str | Path) -> None:
        self.state_path = Path(state_path)
        self.receipt_path = self.state_path.with_name(self.state_path.stem + "-receipts.jsonl")
        self._records: dict[tuple[str, str], PackLifecycleRecord] = {}
        self._active: dict[str, str] = {}
        self._pins: dict[str, PackRunPin] = {}
        self._receipts: list[PackLifecycleReceipt] = []

    def _persist(self) -> None:
        _atomic_json(self.state_path, {"schema": PACK_LIFECYCLE_SCHEMA, "records": [record.to_dict() for record in sorted(self._records.values(), key=lambda item: (item.pack_id, item.version))], "active": dict(sorted(self._active.items())), "run_pins": {key: pin.__dict__ for key, pin in sorted(self._pins.items())}})
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        with self.receipt_path.open("w", encoding="utf-8") as handle:
            for receipt in self._receipts:
                handle.write(json.dumps(receipt.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

    def _receipt(self, record: PackLifecycleRecord, to_state: str, reason: str, from_state: str | None = None) -> PackLifecycleReceipt:
        receipt = PackLifecycleReceipt(len(self._receipts), record.pack_id, record.version, from_state if from_state is not None else record.state, to_state, reason, record.active_run_ids)
        self._receipts.append(receipt)
        return receipt

    def discover(self, manifest: PackManifest, *, role: str = "DOMAIN_PACK") -> PackLifecycleRecord:
        if role == ADVISORY_OVERLAY_ROLE and manifest.domain != "advisory":
            raise PackLifecycleError("advisory overlay role cannot be inferred for a Domain Pack")
        key = (manifest.pack_id, manifest.version)
        digest = sha256_json(manifest.to_dict())
        existing = self._records.get(key)
        if existing:
            return existing
        record = PackLifecycleRecord(manifest.pack_id, manifest.version, "DISCOVERED", digest, role=role)
        self._records[key] = record
        self._receipt(record, "DISCOVERED", "manifest discovered", from_state=None)
        self._persist()
        return record

    def stage(self, pack_id: str, version: str) -> PackLifecycleRecord:
        record = self._require(pack_id, version)
        if record.state != "DISCOVERED":
            raise PackLifecycleError("Pack can only be staged from DISCOVERED")
        return self._transition(record, "STAGED", "manifest staged for transactional validation")

    def validate(self, pack_id: str, version: str, *, validation_receipt_ref: str, validation_status: str = "PASS", authority_upgrade: bool = False) -> PackLifecycleRecord:
        record = self._require(pack_id, version)
        if record.state != "STAGED":
            raise PackLifecycleError("Pack can only be validated from STAGED")
        if validation_status != "PASS" or authority_upgrade:
            return self._transition(record, "QUARANTINED", "validation failed or authority ceiling changed")
        updated = replace(record, state="VALIDATED", validation_receipt_ref=validation_receipt_ref)
        self._records[(pack_id, version)] = updated
        self._receipt(updated, "VALIDATED", "manifest, schema, capability and authority checks passed")
        self._persist()
        return updated

    def activate(self, pack_id: str, version: str, *, fail_activation: bool = False) -> PackLifecycleRecord:
        record = self._require(pack_id, version)
        if record.state != "VALIDATED":
            raise PackLifecycleError("Pack can only be activated from VALIDATED")
        previous_version = self._active.get(pack_id)
        if fail_activation:
            updated = replace(record, state="ROLLED_BACK", last_known_good_version=previous_version)
            self._records[(pack_id, version)] = updated
            self._receipt(updated, "ROLLED_BACK", "activation failed; last-known-good remains active")
            self._persist()
            return updated
        if previous_version and previous_version != version:
            previous = self._require(pack_id, previous_version)
            if previous.active_run_ids:
                self._records[(pack_id, previous_version)] = replace(previous, state="DRAINING")
                self._receipt(self._records[(pack_id, previous_version)], "DRAINING", "new version activated; pinned runs drain on prior version")
            else:
                self._records[(pack_id, previous_version)] = replace(previous, state="DEACTIVATED")
                self._receipt(self._records[(pack_id, previous_version)], "DEACTIVATED", "replaced by new version with no active runs")
        updated = replace(record, state="ACTIVATED", last_known_good_version=previous_version or version)
        self._records[(pack_id, version)] = updated
        self._active[pack_id] = version
        self._receipt(updated, "ACTIVATED", "atomic activation committed")
        self._persist()
        return updated

    def pin_run(self, run_id: str, pack_id: str) -> PackRunPin:
        _id(run_id, "run_id")
        version = self._active.get(pack_id)
        if version is None:
            raise PackLifecycleError("no active Pack version")
        existing = self._pins.get(run_id)
        if existing is not None:
            if existing.pack_id != pack_id:
                raise PackLifecycleError("run cannot silently change Pack identity")
            return existing
        pin = PackRunPin(run_id, pack_id, version)
        record = self._require(pack_id, version)
        updated = replace(record, active_run_ids=tuple(sorted((*record.active_run_ids, run_id))))
        self._records[(pack_id, version)] = updated
        self._pins[run_id] = pin
        self._receipt(updated, "ACTIVATED", f"run pinned to Pack version {version}")
        self._persist()
        return pin

    def complete_run(self, run_id: str) -> None:
        pin = self._pins.pop(run_id, None)
        if pin is None:
            raise PackLifecycleError("unknown run pin")
        record = self._require(pin.pack_id, pin.version)
        updated = replace(record, active_run_ids=tuple(item for item in record.active_run_ids if item != run_id))
        self._records[(pin.pack_id, pin.version)] = updated
        self._receipt(updated, updated.state, f"run {run_id} completed; version pin released")
        self._persist()

    def deactivate(self, pack_id: str, version: str) -> PackLifecycleRecord:
        record = self._require(pack_id, version)
        if record.state not in {"ACTIVATED", "DRAINING"}:
            raise PackLifecycleError("only active or draining Pack can deactivate")
        target = "DRAINING" if record.active_run_ids else "DEACTIVATED"
        updated = replace(record, state=target)
        self._records[(pack_id, version)] = updated
        if target == "DEACTIVATED" and self._active.get(pack_id) == version:
            self._active.pop(pack_id, None)
        self._receipt(updated, target, "deactivation preserves receipt, memory and provenance")
        self._persist()
        return updated

    def quarantine(self, pack_id: str, version: str, *, reason: str) -> PackLifecycleRecord:
        record = self._require(pack_id, version)
        return self._transition(record, "QUARANTINED", reason)

    def active_version(self, pack_id: str) -> str | None:
        return self._active.get(pack_id)

    def get(self, pack_id: str, version: str) -> PackLifecycleRecord:
        return self._require(pack_id, version)

    def receipts(self) -> tuple[PackLifecycleReceipt, ...]:
        return tuple(self._receipts)

    def _require(self, pack_id: str, version: str) -> PackLifecycleRecord:
        try:
            return self._records[(pack_id, version)]
        except KeyError as exc:
            raise PackLifecycleError(f"unknown Pack lifecycle record: {pack_id}@{version}") from exc

    def _transition(self, record: PackLifecycleRecord, state: str, reason: str) -> PackLifecycleRecord:
        updated = replace(record, state=state)
        self._records[(record.pack_id, record.version)] = updated
        self._receipt(updated, state, reason)
        self._persist()
        return updated


def advisory_overlay_record(*, version: str, manifest_digest: str) -> PackLifecycleRecord:
    """Represent the 126 Structural Governance Surface without Pack authority."""

    return PackLifecycleRecord("structural-governance-surface", version, "ACTIVATED", manifest_digest, role=ADVISORY_OVERLAY_ROLE)


__all__ = ["ADVISORY_OVERLAY_ROLE", "PACK_LIFECYCLE_SCHEMA", "PACK_STATES", "PackLifecycleError", "PackLifecycleManager", "PackLifecycleReceipt", "PackLifecycleRecord", "PackRunPin", "advisory_overlay_record"]
