"""Provider-neutral filesystem authority contracts for bounded live attempts.

The contract deliberately separates the disposable task workspace from the
executor's short-lived runtime scratch and from any existing auth reference.
It is a policy/validation layer only: it does not create a process, read
credential contents, or grant a provider capability.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
from typing import Any, Mapping, Sequence

from .contracts import FederationContractError


FILESYSTEM_DOMAINS_SCHEMA = "executor-filesystem-domains-r1"
TASK_WORKSPACE = "TASK_WORKSPACE"
EXECUTOR_RUNTIME_SCRATCH = "EXECUTOR_RUNTIME_SCRATCH"
AUTH_OR_CONFIG_SOURCE = "AUTH_OR_CONFIG_SOURCE"

TASK_WORKSPACE_MODE = "DISPOSABLE_READ_ONLY"
RUNTIME_SCRATCH_MODE = "ATTEMPT_EPHEMERAL_WRITABLE"
AUTH_SOURCE_MODE = "READ_ONLY_REFERENCE"
RUNTIME_SCRATCH_CLEANUP_POLICY = "CLEANUP_FINALLY_FAIL_CLOSED"
RUNTIME_ENV_REDACTION_POLICY = "PRESENCE_ONLY_REDACT_PATHS_NO_VALUES"

PATH_ASSERTION_KEYS = (
    "task_workspace_vs_runtime_scratch",
    "task_workspace_vs_formal_repo",
    "task_workspace_vs_control_repo",
    "task_workspace_vs_persistent_user_document_tree",
    "runtime_scratch_vs_formal_repo",
    "runtime_scratch_vs_control_repo",
    "runtime_scratch_vs_persistent_user_document_tree",
    "auth_source_vs_task_workspace",
    "auth_source_vs_runtime_scratch",
)

SAFE_RUNTIME_ENV_NAMES = frozenset({
    "PATH",
    "LANG",
    "LC_ALL",
    "HOME",
    "TMPDIR",
    "CODEX_HOME",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_RUNTIME_DIR",
    "POINTFIRE_LIVE_CHILD_DEPTH",
})
_WRITE_BITS = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
_SECRET_MARKERS = ("secret", "token", "api_key", "password", "cookie", "authorization", "credential")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FederationContractError(f"{field} must be a non-empty string")
    return value.strip()


def _digest(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise FederationContractError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _strings(values: Sequence[str], field: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise FederationContractError(f"{field} must be an array")
    result = tuple(_text(value, f"{field}[]") for value in values)
    if nonempty and not result:
        raise FederationContractError(f"{field} must not be empty")
    if len(result) != len(set(result)):
        raise FederationContractError(f"{field} must not contain duplicates")
    return result


def _path_text(value: Any, field: str, *, allow_auth_ref: bool = False) -> str:
    value = _text(value, field)
    if allow_auth_ref and value.startswith("auth://"):
        return value
    if not value.startswith("/"):
        raise FederationContractError(f"{field} must be an absolute path or an auth:// reference")
    return value


def _is_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _canonical_existing_path(value: str, field: str, *, directory: bool = True) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise FederationContractError(f"{field} must be absolute")
    try:
        absolute = path.absolute()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise FederationContractError(f"{field} cannot be resolved") from exc
    # A live domain must not itself be a symlink alias whose target escapes
    # the declared boundary.  System parents such as macOS /var may be
    # symlink aliases, so only the domain root is rejected here; symlinks
    # inside the domain tree are rejected separately by _tree_has_symlink.
    if path.is_symlink():
        raise FederationContractError(f"{field} contains a symlink/path escape")
    if directory and not resolved.is_dir():
        raise FederationContractError(f"{field} must be an existing directory")
    if not directory and not resolved.exists():
        raise FederationContractError(f"{field} must be an existing path")
    return resolved


def _tree_has_symlink(path: Path) -> bool:
    try:
        return any(item.is_symlink() for item in (path, *path.rglob("*")))
    except OSError as exc:
        raise FederationContractError(f"cannot inspect symlink boundary: {path}") from exc


def _tree_has_write_bits(path: Path) -> bool:
    try:
        entries = (path, *path.rglob("*")) if path.is_dir() else (path,)
        return any(stat.S_IMODE(item.stat().st_mode) & _WRITE_BITS for item in entries)
    except OSError as exc:
        raise FederationContractError(f"cannot inspect permission boundary: {path}") from exc


def _is_current_owner(path: Path, owner: str) -> bool:
    if owner == "current-user":
        expected_uid = os.getuid()
    elif owner.startswith("uid:"):
        try:
            expected_uid = int(owner[4:])
        except ValueError:
            return False
    else:
        return False
    try:
        return path.stat().st_uid == expected_uid
    except OSError as exc:
        raise FederationContractError("cannot inspect runtime scratch owner") from exc


def _auth_path(value: str) -> Path | None:
    if value.startswith("auth://"):
        if value == "auth://":
            raise FederationContractError("auth_source_ref auth:// reference must be named")
        return None
    return _canonical_existing_path(value, "auth_source_ref", directory=False)


@dataclass(frozen=True)
class ExecutionFilesystemDomains:
    """Machine contract for the three filesystem authority domains."""

    task_workspace_ref: str
    task_workspace_mode: str
    task_workspace_digest_before: str
    task_workspace_digest_after: str
    runtime_scratch_ref: str
    runtime_scratch_mode: str
    runtime_scratch_owner: str
    runtime_scratch_ttl: float
    runtime_scratch_cleanup_policy: str
    runtime_scratch_digest_before: str
    runtime_scratch_digest_after: str
    auth_source_ref: str
    auth_source_mode: str
    auth_source_content_read: bool
    config_mutation_allowed: bool
    runtime_env_allowlist: tuple[str, ...]
    runtime_env_redaction_policy: str
    path_non_overlap_assertions: Mapping[str, bool]
    permission_non_escalation_assertion: bool
    runtime_scratch_persistence_declared: bool
    secret_materialization: bool
    unknown_filesystem_domains: tuple[str, ...]
    formal_repo_ref: str
    control_repo_ref: str
    persistent_user_document_roots: tuple[str, ...]

    def __post_init__(self) -> None:
        _path_text(self.task_workspace_ref, "task_workspace_ref")
        _path_text(self.runtime_scratch_ref, "runtime_scratch_ref")
        _path_text(self.auth_source_ref, "auth_source_ref", allow_auth_ref=True)
        _path_text(self.formal_repo_ref, "formal_repo_ref")
        _path_text(self.control_repo_ref, "control_repo_ref")
        if self.task_workspace_mode != TASK_WORKSPACE_MODE:
            raise FederationContractError("task workspace must be DISPOSABLE_READ_ONLY")
        if self.runtime_scratch_mode != RUNTIME_SCRATCH_MODE:
            raise FederationContractError("runtime scratch must be ATTEMPT_EPHEMERAL_WRITABLE")
        if self.auth_source_mode != AUTH_SOURCE_MODE:
            raise FederationContractError("auth source must be READ_ONLY_REFERENCE")
        for field in (
            "task_workspace_digest_before", "task_workspace_digest_after",
            "runtime_scratch_digest_before", "runtime_scratch_digest_after",
        ):
            _digest(getattr(self, field), field)
        _text(self.runtime_scratch_owner, "runtime_scratch_owner")
        if isinstance(self.runtime_scratch_ttl, bool) or not isinstance(self.runtime_scratch_ttl, (int, float)) or not 0 < self.runtime_scratch_ttl <= 3600:
            raise FederationContractError("runtime_scratch_ttl must be in (0, 3600]")
        if self.runtime_scratch_cleanup_policy != RUNTIME_SCRATCH_CLEANUP_POLICY:
            raise FederationContractError("runtime scratch cleanup must fail closed in finally")
        if self.auth_source_content_read is not False:
            raise FederationContractError("auth source content_read must be false")
        if self.config_mutation_allowed is not False:
            raise FederationContractError("config mutation is forbidden")
        if self.runtime_env_redaction_policy != RUNTIME_ENV_REDACTION_POLICY:
            raise FederationContractError("runtime environment redaction policy is unsupported")
        env_names = _strings(self.runtime_env_allowlist, "runtime_env_allowlist", nonempty=True)
        if any(name not in SAFE_RUNTIME_ENV_NAMES for name in env_names):
            raise FederationContractError("runtime environment contains an unknown or unsafe name")
        if any(any(marker in name.casefold() for marker in _SECRET_MARKERS) for name in env_names):
            raise FederationContractError("runtime environment cannot contain secret-like names")
        if not isinstance(self.path_non_overlap_assertions, Mapping) or set(self.path_non_overlap_assertions) != set(PATH_ASSERTION_KEYS):
            raise FederationContractError("path_non_overlap_assertions must contain exactly the declared domain pairs")
        if any(type(value) is not bool for value in self.path_non_overlap_assertions.values()):
            raise FederationContractError("path_non_overlap_assertions values must be booleans")
        if not self.permission_non_escalation_assertion:
            raise FederationContractError("permission non-escalation assertion must be true")
        if self.runtime_scratch_persistence_declared is not True:
            raise FederationContractError("runtime scratch persistence policy must be explicitly declared")
        if self.secret_materialization is not False:
            raise FederationContractError("secret materialization is forbidden")
        unknown = _strings(self.unknown_filesystem_domains, "unknown_filesystem_domains")
        if unknown:
            raise FederationContractError(f"unknown filesystem domains are forbidden: {unknown}")
        _strings(self.persistent_user_document_roots, "persistent_user_document_roots", nonempty=True)

    def validate_paths(self) -> "ExecutionFilesystemDomains":
        """Validate canonical paths, permissions, owners, overlap and escapes."""

        workspace = _canonical_existing_path(self.task_workspace_ref, "task_workspace_ref")
        scratch = _canonical_existing_path(self.runtime_scratch_ref, "runtime_scratch_ref")
        formal = _canonical_existing_path(self.formal_repo_ref, "formal_repo_ref")
        control = _canonical_existing_path(self.control_repo_ref, "control_repo_ref")
        persistent = tuple(
            _canonical_existing_path(value, "persistent_user_document_roots[]")
            for value in self.persistent_user_document_roots
        )
        auth = _auth_path(self.auth_source_ref)
        domain_trees = (workspace, scratch, formal, control, *persistent)
        if any(_tree_has_symlink(path) for path in domain_trees):
            raise FederationContractError("filesystem domain contains a symlink/path escape")
        if auth is not None and _tree_has_symlink(auth):
            raise FederationContractError("auth source contains a symlink/path escape")
        if _tree_has_write_bits(workspace):
            raise FederationContractError("task workspace is writable")
        if not _tree_has_write_bits(scratch):
            raise FederationContractError("runtime scratch is not writable")
        if not _is_current_owner(scratch, self.runtime_scratch_owner):
            raise FederationContractError("runtime scratch owner is not the current executor owner")
        if auth is not None and _tree_has_write_bits(auth):
            raise FederationContractError("auth source is writable")
        computed = {
            "task_workspace_vs_runtime_scratch": not _is_overlap(workspace, scratch),
            "task_workspace_vs_formal_repo": not _is_overlap(workspace, formal),
            "task_workspace_vs_control_repo": not _is_overlap(workspace, control),
            "task_workspace_vs_persistent_user_document_tree": not any(_is_overlap(workspace, root) for root in persistent),
            "runtime_scratch_vs_formal_repo": not _is_overlap(scratch, formal),
            "runtime_scratch_vs_control_repo": not _is_overlap(scratch, control),
            "runtime_scratch_vs_persistent_user_document_tree": not any(_is_overlap(scratch, root) for root in persistent),
            "auth_source_vs_task_workspace": auth is None or not _is_overlap(auth, workspace),
            "auth_source_vs_runtime_scratch": auth is None or not _is_overlap(auth, scratch),
        }
        for key, passed in computed.items():
            if self.path_non_overlap_assertions[key] is not passed or not passed:
                raise FederationContractError(f"filesystem domain overlap assertion failed: {key}")
        return self

    def to_dict(self, *, redact_paths: bool = False) -> dict[str, Any]:
        def ref(value: str, label: str) -> str:
            return label if redact_paths else value

        return {
            "schema_version": FILESYSTEM_DOMAINS_SCHEMA,
            "task_workspace_ref": ref(self.task_workspace_ref, "DISPOSABLE_TASK_WORKSPACE"),
            "task_workspace_mode": self.task_workspace_mode,
            "task_workspace_digest_before": self.task_workspace_digest_before,
            "task_workspace_digest_after": self.task_workspace_digest_after,
            "runtime_scratch_ref": ref(self.runtime_scratch_ref, "ATTEMPT_RUNTIME_SCRATCH"),
            "runtime_scratch_mode": self.runtime_scratch_mode,
            "runtime_scratch_owner": self.runtime_scratch_owner,
            "runtime_scratch_ttl": self.runtime_scratch_ttl,
            "runtime_scratch_cleanup_policy": self.runtime_scratch_cleanup_policy,
            "runtime_scratch_digest_before": self.runtime_scratch_digest_before,
            "runtime_scratch_digest_after": self.runtime_scratch_digest_after,
            "auth_source_ref": ref(self.auth_source_ref, "AUTH_SOURCE_READ_ONLY_REFERENCE"),
            "auth_source_mode": self.auth_source_mode,
            "auth_source_content_read": self.auth_source_content_read,
            "config_mutation_allowed": self.config_mutation_allowed,
            "runtime_env_allowlist": list(self.runtime_env_allowlist),
            "runtime_env_redaction_policy": self.runtime_env_redaction_policy,
            "path_non_overlap_assertions": dict(self.path_non_overlap_assertions),
            "permission_non_escalation_assertion": self.permission_non_escalation_assertion,
            "runtime_scratch_persistence_declared": self.runtime_scratch_persistence_declared,
            "secret_materialization": self.secret_materialization,
            "unknown_filesystem_domains": list(self.unknown_filesystem_domains),
            "formal_repo_ref": ref(self.formal_repo_ref, "FORMAL_REPOSITORY_PROTECTED"),
            "control_repo_ref": ref(self.control_repo_ref, "CONTROL_REPOSITORY_PROTECTED"),
            "persistent_user_document_roots": [
                ref(value, "PERSISTENT_USER_DOCUMENT_TREE") for value in self.persistent_user_document_roots
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionFilesystemDomains":
        if not isinstance(data, Mapping):
            raise FederationContractError("filesystem domains contract must be an object")
        keys = {
            "schema_version", "task_workspace_ref", "task_workspace_mode", "task_workspace_digest_before",
            "task_workspace_digest_after", "runtime_scratch_ref", "runtime_scratch_mode", "runtime_scratch_owner",
            "runtime_scratch_ttl", "runtime_scratch_cleanup_policy", "runtime_scratch_digest_before",
            "runtime_scratch_digest_after", "auth_source_ref", "auth_source_mode", "auth_source_content_read",
            "config_mutation_allowed", "runtime_env_allowlist", "runtime_env_redaction_policy",
            "path_non_overlap_assertions", "permission_non_escalation_assertion", "runtime_scratch_persistence_declared",
            "secret_materialization", "unknown_filesystem_domains", "formal_repo_ref", "control_repo_ref",
            "persistent_user_document_roots",
        }
        if set(data) != keys:
            raise FederationContractError(f"filesystem domains keys must be exactly {sorted(keys)}")
        if data["schema_version"] != FILESYSTEM_DOMAINS_SCHEMA:
            raise FederationContractError("filesystem domains schema version mismatch")
        values = dict(data)
        values.pop("schema_version")
        values["runtime_env_allowlist"] = tuple(values["runtime_env_allowlist"])
        values["unknown_filesystem_domains"] = tuple(values["unknown_filesystem_domains"])
        values["persistent_user_document_roots"] = tuple(values["persistent_user_document_roots"])
        return cls(**values)


def empty_scratch_digest() -> str:
    """Stable digest for an empty scratch metadata tree."""

    return hashlib.sha256(b"").hexdigest()


__all__ = [
    "AUTH_OR_CONFIG_SOURCE", "AUTH_SOURCE_MODE", "EXECUTOR_RUNTIME_SCRATCH", "FILESYSTEM_DOMAINS_SCHEMA",
    "ExecutionFilesystemDomains", "PATH_ASSERTION_KEYS", "RUNTIME_ENV_REDACTION_POLICY",
    "RUNTIME_SCRATCH_CLEANUP_POLICY", "RUNTIME_SCRATCH_MODE", "SAFE_RUNTIME_ENV_NAMES",
    "TASK_WORKSPACE", "TASK_WORKSPACE_MODE", "empty_scratch_digest",
]
