# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Deterministic identity + canonicalization for the Adaptive Relational Runtime.

Stdlib-only. Mirrors the ``tools/ignition_runtime/hashutil.deterministic_id``
convention (prefix + first 32 hex of sha256) and the six-rule canonicalization
contract from docs/architecture/object-relation-mechanism-model.md section 3.

This module contains no execution surface and no second-executor references; it
is a pure content-addressing helper used by the runtime engine and adapters.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

# Identity input excludes record_id and the declared runtime-annotation fields
# (lifecycle.entered_at_scope; a registered extensions.x_provenance_ingest if
# present). Everything else -- time, provenance, scope -- participates.
_RUNTIME_ANNOTATION_KEYS = ("entered_at_scope", "x_provenance_ingest")

# Set-semantics arrays: element-canonicalized then SORTED before hashing
# (order-independent identity). Source: object-model rule 4.
_SET_SEMANTICS_KEYS = frozenset(
    {"endpoints", "provenance", "observation_refs", "evidence_refs",
     "alternatives", "object_refs", "subject_refs"}
)

_WS_RE = re.compile(r"\s+")


def canonical_json(obj: Any) -> str:
    """Rule 3/5: recursive key sorting, compact separators, deterministic form."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _nfc(text: str) -> str:
    """Rule 1: Unicode NFC normalization for all strings."""
    return unicodedata.normalize("NFC", text)


def trim_fold(text: str) -> str:
    """Rule 2 (prose only): trim + internal whitespace folding."""
    return _WS_RE.sub(" ", text).strip()


def normalize_prose(text: str) -> str:
    """Rule 1 + Rule 2 applied to a prose field."""
    return trim_fold(_nfc(text))


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def deterministic_id(prefix: str, payload: str) -> str:
    """Record id = ``<prefix>_<first 32 hex of sha256(payload)>`` (section 3)."""
    return f"{prefix}_{sha256_hex(payload)[:32]}"


def _nfc_recursive(obj: Any) -> Any:
    """Rule 1: apply Unicode NFC normalization to every string value."""
    if isinstance(obj, str):
        return _nfc(obj)
    if isinstance(obj, list):
        return [_nfc_recursive(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _nfc_recursive(v) for k, v in obj.items()}
    return obj


def record_id(prefix: str, record: dict) -> str:
    """Compute a deterministic record id from canonical content + declared scope.

    ``record_id`` itself and the declared runtime-annotation fields are removed
    before hashing; the remaining content (including ``scope`` and ``time``)
    participates in the identity. Set-semantics arrays are sorted (rule 4) and
    all strings are NFC-normalized (rule 1) before hashing.
    """
    core = {k: v for k, v in record.items() if k != "record_id"}
    if isinstance(core.get("lifecycle"), dict):
        core["lifecycle"] = {
            k: v for k, v in core["lifecycle"].items()
            if k not in _RUNTIME_ANNOTATION_KEYS
        }
    if isinstance(core.get("extensions"), dict):
        core["extensions"] = {
            k: v for k, v in core["extensions"].items()
            if k not in _RUNTIME_ANNOTATION_KEYS
        }
    core = _nfc_recursive(core)
    for key in _SET_SEMANTICS_KEYS:
        if key in core and isinstance(core[key], list):
            core[key] = sorted(core[key], key=canonical_json)
    return deterministic_id(prefix, canonical_json(core))


def reorder_invariance_check() -> bool:
    """Inline self-check (not a committed test file): two differently-ordered
    equivalent inputs must yield identical ids.

    Exercises rule 3 (key sorting), rule 4 (set-semantics arrays normalized by
    (role, ref) order) and rule 6 (null/absent distinct, content-addressing).
    """
    base = {
        "scope": {"domain": "d", "context_ref": None},
        "provenance": ["b", "a"],
        "time": {"ingestion_time": "2026-07-24T00:00:00Z"},
        "endpoints": [
            {"role": "subject", "ref": "x1"},
            {"role": "object", "ref": "x2"},
        ],
        "value": "héllo",
    }
    reordered = {
        "value": "héllo",
        "endpoints": [
            {"ref": "x2", "role": "object"},
            {"role": "subject", "ref": "x1"},
        ],
        "time": {"ingestion_time": "2026-07-24T00:00:00Z"},
        "provenance": ["a", "b"],
        "scope": {"context_ref": None, "domain": "d"},
    }
    id_a = record_id("rel", base)
    id_b = record_id("rel", reordered)
    return id_a == id_b


if __name__ == "__main__":
    ok = reorder_invariance_check()
    print("canonical reorder-invariance:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
