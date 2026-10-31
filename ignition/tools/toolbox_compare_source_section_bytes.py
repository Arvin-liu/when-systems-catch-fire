#!/usr/bin/env python3
"""Compare one marker-delimited source-text section with a checked-out human document."""

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
REPO_ROOT = IGNITION_ROOT.parent.resolve()
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-source-section-parity-input-r0.schema.json"
MAX_INPUT_BYTES = 512_000
MAX_SOURCE_BYTES = 384_000
MAX_CANDIDATE_BYTES = 2 * 1024 * 1024
MAX_PATH_CHARS = 4_096
MAX_PATH_DEPTH = 32
MAX_PATH_COMPONENT_CHARS = 255
MAX_MARKER_BYTES = 1_024
TOOL_ID = "maintenance.compare_source_section_bytes"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "toolbox-source-section-parity-input-r0"
RESULT_SCHEMA_VERSION = "toolbox-source-section-parity-result-r0"
CLAIM_CEILING = (
    "Compares exact UTF-8 bytes between caller-declared unique start and end markers in supplied source text "
    "and one explicitly selected checked-out human-document file. The caller-supplied source reference and "
    "digest are not authenticated; the comparison does not establish authorship, approval, semantic equivalence, "
    "scientific validity, release authority, or permission to edit or publish."
)
PATH_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ALLOWED_HUMAN_ROOTS = {".github", "docs", "ignition"}
ALLOWED_ROOT_DOCUMENTS = {"README.md", "SUMMARY.md", "HUMAN-READING.md", "llms.txt"}
ALLOWED_DOCUMENT_SUFFIXES = {".md", ".txt", ".rst", ".html", ".xml"}


class DuplicateJSONKey(ValueError):
    """Raised when the request repeats any JSON object key."""


class CompareFailure(ValueError):
    def __init__(self, code: str, *, candidate_accessed: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.candidate_accessed = candidate_accessed


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey
        result[key] = value
    return result


def _path_parts(value: Any) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or len(value) > MAX_PATH_CHARS:
        raise CompareFailure("CANDIDATE_PATH_INVALID")
    if PATH_SCHEME_RE.match(value) or value.startswith("/") or "\\" in value or "\x00" in value:
        raise CompareFailure("CANDIDATE_PATH_INVALID")
    parts = tuple(value.split("/"))
    if len(parts) > MAX_PATH_DEPTH:
        raise CompareFailure("CANDIDATE_PATH_INVALID")
    for part in parts:
        if part in {"", ".", ".."} or len(part) > MAX_PATH_COMPONENT_CHARS:
            raise CompareFailure("CANDIDATE_PATH_INVALID")
        if any(ord(char) < 32 or ord(char) == 127 for char in part):
            raise CompareFailure("CANDIDATE_PATH_INVALID")
    root = parts[0]
    if root in ALLOWED_HUMAN_ROOTS:
        if len(parts) < 2 or Path(parts[-1]).suffix.lower() not in ALLOWED_DOCUMENT_SUFFIXES:
            raise CompareFailure("CANDIDATE_PATH_OUTSIDE_HUMAN_DOCUMENTS")
    elif len(parts) == 1 and value in ALLOWED_ROOT_DOCUMENTS:
        pass
    else:
        raise CompareFailure("CANDIDATE_PATH_OUTSIDE_HUMAN_DOCUMENTS")
    return parts


def _open_repo_root() -> int:
    if not all(hasattr(os, attr) for attr in ("O_NOFOLLOW", "O_DIRECTORY")) or os.open not in os.supports_dir_fd:
        raise CompareFailure("PLATFORM_UNSUPPORTED")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        return os.open(str(REPO_ROOT), flags)
    except OSError as exc:
        raise CompareFailure("REPOSITORY_ROOT_UNAVAILABLE") from exc


def _read_candidate(root_fd: int, relative_path: str) -> tuple[bytes, str]:
    parts = _path_parts(relative_path)
    directory_fd = os.dup(root_fd)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        for part in parts[:-1]:
            try:
                next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            except OSError as exc:
                raise CompareFailure("CANDIDATE_PATH_UNAVAILABLE") from exc
            os.close(directory_fd)
            directory_fd = next_fd
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            candidate_fd = os.open(parts[-1], file_flags | getattr(os, "O_NONBLOCK", 0), dir_fd=directory_fd)
        except OSError as exc:
            raise CompareFailure("CANDIDATE_PATH_UNAVAILABLE") from exc
    finally:
        os.close(directory_fd)

    try:
        before = os.fstat(candidate_fd)
        if not stat.S_ISREG(before.st_mode):
            raise CompareFailure("CANDIDATE_NOT_REGULAR_FILE", candidate_accessed=True)
        if before.st_size > MAX_CANDIDATE_BYTES:
            raise CompareFailure("CANDIDATE_FILE_LIMIT_EXCEEDED", candidate_accessed=True)
        chunks: list[bytes] = []
        observed = 0
        while True:
            try:
                chunk = os.read(candidate_fd, min(65_536, MAX_CANDIDATE_BYTES + 1 - observed))
            except OSError as exc:
                raise CompareFailure("CANDIDATE_READ_FAILED", candidate_accessed=True) from exc
            if not chunk:
                break
            observed += len(chunk)
            if observed > MAX_CANDIDATE_BYTES:
                raise CompareFailure("CANDIDATE_FILE_LIMIT_EXCEEDED", candidate_accessed=True)
            chunks.append(chunk)
        after = os.fstat(candidate_fd)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        if identity_before != identity_after or observed != before.st_size:
            raise CompareFailure("CANDIDATE_CHANGED_DURING_READ", candidate_accessed=True)
        data = b"".join(chunks)
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CompareFailure("CANDIDATE_NOT_UTF8", candidate_accessed=True) from exc
        return data, hashlib.sha256(data).hexdigest()
    finally:
        os.close(candidate_fd)


def _find_section(document: bytes, start_marker: bytes, end_marker: bytes, *, prefix: str) -> dict[str, Any]:
    if document.count(start_marker) != 1:
        raise CompareFailure(f"{prefix}_START_MARKER_NOT_UNIQUE")
    if document.count(end_marker) != 1:
        raise CompareFailure(f"{prefix}_END_MARKER_NOT_UNIQUE")
    start = document.find(start_marker)
    end = document.find(end_marker)
    if start >= end or start + len(start_marker) > end:
        raise CompareFailure(f"{prefix}_MARKERS_OUT_OF_ORDER")
    section = document[start:end]
    return {
        "start_offset_bytes": start,
        "end_offset_bytes": end,
        "byte_count": len(section),
        "sha256": hashlib.sha256(section).hexdigest(),
    }


def _result(
    status: str,
    *,
    task_id: str | None = None,
    source_ref: str | None = None,
    source_document: dict[str, Any] | None = None,
    candidate_file: dict[str, Any] | None = None,
    source_section: dict[str, Any] | None = None,
    candidate_section: dict[str, Any] | None = None,
    byte_identical: bool | None = None,
    findings: list[dict[str, str]] | None = None,
    candidate_accessed: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "task_id": task_id,
        "source_ref": source_ref,
        "source_ref_authenticated": False,
        "source_document": source_document,
        "candidate_file": candidate_file,
        "source_section": source_section,
        "candidate_section": candidate_section,
        "byte_identical": byte_identical,
        "findings": findings or [],
        "effects": {
            "candidate_file_accessed": candidate_accessed,
            "files_written": False,
            "network": False,
            "execution_authorized": False,
        },
        "claim_ceiling": CLAIM_CEILING,
    }


def compare_section(value: Any, root_fd: int) -> dict[str, Any]:
    schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""),
    )
    if errors:
        return _result("INPUT_INVALID", findings=[{
            "code": "INPUT_SCHEMA_INVALID",
            "path": error.json_path if hasattr(error, "json_path") else "$",
        } for error in errors[:32]])

    try:
        source_bytes = value["source_document_text"].encode("utf-8")
    except UnicodeEncodeError:
        return _result("INPUT_INVALID", task_id=value["task_id"], source_ref=value["source_ref"],
                       findings=[{"code": "SOURCE_TEXT_NOT_UTF8", "path": "$/source_document_text"}])
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    source_doc = {"sha256": source_digest, "byte_count": len(source_bytes)}
    if len(source_bytes) > MAX_SOURCE_BYTES:
        return _result("INPUT_INVALID", task_id=value["task_id"], source_ref=value["source_ref"],
                       source_document=source_doc,
                       findings=[{"code": "SOURCE_DOCUMENT_LIMIT_EXCEEDED", "path": "$/source_document_text"}])
    if source_digest != value["source_document_sha256"]:
        return _result("INPUT_INVALID", task_id=value["task_id"], source_ref=value["source_ref"],
                       source_document=source_doc,
                       findings=[{"code": "SOURCE_DOCUMENT_DIGEST_MISMATCH", "path": "$/source_document_sha256"}])
    if value["start_marker"] == value["end_marker"]:
        return _result("INPUT_INVALID", task_id=value["task_id"], source_ref=value["source_ref"],
                       source_document=source_doc,
                       findings=[{"code": "MARKERS_MUST_DIFFER", "path": "$/end_marker"}])

    try:
        start_marker = value["start_marker"].encode("utf-8")
        end_marker = value["end_marker"].encode("utf-8")
        if len(start_marker) > MAX_MARKER_BYTES or len(end_marker) > MAX_MARKER_BYTES:
            raise CompareFailure("MARKER_LIMIT_EXCEEDED")
        source_section = _find_section(source_bytes, start_marker, end_marker, prefix="SOURCE")
    except (UnicodeEncodeError, CompareFailure) as exc:
        code = exc.code if isinstance(exc, CompareFailure) else "MARKER_NOT_UTF8"
        return _result("COMPARE_FAILED", task_id=value["task_id"], source_ref=value["source_ref"],
                       source_document=source_doc,
                       findings=[{"code": code, "path": "$/start_marker"}])

    try:
        candidate_data, candidate_digest = _read_candidate(root_fd, value["candidate_path"])
    except CompareFailure as exc:
        return _result("COMPARE_FAILED", task_id=value["task_id"], source_ref=value["source_ref"],
                       source_document=source_doc,
                       candidate_file=({"relative_path": value["candidate_path"], "sha256": None, "byte_count": None}
                                       if exc.candidate_accessed else None),
                       source_section=source_section,
                       findings=[{"code": exc.code, "path": "$/candidate_path"}],
                       candidate_accessed=exc.candidate_accessed)
    candidate_file = {"relative_path": value["candidate_path"], "sha256": candidate_digest,
                      "byte_count": len(candidate_data)}
    try:
        candidate_section = _find_section(candidate_data, start_marker, end_marker, prefix="CANDIDATE")
    except CompareFailure as exc:
        return _result("COMPARE_FAILED", task_id=value["task_id"], source_ref=value["source_ref"],
                       source_document=source_doc, candidate_file=candidate_file,
                       source_section=source_section,
                       findings=[{"code": exc.code, "path": "$/candidate_path"}],
                       candidate_accessed=True)

    identical = source_bytes[source_section["start_offset_bytes"]:source_section["end_offset_bytes"]] == candidate_data[
        candidate_section["start_offset_bytes"]:candidate_section["end_offset_bytes"]
    ]
    return _result("BYTE_IDENTICAL" if identical else "BYTE_DIFFERENT", task_id=value["task_id"],
                   source_ref=value["source_ref"], source_document=source_doc, candidate_file=candidate_file,
                   source_section=source_section, candidate_section=candidate_section,
                   byte_identical=identical, candidate_accessed=True)


def _read_stdin() -> Any:
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise CompareFailure("INPUT_READ_FAILED") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise CompareFailure("INPUT_BYTE_LIMIT_EXCEEDED")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except DuplicateJSONKey:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise CompareFailure("INPUT_INVALID_JSON") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded comparison request from stdin")
    parser.parse_args(argv)
    try:
        value = _read_stdin()
    except DuplicateJSONKey:
        result = _result("INPUT_INVALID", findings=[{"code": "DUPLICATE_JSON_KEY", "path": "$"}])
    except CompareFailure as exc:
        result = _result("INPUT_INVALID", findings=[{"code": exc.code, "path": "$"}])
    else:
        try:
            root_fd = _open_repo_root()
        except CompareFailure as exc:
            result = _result("COMPARE_FAILED", findings=[{"code": exc.code, "path": "$/candidate_path"}])
        else:
            try:
                result = compare_section(value, root_fd)
            finally:
                os.close(root_fd)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"BYTE_IDENTICAL", "BYTE_DIFFERENT"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
