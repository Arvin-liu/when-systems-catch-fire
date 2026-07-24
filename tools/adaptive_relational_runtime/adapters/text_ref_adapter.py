# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Text / transcript source adapter (read-only, typed reference only).

The public formal repo NEVER receives full private note text. This adapter
resolves a typed reference (1111 object id + digest) to a SANITIZED record:
- the digest (already in the manifest),
- a short original paraphrase (authored for testing, not copied verbatim),
- aggregate counts that do not reconstruct private source text.

It reads an optional local evidence stub only to confirm the reference exists;
it never loads or emits full private content.
"""
from __future__ import annotations

from typing import Any


def adapt_text_ref(ref: dict, *, local_evidence_root: str | None = None) -> dict[str, Any]:
    """Return a sanitized representation record for a text/transcript source.

    ref keys: object_id, digest, visibility, short_paraphrase (optional),
    aggregate_counts (optional).
    """
    if ref.get("visibility") not in ("private_1111", "public_formal"):
        raise ValueError(f"text_ref_adapter: unsupported visibility {ref.get('visibility')!r}")

    record: dict[str, Any] = {
        "adapter": "text_ref",
        "object_id": ref["object_id"],
        "digest": ref["digest"],
        "visibility": ref["visibility"],
        "short_paraphrase": ref.get("short_paraphrase", ""),
        "aggregate_counts": ref.get("aggregate_counts", {}),
        "full_content_present": False,
        "read_only": True,
    }
    # If a local evidence root is supplied, confirm the reference digest file
    # exists without reading its contents into the public artifact.
    if local_evidence_root is not None:
        from pathlib import Path
        stub = Path(local_evidence_root) / f"{ref['object_id']}.ref.json"
        record["evidence_stub_present"] = stub.exists()
    return record
