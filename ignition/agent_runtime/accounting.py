"""Replayable OS budget accounting and bounded fairness scheduling."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Iterable, Mapping

from agent_kernel.contracts import sha256_json

from .control import FileLock, _atomic_json


ACCOUNTING_SCHEMA = "ignition-durability-accounting-r1"
ACCOUNTING_EVENT_SCHEMA = "ignition-durability-accounting-event-r1"
ACCOUNTING_EVENT_TYPES = frozenset({"BUDGET_RESERVED", "BUDGET_SETTLED", "BUDGET_CANCELLED"})
ATTEMPT_KINDS = frozenset({"PRIMARY", "RETRY", "FAILOVER", "RECONCILIATION"})
ACCOUNTING_DIMENSIONS = ("principal", "namespace", "workspace", "episode", "pack", "executor")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "thoughts", "reasoning", "api_key", "token", "cookie", "authorization", "secret"})


class AccountingError(ValueError):
    """Base accounting or fairness contract failure."""


class AccountingQuotaExceeded(AccountingError):
    """A reservation would cross one of the bounded scope limits."""


class AccountingDuplicate(AccountingError):
    """An idempotency or settlement identity was reused inconsistently."""


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or ".." in value:
        raise AccountingError(f"{field} is not a canonical identifier")
    return value


def _public(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise AccountingError(f"{field} must be a non-empty public value")
    return value


@dataclass(frozen=True)
class CostVector:
    action_count: int = 0
    wall_clock_seconds: float = 0.0
    output_bytes: int = 0
    event_volume: int = 0
    memory_bytes: int = 0
    retry_cost: int = 0
    failover_cost: int = 0
    reconciliation_cost: int = 0

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:  # type: ignore[attr-defined]
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise AccountingError(f"{field} must be non-negative")
            if field != "wall_clock_seconds" and not isinstance(value, int):
                raise AccountingError(f"{field} must be an integer")

    def add(self, other: "CostVector") -> "CostVector":
        if not isinstance(other, CostVector):
            raise AccountingError("cost addition requires CostVector")
        return CostVector(**{field: getattr(self, field) + getattr(other, field) for field in self.__dataclass_fields__})  # type: ignore[attr-defined]

    def subtract(self, other: "CostVector") -> "CostVector":
        if not other.fits(self):
            raise AccountingError("cost subtraction would become negative")
        return CostVector(**{field: getattr(self, field) - getattr(other, field) for field in self.__dataclass_fields__})  # type: ignore[attr-defined]

    def fits(self, limit: "CostVector") -> bool:
        return all(getattr(self, field) <= getattr(limit, field) for field in self.__dataclass_fields__)  # type: ignore[attr-defined]

    def is_zero(self) -> bool:
        return all(getattr(self, field) == 0 for field in self.__dataclass_fields__)  # type: ignore[attr-defined]

    def to_dict(self) -> dict[str, int | float]:
        return {field: getattr(self, field) for field in self.__dataclass_fields__}  # type: ignore[attr-defined]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CostVector":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise AccountingError("cost vector keys mismatch")
        return cls(**dict(data))


@dataclass(frozen=True)
class BudgetScope:
    principal_id: str
    namespace_id: str
    workspace_id: str
    episode_id: str
    pack_id: str
    executor_id: str

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:  # type: ignore[attr-defined]
            _id(getattr(self, field), field)

    def dimensions(self) -> tuple[tuple[str, str], ...]:
        return (
            ("principal", self.principal_id), ("namespace", self.namespace_id),
            ("workspace", self.workspace_id), ("episode", self.episode_id),
            ("pack", self.pack_id), ("executor", self.executor_id),
        )

    def to_dict(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in self.__dataclass_fields__}  # type: ignore[attr-defined]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BudgetScope":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise AccountingError("budget scope keys mismatch")
        return cls(**dict(data))


@dataclass(frozen=True)
class AccountingPolicy:
    limits: Mapping[str, CostVector]
    workspace_namespace: Mapping[str, str]
    max_consecutive_per_principal: int = 2
    aging_seconds: float = 30.0
    aging_cap: int = 1000

    def __post_init__(self) -> None:
        normalized = {str(key): value for key, value in self.limits.items()}
        if any(not isinstance(value, CostVector) for value in normalized.values()):
            raise AccountingError("accounting limits must be CostVector values")
        if not isinstance(self.max_consecutive_per_principal, int) or self.max_consecutive_per_principal <= 0:
            raise AccountingError("max_consecutive_per_principal must be positive")
        if not isinstance(self.aging_seconds, (int, float)) or self.aging_seconds <= 0:
            raise AccountingError("aging_seconds must be positive")
        if not isinstance(self.aging_cap, int) or self.aging_cap <= 0:
            raise AccountingError("aging_cap must be positive")
        object.__setattr__(self, "limits", normalized)
        object.__setattr__(self, "workspace_namespace", {str(key): _id(value, f"workspace_namespace[{key}]") for key, value in self.workspace_namespace.items()})

    def limit_for(self, dimension: str, identifier: str) -> CostVector:
        try:
            return self.limits[f"{dimension}:{identifier}"]
        except KeyError as exc:
            raise AccountingQuotaExceeded(f"no bounded quota exists for {dimension}:{identifier}") from exc

    def validate_scope(self, scope: BudgetScope) -> None:
        expected_namespace = self.workspace_namespace.get(scope.workspace_id)
        if expected_namespace is None or expected_namespace != scope.namespace_id:
            raise AccountingQuotaExceeded("workspace is not bound to the requested namespace")
        for dimension, identifier in scope.dimensions():
            self.limit_for(dimension, identifier)


@dataclass(frozen=True)
class AccountingEvent:
    event_id: str
    sequence: int
    event_type: str
    reservation_id: str
    scope: BudgetScope
    reserved_add: CostVector
    reserved_release: CostVector
    spent_add: CostVector
    attempt_kind: str
    occurred_at: float
    idempotency_key: str
    previous_event_hash: str
    detail: str
    event_hash: str | None = None

    def __post_init__(self) -> None:
        _id(self.event_id, "event_id")
        _id(self.reservation_id, "reservation_id")
        _id(self.idempotency_key, "idempotency_key")
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise AccountingError("accounting sequence must be non-negative")
        if self.event_type not in ACCOUNTING_EVENT_TYPES:
            raise AccountingError("unknown accounting event type")
        if self.attempt_kind not in ATTEMPT_KINDS:
            raise AccountingError("unknown attempt kind")
        if not isinstance(self.occurred_at, (int, float)) or self.occurred_at < 0:
            raise AccountingError("occurred_at must be non-negative")
        _public(self.detail, "detail")
        if len(self.previous_event_hash) != 64 or any(char not in "0123456789abcdef" for char in self.previous_event_hash):
            raise AccountingError("previous_event_hash must be a lowercase SHA-256 digest")
        expected = sha256_json(self._unsigned_dict())
        if self.event_hash is not None and self.event_hash != expected:
            raise AccountingError("accounting event hash mismatch")
        object.__setattr__(self, "event_hash", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": ACCOUNTING_EVENT_SCHEMA, "event_id": self.event_id, "sequence": self.sequence,
            "event_type": self.event_type, "reservation_id": self.reservation_id, "scope": self.scope.to_dict(),
            "reserved_add": self.reserved_add.to_dict(), "reserved_release": self.reserved_release.to_dict(),
            "spent_add": self.spent_add.to_dict(), "attempt_kind": self.attempt_kind, "occurred_at": self.occurred_at,
            "idempotency_key": self.idempotency_key, "previous_event_hash": self.previous_event_hash, "detail": self.detail,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "event_hash": self.event_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AccountingEvent":
        required = set(cls.__dataclass_fields__) | {"schema"}  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required or data.get("schema") != ACCOUNTING_EVENT_SCHEMA:
            raise AccountingError("accounting event keys/schema mismatch")
        return cls(
            event_id=data["event_id"], sequence=data["sequence"], event_type=data["event_type"], reservation_id=data["reservation_id"],
            scope=BudgetScope.from_dict(data["scope"]), reserved_add=CostVector.from_dict(data["reserved_add"]),
            reserved_release=CostVector.from_dict(data["reserved_release"]), spent_add=CostVector.from_dict(data["spent_add"]),
            attempt_kind=data["attempt_kind"], occurred_at=data["occurred_at"], idempotency_key=data["idempotency_key"],
            previous_event_hash=data["previous_event_hash"], detail=data["detail"], event_hash=data["event_hash"],
        )


@dataclass(frozen=True)
class ReservationReceipt:
    reservation_id: str
    scope: BudgetScope
    estimated_cost: CostVector
    attempt_kind: str
    state: str = "ACTIVE"


@dataclass(frozen=True)
class SettlementReceipt:
    reservation_id: str
    spent_cost: CostVector
    released_cost: CostVector
    cancelled: bool
    state: str = "SETTLED"


class AccountingStore:
    """Append-only budget ledger with deterministic replay and scope rollups."""

    def __init__(self, path: str | Path, policy: AccountingPolicy) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.policy = policy

    def _read_unlocked(self) -> list[AccountingEvent]:
        if not self.path.exists():
            return []
        events: list[AccountingEvent] = []
        previous = "0" * 64
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise AccountingError("accounting ledger cannot be read") from exc
        for line_number, line in enumerate(lines, 1):
            try:
                event = AccountingEvent.from_dict(json.loads(line))
            except (json.JSONDecodeError, TypeError, AccountingError) as exc:
                raise AccountingError(f"invalid accounting event at line {line_number}") from exc
            if event.sequence != len(events) or event.previous_event_hash != previous:
                raise AccountingError("accounting event chain is not contiguous")
            events.append(event)
            previous = event.event_hash or previous
        self._replay(events)
        return events

    def events(self) -> tuple[AccountingEvent, ...]:
        with FileLock(self.lock_path):
            return tuple(self._read_unlocked())

    def _append_unlocked(self, event: AccountingEvent, events: list[AccountingEvent]) -> None:
        if event.sequence != len(events) or event.previous_event_hash != (events[-1].event_hash if events else "0" * 64):
            raise AccountingError("accounting append is not the next chain event")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()

    @staticmethod
    def _scope_key(dimension: str, identifier: str) -> str:
        return f"{dimension}:{identifier}"

    def _replay(self, events: Iterable[AccountingEvent]) -> dict[str, Any]:
        totals: dict[str, dict[str, CostVector]] = {}
        reservations: dict[str, dict[str, Any]] = {}
        seen_idempotency: set[str] = set()
        for event in events:
            if event.idempotency_key in seen_idempotency:
                raise AccountingDuplicate("accounting idempotency key was duplicated")
            seen_idempotency.add(event.idempotency_key)
            for dimension, identifier in event.scope.dimensions():
                key = self._scope_key(dimension, identifier)
                current = totals.setdefault(key, {"spent": CostVector(), "reserved": CostVector()})
                if event.event_type == "BUDGET_RESERVED":
                    current["reserved"] = current["reserved"].add(event.reserved_add)
                else:
                    current["reserved"] = current["reserved"].subtract(event.reserved_release)
                    current["spent"] = current["spent"].add(event.spent_add)
            if event.event_type == "BUDGET_RESERVED":
                if event.reservation_id in reservations:
                    raise AccountingDuplicate("reservation was reserved twice")
                reservations[event.reservation_id] = {"scope": event.scope, "estimated": event.reserved_add, "attempt_kind": event.attempt_kind, "state": "ACTIVE", "spent": CostVector()}
            else:
                reservation = reservations.get(event.reservation_id)
                if reservation is None or reservation["state"] != "ACTIVE":
                    raise AccountingDuplicate("reservation was settled twice or without a reservation")
                if not event.spent_add.fits(reservation["estimated"]):
                    raise AccountingError("settlement exceeded its reservation")
                reservation.update({"state": "CANCELLED" if event.event_type == "BUDGET_CANCELLED" else "SETTLED", "spent": event.spent_add, "released": event.reserved_release})
        for key, value in totals.items():
            if any(getattr(value["reserved"], field) < 0 for field in value["reserved"].__dataclass_fields__):  # type: ignore[attr-defined]
                raise AccountingError(f"negative reserved budget at {key}")
        return {"totals": totals, "reservations": reservations, "seen_idempotency": seen_idempotency}

    def replay(self) -> dict[str, Any]:
        with FileLock(self.lock_path):
            state = self._replay(self._read_unlocked())
        return {
            "totals": {key: {name: value.to_dict() for name, value in current.items()} for key, current in state["totals"].items()},
            "reservations": {key: {**value, "scope": value["scope"].to_dict(), "estimated": value["estimated"].to_dict(), "spent": value["spent"].to_dict(), "released": value.get("released", CostVector()).to_dict()} for key, value in state["reservations"].items()},
        }

    def reserve(
        self,
        reservation_id: str,
        scope: BudgetScope,
        estimated_cost: CostVector,
        *,
        attempt_kind: str = "PRIMARY",
        idempotency_key: str | None = None,
        occurred_at: float | None = None,
    ) -> ReservationReceipt:
        _id(reservation_id, "reservation_id")
        self.policy.validate_scope(scope)
        if estimated_cost.is_zero():
            raise AccountingError("a reservation must carry a positive cost")
        if attempt_kind not in ATTEMPT_KINDS:
            raise AccountingError("unknown attempt kind")
        if attempt_kind == "RETRY" and estimated_cost.retry_cost < 1:
            raise AccountingQuotaExceeded("retry reservation must account retry_cost")
        if attempt_kind == "FAILOVER" and estimated_cost.failover_cost < 1:
            raise AccountingQuotaExceeded("failover reservation must account failover_cost")
        if attempt_kind == "RECONCILIATION" and estimated_cost.reconciliation_cost < 1:
            raise AccountingQuotaExceeded("reconciliation reservation must account reconciliation_cost")
        key = idempotency_key or f"reserve-{reservation_id}"
        _id(key, "idempotency_key")
        occurred = float(time.time() if occurred_at is None else occurred_at)
        with FileLock(self.lock_path):
            events = self._read_unlocked()
            existing_key = next((event for event in events if event.idempotency_key == key), None)
            if existing_key is not None:
                if existing_key.reservation_id != reservation_id or existing_key.reserved_add != estimated_cost:
                    raise AccountingDuplicate("reservation idempotency key has different cost or identity")
                return ReservationReceipt(reservation_id, existing_key.scope, existing_key.reserved_add, existing_key.attempt_kind)
            state = self._replay(events)
            if reservation_id in state["reservations"]:
                raise AccountingDuplicate("reservation identity already exists")
            for dimension, identifier in scope.dimensions():
                key_name = self._scope_key(dimension, identifier)
                current = state["totals"].get(key_name, {"spent": CostVector(), "reserved": CostVector()})
                if not current["spent"].add(current["reserved"]).add(estimated_cost).fits(self.policy.limit_for(dimension, identifier)):
                    raise AccountingQuotaExceeded(f"budget exceeded at {key_name}")
            event = AccountingEvent(
                event_id=f"accounting-event-{reservation_id}-reserve", sequence=len(events), event_type="BUDGET_RESERVED", reservation_id=reservation_id,
                scope=scope, reserved_add=estimated_cost, reserved_release=CostVector(), spent_add=CostVector(), attempt_kind=attempt_kind,
                occurred_at=occurred, idempotency_key=key, previous_event_hash=events[-1].event_hash if events else "0" * 64, detail=f"budget reserved for {attempt_kind.lower()} attempt",
            )
            self._append_unlocked(event, events)
        return ReservationReceipt(reservation_id, scope, estimated_cost, attempt_kind)

    def settle(self, reservation_id: str, spent_cost: CostVector, *, cancelled: bool = False, occurred_at: float | None = None) -> SettlementReceipt:
        _id(reservation_id, "reservation_id")
        if not isinstance(spent_cost, CostVector):
            raise AccountingError("spent_cost must be CostVector")
        occurred = float(time.time() if occurred_at is None else occurred_at)
        with FileLock(self.lock_path):
            events = self._read_unlocked()
            state = self._replay(events)
            reservation = state["reservations"].get(reservation_id)
            if reservation is None:
                raise AccountingError("cannot settle unknown reservation")
            if reservation["state"] != "ACTIVE":
                if reservation["spent"] == spent_cost and bool(reservation["state"] == "CANCELLED") == cancelled:
                    return SettlementReceipt(reservation_id, spent_cost, reservation["released"].subtract(spent_cost), cancelled, reservation["state"])
                raise AccountingDuplicate("reservation was already settled with different cost")
            estimated = reservation["estimated"]
            if not spent_cost.fits(estimated):
                raise AccountingQuotaExceeded("actual cost exceeded reservation; reserve a new bounded attempt")
            event_type = "BUDGET_CANCELLED" if cancelled else "BUDGET_SETTLED"
            event = AccountingEvent(
                event_id=f"accounting-event-{reservation_id}-settle", sequence=len(events), event_type=event_type, reservation_id=reservation_id,
                scope=reservation["scope"], reserved_add=CostVector(), reserved_release=estimated, spent_add=spent_cost, attempt_kind=reservation["attempt_kind"],
                occurred_at=occurred, idempotency_key=f"settle-{reservation_id}", previous_event_hash=events[-1].event_hash if events else "0" * 64,
                detail="cancelled attempt retains occurred cost" if cancelled else "attempt cost committed",
            )
            self._append_unlocked(event, events)
        return SettlementReceipt(reservation_id, spent_cost, estimated.subtract(spent_cost), cancelled)

    def totals_for(self, dimension: str, identifier: str) -> dict[str, CostVector]:
        _public(dimension, "dimension")
        _id(identifier, "identifier")
        state = self._replay(list(self.events()))
        current = state["totals"].get(self._scope_key(dimension, identifier), {"spent": CostVector(), "reserved": CostVector()})
        return dict(current)

    def audit(self) -> dict[str, Any]:
        events = self.events()
        replay = self.replay()
        return {
            "status": "PASS", "schema": ACCOUNTING_SCHEMA, "event_count": len(events),
            "reservation_count": len(replay["reservations"]), "dimension_count": len(replay["totals"]),
            "claim_ceiling": "Replayable local accounting and bounded fairness only; no budget rollback, production quota or Owner authority.",
        }


@dataclass(frozen=True)
class FairWorkItem:
    work_id: str
    principal_id: str
    priority: int
    enqueued_at: float
    cost_units: int = 1
    sequence: int = 0

    def __post_init__(self) -> None:
        _id(self.work_id, "work_id")
        _id(self.principal_id, "principal_id")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool) or not 0 <= self.priority <= 1000:
            raise AccountingError("priority must be between 0 and 1000")
        if not isinstance(self.enqueued_at, (int, float)) or self.enqueued_at < 0:
            raise AccountingError("enqueued_at must be non-negative")
        if not isinstance(self.cost_units, int) or isinstance(self.cost_units, bool) or self.cost_units <= 0:
            raise AccountingError("cost_units must be positive")


class BoundedFairScheduler:
    """Deterministic priority scheduler with bounded consecutive ownership."""

    def __init__(self, policy: AccountingPolicy) -> None:
        self.policy = policy
        self._items: list[FairWorkItem] = []
        self._sequence = 0
        self._last_principal: str | None = None
        self._consecutive = 0

    def enqueue(self, item: FairWorkItem) -> FairWorkItem:
        if any(existing.work_id == item.work_id for existing in self._items):
            raise AccountingDuplicate("work item already queued")
        self._sequence += 1
        queued = replace(item, sequence=self._sequence)
        self._items.append(queued)
        return queued

    def _score(self, item: FairWorkItem, now: float) -> int:
        aged = int(max(0.0, now - item.enqueued_at) / self.policy.aging_seconds)
        return min(1000, item.priority + min(self.policy.aging_cap, aged))

    def select(self, *, now: float) -> FairWorkItem | None:
        if not isinstance(now, (int, float)):
            raise AccountingError("scheduler time must be numeric")
        if not self._items:
            return None
        other_principals = {item.principal_id for item in self._items if item.principal_id != self._last_principal}
        candidates = self._items
        if self._last_principal is not None and self._consecutive >= self.policy.max_consecutive_per_principal and other_principals:
            candidates = [item for item in self._items if item.principal_id != self._last_principal]
        selected = min(candidates, key=lambda item: (-self._score(item, float(now)), item.enqueued_at, item.sequence, item.work_id))
        self._items.remove(selected)
        if selected.principal_id == self._last_principal:
            self._consecutive += 1
        else:
            self._last_principal = selected.principal_id
            self._consecutive = 1
        return selected

    def pending(self) -> tuple[FairWorkItem, ...]:
        return tuple(sorted(self._items, key=lambda item: item.sequence))

    def fairness_state(self) -> dict[str, Any]:
        return {"last_principal": self._last_principal, "consecutive": self._consecutive, "pending": len(self._items), "priority_ceiling": 1000, "bounded": True}


__all__ = [
    "ACCOUNTING_DIMENSIONS", "ACCOUNTING_EVENT_SCHEMA", "ACCOUNTING_SCHEMA", "AccountingDuplicate", "AccountingError", "AccountingEvent", "AccountingPolicy", "AccountingQuotaExceeded", "AccountingStore", "ATTEMPT_KINDS", "BoundedFairScheduler", "BudgetScope", "CostVector", "FairWorkItem", "ReservationReceipt", "SettlementReceipt",
]
