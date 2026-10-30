# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Mechanism / system-state object adapter (read-only).

Consumes a typed reference to a real Function OS capability record, mechanism
contract, execution profile, or state snapshot. Reads the already-fetched
record and returns a sanitized reference. It additionally asserts that the
referenced capability is DECLARED in the adapter-capabilities registry — the
Function OS adapter must never call an undeclared capability (acceptance
matrix boundary).
"""
from __future__ import annotations

from typing import Any


def adapt_mechanism_state(ref: dict, *,
                          declared_capabilities: set[str] | None = None,
                          local_evidence_root: str | None = None) -> dict[str, Any]:
    capability = ref.get("capability")
    if not capability:
        raise ValueError("mechanism_state_adapter: capability is required")
    if declared_capabilities is not None and capability not in declared_capabilities:
        raise ValueError(
            f"mechanism_state_adapter: capability {capability!r} is not declared "
            f"in adapter-capabilities (Function OS may not call undeclared capabilities)")

    record: dict[str, Any] = {
        "adapter": "mechanism_state",
        "object_id": ref.get("object_id"),
        "capability": capability,
        "capability_declared": True if declared_capabilities is None else (capability in declared_capabilities),
        "digest": ref.get("digest"),
        "read_only": True,
    }
    if local_evidence_root is not None:
        from pathlib import Path
        stub = Path(local_evidence_root) / f"{ref['object_id']}.ref.json"
        record["evidence_stub_present"] = stub.exists()
    return record
