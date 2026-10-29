#!/usr/bin/env python3
"""Build a portable episode manifest with read-once SHA-256 observations of included local files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1].resolve()
REPO_ROOT = IGNITION_ROOT.parent
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-portable-research-episode-builder-input-r0.schema.json"
MAX_INPUT_BYTES = 262_144
MAX_FINDINGS = 64
MAX_ARTIFACTS = 64
MAX_REF_CHARS = 4_096
MAX_REF_DEPTH = 32
MAX_COMPONENT_CHARS = 255
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
TOOL_ID = "collaboration.build_portable_research_episode"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "portable-research-episode-builder-input-r0"
RESULT_SCHEMA_VERSION = "portable-research-episode-builder-result-r0"
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
CLAIM_CEILING = (
    "Computes SHA-256 and byte-count observations for caller-selected regular files under an explicit ignition/ root, "
    "then builds a caller-declared portable episode manifest with resolved artifact-version references. "
    "It does not authenticate sources, actors, executions, reviews, timestamps, permissions, or science; "
    "copy/import files; execute work; validate episode semantics; or authorize actions."
)


class DuplicateJSONKey(ValueError):
    """Raised when any input JSON object repeats a key."""


class BuildFailure(ValueError):
    def __init__(self, code: str, *, bytes_read: int = 0) -> None:
        super().__init__(code)
        self.code = code
        self.bytes_read = bytes_read


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey
        result[key] = value
    return result


def _relative_parts(value: Any) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or len(value) > MAX_REF_CHARS:
        raise BuildFailure("UNSAFE_RELATIVE_PATH")
    if SCHEME_RE.match(value) or value.startswith("/") or "\\" in value or "\x00" in value:
        raise BuildFailure("UNSAFE_RELATIVE_PATH")
    parts = tuple(value.split("/"))
    if len(parts) > MAX_REF_DEPTH:
        raise BuildFailure("UNSAFE_RELATIVE_PATH")
    for part in parts:
        if part in {"", ".", ".."} or len(part) > MAX_COMPONENT_CHARS:
            raise BuildFailure("UNSAFE_RELATIVE_PATH")
        if any(ord(char) < 32 or ord(char) == 127 for char in part):
            raise BuildFailure("UNSAFE_RELATIVE_PATH")
    return parts


def _open_workspace_root(value: str | os.PathLike[str]) -> int:
    if not isinstance(value, (str, os.PathLike)) or not str(value).strip() or len(str(value)) > MAX_REF_CHARS:
        raise BuildFailure("WORKSPACE_ROOT_INVALID")
    if not all(hasattr(os, attr) for attr in ("O_NOFOLLOW", "O_DIRECTORY")) or os.open not in os.supports_dir_fd:
        raise BuildFailure("PLATFORM_UNSUPPORTED")
    raw = Path(value)
    if not raw.is_absolute():
        raw = REPO_ROOT / raw
    raw = Path(os.path.abspath(raw))
    try:
        relative = raw.relative_to(IGNITION_ROOT)
    except ValueError as exc:
        raise BuildFailure("WORKSPACE_ROOT_OUTSIDE_IGNITION") from exc
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        current_fd = os.open(str(IGNITION_ROOT), flags)
    except OSError as exc:
        raise BuildFailure("WORKSPACE_ROOT_UNAVAILABLE") from exc
    try:
        for part in relative.parts:
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except OSError as exc:
                raise BuildFailure("WORKSPACE_ROOT_UNAVAILABLE") from exc
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def _open_regular_file(root_fd: int, relative_path: str) -> int:
    parts = _relative_parts(relative_path)
    directory_fd = os.dup(root_fd)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        for part in parts[:-1]:
            try:
                next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            except OSError as exc:
                raise BuildFailure("ARTIFACT_PATH_UNAVAILABLE") from exc
            os.close(directory_fd)
            directory_fd = next_fd
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(parts[-1], file_flags, dir_fd=directory_fd)
        except OSError as exc:
            raise BuildFailure("ARTIFACT_PATH_UNAVAILABLE") from exc
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            os.close(fd)
            raise BuildFailure("ARTIFACT_NOT_REGULAR_FILE")
        return fd
    finally:
        os.close(directory_fd)


def _hash_artifact(root_fd: int, relative_path: str, *, bytes_read: int) -> tuple[str, int]:
    fd = _open_regular_file(root_fd, relative_path)
    try:
        before = os.fstat(fd)
        if before.st_size > MAX_FILE_BYTES:
            raise BuildFailure("ARTIFACT_FILE_LIMIT_EXCEEDED", bytes_read=bytes_read)
        if bytes_read + before.st_size > MAX_TOTAL_BYTES:
            raise BuildFailure("TOTAL_FILE_LIMIT_EXCEEDED", bytes_read=bytes_read)
        digest = hashlib.sha256()
        observed = 0
        while True:
            try:
                chunk = os.read(fd, min(65_536, MAX_FILE_BYTES + 1 - observed))
            except OSError as exc:
                raise BuildFailure("ARTIFACT_READ_FAILED", bytes_read=bytes_read + observed) from exc
            if not chunk:
                break
            observed += len(chunk)
            if observed > MAX_FILE_BYTES or bytes_read + observed > MAX_TOTAL_BYTES:
                raise BuildFailure("TOTAL_FILE_LIMIT_EXCEEDED", bytes_read=bytes_read + observed)
            digest.update(chunk)
        after = os.fstat(fd)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        if identity_before != identity_after or observed != before.st_size:
            raise BuildFailure("ARTIFACT_CHANGED_DURING_READ", bytes_read=bytes_read + observed)
        return digest.hexdigest(), observed
    finally:
        os.close(fd)


def _input_findings(value: Any) -> list[dict[str, str]]:
    schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(value),
        key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""),
    )
    return [
        {
            "code": "INPUT_SCHEMA_INVALID",
            "path": error.json_path if hasattr(error, "json_path") else "$",
        }
        for error in errors[:MAX_FINDINGS]
    ]


def _ref_key(ref: dict[str, Any]) -> tuple[str, str]:
    return ref["artifact_id"], ref["version_id"]


def _assert_ref_known(ref: dict[str, Any], artifacts: dict[tuple[str, str], dict[str, Any]]) -> None:
    if _ref_key(ref) not in artifacts:
        raise BuildFailure("UNKNOWN_ARTIFACT_VERSION_REFERENCE")


def _resolved_ref(ref: dict[str, Any], artifacts: dict[tuple[str, str], dict[str, Any]]) -> dict[str, str]:
    key = _ref_key(ref)
    artifact = artifacts.get(key)
    if artifact is None:
        raise BuildFailure("UNKNOWN_ARTIFACT_VERSION_REFERENCE")
    return {
        "artifact_id": artifact["artifact_id"],
        "version_id": artifact["version_id"],
        "sha256": artifact["sha256"],
    }


def build_episode(value: Any, root_fd: int) -> dict[str, Any]:
    """Build a manifest from explicit caller events and local file observations."""
    findings = _input_findings(value)
    if findings:
        return _result("INPUT_INVALID", findings=findings)
    definitions = value["artifacts"]
    if len(definitions) > MAX_ARTIFACTS:
        return _result("INPUT_INVALID", findings=[{"code": "ARTIFACT_COUNT_LIMIT_EXCEEDED", "path": "$/artifacts"}])
    keys = [_ref_key(item) for item in definitions]
    if len(keys) != len(set(keys)):
        return _result("INPUT_INVALID", findings=[{"code": "DUPLICATE_ARTIFACT_VERSION", "path": "$/artifacts"}])

    # Resolve all references before reading any file so a malformed graph has no file-read effect.
    artifacts: dict[tuple[str, str], dict[str, Any]] = {}
    for artifact in definitions:
        artifacts[_ref_key(artifact)] = artifact
    try:
        for artifact in definitions:
            if artifact["parent_ref"] is not None:
                _assert_ref_known(artifact["parent_ref"], artifacts)
            for ref in artifact["dependency_refs"]:
                _assert_ref_known(ref, artifacts)
        for execution in value["executions"]:
            for relation in ("used_artifact_refs", "attached_artifact_refs", "produced_artifact_refs"):
                for ref in execution[relation]:
                    _assert_ref_known(ref, artifacts)
        for review in value["reviews"]:
            _assert_ref_known(review["target_ref"], artifacts)
    except BuildFailure as exc:
        return _result("INPUT_INVALID", findings=[{"code": exc.code, "path": "$"}])

    receipts: list[dict[str, Any]] = []
    total_bytes = 0
    try:
        for artifact in definitions:
            sha256, byte_count = _hash_artifact(root_fd, artifact["relative_path"], bytes_read=total_bytes)
            total_bytes += byte_count
            bound = dict(artifact)
            bound["sha256"] = sha256
            artifacts[_ref_key(artifact)] = bound
            receipts.append({
                "artifact_id": artifact["artifact_id"],
                "version_id": artifact["version_id"],
                "relative_path": artifact["relative_path"],
                "sha256": sha256,
                "byte_count": byte_count,
                "observation": "LOCAL_READ_ONCE",
            })
    except BuildFailure as exc:
        return _result("BUILD_FAILED", findings=[{"code": exc.code, "path": "$/artifacts"}], total_bytes_read=exc.bytes_read)

    def resolve(ref: dict[str, Any] | None) -> dict[str, str] | None:
        return None if ref is None else _resolved_ref(ref, artifacts)

    episode_artifacts = []
    for artifact in definitions:
        episode_artifacts.append({
            "artifact_id": artifact["artifact_id"],
            "version_id": artifact["version_id"],
            "sha256": artifacts[_ref_key(artifact)]["sha256"],
            "parent_ref": resolve(artifact["parent_ref"]),
            "dependency_refs": [resolve(ref) for ref in artifact["dependency_refs"]],
            "availability": "INCLUDED",
            "omission_reason": None,
            "required": artifact["required"],
            "is_current": artifact["is_current"],
        })
    executions = []
    for execution in value["executions"]:
        executions.append({
            "execution_id": execution["execution_id"],
            "status": execution["status"],
            "run_ref": execution["run_ref"],
            "used_artifact_refs": [resolve(ref) for ref in execution["used_artifact_refs"]],
            "attached_artifact_refs": [resolve(ref) for ref in execution["attached_artifact_refs"]],
            "produced_artifact_refs": [resolve(ref) for ref in execution["produced_artifact_refs"]],
            "not_executed_reason": execution["not_executed_reason"],
        })
    reviews = []
    for review in value["reviews"]:
        reviews.append({
            **review,
            "target_ref": resolve(review["target_ref"]),
        })
    episode = {
        "schema_version": "ignition-portable-research-episode-r0",
        "episode_id": value["episode_id"],
        "package_revision": value["package_revision"],
        "import_mode": value["import_mode"],
        "required_artifact_ids": value["required_artifact_ids"],
        "artifacts": episode_artifacts,
        "executions": executions,
        "reviews": reviews,
        "omissions": value["omissions"],
        "fork_id_mappings": value["fork_id_mappings"],
    }
    return _result("BUILD_SUCCEEDED", episode=episode, file_receipts=receipts, total_bytes_read=total_bytes)


def _result(
    status: str,
    *,
    episode: dict[str, Any] | None = None,
    file_receipts: list[dict[str, Any]] | None = None,
    findings: list[dict[str, str]] | None = None,
    total_bytes_read: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "episode": episode,
        "file_receipts": file_receipts or [],
        "findings": findings or [],
        "total_bytes_read": total_bytes_read,
        "execution_authorized": False,
        "files_copied": False,
        "files_written": False,
        "source_authenticity": "NOT_ESTABLISHED",
        "claim_ceiling": CLAIM_CEILING,
    }


def _read_stdin() -> Any:
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise BuildFailure("INPUT_READ_FAILED") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise BuildFailure("INPUT_BYTE_LIMIT_EXCEEDED")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except DuplicateJSONKey:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise BuildFailure("INPUT_INVALID_JSON") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded builder request from stdin")
    parser.add_argument("--workspace-root", required=True, help="explicit read-only root under ignition/")
    args = parser.parse_args(argv)
    try:
        value = _read_stdin()
        root_fd = _open_workspace_root(args.workspace_root)
    except DuplicateJSONKey:
        result = _result("INPUT_INVALID", findings=[{"code": "DUPLICATE_JSON_KEY", "path": "$"}])
    except BuildFailure as exc:
        result = _result("INPUT_INVALID", findings=[{"code": exc.code, "path": "$"}], total_bytes_read=exc.bytes_read)
    else:
        try:
            result = build_episode(value, root_fd)
        finally:
            os.close(root_fd)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "BUILD_SUCCEEDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
