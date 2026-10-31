#!/usr/bin/env python3
"""Batch exact canonical-asset resolution with a source-pinned stdout receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "foundation"))
import resolve_current_canonical_asset as resolver  # noqa: E402


AUTHORITY_PATHS = {
    "function_identity_cards": "ignition/data/foundation/function-assets/identity-cards.jsonl",
    "nonfunction_claim_registry": "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl",
    "current_alias_index": "ignition/data/governance/knowledge-experience/alias-index.jsonl",
    "current_identity_corrections": "ignition/data/foundation/function-assets/corrections.jsonl",
    "legacy_identity_mappings": "ignition/data/foundation/mappings/legacy-mappings.jsonl",
}
RESOLVER_SOURCE = "ignition/tools/foundation/resolve_current_canonical_asset.py"


class BatchResolutionError(ValueError):
    """Raised when an input batch or its Current authority snapshot is invalid."""


def _read_repo_file(repo_root: Path, relative_path: str) -> bytes:
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        raise BatchResolutionError("authority paths must remain under ignition/")
    root = Path(repo_root)
    if root.is_symlink():
        raise BatchResolutionError("repository root must not be a symlink")
    root = root.resolve()
    parts = Path(relative_path).parts
    if any(part in {".", ".."} for part in parts):
        raise BatchResolutionError("authority path contains traversal")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise BatchResolutionError("authority path contains a symlink: " + relative_path)
    if not path.is_file():
        raise BatchResolutionError("authority file is missing: " + relative_path)
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise BatchResolutionError("authority path escapes the repository: " + relative_path) from exc
    return path.read_bytes()


def _parse_jsonl(data: bytes, relative_path: str) -> list[dict[str, Any]]:
    rows = []
    try:
        lines = data.decode("utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise BatchResolutionError(f"{relative_path}:{line_number} is not an object")
            rows.append(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BatchResolutionError(f"invalid Current authority JSONL: {relative_path}: {exc}") from exc
    return rows


def _validate_references(references: Any) -> list[str]:
    if not isinstance(references, list) or not references:
        raise BatchResolutionError("references must be a nonempty array")
    if any(not isinstance(reference, str) or not reference.strip() for reference in references):
        raise BatchResolutionError("references must contain nonblank strings")
    return list(references)


def build_batch_result(references: Any, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Resolve an ordered batch using the existing Current-first resolver once per reference."""
    references = _validate_references(references)
    raw_sources = {name: _read_repo_file(repo_root, path) for name, path in AUTHORITY_PATHS.items()}
    parsed = {
        name: _parse_jsonl(raw_sources[name], AUTHORITY_PATHS[name])
        for name in AUTHORITY_PATHS
    }
    authority_refs = [
        {"name": name, "path": AUTHORITY_PATHS[name], "sha256": hashlib.sha256(raw_sources[name]).hexdigest()}
        for name in AUTHORITY_PATHS
    ]
    resolver_bytes = _read_repo_file(repo_root, RESOLVER_SOURCE)
    resolver_ref = {"name": "canonical_resolver", "path": RESOLVER_SOURCE, "sha256": hashlib.sha256(resolver_bytes).hexdigest()}

    results = []
    for index, reference in enumerate(references):
        resolved = resolver.resolve_reference_from_rows(
            reference,
            parsed["function_identity_cards"],
            parsed["current_alias_index"],
            parsed["current_identity_corrections"],
            parsed["legacy_identity_mappings"],
            parsed["nonfunction_claim_registry"],
        )
        results.append({
            "input_index": index,
            "submitted_reference": reference,
            "resolution": resolved,
        })

    statuses = [item["resolution"]["resolution_status"] for item in results]
    document = {
        "schema_version": "toolbox-batch-canonical-resolution-r0",
        "result_status": "BATCH_RESOLUTION_PROCESSED",
        "reference_count": len(results),
        "summary": {
            "resolved": statuses.count(resolver.RESOLVED),
            "unresolved": statuses.count(resolver.UNRESOLVED),
            "ambiguous": statuses.count(resolver.AMBIGUOUS),
        },
        "source_refs": [resolver_ref, *authority_refs],
        "results": results,
        "claim_ceiling": "Repository-snapshot canonical identity and migration resolution only; unresolved and ambiguous items remain explicit; no fuzzy identity, truth, proof, evidence upgrade, or external validity is inferred.",
    }
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    document["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read {\"references\":[...]} from stdin")
    args = parser.parse_args(argv)
    _ = args
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict) or set(request) != {"references"}:
            raise BatchResolutionError("stdin object must contain exactly one key: references")
        result = build_batch_result(request["references"])
    except (OSError, json.JSONDecodeError, BatchResolutionError, resolver.CanonicalAuthorityError) as exc:
        print("BATCH_CANONICAL_RESOLUTION_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
