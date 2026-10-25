#!/usr/bin/env python3
"""Emit a read-only typed IR projection from the canonical architecture snapshot."""

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
IGNITION_ROOT = HERE.parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))

from tools.run_task149_archify_adapter import build_ir  # noqa: E402


TOOL_SOURCE = "ignition/tools/toolbox_build_archify_derived_ir.py"
ADAPTER_SOURCE = "ignition/tools/run_task149_archify_adapter.py"
ARCHITECTURE_SOURCE = "ignition/data/architecture/overall-architecture.json"
SYSTEM_MAP_SOURCE = "ignition/data/architecture/interactive-system-map.json"
MAX_REQUEST_BYTES = 4096
MAX_SOURCE_BYTES = 1024 * 1024
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")


class DerivedIRRunError(ValueError):
    """Raised when the bounded read-only IR request cannot be completed."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DerivedIRRunError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _checked_repo_file(relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.startswith("ignition/"):
        raise DerivedIRRunError("source paths must remain under ignition/")
    root = REPO_ROOT.resolve()
    candidate = root
    for part in Path(relative_path).parts:
        if part in {".", ".."}:
            raise DerivedIRRunError("source path contains traversal")
        candidate = candidate / part
        if candidate.is_symlink():
            raise DerivedIRRunError("source path contains a symlink: " + relative_path)
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise DerivedIRRunError("source path escapes the repository: " + relative_path) from exc
    if not candidate.is_file():
        raise DerivedIRRunError("required canonical source is unavailable: " + relative_path)
    if candidate.stat().st_size > MAX_SOURCE_BYTES:
        raise DerivedIRRunError("canonical source exceeds the 1 MiB input limit: " + relative_path)
    return candidate


def _read_json_source(relative_path: str) -> tuple[dict[str, Any], bytes]:
    raw = _checked_repo_file(relative_path).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DerivedIRRunError("canonical source is not valid UTF-8 JSON: " + relative_path) from exc
    if not isinstance(value, dict):
        raise DerivedIRRunError("canonical source root must be a JSON object: " + relative_path)
    return value, raw


def build_derived_ir_result(formal_revision: Any) -> dict[str, Any]:
    """Build one provider-neutral typed IR; never write files or call Archify."""
    if not isinstance(formal_revision, str) or not _REVISION_RE.fullmatch(formal_revision):
        raise DerivedIRRunError("formal_revision must be an exact lowercase 40-character commit SHA")

    architecture, architecture_bytes = _read_json_source(ARCHITECTURE_SOURCE)
    system_map, system_map_bytes = _read_json_source(SYSTEM_MAP_SOURCE)
    if not isinstance(system_map.get("map_version"), str) or not system_map["map_version"].strip():
        raise DerivedIRRunError("current system map has no declared map_version")

    ir = build_ir(architecture, system_map, formal_revision)
    component_ids = [row.get("id") for row in ir.get("components", [])]
    connection_ids = [row.get("id") for row in ir.get("connections", [])]
    if len(component_ids) != len(set(component_ids)) or len(connection_ids) != len(set(connection_ids)):
        raise DerivedIRRunError("derived IR contains duplicate component or connection IDs")
    known_components = set(component_ids)
    if any(
        connection.get("from") not in known_components or connection.get("to") not in known_components
        for connection in ir.get("connections", [])
    ):
        raise DerivedIRRunError("derived IR contains an unresolved connection endpoint")
    if len(ir.get("components", [])) != len(architecture.get("nodes", [])):
        raise DerivedIRRunError("derived component count differs from canonical architecture nodes")
    if len(ir.get("connections", [])) != len(architecture.get("edges", [])):
        raise DerivedIRRunError("derived connection count differs from canonical architecture edges")
    if ir.get("meta", {}).get("repository", {}).get("revision") != formal_revision:
        raise DerivedIRRunError("derived IR did not preserve the caller-supplied revision")

    tool_path = _checked_repo_file(TOOL_SOURCE)
    adapter_path = _checked_repo_file(ADAPTER_SOURCE)
    return {
        "schema_version": "toolbox-archify-derived-ir-r0",
        "result_status": "DERIVED_IR_READY",
        "provider_invoked": False,
        "formal_revision_binding": "CALLER_SUPPLIED_NOT_RESOLVED_BY_THIS_TOOL",
        "current_system_map_version": system_map["map_version"],
        "counts": {
            "components": len(ir["components"]),
            "connections": len(ir["connections"]),
            "boundaries": len(ir["boundaries"]),
        },
        "source_refs": [
            {"path": TOOL_SOURCE, "sha256": hashlib.sha256(tool_path.read_bytes()).hexdigest()},
            {"path": ADAPTER_SOURCE, "sha256": hashlib.sha256(adapter_path.read_bytes()).hexdigest()},
            {"path": ARCHITECTURE_SOURCE, "sha256": hashlib.sha256(architecture_bytes).hexdigest()},
            {"path": SYSTEM_MAP_SOURCE, "sha256": hashlib.sha256(system_map_bytes).hexdigest()},
        ],
        "ir": ir,
        "claim_ceiling": (
            "A deterministic provider-neutral typed IR projection from the checked-out canonical architecture and current system map. "
            "It does not establish external Archify validation or delivery, visual quality, architecture truth, Current integration, "
            "provider admission, or a resolved binding to the caller-supplied revision."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help='read {"formal_revision":"<commit SHA>"} from stdin')
    parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise DerivedIRRunError("stdin request exceeds 4 KiB")
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        if not isinstance(request, dict) or set(request) != {"formal_revision"}:
            raise DerivedIRRunError("stdin object must contain exactly formal_revision")
        result = build_derived_ir_result(request["formal_revision"])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DerivedIRRunError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print("ARCHIFY_DERIVED_IR_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
