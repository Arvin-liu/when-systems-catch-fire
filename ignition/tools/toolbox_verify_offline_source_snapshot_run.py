#!/usr/bin/env python3
"""Verify bounded files listed in one saved E37 source-binding run receipt."""

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


HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1].resolve()
REPO_ROOT = HERE.parents[2].resolve()
TOOL_ID = "research.verify_offline_source_snapshot_run"
TOOL_VERSION = "0.1.0"
RECEIPT_SCHEMA = "ignition-source-binding-slot-run-v1"
MAX_RECEIPT_BYTES = 1_000_000
MAX_ARTIFACTS = 128
MAX_TREE_FILES = MAX_ARTIFACTS + 1
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_PATH_CHARS = 4096
MAX_PATH_DEPTH = 32
MAX_COMPONENT_CHARS = 255
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CLAIM_CEILING = (
    "Checks bounded regular-file bytes and the exact file set against an E37 run receipt's unkeyed SHA-256 declarations. "
    "It does not authenticate the receipt, capture origin, publisher, prior execution, semantic support, scientific truth, "
    "or the correctness of the run."
)


class DuplicateJSONKey(ValueError):
    """Raised when a JSON object repeats a key."""


class UnsafeTree(ValueError):
    """Raised when the selected output tree contains an unsafe or unstable entry."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(key)
        result[key] = value
    return result


def _result(
    status: str,
    *,
    findings: list[dict[str, Any]] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    missing_paths: list[str] | None = None,
    unlisted_paths: list[str] | None = None,
    total_bytes_read: int = 0,
    receipt_bytes_read: int = 0,
    workspace_observation: str = "NOT_RUN",
) -> dict[str, Any]:
    rows = artifacts or []
    return {
        "schema_version": "offline-source-snapshot-run-verification-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "receipt_schema": RECEIPT_SCHEMA,
        "receipt_authenticity": "NOT_ESTABLISHED_UNKEYED_DIGEST",
        "workspace_observation": workspace_observation,
        "artifact_count": len(rows),
        "total_bytes_read": total_bytes_read,
        "receipt_bytes_read": receipt_bytes_read,
        "artifacts": rows,
        "missing_paths": missing_paths or [],
        "unlisted_paths": unlisted_paths or [],
        "findings": findings or [],
        "network_requests": 0,
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _absolute_root(value: str | os.PathLike[str]) -> tuple[Path | None, str | None]:
    if not isinstance(value, (str, os.PathLike)):
        return None, "RUN_ROOT_INVALID"
    text = str(value)
    if not text.strip() or len(text) > MAX_PATH_CHARS:
        return None, "RUN_ROOT_INVALID"
    supplied = Path(text)
    if not supplied.is_absolute() or ".." in supplied.parts:
        return None, "RUN_ROOT_MUST_BE_ABSOLUTE_AND_CANONICAL"
    root = Path(os.path.normpath(text))
    repo = Path(os.path.abspath(REPO_ROOT))
    if root == repo or root in repo.parents or repo in root.parents:
        return None, "RUN_ROOT_INSIDE_OR_CONTAINS_REPOSITORY"
    return root, None


def _open_absolute_directory(root: Path) -> tuple[int | None, str | None]:
    if not all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_DIRECTORY")) or os.open not in os.supports_dir_fd:
        return None, "PLATFORM_UNSUPPORTED"
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        current_fd = os.open("/", flags)
    except OSError:
        return None, "RUN_ROOT_UNAVAILABLE"
    try:
        for component in root.parts[1:]:
            try:
                next_fd = os.open(component, flags, dir_fd=current_fd)
            except FileNotFoundError:
                return None, "RUN_ROOT_UNAVAILABLE"
            except OSError:
                return None, "RUN_ROOT_SYMLINK_OR_NOT_DIRECTORY"
            os.close(current_fd)
            current_fd = next_fd
        if not stat.S_ISDIR(os.fstat(current_fd).st_mode):
            return None, "RUN_ROOT_NOT_DIRECTORY"
        result_fd = current_fd
        current_fd = -1
        return result_fd, None
    finally:
        if current_fd >= 0:
            os.close(current_fd)


def _relative_parts(value: Any) -> tuple[tuple[str, ...] | None, str | None]:
    if not isinstance(value, str) or not value or len(value) > MAX_PATH_CHARS:
        return None, "ARTIFACT_PATH_INVALID"
    if value.startswith("/") or "\\" in value or "\x00" in value:
        return None, "ARTIFACT_PATH_UNSAFE"
    parts = tuple(value.split("/"))
    if len(parts) > MAX_PATH_DEPTH:
        return None, "ARTIFACT_PATH_TOO_DEEP"
    for part in parts:
        if part in {"", ".", ".."} or len(part) > MAX_COMPONENT_CHARS:
            return None, "ARTIFACT_PATH_UNSAFE"
        if any(ord(char) < 32 or ord(char) == 127 for char in part):
            return None, "ARTIFACT_PATH_UNSAFE"
    if value == "receipt.json":
        return None, "ARTIFACT_PATH_RESERVED"
    return parts, None


def _open_relative_file(root_fd: int, parts: tuple[str, ...]) -> int:
    current_fd = os.dup(root_fd)
    try:
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        for component in parts[:-1]:
            next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
        return os.open(parts[-1], file_flags, dir_fd=current_fd)
    finally:
        os.close(current_fd)


def _stat_signature(info: os.stat_result) -> tuple[int | None, ...]:
    return tuple(
        getattr(info, name, None)
        for name in ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    )


def _read_relative_file(root_fd: int, parts: tuple[str, ...], limit: int) -> tuple[bytes | None, str | None]:
    try:
        fd = _open_relative_file(root_fd, parts)
    except FileNotFoundError:
        return None, "MISSING"
    except PermissionError:
        return None, "READ_DENIED"
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            return None, "UNSAFE_PATH"
        return None, "READ_FAILED"
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            return None, "NOT_REGULAR_FILE"
        if before.st_size > limit:
            return None, "SIZE_LIMIT"
        payload = bytearray()
        while True:
            chunk = os.read(fd, min(65_536, limit + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > limit:
                return None, "SIZE_LIMIT"
        after = os.fstat(fd)
        if _stat_signature(before) != _stat_signature(after) or len(payload) != before.st_size:
            return None, "FILE_CHANGED_DURING_READ"
        return bytes(payload), None
    except OSError:
        return None, "READ_FAILED"
    finally:
        os.close(fd)


def _scan_tree(root_fd: int) -> dict[str, tuple[int | None, ...]]:
    files: dict[str, tuple[int | None, ...]] = {}

    def walk(directory_fd: int, prefix: tuple[str, ...], depth: int) -> None:
        if depth > MAX_PATH_DEPTH:
            raise UnsafeTree("RUN_TREE_TOO_DEEP")
        try:
            names = sorted(os.listdir(directory_fd))
        except OSError as exc:
            raise UnsafeTree("RUN_TREE_UNAVAILABLE") from exc
        for name in names:
            if name in {"", ".", ".."} or "/" in name or "\\" in name or "\x00" in name:
                raise UnsafeTree("RUN_TREE_UNSAFE_ENTRY")
            if len(name) > MAX_COMPONENT_CHARS or any(ord(char) < 32 or ord(char) == 127 for char in name):
                raise UnsafeTree("RUN_TREE_UNSAFE_ENTRY")
            relative = prefix + (name,)
            path = "/".join(relative)
            try:
                info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                raise UnsafeTree("RUN_TREE_CHANGED_DURING_SCAN") from exc
            if stat.S_ISDIR(info.st_mode):
                flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
                try:
                    child_fd = os.open(name, flags, dir_fd=directory_fd)
                except OSError as exc:
                    raise UnsafeTree("RUN_TREE_UNSAFE_ENTRY") from exc
                try:
                    walk(child_fd, relative, depth + 1)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(info.st_mode):
                files[path] = _stat_signature(info)
                if len(files) > MAX_TREE_FILES:
                    raise UnsafeTree("RUN_TREE_FILE_COUNT_LIMIT")
            else:
                raise UnsafeTree("RUN_TREE_UNSAFE_ENTRY")

    walk(root_fd, (), 0)
    return files


def _parse_receipt(raw: bytes) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except DuplicateJSONKey:
        return None, "RECEIPT_DUPLICATE_JSON_KEY"
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return None, "RECEIPT_INVALID_JSON"
    if not isinstance(value, dict):
        return None, "RECEIPT_NOT_OBJECT"
    if value.get("schema") != RECEIPT_SCHEMA:
        return None, "RECEIPT_SCHEMA_UNSUPPORTED"
    context = value.get("context")
    inputs = value.get("input")
    if not isinstance(context, dict) or context.get("adapter_id") != "e37-source-snapshot-v1":
        return None, "RECEIPT_ADAPTER_UNSUPPORTED"
    if not isinstance(inputs, dict) or inputs.get("kind") != "offline_source_snapshots":
        return None, "RECEIPT_INPUT_KIND_UNSUPPORTED"
    rows = value.get("artifacts")
    if not isinstance(rows, list) or not rows or len(rows) > MAX_ARTIFACTS:
        return None, "RECEIPT_ARTIFACT_LIST_INVALID"
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            return None, "RECEIPT_ARTIFACT_ROW_INVALID"
        parts, path_error = _relative_parts(row.get("path"))
        if path_error or parts is None:
            return None, path_error or "RECEIPT_ARTIFACT_PATH_INVALID"
        path = "/".join(parts)
        if path in seen:
            return None, "RECEIPT_ARTIFACT_PATH_DUPLICATE"
        seen.add(path)
        digest = row.get("sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            return None, "RECEIPT_ARTIFACT_DIGEST_INVALID"
        size = row.get("bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            return None, "RECEIPT_ARTIFACT_SIZE_INVALID"
    return value, None


def evaluate(run_directory: str | os.PathLike[str]) -> tuple[dict[str, Any], int]:
    root, root_error = _absolute_root(run_directory)
    if root_error or root is None:
        return _result(root_error or "RUN_ROOT_INVALID", findings=[{"code": root_error or "RUN_ROOT_INVALID"}]), 2
    root_fd, open_error = _open_absolute_directory(root)
    if open_error or root_fd is None:
        return _result(open_error or "RUN_ROOT_UNAVAILABLE", findings=[{"code": open_error or "RUN_ROOT_UNAVAILABLE"}]), 2

    try:
        try:
            files_before = _scan_tree(root_fd)
        except UnsafeTree as exc:
            return _result(str(exc), findings=[{"code": str(exc)}], workspace_observation="TREE_REJECTED"), 2
        if "receipt.json" not in files_before:
            return _result("RECEIPT_MISSING", findings=[{"code": "RECEIPT_MISSING"}], workspace_observation="TREE_SCANNED"), 2

        receipt_bytes, receipt_error = _read_relative_file(root_fd, ("receipt.json",), MAX_RECEIPT_BYTES)
        if receipt_error or receipt_bytes is None:
            return _result(
                "RECEIPT_" + (receipt_error or "READ_FAILED"),
                findings=[{"code": "RECEIPT_" + (receipt_error or "READ_FAILED")}],
                workspace_observation="TREE_SCANNED",
            ), 2
        receipt, parse_error = _parse_receipt(receipt_bytes)
        if parse_error or receipt is None:
            return _result(
                parse_error or "RECEIPT_INVALID",
                findings=[{"code": parse_error or "RECEIPT_INVALID"}],
                receipt_bytes_read=len(receipt_bytes),
                workspace_observation="TREE_SCANNED",
            ), 2

        expected_rows: dict[str, dict[str, Any]] = {
            row["path"]: row for row in receipt["artifacts"]
        }
        expected_paths = set(expected_rows) | {"receipt.json"}
        actual_paths = set(files_before)
        missing_paths = sorted(expected_paths - actual_paths)
        unlisted_paths = sorted(actual_paths - expected_paths)
        artifact_results: list[dict[str, Any]] = []
        total_bytes = 0
        for path, row in sorted(expected_rows.items()):
            parts, _ = _relative_parts(path)
            assert parts is not None
            expected_size = row["bytes"]
            if expected_size > MAX_FILE_BYTES:
                artifact_results.append({
                    "path": path, "status": "SIZE_LIMIT", "expected_bytes": expected_size,
                    "expected_sha256": row["sha256"], "bytes_read": 0,
                })
                continue
            remaining = MAX_TOTAL_BYTES - total_bytes
            if expected_size > remaining:
                artifact_results.append({
                    "path": path, "status": "TOTAL_SIZE_LIMIT", "expected_bytes": expected_size,
                    "expected_sha256": row["sha256"], "bytes_read": 0,
                })
                continue
            payload, file_error = _read_relative_file(root_fd, parts, min(MAX_FILE_BYTES, remaining))
            if file_error or payload is None:
                artifact_results.append({
                    "path": path, "status": file_error or "READ_FAILED", "expected_bytes": expected_size,
                    "expected_sha256": row["sha256"], "bytes_read": 0,
                })
                continue
            total_bytes += len(payload)
            observed_sha = hashlib.sha256(payload).hexdigest()
            if len(payload) != expected_size:
                status = "BYTE_LENGTH_MISMATCH"
            elif observed_sha != row["sha256"]:
                status = "DIGEST_MISMATCH"
            else:
                status = "DIGEST_MATCH"
            artifact_results.append({
                "path": path,
                "status": status,
                "expected_bytes": expected_size,
                "observed_bytes": len(payload),
                "expected_sha256": row["sha256"],
                "observed_sha256": observed_sha,
                "bytes_read": len(payload),
            })

        try:
            files_after = _scan_tree(root_fd)
        except UnsafeTree as exc:
            return _result(
                str(exc), findings=[{"code": str(exc)}], artifacts=artifact_results,
                total_bytes_read=total_bytes, receipt_bytes_read=len(receipt_bytes),
                workspace_observation="TREE_CHANGED_OR_REJECTED",
            ), 2
        if files_after != files_before:
            return _result(
                "RUN_TREE_CHANGED_DURING_READ",
                findings=[{"code": "RUN_TREE_CHANGED_DURING_READ"}], artifacts=artifact_results,
                missing_paths=missing_paths, unlisted_paths=unlisted_paths,
                total_bytes_read=total_bytes, receipt_bytes_read=len(receipt_bytes),
                workspace_observation="TREE_CHANGED_DURING_READ",
            ), 2

        statuses = {row["status"] for row in artifact_results}
        if missing_paths or unlisted_paths:
            status = "ARTIFACT_SET_MISMATCH"
            findings = [{"code": "ARTIFACT_SET_MISMATCH"}]
        elif "DIGEST_MISMATCH" in statuses or "BYTE_LENGTH_MISMATCH" in statuses:
            status = "ARTIFACT_BYTES_MISMATCH"
            findings = [{"code": "ARTIFACT_BYTES_MISMATCH"}]
        elif statuses != {"DIGEST_MATCH"}:
            status = "ARTIFACTS_UNVERIFIED"
            findings = [{"code": code} for code in sorted(statuses - {"DIGEST_MATCH"})]
        else:
            status = "ALL_ARTIFACT_DIGESTS_MATCH"
            findings = []
        result = _result(
            status, findings=findings, artifacts=artifact_results,
            missing_paths=missing_paths, unlisted_paths=unlisted_paths,
            total_bytes_read=total_bytes, receipt_bytes_read=len(receipt_bytes),
            workspace_observation="BOUNDED_EXTERNAL_RUN_TREE_READ",
        )
        return result, 0 if status == "ALL_ARTIFACT_DIGESTS_MATCH" else 2
    finally:
        os.close(root_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="canonical absolute E37 run directory outside the checked-out repository")
    args = parser.parse_args(argv)
    result, code = evaluate(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
