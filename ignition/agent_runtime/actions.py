"""Provider-neutral local action plane for Agent Runtime R1.

The action plane is deliberately smaller than a general shell.  It accepts
typed packets, validates every path and command against a declared workspace
policy, snapshots bounded file preimages, and records bounded observations.
It never enables shell parsing, network access, deletion, remote Git
mutation, package installation, sudo, or system settings changes.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from enum import Enum
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import KernelValidationError, _id, _string, _summary, sha256_json


class WorkspaceViolation(ValueError):
    """Raised when a path, command, or action leaves the declared boundary."""


class ActionExecutionError(RuntimeError):
    """Raised when a local action cannot be safely executed."""


class CrashInjected(RuntimeError):
    """Deterministic fault-injection marker used by local recovery pilots."""


class ActionKind(str, Enum):
    READ_FILE = "READ_FILE"
    LIST_DIR = "LIST_DIR"
    WRITE_FILE = "WRITE_FILE"
    CREATE_FILE = "CREATE_FILE"
    PATCH_TEXT_FILE = "PATCH_TEXT_FILE"
    HASH_FILE = "HASH_FILE"
    RUN_COMMAND = "RUN_COMMAND"
    GIT_STATUS = "GIT_STATUS"
    GIT_DIFF = "GIT_DIFF"


class ApprovalClass(str, Enum):
    AUTO_ALLOWED_SAFE = "AUTO_ALLOWED_SAFE"
    BOUNDED_WRITE_REQUIRES_APPROVAL = "BOUNDED_WRITE_REQUIRES_APPROVAL"
    COMMAND_REQUIRES_APPROVAL = "COMMAND_REQUIRES_APPROVAL"
    DESTRUCTIVE_NOT_AVAILABLE_R1 = "DESTRUCTIVE_NOT_AVAILABLE_R1"


class RollbackClass(str, Enum):
    NONE = "NONE"
    ROLLBACKABLE_LOCAL_FILE = "ROLLBACKABLE_LOCAL_FILE"
    NOT_SUPPORTED_R1 = "NOT_SUPPORTED_R1"


_ACTION_CAPABILITIES = {
    ActionKind.READ_FILE.value: "read.files",
    ActionKind.LIST_DIR.value: "read.directories",
    ActionKind.WRITE_FILE.value: "write.files",
    ActionKind.CREATE_FILE.value: "write.files",
    ActionKind.PATCH_TEXT_FILE.value: "write.files",
    ActionKind.HASH_FILE.value: "read.files",
    ActionKind.RUN_COMMAND.value: "run.commands",
    ActionKind.GIT_STATUS.value: "git.read",
    ActionKind.GIT_DIFF.value: "git.read",
}
_KNOWN_CAPABILITIES = frozenset(_ACTION_CAPABILITIES.values())

_FILE_WRITE_ACTIONS = {
    ActionKind.WRITE_FILE.value,
    ActionKind.CREATE_FILE.value,
    ActionKind.PATCH_TEXT_FILE.value,
}

_SHELL_META = set("|;&<>`\n\r")
_FORBIDDEN_PAYLOAD_KEYS = {"chain_of_thought", "hidden_reasoning", "private_model_reasoning"}


def _normalise_relative(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceViolation(f"{field} must be a non-empty relative path")
    value = value.replace("\\", "/")
    if "\x00" in value or value.startswith("/"):
        raise WorkspaceViolation(f"{field} must be a relative path without NUL")
    parts = [part for part in value.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise WorkspaceViolation(f"{field} contains a parent traversal")
    return "/".join(parts) or "."


def _normalise_root(value: str, field: str) -> str:
    return _normalise_relative(value, field)


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bounded_text(data: bytes, limit: int) -> tuple[str, bool]:
    bounded = data[:limit]
    return bounded.decode("utf-8", errors="replace"), len(data) > limit


def _as_tuple_strings(value: Any, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise KernelValidationError(f"{field} must be an array of strings")
    result = tuple(_string(item, f"{field}[]") for item in value)
    if len(result) != len(set(result)):
        raise KernelValidationError(f"{field} must not contain duplicates")
    return result


@dataclass(frozen=True)
class WorkspacePolicy:
    """The canonical local boundary for one run."""

    workspace_root: str
    allowed_read_roots: tuple[str, ...]
    allowed_write_roots: tuple[str, ...]
    allowed_executables: tuple[str, ...]
    allowed_argv_prefixes: tuple[tuple[str, ...], ...] = ()
    timeout_seconds: float = 10.0
    max_output_bytes: int = 65536
    env_allowlist: tuple[str, ...] = ()
    max_actions: int = 32
    max_writes: int = 16
    network_allowed: bool = False
    max_preimage_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        root = Path(self.workspace_root).expanduser()
        if not root.exists() or not root.is_dir():
            raise WorkspaceViolation(f"workspace_root must be an existing directory: {root}")
        root = root.resolve(strict=True)
        object.__setattr__(self, "workspace_root", str(root))
        object.__setattr__(self, "allowed_read_roots", tuple(_normalise_root(item, "allowed_read_roots[]") for item in self.allowed_read_roots))
        object.__setattr__(self, "allowed_write_roots", tuple(_normalise_root(item, "allowed_write_roots[]") for item in self.allowed_write_roots))
        object.__setattr__(self, "allowed_executables", _as_tuple_strings(self.allowed_executables, "allowed_executables"))
        prefixes: list[tuple[str, ...]] = []
        for prefix in self.allowed_argv_prefixes:
            values = _as_tuple_strings(prefix, "allowed_argv_prefixes[]")
            if not values:
                raise WorkspaceViolation("allowed_argv_prefixes must not contain empty prefixes")
            prefixes.append(values)
        object.__setattr__(self, "allowed_argv_prefixes", tuple(prefixes))
        object.__setattr__(self, "env_allowlist", _as_tuple_strings(self.env_allowlist, "env_allowlist"))
        if not isinstance(self.network_allowed, bool):
            raise WorkspaceViolation("network_allowed must be boolean")
        for name, value in (
            ("timeout_seconds", self.timeout_seconds),
            ("max_output_bytes", self.max_output_bytes),
            ("max_actions", self.max_actions),
            ("max_writes", self.max_writes),
            ("max_preimage_bytes", self.max_preimage_bytes),
        ):
            if not isinstance(value, (int, float)) or value <= 0:
                raise WorkspaceViolation(f"{name} must be positive")
        if self.max_output_bytes != int(self.max_output_bytes):
            raise WorkspaceViolation("max_output_bytes must be an integer")
        if self.max_actions != int(self.max_actions) or self.max_writes != int(self.max_writes) or self.max_preimage_bytes != int(self.max_preimage_bytes):
            raise WorkspaceViolation("action, write, and preimage budgets must be integers")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkspacePolicy":
        required = {
            "workspace_root", "allowed_read_roots", "allowed_write_roots", "allowed_executables",
            "allowed_argv_prefixes", "timeout_seconds", "max_output_bytes", "env_allowlist",
            "max_actions", "max_writes", "network_allowed", "max_preimage_bytes",
        }
        unknown = set(data) - required
        missing = {"workspace_root", "allowed_read_roots", "allowed_write_roots", "allowed_executables"} - set(data)
        if unknown or missing:
            raise KernelValidationError(f"WorkspacePolicy keys invalid; missing={sorted(missing)} unknown={sorted(unknown)}")
        prefixes = tuple(tuple(item) for item in data.get("allowed_argv_prefixes", ()))
        return cls(
            workspace_root=data["workspace_root"],
            allowed_read_roots=tuple(data["allowed_read_roots"]),
            allowed_write_roots=tuple(data["allowed_write_roots"]),
            allowed_executables=tuple(data["allowed_executables"]),
            allowed_argv_prefixes=prefixes,
            timeout_seconds=data.get("timeout_seconds", 10.0),
            max_output_bytes=data.get("max_output_bytes", 65536),
            env_allowlist=tuple(data.get("env_allowlist", ())),
            max_actions=data.get("max_actions", 32),
            max_writes=data.get("max_writes", 16),
            network_allowed=data.get("network_allowed", False),
            max_preimage_bytes=data.get("max_preimage_bytes", 1_048_576),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_root": self.workspace_root,
            "allowed_read_roots": list(self.allowed_read_roots),
            "allowed_write_roots": list(self.allowed_write_roots),
            "allowed_executables": list(self.allowed_executables),
            "allowed_argv_prefixes": [list(item) for item in self.allowed_argv_prefixes],
            "timeout_seconds": self.timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
            "env_allowlist": list(self.env_allowlist),
            "max_actions": self.max_actions,
            "max_writes": self.max_writes,
            "network_allowed": self.network_allowed,
            "max_preimage_bytes": self.max_preimage_bytes,
        }

    def _safe_path(self, relative: str) -> Path:
        relative = _normalise_relative(relative, "path")
        current = Path(self.workspace_root)
        if relative != ".":
            for part in relative.split("/"):
                current = current / part
                if os.path.lexists(current):
                    info = os.lstat(current)
                    if stat.S_ISLNK(info.st_mode):
                        raise WorkspaceViolation(f"symlink path component denied: {relative}")
        real = Path(os.path.realpath(current))
        root = Path(self.workspace_root)
        if not _within(real, root):
            raise WorkspaceViolation(f"path escapes workspace root: {relative}")
        return current

    @staticmethod
    def _matches(relative: str, roots: tuple[str, ...]) -> bool:
        return any(root == "." or relative == root or relative.startswith(root.rstrip("/") + "/") for root in roots)

    def resolve_read(self, relative: str, *, directory: bool | None = None) -> Path:
        relative = _normalise_relative(relative, "read path")
        if not self._matches(relative, self.allowed_read_roots):
            raise WorkspaceViolation(f"read path is outside allowed_read_roots: {relative}")
        path = self._safe_path(relative)
        if not os.path.lexists(path):
            raise WorkspaceViolation(f"read path does not exist: {relative}")
        info = os.lstat(path)
        if directory is True and not stat.S_ISDIR(info.st_mode):
            raise WorkspaceViolation(f"expected a directory: {relative}")
        if directory is False and not stat.S_ISREG(info.st_mode):
            raise WorkspaceViolation(f"expected a regular file: {relative}")
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise WorkspaceViolation(f"special files are denied: {relative}")
        return path

    def resolve_write(self, relative: str) -> Path:
        relative = _normalise_relative(relative, "write path")
        if not self._matches(relative, self.allowed_write_roots):
            raise WorkspaceViolation(f"write path is outside allowed_write_roots: {relative}")
        path = self._safe_path(relative)
        parent = path.parent
        if not _within(Path(os.path.realpath(parent)), Path(self.workspace_root)):
            raise WorkspaceViolation(f"write parent escapes workspace root: {relative}")
        if os.path.lexists(path):
            info = os.lstat(path)
            if not stat.S_ISREG(info.st_mode):
                raise WorkspaceViolation(f"write target is not a regular file: {relative}")
        return path

    def command_argv(self, argv: Sequence[str]) -> tuple[str, ...]:
        if isinstance(argv, str) or not argv:
            raise WorkspaceViolation("commands must be a non-empty argv array")
        values = tuple(_string(item, "argv[]") for item in argv)
        if any(any(char in value for char in _SHELL_META) or "$(" in value for value in values):
            raise WorkspaceViolation("shell metacharacters are denied; provide a literal argv array")
        executable = values[0]
        basename = Path(executable).name
        if not any(fnmatch.fnmatchcase(executable, item) or fnmatch.fnmatchcase(basename, item) for item in self.allowed_executables):
            raise WorkspaceViolation(f"executable is not allowlisted: {executable}")
        if self.allowed_argv_prefixes and not any(
            len(prefix) <= len(values) and all(fnmatch.fnmatchcase(actual, expected) for actual, expected in zip(values, prefix))
            for prefix in self.allowed_argv_prefixes
        ):
            raise WorkspaceViolation("argv does not match an allowed command prefix")
        return values

    def env(self) -> dict[str, str]:
        return {key: os.environ[key] for key in self.env_allowlist if key in os.environ}

    def validate_packet(self, packet: "ExecutionPacket", *, allow_declared_read_missing: bool = False) -> None:
        if packet.kind not in _ACTION_CAPABILITIES:
            raise WorkspaceViolation(f"unknown action type: {packet.kind}")
        unknown_capabilities = sorted(set(packet.required_capabilities) - _KNOWN_CAPABILITIES)
        if unknown_capabilities:
            raise WorkspaceViolation(f"unknown capability: {unknown_capabilities}")
        required = _ACTION_CAPABILITIES[packet.kind]
        if required not in packet.required_capabilities:
            raise WorkspaceViolation(f"action packet omits required capability: {required}")
        if packet.network_requested and not self.network_allowed:
            raise WorkspaceViolation("network is denied by the workspace policy")
        for relative in packet.requested_reads:
            if allow_declared_read_missing and not os.path.lexists(self._safe_path(relative)):
                if not self._matches(_normalise_relative(relative, "read path"), self.allowed_read_roots):
                    raise WorkspaceViolation(f"read path is outside allowed_read_roots: {relative}")
            else:
                self.resolve_read(relative)
        for relative in packet.requested_writes:
            self.resolve_write(relative)
        if packet.kind in _FILE_WRITE_ACTIONS:
            path = packet.payload.get("path")
            if not isinstance(path, str):
                raise WorkspaceViolation("file action payload must declare path")
            self.resolve_write(path)
        if packet.kind in {ActionKind.READ_FILE.value, ActionKind.HASH_FILE.value}:
            path = packet.payload.get("path")
            if not isinstance(path, str):
                raise WorkspaceViolation("read action payload must declare path")
            if allow_declared_read_missing and not os.path.lexists(self._safe_path(path)):
                if not self._matches(_normalise_relative(path, "read path"), self.allowed_read_roots):
                    raise WorkspaceViolation(f"read path is outside allowed_read_roots: {path}")
            else:
                self.resolve_read(path, directory=False)
        if packet.kind == ActionKind.LIST_DIR.value:
            path = packet.payload.get("path", ".")
            self.resolve_read(path, directory=True)
        if packet.kind == ActionKind.RUN_COMMAND.value:
            self.command_argv(packet.argv)
        if packet.kind == ActionKind.GIT_STATUS.value:
            self.command_argv(("git", "status", "--short", "--no-branch"))
        if packet.kind == ActionKind.GIT_DIFF.value:
            self.command_argv(("git", "diff", "--no-ext-diff", "--"))
        if packet.approval_class == ApprovalClass.DESTRUCTIVE_NOT_AVAILABLE_R1.value:
            raise WorkspaceViolation("destructive action class is unavailable in R1")


@dataclass(frozen=True)
class ExecutionPacket:
    """A complete, digestible action packet accepted by the executor."""

    run_id: str
    step_id: str
    action_id: str
    kind: str
    required_capabilities: tuple[str, ...]
    requested_reads: tuple[str, ...]
    requested_writes: tuple[str, ...]
    argv: tuple[str, ...]
    approval_class: str
    expected_side_effects: tuple[str, ...]
    validator_refs: tuple[str, ...]
    timeout_seconds: float
    max_output_bytes: int
    idempotency_key: str
    rollback_class: str
    reason_summary: str
    source_plan_hash: str
    payload: Mapping[str, Any] = None
    network_requested: bool = False

    def __post_init__(self) -> None:
        _id(self.run_id, "run_id")
        _id(self.step_id, "step_id")
        _id(self.action_id, "action_id")
        if self.kind not in {item.value for item in ActionKind}:
            raise KernelValidationError(f"unknown action kind: {self.kind}")
        object.__setattr__(self, "required_capabilities", _as_tuple_strings(self.required_capabilities, "required_capabilities"))
        if not self.required_capabilities:
            raise KernelValidationError("required_capabilities must not be empty")
        object.__setattr__(self, "requested_reads", tuple(_normalise_relative(item, "requested_reads[]") for item in self.requested_reads))
        object.__setattr__(self, "requested_writes", tuple(_normalise_relative(item, "requested_writes[]") for item in self.requested_writes))
        object.__setattr__(self, "argv", _as_tuple_strings(self.argv, "argv"))
        if self.approval_class not in {item.value for item in ApprovalClass}:
            raise KernelValidationError(f"unknown approval_class: {self.approval_class}")
        if self.rollback_class not in {item.value for item in RollbackClass}:
            raise KernelValidationError(f"unknown rollback_class: {self.rollback_class}")
        object.__setattr__(self, "expected_side_effects", _as_tuple_strings(self.expected_side_effects, "expected_side_effects"))
        object.__setattr__(self, "validator_refs", _as_tuple_strings(self.validator_refs, "validator_refs"))
        _summary(self.reason_summary, "reason_summary")
        _id(self.idempotency_key, "idempotency_key")
        if not isinstance(self.source_plan_hash, str) or len(self.source_plan_hash) != 64 or any(c not in "0123456789abcdef" for c in self.source_plan_hash):
            raise KernelValidationError("source_plan_hash must be a lowercase SHA-256 digest")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise KernelValidationError("timeout_seconds must be positive")
        if not isinstance(self.max_output_bytes, int) or self.max_output_bytes <= 0:
            raise KernelValidationError("max_output_bytes must be a positive integer")
        if not isinstance(self.network_requested, bool):
            raise KernelValidationError("network_requested must be boolean")
        if self.payload is None:
            object.__setattr__(self, "payload", {})
        if not isinstance(self.payload, Mapping):
            raise KernelValidationError("payload must be an object")
        bad = {str(key).casefold() for key in self.payload} & _FORBIDDEN_PAYLOAD_KEYS
        if bad:
            raise KernelValidationError("payload cannot persist private reasoning")
        try:
            json.dumps(dict(self.payload), ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise KernelValidationError("payload must be JSON serializable") from exc

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionPacket":
        required = {
            "run_id", "step_id", "action_id", "kind", "required_capabilities", "requested_reads",
            "requested_writes", "argv", "approval_class", "expected_side_effects", "validator_refs",
            "timeout_seconds", "max_output_bytes", "idempotency_key", "rollback_class", "reason_summary",
            "source_plan_hash", "payload", "network_requested",
        }
        if set(data) != required:
            raise KernelValidationError(f"ExecutionPacket keys mismatch: missing={sorted(required-set(data))} unknown={sorted(set(data)-required)}")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "step_id": self.step_id,
            "action_id": self.action_id,
            "kind": self.kind,
            "required_capabilities": list(self.required_capabilities),
            "requested_reads": list(self.requested_reads),
            "requested_writes": list(self.requested_writes),
            "argv": list(self.argv),
            "approval_class": self.approval_class,
            "expected_side_effects": list(self.expected_side_effects),
            "validator_refs": list(self.validator_refs),
            "timeout_seconds": self.timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
            "idempotency_key": self.idempotency_key,
            "rollback_class": self.rollback_class,
            "reason_summary": self.reason_summary,
            "source_plan_hash": self.source_plan_hash,
            "payload": dict(self.payload),
            "network_requested": self.network_requested,
        }

    @property
    def action_digest(self) -> str:
        return sha256_json(self.to_dict())

    @property
    def side_effecting(self) -> bool:
        return self.kind in _FILE_WRITE_ACTIONS or self.kind == ActionKind.RUN_COMMAND.value


@dataclass(frozen=True)
class FilePreimage:
    path: str
    existed: bool
    mode: int | None
    sha256: str | None
    size: int
    content_b64: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "existed": self.existed,
            "mode": self.mode,
            "sha256": self.sha256,
            "size": self.size,
            "content_b64": self.content_b64,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FilePreimage":
        return cls(**data)


@dataclass(frozen=True)
class FilePostimage:
    path: str
    existed: bool
    mode: int | None
    sha256: str | None
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "existed": self.existed,
            "mode": self.mode,
            "sha256": self.sha256,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FilePostimage":
        return cls(**data)


@dataclass(frozen=True)
class ActionExecutionResult:
    packet: ExecutionPacket
    executor_class_id: str
    executor_instance_id: str
    status: str
    changed_paths: tuple[str, ...]
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    return_code: int | None
    duration_ms: int
    argv_digest: str
    cwd: str
    preimages: tuple[FilePreimage, ...]
    postimages: tuple[FilePostimage, ...]
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.packet.action_id,
            "run_id": self.packet.run_id,
            "step_id": self.packet.step_id,
            "kind": self.packet.kind,
            "packet_digest": self.packet.action_digest,
            "idempotency_key": self.packet.idempotency_key,
            "executor_class_id": self.executor_class_id,
            "executor_instance_id": self.executor_instance_id,
            "status": self.status,
            "changed_paths": list(self.changed_paths),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "stdout_truncated": self.stdout_truncated,
            "stderr_truncated": self.stderr_truncated,
            "return_code": self.return_code,
            "duration_ms": self.duration_ms,
            "argv_digest": self.argv_digest,
            "cwd": self.cwd,
            "preimages": [item.to_dict() for item in self.preimages],
            "postimages": [item.to_dict() for item in self.postimages],
            "error_code": self.error_code,
        }


class LocalWorkspaceExecutor:
    """A bounded local executor with no shell and no remote mutation."""

    def __init__(
        self,
        policy: WorkspacePolicy,
        *,
        executor_class_id: str = "local-workspace-executor",
        executor_instance_id: str = "instance-1",
        fault_injection: str | None = None,
    ) -> None:
        _id(executor_class_id, "executor_class_id")
        _id(executor_instance_id, "executor_instance_id")
        self.policy = policy
        self.executor_class_id = executor_class_id
        self.executor_instance_id = executor_instance_id
        self.executor_id = f"{executor_class_id}-{executor_instance_id}"
        self.fault_injection = fault_injection

    def _snapshot(self, relative: str, *, allow_missing: bool = True) -> FilePostimage:
        path = self.policy._safe_path(relative)
        if not os.path.lexists(path):
            if allow_missing:
                return FilePostimage(relative, False, None, None, 0)
            raise ActionExecutionError(f"snapshot target does not exist: {relative}")
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise WorkspaceViolation(f"snapshot target must be a regular non-symlink file: {relative}")
        data = path.read_bytes()
        return FilePostimage(relative, True, stat.S_IMODE(info.st_mode), _sha256_bytes(data), len(data))

    def prepare(self, packet: ExecutionPacket) -> tuple[FilePreimage, ...]:
        self.policy.validate_packet(packet)
        if packet.rollback_class != RollbackClass.ROLLBACKABLE_LOCAL_FILE.value or packet.kind not in _FILE_WRITE_ACTIONS:
            return ()
        path = str(packet.payload.get("path", ""))
        target = self.policy.resolve_write(path)
        if not os.path.lexists(target):
            return (FilePreimage(path, False, None, None, 0, None),)
        info = os.lstat(target)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise WorkspaceViolation(f"preimage target must be a regular non-symlink file: {path}")
        data = target.read_bytes()
        if len(data) > self.policy.max_preimage_bytes:
            raise ActionExecutionError("PREIMAGE_TOO_LARGE: bounded rollback snapshot refused")
        return (
            FilePreimage(
                path=path,
                existed=True,
                mode=stat.S_IMODE(info.st_mode),
                sha256=_sha256_bytes(data),
                size=len(data),
                content_b64=base64.b64encode(data).decode("ascii"),
            ),
        )

    def expected_postimages(self, packet: ExecutionPacket, preimages: Sequence[FilePreimage]) -> tuple[FilePostimage, ...]:
        """Derive a bounded file postcondition before a write starts."""

        if packet.kind not in _FILE_WRITE_ACTIONS:
            return ()
        path = str(packet.payload["path"])
        preimage = next((item for item in preimages if item.path == path), None)
        existing: bytes | None = None
        mode = 0o644
        if preimage is not None and preimage.existed:
            if preimage.content_b64 is None:
                raise ActionExecutionError("preimage bytes missing for expected postimage")
            existing = base64.b64decode(preimage.content_b64, validate=True)
            mode = preimage.mode or mode
        elif packet.kind == ActionKind.PATCH_TEXT_FILE.value:
            raise ActionExecutionError("PATCH_TEXT_FILE requires an existing preimage")
        data = self._content_bytes(packet.payload, existing=existing)
        return (FilePostimage(path, True, mode, _sha256_bytes(data), len(data)),)

    def execute(self, packet: ExecutionPacket, preimages: Sequence[FilePreimage] = ()) -> ActionExecutionResult:
        self.policy.validate_packet(packet)
        started = time.monotonic()
        stdout = b""
        stderr = b""
        return_code: int | None = None
        status = "EXECUTED"
        error_code: str | None = None
        changed: tuple[str, ...] = ()
        argv: tuple[str, ...] = packet.argv
        try:
            if self.fault_injection == "pre_execute":
                raise CrashInjected("fault injection: pre_execute")
            if packet.kind == ActionKind.READ_FILE.value:
                path = str(packet.payload["path"])
                data = self.policy.resolve_read(path, directory=False).read_bytes()
                stdout = data
            elif packet.kind == ActionKind.HASH_FILE.value:
                path = str(packet.payload["path"])
                data = self.policy.resolve_read(path, directory=False).read_bytes()
                stdout = (_sha256_bytes(data) + "\n").encode()
            elif packet.kind == ActionKind.LIST_DIR.value:
                path = str(packet.payload.get("path", "."))
                directory = self.policy.resolve_read(path, directory=True)
                stdout = ("\n".join(sorted(item.name for item in directory.iterdir())) + "\n").encode()
            elif packet.kind in _FILE_WRITE_ACTIONS:
                path = str(packet.payload["path"])
                target = self.policy.resolve_write(path)
                if packet.kind == ActionKind.CREATE_FILE.value and target.exists():
                    desired = self._content_bytes(packet.payload)
                    existing = target.read_bytes()
                    if existing == desired:
                        status = "IDEMPOTENT_REPLAY"
                    else:
                        raise ActionExecutionError("CREATE_FILE target already exists with different content")
                else:
                    data = self._content_bytes(packet.payload, existing=target.read_bytes() if target.exists() else None)
                    mode = stat.S_IMODE(os.lstat(target).st_mode) if os.path.lexists(target) else 0o644
                    self._atomic_write(target, data, self.fault_injection == "mid_write", mode=mode)
                    changed = (path,)
                    stdout = (_sha256_bytes(data) + "\n").encode()
            else:
                if packet.kind == ActionKind.GIT_STATUS.value:
                    argv = ("git", "status", "--short", "--no-branch")
                elif packet.kind == ActionKind.GIT_DIFF.value:
                    argv = ("git", "diff", "--no-ext-diff", "--")
                argv = self.policy.command_argv(argv)
                process = subprocess.Popen(
                    list(argv),
                    cwd=self.policy.workspace_root,
                    env=self.policy.env(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    close_fds=True,
                )
                try:
                    stdout, stderr = process.communicate(timeout=min(packet.timeout_seconds, self.policy.timeout_seconds))
                    return_code = process.returncode
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    status = "TIMEOUT"
                    error_code = "COMMAND_TIMEOUT"
        except CrashInjected:
            raise
        except (OSError, WorkspaceViolation, ActionExecutionError) as exc:
            status = "FAILED_EXECUTION"
            error_code = type(exc).__name__.upper()
            stderr = str(exc).encode("utf-8", errors="replace")
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout_text, stdout_truncated = _bounded_text(stdout, min(packet.max_output_bytes, self.policy.max_output_bytes))
        stderr_text, stderr_truncated = _bounded_text(stderr, min(packet.max_output_bytes, self.policy.max_output_bytes))
        postimages = tuple(self._snapshot(item) for item in packet.requested_writes) if packet.requested_writes else ()
        if packet.kind in _FILE_WRITE_ACTIONS and packet.payload.get("path") not in packet.requested_writes:
            postimages = postimages + (self._snapshot(str(packet.payload["path"])),)
        return ActionExecutionResult(
            packet=packet,
            executor_class_id=self.executor_class_id,
            executor_instance_id=self.executor_instance_id,
            status=status,
            changed_paths=changed,
            stdout=stdout_text,
            stderr=stderr_text,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
            return_code=return_code,
            duration_ms=duration_ms,
            argv_digest=sha256_json(list(argv)),
            cwd=".",
            preimages=tuple(preimages),
            postimages=postimages,
            error_code=error_code,
        )

    @staticmethod
    def _content_bytes(payload: Mapping[str, Any], *, existing: bytes | None = None) -> bytes:
        if "content_b64" in payload:
            try:
                return base64.b64decode(str(payload["content_b64"]), validate=True)
            except Exception as exc:
                raise ActionExecutionError("content_b64 is invalid") from exc
        if "content" in payload:
            return str(payload["content"]).encode("utf-8")
        if "find" in payload and "replace" in payload:
            if existing is None:
                raise ActionExecutionError("PATCH_TEXT_FILE target does not exist")
            try:
                text = existing.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ActionExecutionError("PATCH_TEXT_FILE target is not UTF-8") from exc
            expected = payload.get("expected_sha256")
            if expected is not None and _sha256_bytes(existing) != expected:
                raise ActionExecutionError("PATCH_TEXT_FILE precondition hash mismatch")
            find = str(payload["find"])
            if find not in text:
                raise ActionExecutionError("PATCH_TEXT_FILE search text was not found")
            return text.replace(find, str(payload["replace"]), 1).encode("utf-8")
        raise ActionExecutionError("file action payload lacks content or patch specification")

    @staticmethod
    def _atomic_write(target: Path, data: bytes, inject_mid_write: bool = False, *, mode: int = 0o644) -> None:
        target.parent.mkdir(parents=False, exist_ok=True)
        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.r1-", delete=False) as handle:
                temp_name = handle.name
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                os.chmod(handle.name, mode, follow_symlinks=False)
            if inject_mid_write:
                raise CrashInjected("fault injection: mid_write")
            os.replace(temp_name, target)
            temp_name = None
        finally:
            if temp_name is not None:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass

    def rollback(self, preimages: Sequence[FilePreimage]) -> dict[str, Any]:
        restored: list[str] = []
        try:
            for preimage in reversed(tuple(preimages)):
                target = self.policy.resolve_write(preimage.path)
                if preimage.existed:
                    if preimage.content_b64 is None:
                        raise ActionExecutionError(f"preimage bytes missing for {preimage.path}")
                    data = base64.b64decode(preimage.content_b64, validate=True)
                    self._atomic_write(target, data)
                    if preimage.mode is not None:
                        os.chmod(target, preimage.mode, follow_symlinks=False)
                else:
                    if os.path.lexists(target):
                        info = os.lstat(target)
                        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                            raise WorkspaceViolation(f"rollback target is not a regular file: {preimage.path}")
                        target.unlink()
                current = self._snapshot(preimage.path)
                if current.existed != preimage.existed or current.sha256 != preimage.sha256 or current.mode != preimage.mode:
                    raise ActionExecutionError(f"rollback verification mismatch: {preimage.path}")
                restored.append(preimage.path)
            return {"status": "RESTORED", "paths": restored, "error": None}
        except Exception as exc:
            return {"status": "ROLLBACK_FAILED", "paths": restored, "error": str(exc)}

    def postimages_match(self, postimages: Sequence[Mapping[str, Any]]) -> bool:
        for item in postimages:
            expected = FilePostimage.from_dict(item) if not isinstance(item, FilePostimage) else item
            current = self._snapshot(expected.path)
            if current.to_dict() != expected.to_dict():
                return False
        return True

    def preimages_match(self, preimages: Sequence[Mapping[str, Any]]) -> bool:
        for item in preimages:
            expected = FilePreimage.from_dict(item) if not isinstance(item, FilePreimage) else item
            current = self._snapshot(expected.path)
            current_dict = {
                "path": current.path,
                "existed": current.existed,
                "mode": current.mode,
                "sha256": current.sha256,
                "size": current.size,
            }
            if any(current_dict[key] != expected.to_dict()[key] for key in ("path", "existed", "mode", "sha256", "size")):
                return False
        return True
