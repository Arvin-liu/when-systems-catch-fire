# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Temporal event-sequence adapter (read-only).

Consumes a typed reference to a real declared repository/project history with
event / observation / ingestion times kept SEPARATE (the pilot must not replace
event time with note/download time). Returns a sanitized reference preserving
the separated time axes.
"""
from __future__ import annotations

from typing import Any


def adapt_temporal_sequence(ref: dict, *, local_evidence_root: str | None = None) -> dict[str, Any]:
    # The three time axes must be modeled explicitly and never collapsed.
    for axis in ("event_time", "observation_time", "ingestion_time"):
        if axis not in ref and axis != "ingestion_time":
            # event_time and observation_time are required to keep them distinct
            if axis in ("event_time", "observation_time") and axis not in ref:
                raise ValueError(f"temporal_sequence_adapter: missing required {axis}")

    record: dict[str, Any] = {
        "adapter": "temporal_sequence",
        "object_id": ref.get("object_id"),
        "event_time": ref.get("event_time"),
        "observation_time": ref.get("observation_time"),
        "ingestion_time": ref.get("ingestion_time"),
        "time_axes_kept_separate": True,
        "read_only": True,
    }
    if local_evidence_root is not None:
        from pathlib import Path
        stub = Path(local_evidence_root) / f"{ref['object_id']}.ref.json"
        record["evidence_stub_present"] = stub.exists()
    return record
