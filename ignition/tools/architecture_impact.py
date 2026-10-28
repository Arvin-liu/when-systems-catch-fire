"""Semantic architecture-impact classification for formal task receipts.

The legacy ``identity_impact`` field is intentionally small because it drives
the Current surface gate.  This module adds a typed explanation beside that
field so a task cannot call a control-plane behavior change presentation-only
merely because it did not add a diagram node.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "architecture-impact-classification-r1"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/operations/architecture-impact-classification-r1.schema.json"

ARCHITECTURE_CHANGING = "ARCHITECTURE_CHANGING"
BEHAVIORAL_CONTROL_PLANE_CHANGE = "BEHAVIORAL_CONTROL_PLANE_CHANGE"

ALLOWED_CLASSIFICATIONS = frozenset({
    "NONE",
    "ARCHITECTURE_CHANGING",
    "BEHAVIORAL_CONTROL_PLANE_CHANGE",
    "PRESENTATION_ONLY",
    "RELEASE_ONLY",
    "DATA_REFRESH_ONLY",
})

ARCHITECTURAL_SEMANTICS = frozenset({
    "architecture_component",
    "architecture_relation",
    "architecture_ownership",
    "identity_epoch",
})

BEHAVIORAL_CONTROL_PLANE_SEMANTICS = frozenset({
    "process_transport",
    "dispatch_state_machine",
    "observation_capture",
    "independent_validation",
    "reconciliation_state_machine",
    "canonical_state_source",
    "permission_capability_model",
    "durable_recovery_continuity",
    "executor_admission",
})

NON_ARCHITECTURAL_SEMANTICS = frozenset({
    "current_surface_only",
    "publication_only",
    "data_refresh_only",
})

LEGACY_IDENTITY_IMPACT = {
    "NONE": "NONE",
    "ARCHITECTURE_CHANGING": "ARCHITECTURE_CHANGED",
    "BEHAVIORAL_CONTROL_PLANE_CHANGE": "ARCHITECTURE_CHANGED",
    "PRESENTATION_ONLY": "PRESENTATION_ONLY",
    "RELEASE_ONLY": "NONE",
    "DATA_REFRESH_ONLY": "NONE",
}


class ArchitectureImpactError(ValueError):
    """Raised when a semantic impact record is unsafe or contradictory."""


def _strings(values: Iterable[str] | None, field: str) -> list[str]:
    if values is None:
        return []
    result = sorted({value for value in values})
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ArchitectureImpactError(f"{field} must contain non-empty strings")
    return result


def classify_change(
    semantic_changes: Iterable[str] = (),
    *,
    changed_paths: Iterable[str] = (),
    evidence: Iterable[str] = (),
    declared_classification: str | None = None,
) -> dict[str, Any]:
    """Classify a change from the semantics it changes, not its file count.

    ``declared_classification`` is checked against the observed semantic
    markers.  This makes the negative ``process_transport -> PRESENTATION``
    case fail closed instead of silently normalizing it.
    """

    semantics = _strings(semantic_changes, "semantic_changes")
    paths = _strings(changed_paths, "changed_paths")
    evidence_refs = _strings(evidence, "evidence")
    unknown = sorted(set(semantics) - ARCHITECTURAL_SEMANTICS - BEHAVIORAL_CONTROL_PLANE_SEMANTICS - NON_ARCHITECTURAL_SEMANTICS)
    if unknown:
        raise ArchitectureImpactError(f"unknown semantic change markers: {', '.join(unknown)}")

    architecture_hits = sorted(set(semantics) & ARCHITECTURAL_SEMANTICS)
    behavioral_hits = sorted(set(semantics) & BEHAVIORAL_CONTROL_PLANE_SEMANTICS)
    if architecture_hits:
        classification = "ARCHITECTURE_CHANGING"
    elif behavioral_hits:
        classification = "BEHAVIORAL_CONTROL_PLANE_CHANGE"
    elif "publication_only" in semantics:
        classification = "RELEASE_ONLY"
    elif "data_refresh_only" in semantics:
        classification = "DATA_REFRESH_ONLY"
    elif "current_surface_only" in semantics:
        classification = "PRESENTATION_ONLY"
    else:
        classification = "NONE"

    if declared_classification is not None and declared_classification != classification:
        raise ArchitectureImpactError(
            f"declared classification {declared_classification!r} disagrees with semantic classification {classification!r}"
        )
    if classification in {"ARCHITECTURE_CHANGING", "BEHAVIORAL_CONTROL_PLANE_CHANGE"} and not evidence_refs:
        raise ArchitectureImpactError(f"{classification} requires semantic evidence references")

    result = {
        "schema_version": SCHEMA_VERSION,
        "classification": classification,
        "legacy_identity_impact": LEGACY_IDENTITY_IMPACT[classification],
        "semantic_changes": semantics,
        "architecture_markers": architecture_hits,
        "behavioral_control_plane_markers": behavioral_hits,
        "changed_paths": paths,
        "evidence": evidence_refs,
        "current_identity_sync_required": classification in {"ARCHITECTURE_CHANGING", "BEHAVIORAL_CONTROL_PLANE_CHANGE"},
        "claim_ceiling": "Repository-local semantic classification only; no external truth, Owner authority or epistemic upgrade is inferred.",
    }
    return validate_classification(result)


def validate_classification(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a machine-readable classification and return a safe copy."""

    if not isinstance(document, Mapping):
        raise ArchitectureImpactError("architecture-impact classification must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ArchitectureImpactError("architecture-impact schema version mismatch")
    classification = value.get("classification")
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise ArchitectureImpactError(f"unknown architecture-impact classification: {classification!r}")
    expected_legacy = LEGACY_IDENTITY_IMPACT[classification]
    if value.get("legacy_identity_impact") != expected_legacy:
        raise ArchitectureImpactError("legacy identity impact does not match semantic classification")
    semantics = value.get("semantic_changes")
    if not isinstance(semantics, list) or semantics != sorted(set(semantics)) or any(not isinstance(item, str) or not item for item in semantics):
        raise ArchitectureImpactError("semantic_changes must be a sorted unique non-empty string list")
    unknown = sorted(set(semantics) - ARCHITECTURAL_SEMANTICS - BEHAVIORAL_CONTROL_PLANE_SEMANTICS - NON_ARCHITECTURAL_SEMANTICS)
    if unknown:
        raise ArchitectureImpactError(f"unknown semantic change markers: {', '.join(unknown)}")
    architecture_hits = sorted(set(semantics) & ARCHITECTURAL_SEMANTICS)
    behavioral_hits = sorted(set(semantics) & BEHAVIORAL_CONTROL_PLANE_SEMANTICS)
    if value.get("architecture_markers") != architecture_hits:
        raise ArchitectureImpactError("architecture_markers are not derived from semantic_changes")
    if value.get("behavioral_control_plane_markers") != behavioral_hits:
        raise ArchitectureImpactError("behavioral_control_plane_markers are not derived from semantic_changes")
    paths = value.get("changed_paths")
    evidence = value.get("evidence")
    for field, items in (("changed_paths", paths), ("evidence", evidence)):
        if not isinstance(items, list) or items != sorted(set(items)) or any(not isinstance(item, str) or not item for item in items):
            raise ArchitectureImpactError(f"{field} must be a sorted unique non-empty string list")
    expected = "ARCHITECTURE_CHANGING" if architecture_hits else "BEHAVIORAL_CONTROL_PLANE_CHANGE" if behavioral_hits else "RELEASE_ONLY" if "publication_only" in semantics else "DATA_REFRESH_ONLY" if "data_refresh_only" in semantics else "PRESENTATION_ONLY" if "current_surface_only" in semantics else "NONE"
    if classification != expected:
        raise ArchitectureImpactError("classification is not derived from semantic_changes")
    if classification in {"ARCHITECTURE_CHANGING", "BEHAVIORAL_CONTROL_PLANE_CHANGE"} and not evidence:
        raise ArchitectureImpactError(f"{classification} requires evidence")
    expected_sync = classification in {"ARCHITECTURE_CHANGING", "BEHAVIORAL_CONTROL_PLANE_CHANGE"}
    if value.get("current_identity_sync_required") is not expected_sync:
        raise ArchitectureImpactError("current_identity_sync_required is inconsistent")
    if not isinstance(value.get("claim_ceiling"), str) or not value["claim_ceiling"].strip():
        raise ArchitectureImpactError("claim_ceiling is required")
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - bootstrap fallback
        return value
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        raise ArchitectureImpactError(f"schema violation at {error.json_path}: {error.message}")
    return value


__all__ = [
    "ALLOWED_CLASSIFICATIONS",
    "ARCHITECTURE_CHANGING",
    "ArchitectureImpactError",
    "BEHAVIORAL_CONTROL_PLANE_SEMANTICS",
    "BEHAVIORAL_CONTROL_PLANE_CHANGE",
    "classify_change",
    "validate_classification",
]
