"""Bounded public-process transport for the live executor bridge.

The transport is intentionally lower-level than an agent runtime: it starts
one allowlisted process, supplies one bounded input, captures public output,
and tears down the process group on timeout or output overflow.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import shutil
import stat
import subprocess
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence

from .contracts import FederationContractError


class LiveTransportError(FederationContractError):
    """Raised when a public process boundary is invalid before execution."""


RUNTIME_SCRATCH_CLEANED = "CLEANED"
RUNTIME_SCRATCH_FAILED = "FAILED"
RUNTIME_SCRATCH_RECONCILIATION = "REQUIRES_RECONCILIATION"


def _runtime_metadata_digest(root: Path) -> str:
    """Digest names/types/modes/sizes only; never read runtime file contents."""

    digest = hashlib.sha256()
    if not root.exists():
        return digest.hexdigest()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        try:
            info = path.lstat()
        except OSError as exc:
            raise LiveTransportError("runtime scratch metadata cannot be inspected") from exc
        record = f"{relative}\0{stat_type(info.st_mode)}\0{info.st_mode & 0o7777:o}\0{info.st_size}\n"
        digest.update(record.encode("utf-8"))
    return digest.hexdigest()


def auth_source_metadata_digest(root: Path) -> str:
    """Digest auth-source metadata only; never read credential contents."""

    digest = hashlib.sha256()
    if not root.exists() or root.is_symlink():
        return digest.hexdigest()
    entries = (root,) if root.is_file() else (root, *root.rglob("*"))
    for path in sorted(entries, key=lambda item: item.relative_to(root.parent).as_posix()):
        try:
            info = path.lstat()
        except OSError as exc:
            raise LiveTransportError("auth source metadata cannot be inspected") from exc
        relative = path.relative_to(root.parent).as_posix()
        record = f"{relative}\0{stat_type(info.st_mode)}\0{info.st_mode & 0o7777:o}\0{info.st_size}\0{info.st_mtime_ns}\n"
        digest.update(record.encode("utf-8"))
    return digest.hexdigest()


def stat_type(mode: int) -> str:
    if stat.S_ISDIR(mode):
        return "dir"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "other"


def _path_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _tree_has_write_bits(root: Path) -> bool:
    entries = (root, *root.rglob("*"))
    return any(item.lstat().st_mode & 0o222 for item in entries)


def _tree_has_symlink(root: Path) -> bool:
    return any(item.is_symlink() for item in (root, *root.rglob("*")))


def _make_tree_writable(root: Path) -> None:
    for item in sorted(root.rglob("*"), key=lambda value: len(value.parts), reverse=True):
        try:
            item.chmod(0o700 if item.is_dir() else 0o600)
        except OSError:
            pass
    try:
        root.chmod(0o700)
    except OSError:
        pass


@dataclass
class RuntimeScratchLease:
    """Attempt-specific empty scratch root with fail-closed cleanup semantics."""

    path: Path
    attempt_id: str
    owner: str
    ttl_seconds: float
    protected_roots: tuple[Path, ...]
    before_digest: str
    cleanup_status: str | None = None

    @classmethod
    def create(
        cls,
        *,
        attempt_id: str,
        parent: str | Path | None = None,
        protected_roots: Sequence[str | Path] = (),
        ttl_seconds: float = 900.0,
    ) -> "RuntimeScratchLease":
        if not isinstance(attempt_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", attempt_id):
            raise LiveTransportError("runtime scratch attempt_id must be a safe non-empty token")
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, (int, float)) or not 0 < ttl_seconds <= 3600:
            raise LiveTransportError("runtime scratch ttl_seconds must be in (0, 3600]")
        parent_path = Path(parent or tempfile.gettempdir())
        if not parent_path.is_absolute() or not parent_path.is_dir():
            raise LiveTransportError("runtime scratch parent must be an existing absolute directory")
        parent_resolved = parent_path.resolve(strict=True)
        protected = tuple(Path(value).resolve(strict=True) for value in protected_roots)
        if any(parent_resolved == root or root in parent_resolved.parents for root in protected):
            raise LiveTransportError("runtime scratch parent overlaps a protected root")
        root = Path(tempfile.mkdtemp(prefix=f"pointfire-live-{attempt_id}-", dir=str(parent_resolved)))
        root.chmod(0o700)
        if any(_path_overlap(root.resolve(strict=True), protected_root) for protected_root in protected):
            _make_tree_writable(root)
            shutil.rmtree(root)
            raise LiveTransportError("runtime scratch overlaps a protected root")
        return cls(
            path=root,
            attempt_id=attempt_id,
            owner=f"uid:{os.getuid()}",
            ttl_seconds=float(ttl_seconds),
            protected_roots=protected,
            before_digest=_runtime_metadata_digest(root),
        )

    @classmethod
    def from_existing(
        cls,
        path: str | Path,
        *,
        attempt_id: str,
        protected_roots: Sequence[str | Path] = (),
        ttl_seconds: float = 900.0,
    ) -> "RuntimeScratchLease":
        root = Path(path)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise LiveTransportError("runtime scratch must be an existing non-symlink absolute directory")
        resolved = root.resolve(strict=True)
        protected = tuple(Path(value).resolve(strict=True) for value in protected_roots)
        if any(_path_overlap(resolved, item) for item in protected):
            raise LiveTransportError("runtime scratch overlaps a protected root")
        if any(root.iterdir()):
            raise LiveTransportError("runtime scratch must be an empty attempt-specific directory")
        return cls(
            path=resolved,
            attempt_id=attempt_id,
            owner=f"uid:{os.getuid()}",
            ttl_seconds=float(ttl_seconds),
            protected_roots=protected,
            before_digest=_runtime_metadata_digest(resolved),
        )

    def environment_overrides(self, keys: Sequence[str] = ("HOME", "TMPDIR")) -> dict[str, str]:
        targets = {
            "HOME": self.path,
            "TMPDIR": self.path,
            "CODEX_HOME": self.path / ".codex",
            "XDG_CACHE_HOME": self.path / ".cache",
            "XDG_CONFIG_HOME": self.path / ".config",
            "XDG_RUNTIME_DIR": self.path / ".runtime",
        }
        result: dict[str, str] = {}
        for key in keys:
            if key not in targets:
                raise LiveTransportError(f"runtime environment key is not supported: {key}")
            result[key] = str(targets[key])
        return result

    def prepare_runtime_paths(self, keys: Sequence[str]) -> None:
        """Create only declared runtime directories inside the validated lease."""

        targets = {
            "CODEX_HOME": self.path / ".codex",
            "XDG_CACHE_HOME": self.path / ".cache",
            "XDG_CONFIG_HOME": self.path / ".config",
            "XDG_RUNTIME_DIR": self.path / ".runtime",
        }
        for key in keys:
            if key in {"HOME", "TMPDIR"}:
                continue
            if key not in targets:
                raise LiveTransportError(f"runtime environment key is not preparable: {key}")
            target = targets[key]
            if target.exists() and (target.is_symlink() or not target.is_dir()):
                raise LiveTransportError(f"runtime environment directory is not a safe directory: {key}")
            target.mkdir(mode=0o700, exist_ok=True)
            if target.is_symlink() or not target.is_dir():
                raise LiveTransportError(f"runtime environment directory escaped scratch: {key}")
            target.chmod(0o700)

    def validate(self) -> None:
        if self.path.is_symlink() or not self.path.is_dir():
            raise LiveTransportError("runtime scratch path is missing or symlinked")
        if _tree_has_symlink(self.path):
            raise LiveTransportError("runtime scratch contains a symlink/path escape")
        resolved = self.path.resolve(strict=True)
        if any(_path_overlap(resolved, root) for root in self.protected_roots):
            raise LiveTransportError("runtime scratch contains a protected root")
        if any(self.path.iterdir()):
            raise LiveTransportError("runtime scratch is not empty at dispatch start")
        if not _tree_has_write_bits(self.path):
            raise LiveTransportError("runtime scratch is not writable")
        if self.path.stat().st_uid != os.getuid():
            raise LiveTransportError("runtime scratch is not owned by the current executor user")

    def cleanup(self) -> str:
        if self.cleanup_status is not None:
            return self.cleanup_status
        try:
            if self.path.is_symlink() or (self.path.exists() and _tree_has_symlink(self.path)):
                self.cleanup_status = RUNTIME_SCRATCH_FAILED
            elif self.path.exists():
                _make_tree_writable(self.path)
                shutil.rmtree(self.path)
                self.cleanup_status = RUNTIME_SCRATCH_CLEANED if not self.path.exists() else RUNTIME_SCRATCH_FAILED
            else:
                self.cleanup_status = RUNTIME_SCRATCH_CLEANED
        except OSError:
            self.cleanup_status = RUNTIME_SCRATCH_FAILED
        return self.cleanup_status

    def finalize(self, process_group_status: str) -> str:
        if process_group_status in {"CHILD_LEFT_BEHIND", "UNKNOWN"}:
            self.cleanup_status = RUNTIME_SCRATCH_RECONCILIATION
            return self.cleanup_status
        return self.cleanup()

    def public_receipt(self, *, after_digest: str, cleanup_status: str) -> dict[str, Any]:
        return {
            "schema_version": "runtime-scratch-receipt-r1",
            "runtime_scratch_ref": "ATTEMPT_RUNTIME_SCRATCH",
            "attempt_id": self.attempt_id,
            "mode": "ATTEMPT_EPHEMERAL_WRITABLE",
            "owner": self.owner,
            "ttl_seconds": self.ttl_seconds,
            "cleanup_policy": "CLEANUP_FINALLY_FAIL_CLOSED",
            "digest_before": self.before_digest,
            "digest_after": after_digest,
            "cleanup_status": cleanup_status,
            "content_persisted": False,
        }


@dataclass(frozen=True)
class LiveProcessResult:
    argv: tuple[str, ...]
    cwd: str
    returncode: int | None
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool
    output_truncated: bool
    process_group_cleaned: bool
    started_at: str = ""
    ended_at: str = ""
    timeout_seconds: float = 0.0
    timeout_requested: bool = False
    termination_requested: bool = False
    signals_sent: tuple[str, ...] = ()
    process_group_status: str = "UNKNOWN"
    first_public_event_latency_ms: float | None = None
    monotonic_elapsed_ms: float | None = None
    stdout_bytes: int | None = None
    stderr_bytes: int | None = None
    stdout_digest: str | None = None
    stderr_digest: str | None = None
    wall_clock_order: str = "UNOBSERVED"
    runtime_scratch_receipt: Mapping[str, Any] | None = None
    runtime_scratch_cleanup_status: str = "NOT_USED"


def interface_digest(public_help: str) -> str:
    if not isinstance(public_help, str):
        raise LiveTransportError("public interface text must be a string")
    return hashlib.sha256(public_help.encode("utf-8")).hexdigest()


def _validate_argv(argv: Sequence[str], executable_allowlist: Sequence[str]) -> tuple[str, ...]:
    if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(item, str) or not item for item in argv):
        raise LiveTransportError("live argv must be a non-empty sequence of non-empty strings")
    if any(item in {"|", ";", "&&", "||", ">", ">>", "<", "`"} for item in argv):
        raise LiveTransportError("shell syntax is not a literal argv value")
    if not isinstance(executable_allowlist, (list, tuple)) or not executable_allowlist:
        raise LiveTransportError("live process requires a non-empty executable allowlist")
    allowed = {str(item) for item in executable_allowlist}
    if argv[0] not in allowed and Path(argv[0]).name not in {Path(item).name for item in allowed}:
        raise LiveTransportError("executable is outside the live adapter allowlist")
    return tuple(argv)


def _sanitized_env(env_allowlist: Sequence[str], env_overrides: Mapping[str, str] | None) -> dict[str, str]:
    if not isinstance(env_allowlist, (list, tuple)) or any(not isinstance(key, str) or not key for key in env_allowlist):
        raise LiveTransportError("env_allowlist must contain non-empty names")
    allowed = set(env_allowlist)
    if any(any(marker in key.casefold() for marker in ("secret", "token", "api_key", "password", "cookie")) for key in allowed):
        raise LiveTransportError("secret-like environment names are not permitted in the live allowlist")
    result = {key: os.environ[key] for key in sorted(allowed) if key in os.environ}
    if env_overrides is not None:
        if not isinstance(env_overrides, Mapping):
            raise LiveTransportError("env_overrides must be an object")
        for key, value in env_overrides.items():
            if key not in allowed:
                raise LiveTransportError(f"environment override is outside the allowlist: {key}")
            if not isinstance(value, str):
                raise LiveTransportError(f"environment override must be text: {key}")
            result[key] = value
    return result


def _group_exists(pid: int) -> bool | None:
    """Return group existence, or None when the OS cannot prove it."""

    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return None
    return True


def _terminate_group(
    process: subprocess.Popen[bytes],
    *,
    grace_seconds: float = 0.5,
    descendant_streams_open: bool = False,
) -> tuple[str, tuple[str, ...]]:
    """Terminate the process group and report signals plus proof status.

    A returned ``CONFIRMED_GONE`` only describes the original process group.
    If the leader already exited while inherited pipes remain open, the
    transport cannot prove that a child did not escape that group and reports
    ``CHILD_LEFT_BEHIND`` instead.
    """

    signals_sent: list[str] = []
    initial = _group_exists(process.pid)
    if initial is False:
        if process.poll() is not None and descendant_streams_open:
            return "CHILD_LEFT_BEHIND", tuple(signals_sent)
        return "CONFIRMED_GONE", tuple(signals_sent)
    try:
        os.killpg(process.pid, signal.SIGTERM)
        signals_sent.append("SIGTERM")
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            signals_sent.append("SIGKILL")
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
    final = _group_exists(process.pid)
    if final is False:
        return "CONFIRMED_GONE", tuple(signals_sent)
    if final is None:
        return "UNKNOWN", tuple(signals_sent)
    return "UNKNOWN", tuple(signals_sent)


def _wall_clock_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _wall_clock_order(started_at: str, ended_at: str) -> str:
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at)
    except ValueError:
        return "UNPARSEABLE"
    return "ORDERED" if end >= start else "DRIFTED"


class LiveProcessTransport:
    """Run exactly one bounded public process with an explicit cwd and env."""

    supports_runtime_scratch = True

    def __init__(
        self,
        *,
        executable_allowlist: Sequence[str],
        env_allowlist: Sequence[str] = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "CODEX_HOME", "HERMES_HOME"),
        output_cap_bytes: int = 128 * 1024,
        input_cap_bytes: int = 32 * 1024,
        wall_clock: Callable[[], str] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(output_cap_bytes, int) or isinstance(output_cap_bytes, bool) or output_cap_bytes <= 0:
            raise LiveTransportError("output_cap_bytes must be positive")
        if not isinstance(input_cap_bytes, int) or isinstance(input_cap_bytes, bool) or input_cap_bytes <= 0:
            raise LiveTransportError("input_cap_bytes must be positive")
        self.executable_allowlist = tuple(executable_allowlist)
        self.env_allowlist = tuple(env_allowlist)
        self.output_cap_bytes = output_cap_bytes
        self.input_cap_bytes = input_cap_bytes
        self._wall_clock = wall_clock or _wall_clock_iso
        self._monotonic = monotonic_clock or time.monotonic

    def _run_process(
        self,
        argv: Sequence[str],
        *,
        cwd: str | Path,
        timeout_seconds: float,
        input_text: str | None = None,
        env_overrides: Mapping[str, str] | None = None,
    ) -> LiveProcessResult:
        argv_tuple = _validate_argv(argv, self.executable_allowlist)
        root = Path(cwd)
        if not root.is_absolute() or not root.is_dir():
            raise LiveTransportError("live process cwd must be an existing absolute directory")
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise LiveTransportError("timeout_seconds must be positive")
        if input_text is not None:
            if not isinstance(input_text, str):
                raise LiveTransportError("input_text must be text or null")
            if len(input_text.encode("utf-8")) > self.input_cap_bytes:
                raise LiveTransportError("input_text exceeds the live input cap")
        environment = _sanitized_env(self.env_allowlist, env_overrides)
        started_at = self._wall_clock()
        start = self._monotonic()
        process = subprocess.Popen(
            list(argv_tuple),
            cwd=str(root),
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
        )
        if process.stdin is not None:
            try:
                if input_text is not None:
                    process.stdin.write(input_text.encode("utf-8"))
                process.stdin.close()
            except (BrokenPipeError, OSError):
                pass

        selector = selectors.DefaultSelector()
        assert process.stdout is not None and process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        buffers: dict[str, bytearray] = {"stdout": bytearray(), "stderr": bytearray()}
        digests = {"stdout": hashlib.sha256(), "stderr": hashlib.sha256()}
        byte_counts = {"stdout": 0, "stderr": 0}
        first_public_event_latency_ms: float | None = None
        timed_out = False
        output_truncated = False
        cleaned = False
        signals_sent: tuple[str, ...] = ()
        process_group_status = "UNKNOWN"
        deadline = start + float(timeout_seconds)
        while selector.get_map():
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                timed_out = True
                process_group_status, signals_sent = _terminate_group(
                    process, descendant_streams_open=bool(selector.get_map()) and process.poll() is not None,
                )
                cleaned = process_group_status == "CONFIRMED_GONE"
                break
            for key, _ in selector.select(timeout=min(remaining, 0.05)):
                stream = key.fileobj
                try:
                    chunk = os.read(stream.fileno(), 64 * 1024)
                except OSError:
                    chunk = b""
                if not chunk:
                    selector.unregister(stream)
                    stream.close()
                    continue
                if first_public_event_latency_ms is None:
                    first_public_event_latency_ms = round((self._monotonic() - start) * 1000, 3)
                target = buffers[key.data]
                digests[key.data].update(chunk)
                byte_counts[key.data] += len(chunk)
                target.extend(chunk)
                if len(target) > self.output_cap_bytes:
                    output_truncated = True
                    process_group_status, signals_sent = _terminate_group(
                        process, descendant_streams_open=bool(selector.get_map()) and process.poll() is not None,
                    )
                    cleaned = process_group_status == "CONFIRMED_GONE"
                    selector.unregister(stream)
                    stream.close()
                    break
            if output_truncated:
                break
            if process.poll() is not None and not selector.get_map():
                break
        selector.close()
        for stream in (process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
        if timed_out or output_truncated:
            if process.poll() is None:
                process_group_status, signals_sent = _terminate_group(process)
                cleaned = process_group_status == "CONFIRMED_GONE"
        try:
            returncode = process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            process_group_status, signals_sent = _terminate_group(process) 
            cleaned = process_group_status == "CONFIRMED_GONE"
            returncode = process.poll()
        ended_at = self._wall_clock()
        duration_ms = round((self._monotonic() - start) * 1000, 3)
        if not timed_out and not output_truncated:
            group_exists = _group_exists(process.pid)
            if group_exists is False:
                process_group_status = "CONFIRMED_GONE"
                cleaned = True
            elif group_exists is None:
                process_group_status = "UNKNOWN"
                cleaned = False
            elif process.poll() is not None:
                process_group_status = "CHILD_LEFT_BEHIND"
                cleaned = False
        if process_group_status == "UNKNOWN" and cleaned:
            cleaned = False
        stdout = bytes(buffers["stdout"][: self.output_cap_bytes]).decode("utf-8", errors="replace")
        stderr = bytes(buffers["stderr"][: self.output_cap_bytes]).decode("utf-8", errors="replace")
        return LiveProcessResult(
            argv_tuple, str(root), returncode, stdout, stderr, duration_ms, timed_out, output_truncated, cleaned,
            started_at=started_at, ended_at=ended_at, timeout_seconds=float(timeout_seconds),
            timeout_requested=timed_out, termination_requested=timed_out or output_truncated,
            signals_sent=signals_sent, process_group_status=process_group_status,
            first_public_event_latency_ms=first_public_event_latency_ms, monotonic_elapsed_ms=duration_ms,
            stdout_bytes=byte_counts["stdout"], stderr_bytes=byte_counts["stderr"],
            stdout_digest=digests["stdout"].hexdigest(), stderr_digest=digests["stderr"].hexdigest(),
            wall_clock_order=_wall_clock_order(started_at, ended_at),
        )

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: str | Path,
        timeout_seconds: float,
        input_text: str | None = None,
        env_overrides: Mapping[str, str] | None = None,
        runtime_scratch: RuntimeScratchLease | None = None,
        runtime_env_keys: Sequence[str] = ("HOME", "TMPDIR"),
    ) -> LiveProcessResult:
        """Run one process and, when supplied, close one scratch lease."""

        if runtime_scratch is None:
            return self._run_process(
                argv, cwd=cwd, timeout_seconds=timeout_seconds, input_text=input_text, env_overrides=env_overrides,
            )
        if not isinstance(runtime_scratch, RuntimeScratchLease):
            raise LiveTransportError("runtime_scratch must be a RuntimeScratchLease")
        try:
            runtime_scratch.validate()
            keys = tuple(runtime_env_keys)
            if any(key not in self.env_allowlist for key in keys):
                raise LiveTransportError("runtime environment key is outside the transport allowlist")
            if env_overrides is None:
                raise LiveTransportError("runtime scratch requires explicit attempt environment overrides")
            scratch_root = runtime_scratch.path.resolve(strict=True)
            for key in keys:
                value = env_overrides.get(key)
                if not isinstance(value, str) or not value:
                    raise LiveTransportError(f"runtime environment override is missing: {key}")
                candidate = Path(value)
                if candidate.is_symlink() or not candidate.absolute().resolve(strict=False).is_relative_to(scratch_root):
                    raise LiveTransportError(f"runtime environment path escapes scratch: {key}")
            runtime_scratch.prepare_runtime_paths(keys)
        except Exception as exc:
            cleanup_status = runtime_scratch.cleanup()
            if cleanup_status == RUNTIME_SCRATCH_FAILED:
                raise LiveTransportError("runtime scratch cleanup failed during preflight") from exc
            raise
        try:
            result = self._run_process(
                argv, cwd=cwd, timeout_seconds=timeout_seconds, input_text=input_text, env_overrides=env_overrides,
            )
        except Exception:
            cleanup_status = runtime_scratch.cleanup()
            if cleanup_status == RUNTIME_SCRATCH_FAILED:
                raise LiveTransportError("runtime scratch cleanup failed after process startup error")
            raise
        after_digest = _runtime_metadata_digest(runtime_scratch.path)
        cleanup_status = runtime_scratch.finalize(result.process_group_status)
        receipt = runtime_scratch.public_receipt(after_digest=after_digest, cleanup_status=cleanup_status)
        return replace(
            result,
            runtime_scratch_receipt=receipt,
            runtime_scratch_cleanup_status=cleanup_status,
        )


def parse_bounded_jsonl(text: str, *, max_events: int = 256, max_line_bytes: int = 64 * 1024) -> tuple[dict[str, Any], ...]:
    if not isinstance(text, str) or not text.strip():
        raise LiveTransportError("public JSONL output is empty")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > max_line_bytes:
            raise LiveTransportError(f"JSONL line {line_number} exceeds the public line cap")
        if len(events) >= max_events:
            raise LiveTransportError("JSONL event count exceeds the public cap")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LiveTransportError(f"JSONL line {line_number} is malformed") from exc
        if not isinstance(value, dict):
            raise LiveTransportError(f"JSONL line {line_number} is not an object")
        events.append(value)
    if not events:
        raise LiveTransportError("public JSONL output contains no events")
    return tuple(events)


__all__ = [
    "LiveProcessResult", "LiveProcessTransport", "LiveTransportError", "RuntimeScratchLease",
    "RUNTIME_SCRATCH_CLEANED", "RUNTIME_SCRATCH_FAILED", "RUNTIME_SCRATCH_RECONCILIATION",
    "auth_source_metadata_digest", "interface_digest", "parse_bounded_jsonl",
]
