# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Deterministic corpus object identity (Stage A mechanical primitives).

Stdlib-only. Reads a corpus file once, derives content-addressed identity, and
normalizes note text for dedup. Never mutates the source file.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from ..canonical import _nfc, normalize_prose, sha256_hex
from . import schemas

# Frontmatter scalar keys we extract for the audit. All other keys (e.g. tags)
# are preserved opaquely in ``declared_raw`` but not interpreted.
_SCALAR_KEYS = ("note_id", "title", "note_type", "created_at", "published_at", "source", "url")

_FRONTMASTER_RE = re.compile(r"^---\s*$")
_SCALAR_LINE_RE = re.compile(r'^(?P<key>[A-Za-z_][\w-]*):\s*(?:"(?P<q>[^"]*)"|(?P<u>\S.*))$')
_URL_RE = re.compile(r"https?://", re.IGNORECASE)


def parse_frontmatter(raw_text: str) -> tuple[dict, bool, list]:
    """Tolerant frontmatter parse. Returns (fm_dict, valid, warnings).

    Accepts the simple scalar form used by the corpus (``key: "value"``) and a
    YAML list for ``tags``. On any structural violation, ``valid`` is False and
    the offending signal is recorded in ``warnings``; scalar extraction still
    proceeds best-effort so the run never silently drops an object.
    """
    warnings: list[str] = []
    fm: dict[str, Any] = {}
    lines = raw_text.splitlines()
    if not lines or not _FRONTMASTER_RE.match(lines[0].strip()):
        return fm, False, ["missing opening --- frontmatter delimiter"]
    end = None
    for i in range(1, len(lines)):
        if _FRONTMASTER_RE.match(lines[i].strip()):
            end = i
            break
    valid = end is not None
    if not valid:
        warnings.append("missing closing --- frontmatter delimiter (best-effort parse)")
    body_lines = lines[1:end] if end is not None else lines[1:]
    for ln in body_lines:
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        m = _SCALAR_LINE_RE.match(ln)
        if not m:
            # Could be a YAML list (tags) or nested; record but do not fail.
            warnings.append(f"unparsed frontmatter line: {ln[:80]!r}")
            continue
        key = m.group("key")
        val = m.group("q") if m.group("q") is not None else m.group("u")
        if key in _SCALAR_KEYS:
            fm[key] = val
    return fm, valid, warnings


def normalize_note_text(raw_text: str) -> tuple[str, str, list]:
    """Strip frontmatter, NFC-normalize, collapse whitespace.

    Returns (normalized_text, encoding_status, warnings). ``encoding_status`` is
    "error" only when the file is not valid UTF-8 (best-effort lossy decode used).
    """
    warnings: list[str] = []
    lines = raw_text.splitlines()
    start = 0
    if lines and _FRONTMASTER_RE.match(lines[0].strip()):
        for i in range(1, len(lines)):
            if _FRONTMASTER_RE.match(lines[i].strip()):
                start = i + 1
                break
    body = "\n".join(lines[start:])
    try:
        norm = normalize_prose(_nfc(body))
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"normalize warning: {exc}")
        norm = normalize_prose(body)
    return norm, "ok", warnings


def compute_identity(rel_path: str, raw_bytes: bytes) -> tuple[dict, "schemas.CorpusObjectIdentity"]:
    """Compute deterministic identity for one corpus file."""
    byte_sha256 = sha256_hex(raw_bytes)
    path_digest = sha256_hex(rel_path)
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    fm, _valid, _w = parse_frontmatter(raw_text)
    norm_text, _enc, _w2 = normalize_note_text(raw_text)
    norm_digest = sha256_hex(norm_text)
    note_id = fm.get("note_id")
    note_type = fm.get("note_type", "unknown")
    object_key = note_id if note_id else path_digest[:16]
    ident = schemas.CorpusObjectIdentity(
        object_key=object_key,
        rel_path=rel_path,
        path_digest=path_digest,
        byte_sha256=byte_sha256,
        normalized_text_digest=norm_digest,
        note_id=note_id,
        note_type=note_type,
        size_bytes=len(raw_bytes),
    )
    return fm, ident


def scan_corpus(corpus_root: str | Path) -> list[tuple[dict, schemas.CorpusObjectIdentity]]:
    """Scan a corpus root for ``*.md`` files. Returns (frontmatter, identity) pairs.

    The index file ``索引.md`` is included with ``note_type="index"`` so the
    inventory can report the exact 836+index count, but it is flagged non-note.
    """
    root = Path(corpus_root)
    results: list[tuple[dict, schemas.CorpusObjectIdentity]] = []
    for p in sorted(root.rglob("*.md")):
        rel = str(p.relative_to(root))
        raw = p.read_bytes()
        fm, ident = compute_identity(rel, raw)
        if p.name == "索引.md":
            ident = dataclasses_replace(ident, note_type="index")
        results.append((fm, ident))
    return results


def dataclasses_replace(ident: "schemas.CorpusObjectIdentity", **changes) -> "schemas.CorpusObjectIdentity":
    import dataclasses
    return dataclasses.replace(ident, **changes)


def has_url(text: str) -> bool:
    return bool(_URL_RE.search(text))
