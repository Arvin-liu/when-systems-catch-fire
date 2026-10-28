# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Validator for the immutable R2 real-object selection manifest (ADR-R2 contract).

The manifest must:
- validate against real-object-selection-manifest.schema.json;
- contain EXACTLY 48 objects;
- assign unique object_ids (OBJ-01..OBJ-48);
- never permit a private/third_party/personal object to carry a
  permitted_formal_representation that would copy excluded content into the
  public repo (privacy boundary enforced by the privacy auditor, but the
  validator rejects obviously impossible representations up front).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.ignition_runtime.schemas_loader import Draft202012Validator

from . import canonical

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas/architecture/adaptive-relational-runtime"
REQUIRED_COUNT = 48


class ManifestValidationError(Exception):
    """Raised when the selection manifest violates the R2 contract."""


def _load_schema() -> dict:
    return json.loads(
        (SCHEMA_DIR / "real-object-selection-manifest.schema.json").read_text(encoding="utf-8")
    )


def validate_manifest(manifest: dict) -> dict:
    """Validate and return the manifest with derived invariants.

    Raises ManifestValidationError on any contract violation.
    """
    schema = _load_schema()
    errors = sorted(
        Draft202012Validator(schema).iter_errors(manifest), key=lambda e: list(e.path)
    )
    if errors:
        first = errors[0]
        loc = ".".join(str(p) for p in first.path) or "<root>"
        raise ManifestValidationError(f"manifest schema error at {loc}: {first.message}")

    objects = manifest["objects"]
    if len(objects) != REQUIRED_COUNT:
        raise ManifestValidationError(
            f"manifest must contain exactly {REQUIRED_COUNT} objects, got {len(objects)}")

    ids = [o["object_id"] for o in objects]
    if len(set(ids)) != len(ids):
        raise ManifestValidationError("object_id values must be unique")

    expected = {f"OBJ-{i:02d}" for i in range(1, REQUIRED_COUNT + 1)}
    if set(ids) != expected:
        raise ManifestValidationError(
            f"object_ids must be exactly {sorted(expected)}")

    # Privacy boundary: any object whose rights_tier is third_party_copyright or
    # personal_data must NOT permit a representation that copies content.
    for o in objects:
        if o["rights_tier"] in ("third_party_copyright", "personal_data"):
            rep = o["permitted_formal_representation"].lower()
            if "full text" in rep or "verbatim" in rep or "transcript" in rep:
                raise ManifestValidationError(
                    f"{o['object_id']}: {o['rights_tier']} may not carry a content-copying representation")

    manifest_digest = canonical.sha256_hex(canonical.canonical_json({
        "pilot_id": manifest["pilot_id"],
        "object_count": manifest["object_count"],
        "objects": ids,
    }))
    return {
        "valid": True,
        "object_count": len(objects),
        "object_ids": ids,
        "manifest_digest": manifest_digest,
    }
