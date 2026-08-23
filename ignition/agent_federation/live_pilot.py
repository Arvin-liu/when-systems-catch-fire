"""Disposable synthetic fixture and independent live-success validator."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import tempfile
from typing import Any, Mapping

from agent_kernel.contracts import _id, sha256_json

from .live_privacy import LivePrivacyError, sanitize_live_result


LIVE_PILOT_SCHEMA = "ignition-136-live-pilot-r1"
_NONCE = re.compile(r"^[a-f0-9]{24}$")


class LivePilotError(ValueError):
    """Raised when the disposable fixture cannot be safely constructed."""


def tree_digest(root: str | Path) -> str:
    """Hash relative file names and bytes only; never include an absolute path."""

    base = Path(root)
    if not base.is_absolute() or not base.is_dir():
        raise LivePilotError("fixture root must be an existing absolute directory")
    entries: list[dict[str, Any]] = []
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(base).as_posix()
        if path.is_symlink():
            raise LivePilotError(f"fixture contains a symlink: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise LivePilotError(f"fixture contains unsupported entry: {relative}")
        data = path.read_bytes()
        entries.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return sha256_json(entries)


@dataclass(frozen=True)
class LivePilotExpectation:
    nonce: str
    line_count: int
    field_value: str
    checksum_prefix: str
    expected_files: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _NONCE.fullmatch(self.nonce):
            raise LivePilotError("fixture nonce must be a synthetic lowercase hex value")
        if self.line_count <= 0 or not isinstance(self.line_count, int):
            raise LivePilotError("fixture line count must be positive")
        if not isinstance(self.field_value, str) or not self.field_value:
            raise LivePilotError("fixture field value must be non-empty")
        if not re.fullmatch(r"[a-f0-9]{8}", self.checksum_prefix):
            raise LivePilotError("fixture checksum prefix must be eight lowercase hex characters")
        if tuple(sorted(self.expected_files)) != self.expected_files:
            raise LivePilotError("fixture files must be canonical ordered")

    def to_dict(self) -> dict[str, Any]:
        return {
            "nonce": self.nonce, "line_count": self.line_count, "field_value": self.field_value,
            "checksum_prefix": self.checksum_prefix, "expected_files": list(self.expected_files),
        }


class DisposableLiveFixture:
    """A tiny read-only workspace whose lifecycle is explicit and disposable."""

    def __init__(self, root: Path, expectation: LivePilotExpectation) -> None:
        self.root = root
        self.expectation = expectation
        self.before_digest = tree_digest(root)
        self._read_only = False

    @classmethod
    def create(cls, parent: str | Path | None = None, *, nonce: str | None = None) -> "DisposableLiveFixture":
        parent_path = Path(parent) if parent is not None else None
        if parent_path is not None and (not parent_path.is_absolute() or not parent_path.is_dir()):
            raise LivePilotError("fixture parent must be an existing absolute directory")
        root = Path(tempfile.mkdtemp(prefix="ignition-live-136-", dir=str(parent_path) if parent_path else None))
        value = nonce or secrets.token_hex(12)
        if not _NONCE.fullmatch(value):
            raise LivePilotError("fixture nonce must be exactly 24 lowercase hex characters")
        readme = "alpha\nbeta\ngamma\n"
        table = {"field": "value-136", "rows": [1, 2, 3]}
        table_text = json.dumps(table, sort_keys=True, separators=(",", ":")) + "\n"
        (root / "README.txt").write_text(readme, encoding="utf-8")
        (root / "nonce.txt").write_text(value + "\n", encoding="utf-8")
        (root / "table.json").write_text(table_text, encoding="utf-8")
        checksum = hashlib.sha256((readme + value + "\n" + table_text).encode("utf-8")).hexdigest()[:8]
        expectation = LivePilotExpectation(value, 3, "value-136", checksum, ("README.txt", "nonce.txt", "table.json"))
        return cls(root, expectation)

    def make_read_only(self) -> None:
        if not self.root.is_dir():
            raise LivePilotError("fixture root no longer exists")
        for path in self.root.iterdir():
            if path.is_file():
                path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        self.root.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        self._read_only = True

    def read_only_guard_observed(self) -> bool:
        if not self._read_only:
            return False
        root_mode = stat.S_IMODE(self.root.stat().st_mode)
        if root_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            return False
        return all(not (stat.S_IMODE(path.stat().st_mode) & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)) for path in self.root.iterdir() if path.is_file())

    def current_digest(self) -> str:
        return tree_digest(self.root)

    def file_names(self) -> tuple[str, ...]:
        return tuple(sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*") if path.is_file()))

    def cleanup(self) -> None:
        if self.root.exists():
            for path in self.root.rglob("*"):
                if path.is_file():
                    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            self.root.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            shutil.rmtree(self.root)

    def __enter__(self) -> "DisposableLiveFixture":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.cleanup()


@dataclass(frozen=True)
class LiveValidationReport:
    status: str
    checks: Mapping[str, bool]
    failure_codes: tuple[str, ...]
    result_digest: str
    claim_ceiling: str = "Independent synthetic fixture validation only; no Goal completion or external truth is inferred."

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": LIVE_PILOT_SCHEMA + ".validation", "status": self.status, "checks": dict(self.checks),
            "failure_codes": list(self.failure_codes), "result_digest": self.result_digest, "claim_ceiling": self.claim_ceiling,
        }


class LivePilotValidator:
    """Pure local validator for the synthetic read-only task."""

    def __init__(self, fixture: DisposableLiveFixture, *, task_id: str, dispatch_id: str, attempt_id: str, executor_id: str) -> None:
        for value, field in ((task_id, "task_id"), (dispatch_id, "dispatch_id"), (attempt_id, "attempt_id"), (executor_id, "executor_id")):
            try:
                _id(value, field)
            except ValueError as exc:
                raise LivePilotError(f"validator binding {field} is invalid") from exc
        self.fixture = fixture
        self.task_id = task_id
        self.dispatch_id = dispatch_id
        self.attempt_id = attempt_id
        self.executor_id = executor_id

    def validate(
        self,
        result: Mapping[str, Any],
        *,
        before_digest: str,
        after_digest: str,
        result_task_id: str | None = None,
        result_dispatch_id: str | None = None,
        result_attempt_id: str | None = None,
        result_executor_id: str | None = None,
        side_effect_observation: str = "READ_ONLY_UNCHANGED",
    ) -> LiveValidationReport:
        failures: list[str] = []
        checks: dict[str, bool] = {}
        try:
            sanitized = sanitize_live_result(result, allowed_keys=("nonce", "line_count", "field_value", "checksum_prefix"))
            value = dict(sanitized.value)
        except LivePrivacyError:
            sanitized = None
            value = {}
            failures.append("RESULT_PRIVACY_REJECTED")
        expected_keys = {"nonce", "line_count", "field_value", "checksum_prefix"}
        checks["output_schema_exact"] = set(value) == expected_keys
        checks["nonce_exact"] = value.get("nonce") == self.fixture.expectation.nonce
        checks["line_count_exact"] = value.get("line_count") == self.fixture.expectation.line_count
        checks["field_value_exact"] = value.get("field_value") == self.fixture.expectation.field_value
        checks["checksum_prefix_exact"] = value.get("checksum_prefix") == self.fixture.expectation.checksum_prefix
        checks["fixture_files_exact"] = self.fixture.file_names() == self.fixture.expectation.expected_files
        checks["tree_unchanged"] = before_digest == after_digest == self.fixture.before_digest == self.fixture.current_digest()
        checks["read_only_guard"] = self.fixture.read_only_guard_observed()
        checks["side_effect_free"] = side_effect_observation == "READ_ONLY_UNCHANGED"
        checks["task_binding"] = result_task_id in {None, self.task_id}
        checks["dispatch_binding"] = result_dispatch_id in {None, self.dispatch_id}
        checks["attempt_binding"] = result_attempt_id in {None, self.attempt_id}
        checks["executor_binding"] = result_executor_id in {None, self.executor_id}
        if sanitized is None:
            checks["output_schema_exact"] = False
        for name, passed in checks.items():
            if not passed:
                failures.append(name.upper())
        failures = sorted(set(failures))
        return LiveValidationReport(
            status="PASS" if not failures else "FAIL",
            checks=checks,
            failure_codes=tuple(failures),
            result_digest=sha256_json(result),
        )


__all__ = [
    "LIVE_PILOT_SCHEMA", "DisposableLiveFixture", "LivePilotError", "LivePilotExpectation", "LivePilotValidator",
    "LiveValidationReport", "tree_digest",
]
