"""Durable host-side capture capsule and bounded sanitized projection.

The writer owns an attempt-specific raw spool.  ``LiveCaptureCapsule`` never
exposes the filesystem path or raw bytes; it is the public evidence boundary
that can survive loss of the outer model/tool context.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import tempfile
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json


CAPTURE_SCHEMA = "live-capture-capsule-r1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
TASK_RE = re.compile(r"^IGNITION-[0-9]{8}-[0-9]+$")
PRIVATE_MARKERS = (
    "access_token", "api_key", "bearer ", "client_secret", "password", "secret",
    "hidden reasoning", "private model reasoning", "chain-of-thought", "chain of thought",
    "full_prompt", "raw_prompt", "prompt_body", "token_telemetry", "session_db",
)
PRIVATE_KEY_MARKERS = tuple(marker for marker in PRIVATE_MARKERS if marker != "secret") + ("secret_value", "secret_data")


class LiveCaptureError(RuntimeError):
    """Raised when capture cannot be initialized or safely projected."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _scan_public(value: Any, field: str = "capture") -> None:
    if isinstance(value, str):
        if any(marker in value.casefold() for marker in PRIVATE_MARKERS):
            raise LiveCaptureError(f"{field} contains private or hidden material")
        return
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str) or not key.strip():
                raise LiveCaptureError(f"{field} contains an invalid key")
            lowered = key.casefold()
            if any(marker in lowered for marker in PRIVATE_KEY_MARKERS) or "prompt" in lowered:
                raise LiveCaptureError(f"{field}.{key} is not a public capture field")
            _scan_public(child, f"{field}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _scan_public(child, f"{field}[{index}]")
        return
    raise LiveCaptureError(f"{field} contains a non-JSON value")


def _digest_or_none(value: Any, field: str, *, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise LiveCaptureError(f"{field} must be a lowercase SHA-256 digest")


def _timestamp(value: Any, field: str, *, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if not isinstance(value, str):
        raise LiveCaptureError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LiveCaptureError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LiveCaptureError(f"{field} must include a timezone")


def _schema_validate(document: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover
        return
    schema_path = Path(__file__).resolve().parents[1] / "schemas/operations/live-capture-capsule-r1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "$"
        raise LiveCaptureError(f"capture schema violation at {path}: {error.message}")


def validate_capsule(document: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise LiveCaptureError("capture capsule must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    _schema_validate(value)
    _scan_public(value)
    if value["schema_version"] != CAPTURE_SCHEMA:
        raise LiveCaptureError("capture schema version mismatch")
    if not ID_RE.fullmatch(value["capture_id"]) or not ID_RE.fullmatch(value["dispatch_id"]) or not ID_RE.fullmatch(value["attempt_id"]):
        raise LiveCaptureError("capture identity must be safe and stable")
    if not TASK_RE.fullmatch(value["task_id"]):
        raise LiveCaptureError("capture task_id is invalid")
    _timestamp(value["spool_initialized_at"], "spool_initialized_at")
    _timestamp(value["capture_finalized_at"], "capture_finalized_at", allow_null=True)
    for field in ("stdout", "stderr"):
        stream = value[field]
        if not isinstance(stream["byte_count"], int) or isinstance(stream["byte_count"], bool) or stream["byte_count"] < 0:
            raise LiveCaptureError(f"{field}.byte_count must be non-negative")
        _digest_or_none(stream["digest"], f"{field}.digest")
    events = value["public_events"]
    if events["count"] == 0:
        if events["sequence_start"] is not None or events["sequence_end"] is not None:
            raise LiveCaptureError("empty public event capture cannot have a sequence range")
    elif events["sequence_start"] is None or events["sequence_end"] is None or events["sequence_end"] < events["sequence_start"]:
        raise LiveCaptureError("public event sequence range is invalid")
    _digest_or_none(events["digest"], "public_events.digest")
    structured = value["structured_result"]
    if structured["present"]:
        if not isinstance(structured["ref"], str) or not structured["ref"]:
            raise LiveCaptureError("structured result presence requires a public ref")
        _digest_or_none(structured["digest"], "structured_result.digest")
    elif structured["ref"] is not None or structured["digest"] is not None:
        raise LiveCaptureError("absent structured result cannot have a ref or digest")
    context = value["context_projection"]
    if context["summary_ref"] is None and context["summary_digest"] is not None:
        raise LiveCaptureError("context summary digest requires a ref")
    if context["summary_digest"] is not None:
        _digest_or_none(context["summary_digest"], "context_projection.summary_digest")
    process = value["process_observation"]
    if process["return_code"] is not None and (not isinstance(process["return_code"], int) or isinstance(process["return_code"], bool)):
        raise LiveCaptureError("process return code must be an integer or null")
    if value["capture_completeness"] == "COMPLETE" and value["finalization_state"] != "FINALIZED":
        raise LiveCaptureError("complete capture must be finalized")
    if value["output_truncated"] and value["capture_completeness"] == "COMPLETE":
        raise LiveCaptureError("truncated output cannot be marked complete")
    if value["secret_scan_status"] == "FAIL" and value["capture_completeness"] == "COMPLETE":
        raise LiveCaptureError("secret scan failure cannot be complete")
    return value


@dataclass
class LiveCaptureWriter:
    """Stream raw bytes/events to a private spool and finalize one capsule."""

    capture_id: str
    task_id: str
    dispatch_id: str
    attempt_id: str
    executor_id: str
    adapter_id: str
    spool_path: Path
    spool_initialized_at: str
    _stdout_digest: Any
    _stderr_digest: Any
    _event_digest: Any
    _stdout_count: int = 0
    _stderr_count: int = 0
    _event_count: int = 0
    _event_start: int | None = None
    _event_end: int | None = None
    _structured_result: Mapping[str, Any] | None = None
    _structured_digest: str | None = None
    _secret_scan_status: str = "PASS"
    _finalized: bool = False
    _capsule: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        *,
        capture_id: str,
        task_id: str,
        dispatch_id: str,
        attempt_id: str,
        executor_id: str,
        adapter_id: str,
        parent: str | Path | None = None,
        protected_roots: tuple[str | Path, ...] = (),
    ) -> "LiveCaptureWriter":
        if not ID_RE.fullmatch(capture_id) or not ID_RE.fullmatch(dispatch_id) or not ID_RE.fullmatch(attempt_id):
            raise LiveCaptureError("capture identities must be safe tokens")
        if not TASK_RE.fullmatch(task_id):
            raise LiveCaptureError("capture task_id is invalid")
        if not isinstance(parent, (str, Path)) and parent is not None:
            raise LiveCaptureError("capture spool parent must be a path")
        parent_path = Path(parent) if parent is not None else Path(tempfile.gettempdir())
        if not parent_path.is_absolute() or not parent_path.is_dir() or parent_path.is_symlink():
            raise LiveCaptureError("capture spool parent must be an existing absolute directory")
        parent_resolved = parent_path.resolve(strict=True)
        protected = tuple(Path(root).resolve(strict=True) for root in protected_roots)
        if any(parent_resolved == root or root in parent_resolved.parents for root in protected):
            raise LiveCaptureError("capture spool parent overlaps a protected root")
        spool = Path(tempfile.mkdtemp(prefix=f"pointfire-capture-{capture_id}-", dir=str(parent_resolved)))
        spool.chmod(stat.S_IRWXU)
        for name in ("stdout.bin", "stderr.bin", "public-events.jsonl"):
            (spool / name).touch(mode=0o600)
        return cls(
            capture_id=capture_id, task_id=task_id, dispatch_id=dispatch_id, attempt_id=attempt_id,
            executor_id=executor_id, adapter_id=adapter_id, spool_path=spool,
            spool_initialized_at=_now(), _stdout_digest=hashlib.sha256(), _stderr_digest=hashlib.sha256(),
            _event_digest=hashlib.sha256(),
        )

    @property
    def spool_ref(self) -> str:
        return f"capture://{self.capture_id}"

    def _write_bytes(self, stream: str, chunk: bytes) -> None:
        if self._finalized:
            raise LiveCaptureError("capture is already finalized")
        if not isinstance(chunk, (bytes, bytearray)):
            raise LiveCaptureError("capture stream chunk must be bytes")
        raw = bytes(chunk)
        if any(marker.encode("utf-8") in raw.lower() for marker in PRIVATE_MARKERS):
            self._secret_scan_status = "FAIL"
            raise LiveCaptureError("private marker detected in raw process output")
        path = self.spool_path / f"{stream}.bin"
        try:
            with path.open("ab") as handle:
                handle.write(raw)
                handle.flush()
        except OSError as exc:
            raise LiveCaptureError("capture spool write failed") from exc
        digest = self._stdout_digest if stream == "stdout" else self._stderr_digest
        digest.update(raw)
        if stream == "stdout":
            self._stdout_count += len(raw)
        else:
            self._stderr_count += len(raw)

    def write_stdout(self, chunk: bytes) -> None:
        self._write_bytes("stdout", chunk)

    def write_stderr(self, chunk: bytes) -> None:
        self._write_bytes("stderr", chunk)

    def record_public_event(self, event: Mapping[str, Any]) -> int:
        if self._finalized:
            raise LiveCaptureError("capture is already finalized")
        _scan_public(event, "public_event")
        if not isinstance(event, Mapping):
            raise LiveCaptureError("public event must be an object")
        sequence = self._event_count
        encoded = (json.dumps(dict(event), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            with (self.spool_path / "public-events.jsonl").open("ab") as handle:
                handle.write(encoded)
                handle.flush()
        except OSError as exc:
            raise LiveCaptureError("public event spool write failed") from exc
        self._event_digest.update(encoded)
        self._event_count += 1
        self._event_start = 0 if self._event_start is None else self._event_start
        self._event_end = sequence
        return sequence

    def record_structured_result(self, result: Mapping[str, Any]) -> str:
        if self._finalized:
            raise LiveCaptureError("capture is already finalized")
        _scan_public(result, "structured_result")
        if not isinstance(result, Mapping):
            raise LiveCaptureError("structured result must be an object")
        value = json.loads(json.dumps(result, ensure_ascii=False, sort_keys=True))
        digest = sha256_json(value)
        try:
            (self.spool_path / "structured-result.json").write_text(
                json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            raise LiveCaptureError("structured result spool write failed") from exc
        self._structured_result = value
        self._structured_digest = digest
        return f"{self.spool_ref}/structured-result"

    def finalize(
        self,
        *,
        return_code: int | None,
        signal_name: str | None = None,
        timed_out: bool = False,
        process_group_status: str = "CONFIRMED_GONE",
        capture_completeness: str = "COMPLETE",
        output_truncated: bool = False,
        cleanup: bool = True,
        context_summary: str | None = None,
        secret_scan_status: str | None = None,
    ) -> dict[str, Any]:
        if self._finalized:
            assert self._capsule is not None
            return dict(self._capsule)
        if capture_completeness not in {"COMPLETE", "INCOMPLETE", "NOT_OBSERVED"}:
            raise LiveCaptureError("unknown capture completeness")
        if return_code is not None and (not isinstance(return_code, int) or isinstance(return_code, bool)):
            raise LiveCaptureError("return code must be an integer or null")
        if process_group_status not in {"CONFIRMED_GONE", "CHILD_LEFT_BEHIND", "UNKNOWN", "NOT_OBSERVED"}:
            raise LiveCaptureError("unknown process group status")
        final_status = secret_scan_status or self._secret_scan_status
        if final_status not in {"PASS", "FAIL", "NOT_RUN", "REDACTED"}:
            raise LiveCaptureError("unknown secret scan status")
        finalized_at = _now()
        if context_summary is not None:
            _scan_public(context_summary, "context_summary")
        summary_ref = f"{self.spool_ref}/summary" if context_summary is not None else None
        summary_digest = hashlib.sha256(context_summary.encode("utf-8")).hexdigest() if context_summary is not None else None
        summary_count = len(context_summary.encode("utf-8")) if context_summary is not None else 0
        cleanup_status = "NOT_REQUIRED"
        finalization_state = "FINALIZED"
        if cleanup:
            try:
                if self.spool_path.is_symlink() or (self.spool_path.exists() and any(path.is_symlink() for path in self.spool_path.rglob("*"))):
                    raise OSError("capture spool contains a symlink")
                if self.spool_path.exists():
                    shutil.rmtree(self.spool_path)
                cleanup_status = "CLEANED" if not self.spool_path.exists() else "FAILED"
            except OSError:
                cleanup_status = "FAILED"
                finalization_state = "RECOVERY_REQUIRED"
        else:
            cleanup_status = "PENDING"
        capsule = {
            "schema_version": CAPTURE_SCHEMA,
            "capture_id": self.capture_id,
            "task_id": self.task_id,
            "dispatch_id": self.dispatch_id,
            "attempt_id": self.attempt_id,
            "executor_id": self.executor_id,
            "adapter_id": self.adapter_id,
            "spool_ref": self.spool_ref,
            "spool_initialized_at": self.spool_initialized_at,
            "capture_finalized_at": finalized_at,
            "process_observation": {
                "pid_ref": "REDACTED",
                "process_group_ref": "REDACTED",
                "process_group_status": process_group_status,
                "return_code": return_code,
                "signal": signal_name,
                "timed_out": bool(timed_out),
            },
            "stdout": {"byte_count": self._stdout_count, "digest": self._stdout_digest.hexdigest()},
            "stderr": {"byte_count": self._stderr_count, "digest": self._stderr_digest.hexdigest()},
            "public_events": {
                "sequence_start": self._event_start,
                "sequence_end": self._event_end,
                "count": self._event_count,
                "digest": self._event_digest.hexdigest(),
            },
            "structured_result": {
                "present": self._structured_result is not None,
                "ref": f"{self.spool_ref}/structured-result" if self._structured_result is not None else None,
                "digest": self._structured_digest,
            },
            "context_projection": {
                "summary_ref": summary_ref,
                "summary_digest": summary_digest,
                "summary_byte_count": summary_count,
            },
            "capture_completeness": capture_completeness,
            "output_truncated": bool(output_truncated),
            "finalization_state": finalization_state,
            "spool_cleanup_status": cleanup_status,
            "secret_scan_status": final_status,
            "claim_ceiling": "Host-side public capture integrity and bounded sanitized projection only; raw output and external completion are not claimed.",
        }
        self._capsule = validate_capsule(capsule)
        self._finalized = True
        return dict(self._capsule)


__all__ = ["CAPTURE_SCHEMA", "LiveCaptureError", "LiveCaptureWriter", "validate_capsule"]
