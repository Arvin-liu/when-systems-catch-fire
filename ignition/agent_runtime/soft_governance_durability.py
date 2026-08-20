"""Persistence and migration gates for 126's advisory soft-governance state."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json


SOFT_SCHEMA = "ignition-durability-soft-governance-r1"
ADVISORY_STATUSES = frozenset({"CANDIDATE_ESI_SIGNAL", "READY_NOT_RUN", "NOT_RUN_LIVE_EXTERNAL", "ADVISORY_ONLY", "WITHDRAWN"})
FORBIDDEN_HARD_FIELDS = frozenset({"permission", "permissions", "authorization", "authorize", "truth", "truth_status", "owner_acceptance", "epistemic_acceptance", "safety_release", "capability_grant"})
NONE_FIELDS = frozenset({"capability_delta", "permission_delta", "authorization_delta", "truth_status_delta", "owner_status_delta", "epistemic_acceptance_delta", "safety_delta"})


class SoftGovernanceDurabilityError(ValueError):
    """Raised when a persisted soft field would escalate authority."""


def _scan(value: Any, path: str = "record") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).casefold()
            if lowered in FORBIDDEN_HARD_FIELDS and (lowered not in NONE_FIELDS or child != "NONE"):
                errors.append(f"{path}.{key} attempts a hard authority mapping")
            if lowered == "requested_effect" and str(child).casefold() not in {"advisory_context", "display_only", "none"}:
                errors.append(f"{path}.{key} is not a bounded advisory effect")
            errors.extend(_scan(child, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            errors.extend(_scan(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in ("grant permission", "becomes truth", "owner accepted", "epistemically accepted", "safety release")):
            errors.append(f"{path} contains a hard authority assertion")
    return errors


def validate_soft_state(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != SOFT_SCHEMA:
        errors.append("soft governance schema mismatch")
    if record.get("status") not in ADVISORY_STATUSES:
        errors.append("soft governance status is not an allowed advisory lifecycle state")
    ceiling = str(record.get("claim_ceiling", "")).casefold()
    if not ceiling or any(marker in ceiling for marker in ("confirmed", "truth established", "permission granted", "owner accepted", "epistemically accepted")):
        errors.append("claim ceiling is missing or escalated")
    effects = record.get("authority_effects")
    if not isinstance(effects, Mapping) or set(effects) != NONE_FIELDS or any(value != "NONE" for value in effects.values()):
        errors.append("all soft-governance authority effects must be NONE")
    if record.get("experiment_protocol_state") == "LIVE_CONFIRMED":
        errors.append("live confirmed experiment state is outside the advisory contract")
    errors.extend(_scan(record))
    return sorted(set(errors))


def migrate_soft_state(record: Mapping[str, Any], *, target_format_epoch: int, migration_id: str) -> dict[str, Any]:
    """Upgrade/downgrade representation while preserving advisory semantics."""

    errors = validate_soft_state(record)
    if errors:
        raise SoftGovernanceDurabilityError("; ".join(errors))
    source_epoch = record.get("format_epoch")
    if not isinstance(source_epoch, int) or source_epoch not in {1, 2} or target_format_epoch not in {1, 2}:
        raise SoftGovernanceDurabilityError("unknown soft-governance format epoch")
    migrated = deepcopy(dict(record))
    migrated["format_epoch"] = target_format_epoch
    if target_format_epoch == 1:
        migrated.pop("withdrawal_reason", None)
    elif migrated.get("status") == "WITHDRAWN":
        migrated.setdefault("withdrawal_reason", "withdrawal preserved across format migration")
    migrated["migration_receipt_ref"] = migration_id
    # The extra reference is a machine audit field, not authority-bearing state.
    errors = validate_soft_state({key: value for key, value in migrated.items() if key != "migration_receipt_ref"})
    if errors:
        raise SoftGovernanceDurabilityError("migration would escalate soft governance: " + "; ".join(errors))
    return migrated


def soft_state_digest(record: Mapping[str, Any]) -> str:
    errors = validate_soft_state(record)
    if errors:
        raise SoftGovernanceDurabilityError("; ".join(errors))
    return sha256_json(record)


__all__ = ["ADVISORY_STATUSES", "SOFT_SCHEMA", "SoftGovernanceDurabilityError", "migrate_soft_state", "soft_state_digest", "validate_soft_state"]
