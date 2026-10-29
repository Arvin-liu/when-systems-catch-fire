#!/usr/bin/env python3
"""Select exact JSONL records from one bounded file under ignition/."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, BinaryIO


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
TOOL_ID = "knowledge.select_jsonl_records"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = "toolbox-jsonl-selector-output-r0"
MAX_REQUEST_BYTES = 64_000
MAX_SOURCE_BYTES = 32_000_000
MAX_RETURNED_BYTES = 262_144
MAX_MATCHES = 100
MAX_POINTER_CHARS = 4_096
MAX_RECORD_BYTES = 1_048_576
_SOURCE_PATH_RE = re.compile(r"^ignition/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+$")
_ARRAY_INDEX_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")

CLAIM_CEILING = (
    "Selects exact JSONL records by one caller-supplied JSON Pointer and JSON scalar equality from one regular "
    "file under ignition/ (strings exact, numbers by numeric value, booleans distinct from numbers, null only "
    "with null), returning selected record text, its byte range, and source/record SHA-256. "
    "It does not cache, redact, discover files, establish semantic relevance or source authority, evaluate claims, "
    "or establish token savings, completeness outside the selected file, or publication readiness."
)


class SelectorError(ValueError):
    """A bounded, fail-closed request or file observation could not be completed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SelectorError("DUPLICATE_JSON_KEY", "duplicate object key encountered")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> None:
    raise SelectorError("NON_JSON_NUMBER", "NaN and Infinity are not valid JSON values")


def _parse_finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise SelectorError("NON_JSON_NUMBER", "JSON numeric value exceeds the finite range")
    return result


def _load_json(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
            parse_float=_parse_finite_float,
        )
    except SelectorError:
        raise
    except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError) as exc:
        raise SelectorError("INVALID_JSON", "input is not valid UTF-8 JSON") from exc


def _is_json_scalar(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _json_scalar_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return isinstance(left, str) and isinstance(right, str) and left == right


def _validate_pointer(pointer: Any) -> list[str]:
    if not isinstance(pointer, str) or len(pointer) > MAX_POINTER_CHARS:
        raise SelectorError("INVALID_JSON_POINTER", "json_pointer must be a string of at most 4096 characters")
    try:
        pointer.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise SelectorError("INVALID_JSON_POINTER", "json_pointer must contain valid Unicode scalar values") from exc
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise SelectorError("INVALID_JSON_POINTER", "json_pointer must be empty or begin with slash")
    result: list[str] = []
    for encoded in pointer[1:].split("/"):
        decoded: list[str] = []
        index = 0
        while index < len(encoded):
            char = encoded[index]
            if char != "~":
                decoded.append(char)
                index += 1
                continue
            if index + 1 >= len(encoded) or encoded[index + 1] not in "01":
                raise SelectorError("INVALID_JSON_POINTER", "json_pointer contains an invalid tilde escape")
            decoded.append("~" if encoded[index + 1] == "0" else "/")
            index += 2
        result.append("".join(decoded))
    return result


def _pointer_value(document: Any, segments: list[str]) -> tuple[bool, Any]:
    value = document
    for segment in segments:
        if isinstance(value, dict):
            if segment not in value:
                return False, None
            value = value[segment]
        elif isinstance(value, list):
            if not _ARRAY_INDEX_RE.fullmatch(segment):
                return False, None
            position = int(segment)
            if position >= len(value):
                return False, None
            value = value[position]
        else:
            return False, None
    return True, value


def _validate_request(request: Any) -> dict[str, Any]:
    required = {
        "schema_version",
        "source_path",
        "json_pointer",
        "equals",
        "max_source_bytes",
        "max_returned_bytes",
        "max_matches",
    }
    if not isinstance(request, dict) or set(request) != required:
        raise SelectorError("INVALID_REQUEST", "request must contain exactly the documented fields")
    if request["schema_version"] != "toolbox-jsonl-selector-input-r0":
        raise SelectorError("INVALID_REQUEST", "schema_version is not supported")
    source_path = request["source_path"]
    if not isinstance(source_path, str) or len(source_path) > 1024 or not _SOURCE_PATH_RE.fullmatch(source_path):
        raise SelectorError("INVALID_SOURCE_PATH", "source_path must be a normalized path under ignition/")
    if any(part in {".", ".."} for part in source_path.split("/")):
        raise SelectorError("INVALID_SOURCE_PATH", "source_path must not contain dot or traversal components")
    if not _is_json_scalar(request["equals"]):
        raise SelectorError("INVALID_REQUEST", "equals must be one JSON scalar value")
    if isinstance(request["equals"], str):
        try:
            request["equals"].encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise SelectorError("INVALID_REQUEST", "equals string must contain valid Unicode scalar values") from exc
    pointer_segments = _validate_pointer(request["json_pointer"])
    for key, minimum, maximum in (
        ("max_source_bytes", 1, MAX_SOURCE_BYTES),
        ("max_returned_bytes", 1, MAX_RETURNED_BYTES),
        ("max_matches", 1, MAX_MATCHES),
    ):
        value = request[key]
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            raise SelectorError("INVALID_LIMIT", f"{key} must be an integer from {minimum} to {maximum}")
    return {
        "source_path": source_path,
        "json_pointer": request["json_pointer"],
        "pointer_segments": pointer_segments,
        "equals": request["equals"],
        "max_source_bytes": request["max_source_bytes"],
        "max_returned_bytes": request["max_returned_bytes"],
        "max_matches": request["max_matches"],
    }


def _open_repo_file(workspace_root: str | Path, source_path: str) -> BinaryIO:
    """Open one file beneath ignition/ without following symlink components."""
    root_arg = Path(workspace_root)
    if not root_arg.is_absolute():
        raise SelectorError("INVALID_WORKSPACE_ROOT", "workspace_root must be an absolute directory path")
    try:
        root = root_arg.resolve(strict=True)
    except OSError as exc:
        raise SelectorError("WORKSPACE_ROOT_UNAVAILABLE", "workspace_root is unavailable") from exc
    if not root.is_dir():
        raise SelectorError("INVALID_WORKSPACE_ROOT", "workspace_root must be a directory")
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, flag) for flag in required_flags) or os.open not in os.supports_dir_fd:
        raise SelectorError("SAFE_OPEN_UNAVAILABLE", "platform lacks required no-follow directory-descriptor support")

    directory_flag = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flag = os.O_RDONLY | os.O_NOFOLLOW
    opened_dirs: list[int] = []
    root_fd: int | None = None
    file_fd: int | None = None
    try:
        root_fd = os.open(root, directory_flag)
        current_fd = root_fd
        parts = source_path.split("/")
        for part in parts[:-1]:
            current_fd = os.open(part, directory_flag, dir_fd=current_fd)
            opened_dirs.append(current_fd)
        file_fd = os.open(parts[-1], file_flag, dir_fd=current_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise SelectorError("SOURCE_NOT_REGULAR", "source_path must identify a regular file")
        stream = os.fdopen(file_fd, "rb")
        file_fd = None
        return stream
    except SelectorError:
        raise
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise SelectorError("SOURCE_SYMLINK", "source_path contains a symlink") from exc
        raise SelectorError("SOURCE_UNAVAILABLE", "source_path could not be opened safely") from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for descriptor in reversed(opened_dirs):
            os.close(descriptor)
        if root_fd is not None:
            os.close(root_fd)


def execute_request(request: Any, workspace_root: str | Path) -> dict[str, Any]:
    clean = _validate_request(request)
    source_path = clean["source_path"]
    try:
        stream = _open_repo_file(workspace_root, source_path)
    except SelectorError:
        raise

    records: list[dict[str, Any]] = []
    source_hash = hashlib.sha256()
    source_bytes = 0
    line_number = 0
    returned_bytes = 0
    before = os.fstat(stream.fileno())
    if before.st_size > clean["max_source_bytes"]:
        stream.close()
        raise SelectorError("SOURCE_TOO_LARGE", "source file exceeds max_source_bytes")

    try:
        while True:
            raw_line = stream.readline(MAX_RECORD_BYTES + 3)
            if not raw_line:
                break
            if len(raw_line) > MAX_RECORD_BYTES + 2:
                raise SelectorError("RECORD_TOO_LARGE", "a JSONL record exceeds the fixed 1 MiB parse limit")
            source_bytes += len(raw_line)
            if source_bytes > clean["max_source_bytes"]:
                raise SelectorError("SOURCE_TOO_LARGE", "source file grew beyond max_source_bytes while being read")
            source_hash.update(raw_line)
            line_number += 1
            body = raw_line[:-1] if raw_line.endswith(b"\n") else raw_line
            if raw_line.endswith(b"\r\n"):
                body = body[:-1]
            if len(body) > MAX_RECORD_BYTES:
                raise SelectorError("RECORD_TOO_LARGE", "a JSONL record exceeds the fixed 1 MiB parse limit")
            if not body:
                raise SelectorError("BLANK_RECORD", f"blank JSONL record at line {line_number}")
            try:
                text = body.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise SelectorError("INVALID_UTF8", f"JSONL record at line {line_number} is not UTF-8") from exc
            try:
                document = _load_json(text)
            except SelectorError as exc:
                raise SelectorError(exc.code, f"invalid JSONL record at line {line_number}: {exc.message}") from exc
            if not isinstance(document, dict):
                raise SelectorError("RECORD_NOT_OBJECT", f"JSONL record at line {line_number} is not an object")
            found, value = _pointer_value(document, clean["pointer_segments"])
            if found and _json_scalar_equal(value, clean["equals"]):
                if len(records) >= clean["max_matches"]:
                    raise SelectorError("TOO_MANY_MATCHES", "matching records exceed max_matches; no records returned")
                if returned_bytes + len(body) > clean["max_returned_bytes"]:
                    raise SelectorError("RETURN_LIMIT_EXCEEDED", "matching record bytes exceed max_returned_bytes; no records returned")
                start = source_bytes - len(raw_line)
                returned_bytes += len(body)
                records.append({
                    "line_number": line_number,
                    "start_byte_offset": start,
                    "end_byte_offset_exclusive": start + len(body),
                    "byte_count": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "text": text,
                })
        after = os.fstat(stream.fileno())
    finally:
        stream.close()

    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns
    ):
        raise SelectorError("SOURCE_CHANGED_DURING_READ", "source metadata changed during the bounded read")
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": "COMPLETE",
        "source_path": source_path,
        "source_sha256": source_hash.hexdigest(),
        "source_bytes": source_bytes,
        "lines_scanned": line_number,
        "selector": {
            "json_pointer": clean["json_pointer"],
            "equals": clean["equals"],
            "equality": "JSON_SCALAR_VALUE_EXACT",
        },
        "selected_record_count": len(records),
        "selected_record_bytes": returned_bytes,
        "records": records,
        "effects": {"files_written": False, "network": False, "execution_authorized": False},
        "claim_ceiling": CLAIM_CEILING,
    }


def _rejection(exc: SelectorError) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": "REJECTED",
        "error": {"code": exc.code, "message": exc.message},
        "effects": {"files_written": False, "network": False, "execution_authorized": False},
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True)
    parser.add_argument("--workspace-root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        if len(raw) > MAX_REQUEST_BYTES:
            raise SelectorError("REQUEST_TOO_LARGE", "stdin exceeds the 64000-byte request limit")
        try:
            request = _load_json(raw.decode("utf-8", errors="strict"))
        except UnicodeDecodeError as exc:
            raise SelectorError("INVALID_UTF8", "stdin is not UTF-8") from exc
        result = execute_request(request, args.workspace_root)
    except SelectorError as exc:
        result = _rejection(exc)
        exit_code = 1
    else:
        exit_code = 0
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
