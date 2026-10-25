#!/usr/bin/env python3
"""Compare bounded local handoff artifact bytes with a typed receipt's SHA-256 values."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1].resolve()
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))
TOOL_ID = "collaboration.verify_handoff_artifact_files"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "handoff-artifact-byte-check-r0"
MAX_INPUT_BYTES = 262_144
MAX_ARTIFACTS = 64
MAX_REF_CHARS = 4_096
MAX_REF_DEPTH = 32
MAX_COMPONENT_CHARS = 255
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
INPUT_KEYS = {"schema_version", "source_receipt"}
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
CLAIM_CEILING = (
    "Checks whether bounded bytes read from regular files under an explicit repository-local ignition/ workspace root "
    "match the SHA-256 values in a typed FederatedResultReceipt whose canonical unkeyed self-digest passes. "
    "It does not authenticate the receipt or source, prove file provenance or task correctness, observe a stable runtime "
    "workspace after reading, authorize actions, enforce runtime isolation, or establish scientific truth."
)


class DuplicateJSONKey(ValueError):
    """Raised when an input object repeats a JSON key."""


class WorkspaceRootError(ValueError):
    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey
        result[key] = value
    return result


def _result(
    status: str,
    receipt_check: str,
    artifact_results: list[dict[str, Any]],
    *,
    workspace_observation: str,
    total_bytes_read: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": "handoff-artifact-byte-check-result-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "source_receipt_canonical_digest": receipt_check,
        "receipt_authenticity": "NOT_ESTABLISHED_UNKEYED_DIGEST",
        "workspace_observation": workspace_observation,
        "artifact_count": len(artifact_results),
        "total_bytes_read": total_bytes_read,
        "artifacts": artifact_results,
        "execution_authorized": False,
        "runtime_enforcement_status": "NOT_EVALUATED",
        "claim_ceiling": CLAIM_CEILING,
    }


def _input_error(code: str) -> tuple[dict[str, Any], int]:
    result = _result(
        "INPUT_INVALID",
        "NOT_RUN",
        [],
        workspace_observation="NOT_RUN",
    )
    result["findings"] = [{"code": code}]
    return result, 2


def _artifact_result(
    index: int,
    artifact: Any,
    status: str,
    *,
    observed_sha256: str | None = None,
    bytes_read: int = 0,
    ref_included: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "artifact_index": index,
        "kind": artifact.kind,
        "expected_sha256": artifact.sha256,
        "status": status,
        "bytes_read": bytes_read,
    }
    if ref_included:
        result["ref"] = artifact.ref
    if observed_sha256 is not None:
        result["observed_sha256"] = observed_sha256
    return result


def _relative_parts(ref: str) -> tuple[tuple[str, ...] | None, str | None]:
    if not ref or len(ref) > MAX_REF_CHARS:
        return None, "UNSAFE_REFERENCE"
    if SCHEME_RE.match(ref):
        return None, "UNSUPPORTED_REFERENCE"
    if ref.startswith("/") or "\\" in ref or "\x00" in ref:
        return None, "UNSAFE_REFERENCE"
    parts = tuple(ref.split("/"))
    if len(parts) > MAX_REF_DEPTH:
        return None, "UNSAFE_REFERENCE"
    for part in parts:
        if part in {"", ".", ".."} or len(part) > MAX_COMPONENT_CHARS:
            return None, "UNSAFE_REFERENCE"
        if any(ord(char) < 32 or ord(char) == 127 for char in part):
            return None, "UNSAFE_REFERENCE"
    return parts, None


def _open_workspace_root(value: str | os.PathLike[str]) -> int:
    if not isinstance(value, (str, os.PathLike)) or not str(value).strip() or len(str(value)) > MAX_REF_CHARS:
        raise WorkspaceRootError("WORKSPACE_ROOT_INVALID")
    if not all(hasattr(os, attr) for attr in ("O_NOFOLLOW", "O_DIRECTORY")) or os.open not in os.supports_dir_fd:
        raise WorkspaceRootError("PLATFORM_UNSUPPORTED")

    raw = Path(value)
    if not raw.is_absolute():
        raw = REPO_ROOT / raw
    raw = Path(os.path.abspath(raw))
    try:
        relative = raw.relative_to(IGNITION_ROOT)
    except ValueError as exc:
        raise WorkspaceRootError("WORKSPACE_ROOT_OUTSIDE_IGNITION") from exc
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        current_fd = os.open(str(IGNITION_ROOT), flags)
    except OSError as exc:
        raise WorkspaceRootError("WORKSPACE_ROOT_UNAVAILABLE") from exc
    try:
        for part in relative.parts:
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise WorkspaceRootError("WORKSPACE_ROOT_SYMLINK_OR_NOT_DIRECTORY") from exc
                raise WorkspaceRootError("WORKSPACE_ROOT_UNAVAILABLE") from exc
            os.close(current_fd)
            current_fd = next_fd
        if not stat.S_ISDIR(os.fstat(current_fd).st_mode):
            raise WorkspaceRootError("WORKSPACE_ROOT_NOT_DIRECTORY")
        result_fd = current_fd
        current_fd = -1
        return result_fd
    finally:
        if current_fd >= 0:
            os.close(current_fd)


def _open_relative_file(root_fd: int, parts: tuple[str, ...]) -> int:
    current_fd = os.dup(root_fd)
    try:
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        for part in parts[:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
        return os.open(parts[-1], file_flags, dir_fd=current_fd)
    finally:
        os.close(current_fd)


def _stat_changed(before: os.stat_result, after: os.stat_result) -> bool:
    return any(
        getattr(before, name, None) != getattr(after, name, None)
        for name in ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    )


def _read_bounded(fd: int, limit: int) -> tuple[bytes, bool, bool]:
    result = bytearray()
    while True:
        remaining = limit - len(result)
        if remaining <= 0:
            return bytes(result), True, False
        try:
            chunk = os.read(fd, min(65_536, remaining))
        except OSError:
            return bytes(result), False, True
        if not chunk:
            return bytes(result), False, False
        result.extend(chunk)


def _verify_one(root_fd: int, index: int, artifact: Any, remaining_total: int) -> tuple[dict[str, Any], int]:
    parts, path_error = _relative_parts(artifact.ref)
    if path_error:
        return _artifact_result(index, artifact, path_error), 0
    assert parts is not None
    try:
        fd = _open_relative_file(root_fd, parts)
    except FileNotFoundError:
        return _artifact_result(index, artifact, "MISSING", ref_included=True), 0
    except PermissionError:
        return _artifact_result(index, artifact, "READ_DENIED", ref_included=True), 0
    except OSError as exc:
        status = "UNSAFE_PATH" if exc.errno in {errno.ELOOP, errno.ENOTDIR} else "ARTIFACT_READ_FAILED"
        return _artifact_result(index, artifact, status, ref_included=True), 0

    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            return _artifact_result(index, artifact, "NOT_REGULAR_FILE", ref_included=True), 0
        if before.st_size > MAX_FILE_BYTES:
            return _artifact_result(index, artifact, "FILE_SIZE_LIMIT", ref_included=True), 0
        if before.st_size > remaining_total:
            return _artifact_result(index, artifact, "TOTAL_SIZE_LIMIT", ref_included=True), 0
        limit = min(MAX_FILE_BYTES, remaining_total)
        payload, hit_limit, read_error = _read_bounded(fd, limit)
        if read_error:
            return _artifact_result(
                index, artifact, "ARTIFACT_READ_FAILED", bytes_read=len(payload), ref_included=True,
            ), len(payload)
        if hit_limit and before.st_size > len(payload):
            status = "FILE_SIZE_LIMIT" if limit == MAX_FILE_BYTES else "TOTAL_SIZE_LIMIT"
            return _artifact_result(index, artifact, status, bytes_read=len(payload), ref_included=True), len(payload)
        after = os.fstat(fd)
        observed = hashlib.sha256(payload).hexdigest()
        if _stat_changed(before, after):
            status = "FILE_CHANGED_DURING_READ"
        elif observed != artifact.sha256:
            status = "DIGEST_MISMATCH"
        else:
            status = "DIGEST_MATCH"
        return _artifact_result(
            index,
            artifact,
            status,
            observed_sha256=observed,
            bytes_read=len(payload),
            ref_included=True,
        ), len(payload)
    except OSError:
        return _artifact_result(index, artifact, "ARTIFACT_READ_FAILED", ref_included=True), 0
    finally:
        os.close(fd)


def evaluate(document: Any, workspace_root: str | os.PathLike[str]) -> tuple[dict[str, Any], int]:
    """Verify receipt artifact bytes under a caller-selected repository-local ignition/ root."""
    if not isinstance(document, dict) or set(document) != INPUT_KEYS:
        return _input_error("INPUT_KEYS_MISMATCH")
    if document.get("schema_version") != INPUT_SCHEMA_VERSION:
        return _input_error("INPUT_SCHEMA_VERSION_UNSUPPORTED")
    if not isinstance(document.get("source_receipt"), dict):
        return _input_error("SOURCE_RECEIPT_MUST_BE_OBJECT")

    from agent_federation.contracts import FederatedResultReceipt  # local import keeps startup failure explicit

    try:
        receipt = FederatedResultReceipt.from_dict(document["source_receipt"])
    except (TypeError, ValueError, KeyError, RecursionError):
        return _input_error("SOURCE_RECEIPT_INVALID")

    if not receipt.artifact_refs:
        return _result(
            "NO_ARTIFACTS_TO_VERIFY", "PASS", [], workspace_observation="ROOT_NOT_OPENED_NO_ARTIFACTS",
        ), 2
    if len(receipt.artifact_refs) > MAX_ARTIFACTS:
        return _result(
            "ARTIFACT_COUNT_LIMIT", "PASS", [], workspace_observation="ROOT_NOT_OPENED_ARTIFACT_LIMIT",
        ), 2

    try:
        root_fd = _open_workspace_root(workspace_root)
    except WorkspaceRootError as exc:
        result = _result(
            exc.status, "PASS", [], workspace_observation="ROOT_NOT_OPENED_OR_REJECTED",
        )
        result["artifact_count"] = len(receipt.artifact_refs)
        return result, 2

    items: list[dict[str, Any]] = []
    total_read = 0
    try:
        for index, artifact in enumerate(receipt.artifact_refs):
            item, consumed = _verify_one(root_fd, index, artifact, MAX_TOTAL_BYTES - total_read)
            items.append(item)
            total_read += consumed
    finally:
        os.close(root_fd)

    statuses = {item["status"] for item in items}
    if statuses == {"DIGEST_MATCH"}:
        status = "ALL_DIGESTS_MATCH"
    elif "DIGEST_MISMATCH" in statuses:
        status = "DIGEST_MISMATCH"
    else:
        status = "ARTIFACTS_UNVERIFIED"
    result = _result(
        status,
        "PASS",
        items,
        workspace_observation="BOUNDED_LOCAL_FILE_BYTES_READ_UNDER_CALLER_ROOT",
        total_bytes_read=total_read,
    )
    return result, 0 if status == "ALL_DIGESTS_MATCH" else 2


def _read_stdin() -> Any:
    data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds the 262144-byte limit")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded receipt object from stdin")
    parser.add_argument("--workspace-root", required=True, help="explicit local root under the repository's ignition/ directory")
    args = parser.parse_args(argv)
    try:
        document = _read_stdin()
        result, code = evaluate(document, args.workspace_root)
    except DuplicateJSONKey:
        result, code = _input_error("DUPLICATE_JSON_KEY")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        result, code = _input_error("INPUT_UNAVAILABLE_OR_INVALID")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
