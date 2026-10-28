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
LIVE_COMPLETION_PILOT_SCHEMA = "ignition-137-live-pilot-r1"
LIVE_COMPLETION_138_PILOT_SCHEMA = "ignition-138-live-pilot-r1"
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
    schema: str = LIVE_PILOT_SCHEMA + ".validation"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema, "status": self.status, "checks": dict(self.checks),
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


@dataclass(frozen=True)
class LiveCompletionExpectation:
    nonce: str
    selected_ids: tuple[str, ...]
    count: int
    workspace_digest: str
    expected_files: tuple[str, ...]


class DisposableLiveCompletionFixture:
    """Task137 fixture with an independently computable answer."""

    def __init__(self, root: Path, expectation: LiveCompletionExpectation) -> None:
        self.root = root
        self.expectation = expectation
        self.before_digest = tree_digest(root)
        self._read_only = False

    @classmethod
    def create(cls, parent: str | Path | None = None, *, nonce: str | None = None) -> "DisposableLiveCompletionFixture":
        parent_path = Path(parent) if parent is not None else None
        if parent_path is not None and (not parent_path.is_absolute() or not parent_path.is_dir()):
            raise LivePilotError("fixture parent must be an existing absolute directory")
        root = Path(tempfile.mkdtemp(prefix="ignition-live-137-", dir=str(parent_path) if parent_path else None))
        value = nonce or secrets.token_hex(12)
        if not _NONCE.fullmatch(value):
            raise LivePilotError("fixture nonce must be exactly 24 lowercase hex characters")
        readme = (
            "Task137 synthetic read-only fixture.\n"
            "Select rows where eligible is true and score is at least 50.\n"
            "Sort selected ids by score ascending, then id ascending.\n"
            "workspace_digest_claim is the path-independent tree digest of all three files.\n"
        )
        table = {
            "rule": {"eligible": True, "minimum_score": 50, "sort": ["score", "id"]},
            "rows": [
                {"id": "row-c", "eligible": True, "score": 70},
                {"id": "row-a", "eligible": True, "score": 50},
                {"id": "row-b", "eligible": False, "score": 99},
                {"id": "row-d", "eligible": True, "score": 50},
                {"id": "row-e", "eligible": True, "score": 20},
            ],
        }
        (root / "README.txt").write_text(readme, encoding="utf-8")
        (root / "nonce.txt").write_text(value + "\n", encoding="utf-8")
        (root / "table.json").write_text(json.dumps(table, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        selected = tuple(row["id"] for row in sorted((row for row in table["rows"] if row["eligible"] and row["score"] >= table["rule"]["minimum_score"]), key=lambda row: (row["score"], row["id"])))
        expected_files = ("README.txt", "nonce.txt", "table.json")
        digest = tree_digest(root)
        return cls(root, LiveCompletionExpectation(value, selected, len(selected), digest, expected_files))

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
        return not (root_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)) and all(
            not (stat.S_IMODE(path.stat().st_mode) & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
            for path in self.root.iterdir() if path.is_file()
        )

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

    def __enter__(self) -> "DisposableLiveCompletionFixture":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.cleanup()


@dataclass(frozen=True)
class Live138CompletionExpectation:
    nonce: str
    selected_ids: tuple[str, ...]
    count: int
    workspace_digest: str
    expected_files: tuple[str, ...]


class DisposableLive138CompletionFixture:
    """Task138 disposable fixture with a frozen local answer and strict schema."""

    def __init__(self, root: Path, schema_path: Path, expectation: Live138CompletionExpectation) -> None:
        self.root = root
        self.schema_path = schema_path
        self.expectation = expectation
        self.before_digest = tree_digest(root)
        self._read_only = False

    @classmethod
    def create(cls, parent: str | Path | None = None, *, nonce: str | None = None) -> "DisposableLive138CompletionFixture":
        parent_path = Path(parent) if parent is not None else None
        if parent_path is not None and (not parent_path.is_absolute() or not parent_path.is_dir()):
            raise LivePilotError("fixture parent must be an existing absolute directory")
        root = Path(tempfile.mkdtemp(prefix="ignition-live-138-", dir=str(parent_path) if parent_path else None))
        value = nonce or secrets.token_hex(12)
        if not _NONCE.fullmatch(value):
            raise LivePilotError("fixture nonce must be exactly 24 lowercase hex characters")
        readme = (
            "Task138 synthetic read-only fixture.\n"
            "Select rows where eligible is true and score is at least 60.\n"
            "Sort selected ids by score ascending, then id ascending.\n"
            "Return nonce, selected ids, count and the workspace digest claim.\n"
        )
        table = {
            "rule": {"eligible": True, "minimum_score": 60, "sort": ["score", "id"]},
            "rows": [
                {"id": "item-c", "eligible": True, "score": 85},
                {"id": "item-a", "eligible": True, "score": 60},
                {"id": "item-b", "eligible": False, "score": 99},
                {"id": "item-d", "eligible": True, "score": 60},
                {"id": "item-e", "eligible": True, "score": 40},
                {"id": "item-f", "eligible": True, "score": 75},
                {"id": "item-g", "eligible": False, "score": 100},
            ],
        }
        (root / "README.txt").write_text(readme, encoding="utf-8")
        (root / "nonce.txt").write_text(value + "\n", encoding="utf-8")
        (root / "table.json").write_text(json.dumps(table, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        schema_path = root.parent / (root.name + "-output-schema.json")
        schema_path.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["nonce", "selected_ids", "count", "workspace_digest_claim"],
            "properties": {
                "nonce": {"type": "string", "pattern": "^[a-f0-9]{24}$"},
                "selected_ids": {"type": "array", "items": {"type": "string"}},
                "count": {"type": "integer", "minimum": 0},
                "workspace_digest_claim": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            },
        }, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        schema_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        selected = tuple(
            row["id"] for row in sorted(
                (row for row in table["rows"] if row["eligible"] is True and row["score"] >= table["rule"]["minimum_score"]),
                key=lambda row: (row["score"], row["id"]),
            )
        )
        expectation = Live138CompletionExpectation(value, selected, len(selected), tree_digest(root), ("README.txt", "nonce.txt", "table.json"))
        return cls(root, schema_path, expectation)

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
        return not (root_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)) and all(
            not (stat.S_IMODE(path.stat().st_mode) & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
            for path in self.root.iterdir() if path.is_file()
        )

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
        if self.schema_path.exists():
            self.schema_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            self.schema_path.unlink()

    def __enter__(self) -> "DisposableLive138CompletionFixture":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.cleanup()


class Live138CompletionValidator:
    """Independent validator for the Task138 fixture's exact result contract."""

    def __init__(self, fixture: DisposableLive138CompletionFixture) -> None:
        self.fixture = fixture

    def validate(
        self,
        result: Mapping[str, Any],
        *,
        before_digest: str,
        after_digest: str,
        side_effect_observation: str = "READ_ONLY_UNCHANGED",
    ) -> LiveValidationReport:
        failures: list[str] = []
        checks: dict[str, bool] = {}
        expected_nonce = None
        expected_selected: tuple[str, ...] = ()
        expected_count = 0
        try:
            expected_nonce = (self.fixture.root / "nonce.txt").read_text(encoding="utf-8").strip()
            table = json.loads((self.fixture.root / "table.json").read_text(encoding="utf-8"))
            rule = table["rule"]
            if rule != {"eligible": True, "minimum_score": 60, "sort": ["score", "id"]}:
                raise ValueError("fixture rule drifted")
            expected_selected = tuple(
                row["id"] for row in sorted(
                    (row for row in table["rows"] if row["eligible"] is True and row["score"] >= rule["minimum_score"]),
                    key=lambda row: (row["score"], row["id"]),
                )
            )
            expected_count = len(expected_selected)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            failures.append("FIXTURE_EXPECTATION_RECOMPUTE_FAILED")
        try:
            sanitized = sanitize_live_result(result, allowed_keys=("nonce", "selected_ids", "count", "workspace_digest_claim"))
            value = dict(sanitized.value)
        except LivePrivacyError:
            value = {}
            failures.append("RESULT_PRIVACY_REJECTED")
        expected_keys = {"nonce", "selected_ids", "count", "workspace_digest_claim"}
        checks["output_schema_exact"] = isinstance(result, Mapping) and set(result) == expected_keys and set(value) == expected_keys
        checks["output_schema_types"] = (
            isinstance(value.get("nonce"), str)
            and isinstance(value.get("selected_ids"), list)
            and all(isinstance(item, str) for item in value.get("selected_ids", ()))
            and type(value.get("count")) is int
            and isinstance(value.get("workspace_digest_claim"), str)
        )
        checks["nonce_exact"] = value.get("nonce") == expected_nonce
        checks["selected_ids_exact"] = value.get("selected_ids") == list(expected_selected)
        checks["count_exact"] = value.get("count") == expected_count
        checks["workspace_digest_claim_exact"] = value.get("workspace_digest_claim") == before_digest
        checks["fixture_files_exact"] = self.fixture.file_names() == self.fixture.expectation.expected_files
        checks["tree_unchanged"] = before_digest == after_digest == self.fixture.before_digest == self.fixture.current_digest()
        checks["read_only_guard"] = self.fixture.read_only_guard_observed()
        checks["side_effect_free"] = side_effect_observation == "READ_ONLY_UNCHANGED"
        for name, passed in checks.items():
            if not passed:
                failures.append(name.upper())
        return LiveValidationReport(
            status="PASS" if not failures else "FAIL",
            checks=checks,
            failure_codes=tuple(sorted(set(failures))),
            result_digest=sha256_json(result),
            claim_ceiling="Independent Task138 synthetic fixture validation only; no Goal completion or external truth is inferred.",
            schema=LIVE_COMPLETION_138_PILOT_SCHEMA + ".validation",
        )


class LiveCompletionValidator:
    """Independent answer validator for the Task137 fixture."""

    def __init__(self, fixture: DisposableLiveCompletionFixture) -> None:
        self.fixture = fixture

    def validate(
        self,
        result: Mapping[str, Any],
        *,
        before_digest: str,
        after_digest: str,
        side_effect_observation: str = "READ_ONLY_UNCHANGED",
    ) -> LiveValidationReport:
        failures: list[str] = []
        checks: dict[str, bool] = {}
        expected_nonce = None
        expected_selected: tuple[str, ...] = ()
        expected_count = 0
        try:
            expected_nonce = (self.fixture.root / "nonce.txt").read_text(encoding="utf-8").strip()
            table = json.loads((self.fixture.root / "table.json").read_text(encoding="utf-8"))
            rule = table["rule"]
            if rule != {"eligible": True, "minimum_score": 50, "sort": ["score", "id"]}:
                raise ValueError("fixture rule drifted")
            rows = table["rows"]
            selected_rows = [row for row in rows if row["eligible"] is True and row["score"] >= rule["minimum_score"]]
            expected_selected = tuple(row["id"] for row in sorted(selected_rows, key=lambda row: (row["score"], row["id"])))
            expected_count = len(expected_selected)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            failures.append("FIXTURE_EXPECTATION_RECOMPUTE_FAILED")
        try:
            sanitized = sanitize_live_result(result, allowed_keys=("nonce", "selected_ids", "count", "workspace_digest_claim"))
            value = dict(sanitized.value)
        except LivePrivacyError:
            value = {}
            failures.append("RESULT_PRIVACY_REJECTED")
        expected_keys = {"nonce", "selected_ids", "count", "workspace_digest_claim"}
        checks["output_schema_exact"] = isinstance(result, Mapping) and set(result) == expected_keys and set(value) == expected_keys
        checks["nonce_exact"] = value.get("nonce") == expected_nonce
        checks["selected_ids_exact"] = value.get("selected_ids") == list(expected_selected)
        checks["count_exact"] = value.get("count") == expected_count
        checks["workspace_digest_claim_exact"] = value.get("workspace_digest_claim") == before_digest
        checks["fixture_files_exact"] = self.fixture.file_names() == self.fixture.expectation.expected_files
        checks["tree_unchanged"] = before_digest == after_digest == self.fixture.before_digest == self.fixture.current_digest()
        checks["read_only_guard"] = self.fixture.read_only_guard_observed()
        checks["side_effect_free"] = side_effect_observation == "READ_ONLY_UNCHANGED"
        if not checks["output_schema_exact"]:
            failures.append("OUTPUT_SCHEMA_EXACT")
        for name, passed in checks.items():
            if not passed:
                failures.append(name.upper())
        return LiveValidationReport(
            status="PASS" if not failures else "FAIL", checks=checks, failure_codes=tuple(sorted(set(failures))),
            result_digest=sha256_json(result),
            claim_ceiling="Independent Task137 synthetic fixture validation only; no Goal completion or external truth is inferred.",
            schema=LIVE_COMPLETION_PILOT_SCHEMA + ".validation",
        )


__all__ = [
    "LIVE_COMPLETION_138_PILOT_SCHEMA", "LIVE_COMPLETION_PILOT_SCHEMA", "LIVE_PILOT_SCHEMA",
    "DisposableLive138CompletionFixture", "DisposableLiveCompletionFixture", "DisposableLiveFixture",
    "Live138CompletionExpectation", "Live138CompletionValidator", "LiveCompletionExpectation", "LiveCompletionValidator",
    "LivePilotError", "LivePilotExpectation", "LivePilotValidator",
    "LiveValidationReport", "tree_digest",
]
