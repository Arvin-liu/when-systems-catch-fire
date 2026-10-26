#!/usr/bin/env python3
"""Group caller-supplied unmapped repository paths for human triage.

This utility reports directory rollups and conservative filename-prefix
cohorts. It never proposes a component owner or edits a canonical registry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

MAX_INPUT_BYTES = 1_048_576
MAX_PATHS = 5_000
MAX_PATH_LENGTH = 512
FAMILY_MARKERS = (
    "-route-evidence",
    "-route-profile",
    "-route-plan",
    "-source-binding-",
    "-source-provenance-",
    "-live-task-",
    "-blueprint-reference",
    "-c1-",
    "-real-task",
    "-evidence-",
)
TRAILING_MARKER_RE = re.compile(r"-(?:r[0-9]+|v[0-9]+|routing|schema)$")


class InputError(ValueError):
    """Raised when the supplied residue envelope is invalid."""


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _validate_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value or len(value) > MAX_PATH_LENGTH:
        raise InputError("each residue path must be a non-empty string up to 512 characters")
    if value.startswith("/") or "\\" in value or any(ord(ch) < 32 for ch in value):
        raise InputError("residue paths must be repository-relative POSIX paths")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InputError("residue paths must already be normalized")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        raise InputError("residue paths must already be normalized")
    return path


def _extension(path: PurePosixPath) -> str:
    return path.suffix.lower() or "[no extension]"


def _filename_family(path: PurePosixPath) -> str | None:
    stem = path.stem.lower().replace("_", "-")
    if stem.startswith("test-"):
        stem = stem[5:]
    for marker in FAMILY_MARKERS:
        index = stem.find(marker)
        if index > 0:
            stem = stem[:index]
            break
    stem = TRAILING_MARKER_RE.sub("", stem)
    if len(stem.split("-")) < 3:
        return None
    return stem


def summarize_residue(envelope: dict[str, Any], *, input_bytes: bytes,
                      source_bytes: bytes) -> dict[str, Any]:
    if not isinstance(envelope, dict) or set(envelope) != {"schema_version", "residues"}:
        raise InputError("input must contain exactly schema_version and residues")
    if envelope["schema_version"] != "component-path-residue-input-r0":
        raise InputError("unsupported schema_version")
    residues = envelope["residues"]
    if not isinstance(residues, list) or not residues or len(residues) > MAX_PATHS:
        raise InputError("residues must contain 1 to 5000 entries")

    paths: list[PurePosixPath] = []
    seen: set[str] = set()
    for item in residues:
        if not isinstance(item, dict) or not {"type", "path"} <= set(item) <= {"type", "path", "message"}:
            raise InputError("each residue must contain type/path and optional message")
        if item["type"] != "unmapped_path":
            raise InputError("only unmapped_path residue may be grouped")
        path = _validate_path(item["path"])
        if path.as_posix() in seen:
            raise InputError("duplicate residue path")
        seen.add(path.as_posix())
        if "message" in item and not isinstance(item["message"], str):
            raise InputError("residue message must be a string when supplied")
        paths.append(path)

    directory_paths: dict[str, list[str]] = defaultdict(list)
    directory_extensions: dict[str, Counter[str]] = defaultdict(Counter)
    family_paths: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        raw = path.as_posix()
        parent = path.parent.as_posix()
        directory_paths[parent].append(raw)
        directory_extensions[parent][_extension(path)] += 1
        family = _filename_family(path)
        if family is not None:
            family_paths[family].append(raw)

    repeated_families = [
        {
            "family_prefix": family,
            "path_count": len(members),
            "paths": sorted(members),
            "basis": "normalized_filename_prefix_and_known_artifact_suffixes",
        }
        for family, members in sorted(family_paths.items())
        if len(members) > 1
    ]
    repeated_paths = {path for row in repeated_families for path in row["paths"]}
    return {
        "schema_version": "component-path-residue-output-r0",
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "tool_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "summary": {
            "path_count": len(paths),
            "unique_path_count": len(seen),
            "directory_group_count": len(directory_paths),
            "repeated_filename_family_count": len(repeated_families),
            "paths_in_repeated_filename_families": len(repeated_paths),
            "uncohorted_path_count": len(paths) - len(repeated_paths),
        },
        "directory_groups": [
            {
                "directory": directory,
                "path_count": len(members),
                "extensions": dict(sorted(directory_extensions[directory].items())),
                "paths": sorted(members),
            }
            for directory, members in sorted(directory_paths.items())
        ],
        "repeated_filename_families": repeated_families,
        "uncohorted_paths": sorted(seen - repeated_paths),
        "mapping_authority": {
            "component_ids_suggested": [],
            "path_patterns_suggested": [],
            "canonical_registry_modified": False,
            "human_mapping_decision_required": True,
        },
        "claim_ceiling": (
            "Deterministic grouping of caller-supplied unmapped path strings by directory "
            "and normalized filename prefix. Groups do not establish shared component "
            "ownership, path equivalence, or validation scope."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True)
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        print("ERROR: input exceeds 1048576 bytes", file=sys.stderr)
        return 2
    try:
        text = raw.decode("utf-8", errors="strict")
        envelope = json.loads(text, object_pairs_hook=_pairs_without_duplicates)
        source_bytes = Path(__file__).read_bytes()
        result = summarize_residue(envelope, input_bytes=raw, source_bytes=source_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, InputError) as exc:
        print(f"ERROR: invalid residue input: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
