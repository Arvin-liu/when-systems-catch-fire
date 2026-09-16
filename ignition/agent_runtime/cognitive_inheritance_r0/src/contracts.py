"""Small deterministic helpers for Cognitive Inheritance Architecture R0.

This module deliberately has no model, provider, network, or training
dependency.  It handles serialization, the explicitly backward-readable
R0a-to-R0b adapter fixture, and the negative surface that prevents hidden
reasoning or model-training state from entering the observable substrate.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_KEYS = frozenset(
    {
        "chain_of_thought",
        "hidden_chain_of_thought",
        "private_reasoning",
        "model_weights",
        "weight_update",
        "training_weights",
        "training_step",
        "self_verdict",
        "independent_verdict",
    }
)


def canonical_json(value: Any) -> str:
    """Return a stable JSON representation suitable for replay comparison."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: str | Path) -> Any:
    """Load UTF-8 JSON without applying an implicit migration or normalization."""

    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _walk_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if key_text.casefold() in FORBIDDEN_KEYS:
                findings.append(f"{path}.{key_text}")
            findings.extend(_walk_keys(child, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_walk_keys(child, f"{path}[{index}]"))
    return findings


def validate_no_forbidden_fields(value: Any) -> None:
    """Raise when an artifact attempts to persist a prohibited private field."""

    findings = _walk_keys(value)
    if findings:
        joined = ", ".join(findings)
        raise ValueError(f"prohibited R0 field(s): {joined}")


def migrate_r0a_to_r0b(record: dict[str, Any]) -> dict[str, Any]:
    """Adapt the minimum R0a fixture without deleting or rewriting its facts.

    The adapter adds lineage and a schema version only.  Unknown relations and
    all source/provenance fields remain byte-for-byte equivalent after JSON
    parsing.  It is intentionally not a general migration engine.
    """

    if not isinstance(record, dict):
        raise TypeError("R0a record must be a JSON object")
    if record.get("schema_version") != "cognitive-ir-r0a":
        raise ValueError("adapter accepts only cognitive-ir-r0a")
    validate_no_forbidden_fields(record)

    migrated = deepcopy(record)
    migrated["schema_version"] = "cognitive-ir-r0b"
    lineage = list(migrated.get("migration_lineage", []))
    lineage.append(
        {
            "lineage_id": "lineage:cognitive-ir:r0a-to-r0b",
            "operation": "BACKWARD_READABLE_ADAPTER",
            "source_schema": "cognitive-ir-r0a",
            "target_schema": "cognitive-ir-r0b",
            "destructive_rewrite": False,
        }
    )
    migrated["migration_lineage"] = lineage
    validate_no_forbidden_fields(migrated)
    return migrated


def keys_preserved(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """Check the adapter's non-destructive top-level preservation invariant."""

    return all(key in after for key in before)


__all__ = [
    "FORBIDDEN_KEYS",
    "ROOT",
    "canonical_json",
    "keys_preserved",
    "load_json",
    "migrate_r0a_to_r0b",
    "validate_no_forbidden_fields",
]
