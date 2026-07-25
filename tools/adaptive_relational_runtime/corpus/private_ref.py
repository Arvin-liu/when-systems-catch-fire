# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Privacy-aware private-reference exporter (IGNITION §12).

Produces a typed reference (kind + note_id + content hashes) only. It NEVER
carries note body text, titles, audio transcripts, or anything sufficient to
reconstruct private content. The public formal repository may store these typed
references; the full per-note detail lives only in the private evidence branch.
"""
from __future__ import annotations

from . import schemas


def build_private_ref(rec: schemas.StageAMechanicalRecord) -> dict:
    return {
        "kind": "corpus_note",
        "note_id": rec.identity.note_id,
        "note_type": rec.identity.note_type,
        "byte_sha256": rec.identity.byte_sha256,
        "path_digest": rec.identity.path_digest,
        "normalized_text_digest": rec.identity.normalized_text_digest,
    }


def export_receipt_ref(receipt_dict: dict) -> dict:
    """Export a hash+typed reference slice of a receipt (public-safe subset)."""
    return {
        "object_key": receipt_dict.get("object_key"),
        "note_type": receipt_dict.get("note_type"),
        "outcome": receipt_dict.get("outcome"),
        "claim_class": receipt_dict.get("claim_class"),
        "byte_sha256": receipt_dict.get("byte_sha256"),
        "path_digest": receipt_dict.get("path_digest"),
        "real_world_action": receipt_dict.get("real_world_action"),
        "promote": receipt_dict.get("promote"),
        "evolve": receipt_dict.get("evolve"),
    }
