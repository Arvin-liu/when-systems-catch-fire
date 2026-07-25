# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Stage B — bounded semantic ARR batch adapter (IGNITION §7-§8).

This adapter extracts ONLY bounded, typed candidate structures and enforces the
epistemic ceilings. It MUST NOT:
  * call PROMOTE or EVOLVE,
  * perform any real-world action,
  * elevate a speaker/company claim to ``INDEPENDENTLY_VERIFIED``,
  * infer event year from folder name or replace missing event time with the
    note creation time,
  * embed note body text in any receipt (only hashes + typed fields + a derived
    date string when explicitly framed).

The processor re-reads the source file read-only to apply a CONSERVATIVE event-date
heuristic; it stores the derived date, never the body.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import schemas
from .identity import compute_identity, has_url
from .private_ref import build_private_ref

# Conservative, fully-explicit event-date extraction. We require the COMPLETE
# ``YEAR年MONTH月DAY日`` span anywhere in the body. A bare year, a month/day
# without a year, or a folder-derived year is NEVER accepted (missing time is
# not guessed, and the year is never inferred from the path).
_EVENT_RE = re.compile(
    r"((?:19|20)\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
)


def classify_claim(rec: schemas.StageAMechanicalRecord) -> str:
    """Map note type to a conservative claim class. Never INDEPENDENTLY_VERIFIED."""
    mapping = {
        "link": "SECONDARY_ARCHIVE_CLAIM",
        "plain_text": "AUTHOR_OBSERVATION",
        "local_audio": "TRANSCRIPT_INFERENCE",
        "recorder_audio": "TRANSCRIPT_INFERENCE",
        "index": "UNKNOWN",
    }
    return mapping.get(rec.identity.note_type, "UNKNOWN")


def extract_event_time(text: str) -> str:
    """Return an explicitly-framed event date (YYYY-MM-DD) or UNKNOWN."""
    m = _EVENT_RE.search(text)
    if not m:
        return schemas.UNKNOWN_TIME
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return schemas.UNKNOWN_TIME
    return f"{y}-{mo:02d}-{d:02d}"


def build_temporal(rec: schemas.StageAMechanicalRecord, text: str) -> dict:
    event_time = extract_event_time(text)
    note_created_at = rec.declared_times.get("created_at", schemas.UNKNOWN_TIME)
    publication_time = rec.declared_times.get("published_at", schemas.UNKNOWN_TIME)
    scope = event_time[:4] if event_time != schemas.UNKNOWN_TIME else schemas.UNKNOWN_TIME
    unknowns = [
        f
        for f in ("event_time", "publication_time", "note_created_at", "observed_at",
                  "ingested_at", "valid_from", "valid_to")
        if {
            "event_time": event_time,
            "publication_time": publication_time,
            "note_created_at": note_created_at,
            "observed_at": schemas.UNKNOWN_TIME,
            "ingested_at": schemas.UNKNOWN_TIME,
            "valid_from": schemas.UNKNOWN_TIME,
            "valid_to": schemas.UNKNOWN_TIME,
        }[f] == schemas.UNKNOWN_TIME
    ]
    return {
        "event_time": event_time,
        "publication_time": publication_time,
        "note_created_at": note_created_at,
        "observed_at": schemas.UNKNOWN_TIME,
        "ingested_at": schemas.UNKNOWN_TIME,
        "valid_from": schemas.UNKNOWN_TIME,
        "valid_to": schemas.UNKNOWN_TIME,
        "temporal_scope": scope,
        "temporal_unknowns": unknowns,
    }


def build_envelope(run_id: str, rec: schemas.StageAMechanicalRecord, claim_class: str, temporal: dict) -> schemas.CorpusEnvelope:
    return schemas.CorpusEnvelope(
        envelope_id=schemas.make_envelope_id(run_id, rec.identity.object_key),
        object_key=rec.identity.object_key,
        claim_class=claim_class,
        claim_surface={
            "note_type": rec.identity.note_type,
            "source_ref_present": rec.source_ref_present,
            "title_present": rec.title_present,
        },
        temporal=temporal,
        inference_labeled=True,
    )


def default_semantic_processor(corpus_root: str | Path):
    """Factory: returns a ``ProcessFn`` wired to the bounded semantic adapter.

    Re-reads each source file read-only (no mutation) to apply the conservative
    event-date heuristic. Emits one final receipt per note with epistemic
    ceilings enforced.
    """
    root = Path(corpus_root)

    def _process(rec: schemas.StageAMechanicalRecord, ctx: dict) -> tuple[str, dict]:
        claim_class = classify_claim(rec)
        path = root / rec.identity.rel_path
        text = ""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ""
        temporal = build_temporal(rec, text)
        envelope = build_envelope(ctx["run_id"], rec, claim_class, temporal)
        if not rec.frontmatter_valid:
            outcome = "EXPECTED_QUARANTINE"
        elif claim_class == "UNKNOWN":
            outcome = "EXPECTED_UNKNOWN"
        else:
            outcome = "SUCCESS"
        receipt = schemas.CorpusReceipt(
            receipt_id=schemas.make_receipt_id(ctx["run_id"], rec.identity.object_key),
            run_id=ctx["run_id"],
            object_key=rec.identity.object_key,
            note_type=rec.identity.note_type,
            path_digest=rec.identity.path_digest,
            byte_sha256=rec.identity.byte_sha256,
            normalized_text_digest=rec.identity.normalized_text_digest,
            outcome=outcome,
            claim_class=claim_class,
            temporal=temporal,
            source_ref_present=rec.source_ref_present,
            rights_boundary=rec.rights_boundary,
            private_ref=build_private_ref(rec),
            real_world_action=False,
            promote=False,
            evolve=False,
            generated_at=schemas.RENDER_STAMP,
        )
        payload = receipt.to_dict()
        payload["envelope_id"] = envelope.envelope_id
        payload["envelope"] = envelope.to_dict()
        return outcome, payload

    return _process
