"""121Q6C Step 003: minimal READ-ONLY legacy asset importer.

Scope: ONLY assets classified IMPORTABLE_NOW in asset-bridge-audit-35.json
(core framework definitions: meta_function + psi0_definition).
Produces an N1 FunctionSpec *draft* (NOT executable) with provenance,
source_hash, extraction_warnings, manual_review_required=True.

Hard rules (per protocol):
- Read-only: never mutates the source asset.
- Never guesses formula / variables / preconditions / postconditions.
- If a required field cannot be reliably extracted -> mark BLOCKED, do not fabricate.
- Symbolic markdown only; no weight-space / probabilistic semantics.
"""
import hashlib
import json
import os
import re
from typing import Dict, Any, Optional

ALLOWED_CLASSES = {"IMPORTABLE_NOW"}
SPEC_VERSION = "0.2.1-candidate"


def _source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _extract_title(text: str) -> Optional[str]:
    for line in text.splitlines():
        m = re.match(r"^#+\s+(.*)$", line.strip())
        if m:
            return m.group(1).strip()
    return None


def _count_symbols(text: str) -> int:
    math_blocks = len(re.findall(r"\$\$.*?\$\$|\$.*?\$", text, re.S))
    ops = len(re.findall(r"[∀∃∈⊆⊂→↔∧∨¬⇒⇔∂∇∫∑∏≡≈≤≥]", text))
    return math_blocks + ops


def import_asset(asset_record: Dict[str, Any], source_text: Optional[str] = None) -> Dict[str, Any]:
    if asset_record.get("classification") not in ALLOWED_CLASSES:
        return {
            "status": "BLOCKED",
            "reason": "asset not in IMPORTABLE_NOW set; importer is read-only and scoped",
            "asset_id": asset_record.get("asset_id"),
        }
    if source_text is None:
        return {
            "status": "BLOCKED",
            "reason": "source_text not supplied; importer refuses to guess asset body",
            "asset_id": asset_record.get("asset_id"),
            "manual_review_required": True,
        }
    src_hash = _source_hash(source_text)
    title = _extract_title(source_text)
    sym = _count_symbols(source_text)
    warnings = []
    if title is None:
        warnings.append("no markdown heading found; name unset")
    if sym == 0:
        warnings.append("no symbolic/math content detected; likely non-symbolic")
    draft = {
        "function_id": "DRAFT-" + asset_record["asset_id"],
        "spec_version": SPEC_VERSION,
        "name": title or asset_record["file_name"],
        "domain": "legacy_symbolic",
        "inputs": {},
        "outputs": {},
        "preconditions": [],
        "postconditions": [],
        "effects_declared": ["pure"],
        "provenance": {
            "source_asset_id": asset_record["asset_id"],
            "source_path": asset_record.get("source_path"),
            "source_hash": src_hash,
            "carrier_type": asset_record.get("carrier_type"),
            "extraction_warnings": warnings,
            "manual_review_required": True,
            "importer": "legacy_asset_importer@v0.2.1-candidate",
        },
        "created_at": "2026-07-15T12:00:00Z",
    }
    return {"status": "DRAFT_OK", "draft": draft, "asset_id": asset_record["asset_id"]}


if __name__ == "__main__":
    print("legacy_asset_importer: read-only draft generator; run via tests.")
