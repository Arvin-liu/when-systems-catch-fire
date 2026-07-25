# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Stage A — deterministic mechanical pass over a corpus.

Reads each file once (read-only), derives identity via ``identity.compute_identity``
and records mechanical metadata: title presence, frontmatter validity, encoding
status, body presence/length class, declared time fields, source-reference
presence, rights boundary, parse warnings. Produces the immutable manifest and
the inventory/audit transforms as plain dicts (the runner writes them to the
private evidence workspace).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import schemas
from .identity import compute_identity, has_url, normalize_note_text, parse_frontmatter


def _body_length_class(normalized_text: str) -> str:
    n = len(normalized_text)
    if n == 0:
        return "empty"
    if n < 800:
        return "short"
    if n < 4000:
        return "medium"
    return "long"


def stage_a_mechanical_pass(corpus_root: str | Path) -> list[schemas.StageAMechanicalRecord]:
    """Scan the corpus root and build one Stage A record per ``*.md`` file."""
    root = Path(corpus_root)
    records: list[schemas.StageAMechanicalRecord] = []
    for p in sorted(root.rglob("*.md")):
        rel = str(p.relative_to(root))
        raw = p.read_bytes()
        raw_text = raw.decode("utf-8", errors="replace")
        # strict encoding check
        try:
            raw.decode("utf-8")
            encoding_status = "ok"
        except UnicodeDecodeError:
            encoding_status = "error"
        fm, valid, fm_warnings = parse_frontmatter(raw_text)
        norm_text, _enc, norm_warnings = normalize_note_text(raw_text)
        if p.name == "索引.md":
            valid = False if not valid else valid
            # index is not a note; keep mechanical record but mark type index
            fm = dict(fm)
            fm["note_type"] = "index"
        ident = compute_identity(rel, raw)[1]
        if p.name == "索引.md":
            ident = schemas.CorpusObjectIdentity(
                object_key="索引.md",
                rel_path=rel,
                path_digest=ident.path_digest,
                byte_sha256=ident.byte_sha256,
                normalized_text_digest=ident.normalized_text_digest,
                note_id=None,
                note_type="index",
                size_bytes=ident.size_bytes,
            )
        declared_times = {
            k: fm[k] for k in ("created_at", "published_at", "event_time") if k in fm
        }
        rec = schemas.StageAMechanicalRecord(
            identity=ident,
            title_present=bool(fm.get("title")),
            frontmatter_valid=valid,
            encoding_status=encoding_status,
            body_present=len(norm_text.strip()) > 0,
            body_length_class=_body_length_class(norm_text),
            declared_times=declared_times,
            source_ref_present=has_url(raw_text),
            rights_boundary="private",
            parse_warnings=fm_warnings + norm_warnings,
        )
        records.append(rec)
    return records


def build_corpus_manifest(records: list[schemas.StageAMechanicalRecord], frozen_corpus_ref: str) -> dict:
    notes = [r for r in records if r.identity.note_type != "index"]
    index = [r for r in records if r.identity.note_type == "index"]
    return {
        "schema": "corpus_manifest/v1",
        "frozen_corpus_ref": frozen_corpus_ref,
        "expected_notes": 836,
        "note_count": len(notes),
        "index_count": len(index),
        "total_paths": len(records),
        "type_distribution": _type_distribution(notes),
        "identities": [r.identity.to_dict() for r in records],
    }


def build_corpus_inventory(records: list[schemas.StageAMechanicalRecord]) -> dict:
    return {
        "schema": "corpus_inventory/v1",
        "count": len(records),
        "entries": [
            {
                "object_key": r.identity.object_key,
                "rel_path": r.identity.rel_path,
                "note_id": r.identity.note_id,
                "note_type": r.identity.note_type,
                "size_bytes": r.identity.size_bytes,
                "byte_sha256": r.identity.byte_sha256,
                "normalized_text_digest": r.identity.normalized_text_digest,
                "is_note": r.identity.note_type != "index",
            }
            for r in records
        ],
    }


def build_frontmatter_audit(records: list[schemas.StageAMechanicalRecord]) -> dict:
    invalid = [r.identity.object_key for r in records if not r.frontmatter_valid]
    return {
        "schema": "frontmatter_audit/v1",
        "total": len(records),
        "valid": sum(1 for r in records if r.frontmatter_valid),
        "invalid_object_keys": invalid,
        "warnings_by_key": {
            r.identity.object_key: r.parse_warnings for r in records if r.parse_warnings
        },
    }


def build_note_id_audit(records: list[schemas.StageAMechanicalRecord]) -> dict:
    seen: dict[str, list[str]] = {}
    for r in records:
        nid = r.identity.note_id
        if nid is None:
            continue
        seen.setdefault(nid, []).append(r.identity.object_key)
    duplicates = {nid: keys for nid, keys in seen.items() if len(keys) > 1}
    path_mismatch = [
        r.identity.object_key
        for r in records
        if r.identity.note_id is not None
        and not r.identity.rel_path.startswith(r.identity.note_id)
    ]
    return {
        "schema": "note_id_audit/v1",
        "distinct_note_ids": len(seen),
        "duplicate_note_id_groups": duplicates,
        "path_note_id_mismatches": path_mismatch,
    }


def build_encoding_parse_errors(records: list[schemas.StageAMechanicalRecord]) -> dict:
    errors = [
        {
            "object_key": r.identity.object_key,
            "encoding_status": r.encoding_status,
            "parse_warnings": r.parse_warnings,
        }
        for r in records
        if r.encoding_status != "ok" or r.parse_warnings
    ]
    return {
        "schema": "encoding_and_parse_errors/v1",
        "error_count": len(errors),
        "entries": errors,
    }


def _type_distribution(notes: list[schemas.StageAMechanicalRecord]) -> dict:
    dist: dict[str, int] = {}
    for r in notes:
        dist[r.identity.note_type] = dist.get(r.identity.note_type, 0) + 1
    return dist
