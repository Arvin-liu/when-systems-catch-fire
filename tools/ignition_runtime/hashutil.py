"""Hashing and path-safety helpers (stdlib only)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from .errors import PathEscapeError


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def deterministic_id(prefix: str, payload: str) -> str:
    """Build a prefixed id from a sha256 payload (first 32 hex chars)."""
    return f"{prefix}_{sha256_text(payload)[:32]}"


# Allowed characters for a generation id / CURRENT token (no traversal, no slash).
_GEN_ID_RE = __import__("re").compile(r"^[A-Za-z0-9._-]+$")


def is_safe_token(token: str) -> bool:
    """"A CURRENT pointer token must be a single non-empty safe token."""
    return bool(token) and _GEN_ID_RE.match(token) is not None and "\n" not in token


def assert_under_root(path: Path, root: Path) -> Path:
    """Fail closed if ``path`` escapes ``root`` (resolving symlinks).

    Used both for the store directory (never write outside the store) and for
    the FileSystemProvider (never read outside the inputs root).
    """
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:  # not under root
        raise PathEscapeError(
            f"path {resolved} escapes authorized root {root_resolved}"
        ) from exc
    return resolved


def safe_open_nofollow(path: Path, flags: int):
    """Open ``path`` without following symlinks (O_NOFOLLOW)."""
    return os.open(str(path), flags | getattr(os, "O_NOFOLLOW", 0))
