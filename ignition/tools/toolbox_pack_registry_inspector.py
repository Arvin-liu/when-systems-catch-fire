#!/usr/bin/env python3
"""Inspect declared Pack manifests and routes without loading or running hooks."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))
from agent_runtime.pack_registry import PackRegistry, PackRegistryError  # noqa: E402


PACKS_REL = "ignition/packs"
TOOL_SOURCE = "ignition/tools/toolbox_pack_registry_inspector.py"
RUNTIME_SOURCE = "ignition/agent_runtime"
KERNEL_SOURCE = "ignition/agent_kernel"


class PackInspectionError(ValueError):
    """Raised when a manifest source is unsafe or unavailable."""


def _safe_repo_path(repo_root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        raise PackInspectionError("source paths must remain under ignition/")
    root = Path(repo_root)
    if root.is_symlink():
        raise PackInspectionError("repository root must not be a symlink")
    root = root.resolve()
    parts = Path(relative_path).parts
    if any(part in {".", ".."} for part in parts):
        raise PackInspectionError("source path contains traversal")
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise PackInspectionError("source path contains a symlink: " + relative_path)
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise PackInspectionError("source path escapes the repository: " + relative_path) from exc
    return candidate


def _manifest_snapshot(repo_root: Path) -> tuple[Path, dict[str, bytes]]:
    packs_path = _safe_repo_path(repo_root, PACKS_REL)
    if not packs_path.is_dir():
        raise PackInspectionError("Pack manifests directory is unavailable")
    manifest_bytes: dict[str, bytes] = {}
    for child in sorted(packs_path.iterdir()):
        if child.is_symlink():
            raise PackInspectionError("Pack directory must not be a symlink: " + child.name)
        if not child.is_dir():
            continue
        relative = f"{PACKS_REL}/{child.name}/manifest.json"
        manifest_path = _safe_repo_path(repo_root, relative)
        if manifest_path.exists():
            if not manifest_path.is_file():
                raise PackInspectionError("Pack manifest is not a file: " + relative)
            manifest_bytes[relative] = manifest_path.read_bytes()
    if not manifest_bytes:
        raise PackInspectionError("no Pack manifests found")
    return packs_path, manifest_bytes


def _tree_digest(repo_root: Path, relative_path: str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    directory = _safe_repo_path(root, relative_path)
    if not directory.is_dir():
        raise PackInspectionError("source directory is unavailable: " + relative_path)
    entries = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise PackInspectionError("runtime source tree contains a symlink: " + path.relative_to(root).as_posix())
        if path.is_file():
            entries.append({
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "path": relative_path,
        "hash_kind": "SHA256_FILE_TREE_R0",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "file_count": len(entries),
    }


def build_inspection(action: str, pack_id: str | None = None, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Return a deterministic metadata projection; no Pack loader or hook is called."""
    if action not in {"list", "show"}:
        raise PackInspectionError("action must be list or show")
    if action == "show" and (not isinstance(pack_id, str) or not pack_id.strip()):
        raise PackInspectionError("show requires a nonblank Pack ID")
    if action == "list" and pack_id is not None:
        raise PackInspectionError("list does not accept a Pack ID")

    packs_path, manifest_bytes = _manifest_snapshot(repo_root)
    registry = PackRegistry.discover(packs_path)
    selected_ids = registry.pack_ids if action == "list" else (pack_id,)
    packs = []
    for selected_id in selected_ids:
        manifest = registry.get(selected_id)
        # Pack IDs need not match directory names; bind the exact discovered manifest by content digest.
        matches = [
            path for path, raw in manifest_bytes.items()
            if json.loads(raw.decode("utf-8")).get("pack_id") == selected_id
        ]
        if len(matches) != 1:
            raise PackInspectionError("Pack ID does not bind exactly one discovered manifest: " + selected_id)
        manifest_path = matches[0]
        routes = [route.to_dict() for route in registry.routes() if route.pack_id == selected_id]
        packs.append({
            "manifest": manifest.to_dict(),
            "manifest_source": {
                "path": manifest_path,
                "sha256": hashlib.sha256(manifest_bytes[manifest_path]).hexdigest(),
            },
            "declared_routes": routes,
        })

    source_refs = [
        {"path": TOOL_SOURCE, "sha256": hashlib.sha256(_safe_repo_path(repo_root, TOOL_SOURCE).read_bytes()).hexdigest()},
        _tree_digest(repo_root, RUNTIME_SOURCE),
        _tree_digest(repo_root, KERNEL_SOURCE),
        *[
            {"path": path, "sha256": hashlib.sha256(raw).hexdigest()}
            for path, raw in sorted(manifest_bytes.items())
        ],
    ]
    return {
        "schema_version": "toolbox-pack-catalog-result-r0",
        "result_status": "DECLARED_PACK_METADATA_LISTED" if action == "list" else "DECLARED_PACK_METADATA_SHOWN",
        "source_status": "LOCAL_PACK_MANIFESTS_ONLY",
        "pack_count": len(packs),
        "declared_route_count": sum(len(pack["declared_routes"]) for pack in packs),
        "packs": packs,
        "source_refs": source_refs,
        "claim_ceiling": "Local Pack manifest declarations and versioned capability-route metadata only; no Pack module is loaded, no hook is executed, and no declared capability is proved callable in another environment.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("list", help="list declared local Pack metadata and routes")
    show = subparsers.add_parser("show", help="show one declared local Pack and its routes")
    show.add_argument("pack_id")
    args = parser.parse_args(argv)
    try:
        result = build_inspection(args.action, getattr(args, "pack_id", None))
    except (OSError, json.JSONDecodeError, PackInspectionError, PackRegistryError) as exc:
        print("PACK_METADATA_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
