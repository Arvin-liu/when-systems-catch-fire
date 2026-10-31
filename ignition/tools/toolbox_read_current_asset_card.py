#!/usr/bin/env python3
"""Read one exact Current Foundation record and return a source-hashed card."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]

FUNCTION_CARDS = "ignition/data/foundation/function-assets/identity-cards.jsonl"
NONFUNCTION_CLAIMS = "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
AUTHORITY_PATHS = {
    "function_identity_cards": FUNCTION_CARDS,
    "nonfunction_claim_registry": NONFUNCTION_CLAIMS,
}
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


class CurrentAssetReadError(ValueError):
    """Raised when an exact Current record cannot be read safely."""


def _safe_repo_file(repo_root: Path, relative_path: str) -> bytes:
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        raise CurrentAssetReadError("authority paths must remain under ignition/")
    root = Path(repo_root)
    if root.is_symlink():
        raise CurrentAssetReadError("repository root must not be a symlink")
    root = root.resolve()
    candidate = root
    for part in Path(relative_path).parts:
        if part in {".", ".."}:
            raise CurrentAssetReadError("authority path contains traversal")
        candidate = candidate / part
        if candidate.is_symlink():
            raise CurrentAssetReadError("authority path contains a symlink: " + relative_path)
    if not candidate.is_file():
        raise CurrentAssetReadError("Current authority file is missing: " + relative_path)
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise CurrentAssetReadError("authority path escapes the repository: " + relative_path) from exc
    return candidate.read_bytes()


def _parse_jsonl(raw: bytes, relative_path: str) -> list[dict[str, Any]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CurrentAssetReadError("Current authority is not UTF-8: " + relative_path) from exc
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
        except json.JSONDecodeError as exc:
            raise CurrentAssetReadError(f"malformed Current JSONL: {relative_path}:{line_number}") from exc
        if not isinstance(value, dict):
            raise CurrentAssetReadError(f"Current authority row is not an object: {relative_path}:{line_number}")
        rows.append(value)
    return rows


def _record_hash(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_record_result(canonical_id: Any, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Return exactly one Current identity or claim record; aliases are not accepted."""
    if not isinstance(canonical_id, str) or not _ID_RE.fullmatch(canonical_id):
        raise CurrentAssetReadError("canonical_id must be an exact bounded identifier")

    raw_sources = {
        name: _safe_repo_file(repo_root, path)
        for name, path in AUTHORITY_PATHS.items()
    }
    parsed = {
        name: _parse_jsonl(raw_sources[name], AUTHORITY_PATHS[name])
        for name in AUTHORITY_PATHS
    }

    matches: list[tuple[str, str, dict[str, Any]]] = []
    for name, rows in parsed.items():
        for row in rows:
            if row.get("canonical_id") == canonical_id:
                matches.append((name, AUTHORITY_PATHS[name], row))
    if len(matches) != 1:
        if not matches:
            raise CurrentAssetReadError("canonical_id is not present in the checked-out Current registries")
        raise CurrentAssetReadError("canonical_id is duplicated across Current registries")

    authority_name, authority_path, record = matches[0]
    stored_hash = record.get("record_sha256")
    if not isinstance(stored_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", stored_hash):
        raise CurrentAssetReadError("Current record has no valid stored SHA-256")
    computed_hash = _record_hash(record)
    if stored_hash != computed_hash:
        raise CurrentAssetReadError("Current record SHA-256 does not match its content")

    source_refs = [
        {"name": name, "path": AUTHORITY_PATHS[name], "sha256": hashlib.sha256(raw_sources[name]).hexdigest()}
        for name in AUTHORITY_PATHS
    ]
    return {
        "schema_version": "toolbox-current-foundation-record-r0",
        "result_status": "CURRENT_CANONICAL_RECORD_READ",
        "canonical_id": canonical_id,
        "record_kind": "FUNCTION_ASSET" if authority_name == "function_identity_cards" else "NONFUNCTION_CLAIM",
        "authority_path": authority_path,
        "record_sha256": computed_hash,
        "record_sha256_verified": True,
        "record": record,
        "source_refs": source_refs,
        "claim_ceiling": (
            "Exact content of one checked-out Current identity-card or non-function claim record, with its stored "
            "record hash verified and both identity registries source-hashed. This does not establish truth, proof, "
            "external validity, or independent verification of linked source anchors."
        ),
    }


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON input key: " + key)
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help='read {"canonical_id":"..."} from stdin')
    parser.parse_args(argv)
    try:
        request = json.load(sys.stdin, object_pairs_hook=_reject_duplicate_keys)
        if not isinstance(request, dict) or set(request) != {"canonical_id"}:
            raise CurrentAssetReadError("stdin object must contain exactly one key: canonical_id")
        result = build_record_result(request["canonical_id"])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("CURRENT_FOUNDATION_RECORD_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
