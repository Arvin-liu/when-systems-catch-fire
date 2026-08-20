"""Schema epoch migration and downgrade safety for durable OS state."""

from __future__ import annotations

from dataclasses import dataclass
import copy
from collections import deque
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json


MIGRATION_SCHEMA = "ignition-durability-schema-migration-r1"
MIGRATION_RECEIPT_SCHEMA = "ignition-durability-migration-receipt-r1"
SAFE = "SAFE"
LOSSY_REQUIRES_APPROVAL = "LOSSY_REQUIRES_APPROVAL"
FORBIDDEN = "FORBIDDEN"
DRY_RUN = "DRY_RUN"
APPLIED = "APPLIED"
ROLLED_BACK = "ROLLED_BACK"


class MigrationError(RuntimeError):
    """Base fail-closed migration error."""


class UnknownEpochError(MigrationError):
    """An input or target epoch is not supported by the registry."""


class MigrationPathError(MigrationError):
    """No explicit migration graph path exists."""


class LossyDowngradeRequiresApproval(MigrationError):
    """A lossy downgrade was requested without an explicit approval."""


class ForbiddenMigrationError(MigrationError):
    """A downgrade or transform is categorically forbidden."""


class MigrationExecutionError(MigrationError):
    """A migration failed and was rolled back to last-known-good state."""


@dataclass(frozen=True)
class MigrationRule:
    from_epoch: str
    to_epoch: str
    classification: str
    operation: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.from_epoch or not self.to_epoch or self.from_epoch == self.to_epoch:
            raise MigrationError("migration rule epochs must be distinct and non-empty")
        if self.classification not in {SAFE, LOSSY_REQUIRES_APPROVAL, FORBIDDEN}:
            raise MigrationError("unknown migration classification")
        if not self.operation or not self.rationale:
            raise MigrationError("migration rule operation and rationale are required")

    def to_dict(self) -> dict[str, str]:
        return {"from_epoch": self.from_epoch, "to_epoch": self.to_epoch, "classification": self.classification, "operation": self.operation, "rationale": self.rationale}


class MigrationRegistry:
    def __init__(self, supported_epochs: Sequence[str], rules: Sequence[MigrationRule]) -> None:
        self.supported_epochs = tuple(supported_epochs)
        self.rules = tuple(rules)
        if len(self.supported_epochs) < 3 or len(set(self.supported_epochs)) != len(self.supported_epochs):
            raise MigrationError("registry must support at least three unique epochs")
        if any(not epoch for epoch in self.supported_epochs):
            raise MigrationError("supported epochs must be non-empty")
        pairs = [(rule.from_epoch, rule.to_epoch) for rule in self.rules]
        if len(pairs) != len(set(pairs)):
            raise MigrationError("migration graph contains duplicate edges")
        if any(rule.from_epoch not in self.supported_epochs or rule.to_epoch not in self.supported_epochs for rule in self.rules):
            raise MigrationError("migration rule references an unsupported epoch")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MigrationRegistry":
        if data.get("schema_version") != MIGRATION_SCHEMA:
            raise MigrationError("migration registry schema mismatch")
        return cls(
            tuple(data.get("supported_epochs", ())),
            tuple(MigrationRule(**dict(rule)) for rule in data.get("compatibility_matrix", ())),
        )

    def rule(self, from_epoch: str, to_epoch: str) -> MigrationRule:
        for rule in self.rules:
            if rule.from_epoch == from_epoch and rule.to_epoch == to_epoch:
                return rule
        raise MigrationPathError(f"no explicit migration edge {from_epoch}->{to_epoch}")

    def path(self, from_epoch: str, to_epoch: str) -> tuple[MigrationRule, ...]:
        if from_epoch not in self.supported_epochs or to_epoch not in self.supported_epochs:
            raise UnknownEpochError(f"unsupported schema epoch: {from_epoch} or {to_epoch}")
        if from_epoch == to_epoch:
            return ()
        queue: deque[tuple[str, tuple[MigrationRule, ...]]] = deque([(from_epoch, ())])
        visited = {from_epoch}
        while queue:
            current, edges = queue.popleft()
            for rule in self.rules:
                if rule.from_epoch != current or rule.to_epoch in visited:
                    continue
                next_edges = edges + (rule,)
                if rule.to_epoch == to_epoch:
                    return next_edges
                visited.add(rule.to_epoch)
                queue.append((rule.to_epoch, next_edges))
        raise MigrationPathError(f"no migration path {from_epoch}->{to_epoch}")

    def compatibility_matrix(self) -> list[dict[str, str]]:
        return [rule.to_dict() for rule in self.rules]


@dataclass(frozen=True)
class MigrationReceipt:
    migration_id: str
    from_epoch: str
    to_epoch: str
    classification: str
    mode: str
    pre_digest: str
    post_digest: str
    event_lineage_digest: str
    events_rewritten: bool
    status: str
    rollback_reason: str | None = None
    receipt_sha256: str | None = None

    def __post_init__(self) -> None:
        for field in ("pre_digest", "post_digest", "event_lineage_digest"):
            value = getattr(self, field)
            if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise MigrationError(f"{field} must be a lowercase SHA-256 digest")
        if self.classification not in {SAFE, LOSSY_REQUIRES_APPROVAL, FORBIDDEN}:
            raise MigrationError("invalid receipt classification")
        if self.mode not in {DRY_RUN, APPLIED}:
            raise MigrationError("invalid receipt mode")
        if self.status not in {DRY_RUN, APPLIED, ROLLED_BACK}:
            raise MigrationError("invalid receipt status")
        if self.events_rewritten:
            raise MigrationError("historical event rewriting is forbidden")
        expected = sha256_json(self._unsigned_dict())
        if self.receipt_sha256 is not None and self.receipt_sha256 != expected:
            raise MigrationError("migration receipt digest mismatch")
        object.__setattr__(self, "receipt_sha256", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": MIGRATION_RECEIPT_SCHEMA, "migration_id": self.migration_id,
            "from_epoch": self.from_epoch, "to_epoch": self.to_epoch,
            "classification": self.classification, "mode": self.mode,
            "pre_digest": self.pre_digest, "post_digest": self.post_digest,
            "event_lineage_digest": self.event_lineage_digest,
            "events_rewritten": self.events_rewritten, "status": self.status,
            "rollback_reason": self.rollback_reason,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "receipt_sha256": self.receipt_sha256}


@dataclass(frozen=True)
class MigrationResult:
    state: Mapping[str, Any]
    receipt: MigrationReceipt


def _event_lineage_digest(event_lineage: Sequence[Mapping[str, Any]] | Sequence[str]) -> str:
    return sha256_json(list(event_lineage))


def _apply_operation(state: dict[str, Any], operation: str) -> dict[str, Any]:
    result = copy.deepcopy(state)
    if result.get("__migration_fail__") == operation:
        raise MigrationExecutionError(f"fixture requested failure at {operation}")
    if operation == "ADD_LIFECYCLE_METADATA":
        result.setdefault("lifecycle", {"state": "UNKNOWN", "version_pinned": False})
    elif operation == "ADD_NAMESPACE_SCOPE":
        result.setdefault("namespace_scope", "global")
    elif operation == "ADD_ADVISORY_POINTER":
        result.setdefault("advisory_soft_governance", {"status": "ADVISORY_ONLY", "claim_ceiling": "bounded"})
    elif operation == "REMOVE_ADVISORY_POINTER_LOSSY":
        result.pop("advisory_soft_governance", None)
    elif operation == "FORBIDDEN_LEGACY_REWRITE":
        raise ForbiddenMigrationError("forbidden migration operation")
    else:
        raise MigrationPathError(f"unknown migration operation: {operation}")
    return result


class StateMigrator:
    def __init__(self, registry: MigrationRegistry) -> None:
        self.registry = registry

    def migrate(
        self,
        state: Mapping[str, Any],
        *,
        migration_id: str,
        from_epoch: str,
        to_epoch: str,
        event_lineage: Sequence[Mapping[str, Any]] | Sequence[str] = (),
        mode: str = DRY_RUN,
        approval: bool = False,
        last_known_good: Mapping[str, Any] | None = None,
    ) -> MigrationResult:
        if mode not in {DRY_RUN, APPLIED}:
            raise MigrationError("mode must be DRY_RUN or APPLIED")
        path = self.registry.path(from_epoch, to_epoch)
        classification = FORBIDDEN if any(rule.classification == FORBIDDEN for rule in path) else LOSSY_REQUIRES_APPROVAL if any(rule.classification == LOSSY_REQUIRES_APPROVAL for rule in path) else SAFE
        if classification == FORBIDDEN:
            raise ForbiddenMigrationError(f"migration {from_epoch}->{to_epoch} is forbidden")
        if classification == LOSSY_REQUIRES_APPROVAL and not approval:
            raise LossyDowngradeRequiresApproval(f"migration {from_epoch}->{to_epoch} requires explicit approval")
        original = copy.deepcopy(dict(state))
        pre_digest = sha256_json(original)
        lineage_digest = _event_lineage_digest(event_lineage)
        candidate = copy.deepcopy(original)
        try:
            for rule in path:
                candidate = _apply_operation(candidate, rule.operation)
        except MigrationExecutionError as exc:
            rollback = copy.deepcopy(dict(last_known_good if last_known_good is not None else original))
            receipt = MigrationReceipt(
                migration_id=migration_id, from_epoch=from_epoch, to_epoch=to_epoch,
                classification=classification, mode=mode, pre_digest=pre_digest,
                post_digest=sha256_json(rollback), event_lineage_digest=lineage_digest,
                events_rewritten=False, status=ROLLED_BACK, rollback_reason=str(exc),
            )
            return MigrationResult(rollback, receipt)
        result_state = original if mode == DRY_RUN else candidate
        receipt = MigrationReceipt(
            migration_id=migration_id, from_epoch=from_epoch, to_epoch=to_epoch,
            classification=classification, mode=mode, pre_digest=pre_digest,
            post_digest=sha256_json(candidate), event_lineage_digest=lineage_digest,
            events_rewritten=False, status=DRY_RUN if mode == DRY_RUN else APPLIED,
        )
        return MigrationResult(result_state, receipt)


__all__ = [
    "APPLIED", "DRY_RUN", "FORBIDDEN", "LOSSY_REQUIRES_APPROVAL", "MIGRATION_RECEIPT_SCHEMA", "MIGRATION_SCHEMA", "MigrationError", "MigrationExecutionError", "MigrationPathError", "MigrationReceipt", "MigrationRegistry", "MigrationResult", "MigrationRule", "ForbiddenMigrationError", "LossyDowngradeRequiresApproval", "StateMigrator", "UnknownEpochError", "ROLLED_BACK",
]
