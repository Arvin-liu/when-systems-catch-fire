# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Structured-data object adapter (read-only).

Consumes a typed reference to a real registry / manifest / topology / map /
schema-conformant project record. Reads the already-fetched local evidence and
returns a sanitized reference (digest + type + aggregate counts), never the
full payload into the public artifact.
"""
from __future__ import annotations

from typing import Any


def adapt_structured_data(ref: dict, *, local_evidence_root: str | None = None) -> dict[str, Any]:
    data_kind = ref.get("data_kind")
    if not data_kind:
        raise ValueError("structured_data_adapter: data_kind is required")

    record: dict[str, Any] = {
        "adapter": "structured_data",
        "object_id": ref.get("object_id"),
        "data_kind": data_kind,
        "digest": ref.get("digest"),
        "aggregate_counts": ref.get("aggregate_counts", {}),
        "read_only": True,
    }
    if local_evidence_root is not None:
        from pathlib import Path
        stub = Path(local_evidence_root) / f"{ref['object_id']}.ref.json"
        record["evidence_stub_present"] = stub.exists()
    return record
