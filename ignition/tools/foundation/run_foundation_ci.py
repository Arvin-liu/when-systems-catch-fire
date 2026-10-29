#!/usr/bin/env python3
"""Run Foundation CI checks sequentially and retain per-command evidence.

Every declared check runs even after an earlier check fails. The aggregate
process exits nonzero if any check fails, so diagnostic continuation never
turns a failed run green. Checks run in one process at a time to keep the
memory-heavy Foundation generators from overlapping. Cancellation and an
unreconciled timeout/process group stop later checks and are written to the
command ledger.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


APP_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = APP_ROOT.parent
DEFAULT_CHECK_TIMEOUT_SECONDS = 45 * 60
OUTPUT_TAIL_BYTES = 256 * 1024
OUTPUT_CHUNK_BYTES = 64 * 1024
MAX_OUTPUT_ARTIFACT_BYTES = 16 * 1024 * 1024
PROCESS_TERMINATION_GRACE_SECONDS = 5


@dataclass(frozen=True)
class Check:
    name: str
    argv: tuple[str, ...]
    cwd: str = "."
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("Foundation check timeout_seconds must be positive")


class _CaptureBuffer:
    """Stream full output to bounded disk storage and keep a bounded tail."""

    def __init__(self, destination: Path | None = None, limit: int = OUTPUT_TAIL_BYTES) -> None:
        if limit <= 0:
            raise ValueError("output capture limit must be positive")
        self.limit = limit
        self.destination = destination
        self._output = None
        self.tail = bytearray()
        self.total_bytes = 0
        self.stored_bytes = 0
        self.digest = hashlib.sha256()
        self.read_error: str | None = None
        self._storage_failed = False
        self._overflowed = False
        self._lock = threading.Lock()

    def append(self, chunk: bytes) -> None:
        with self._lock:
            self.total_bytes += len(chunk)
            self.digest.update(chunk)
            self.tail.extend(chunk)
            if len(self.tail) > self.limit:
                del self.tail[: len(self.tail) - self.limit]
            if self.destination is not None and not self._overflowed and not self._storage_failed:
                remaining = MAX_OUTPUT_ARTIFACT_BYTES - self.stored_bytes
                portion = chunk[:remaining]
                if portion:
                    try:
                        if self._output is None:
                            self._output = self.destination.open("wb")
                        self._output.write(portion)
                        self.stored_bytes += len(portion)
                    except OSError as exc:
                        self.read_error = f"output artifact write failed: {type(exc).__name__}: {exc}"
                        self._storage_failed = True
                if len(chunk) > remaining:
                    self._overflowed = True

    def mark_read_error(self, error: Exception) -> None:
        with self._lock:
            self.read_error = f"{type(error).__name__}: {error}"

    def record(self, path: Path) -> dict[str, object]:
        with self._lock:
            retained = bytes(self.tail)
            total_bytes = self.total_bytes
            stream_digest = self.digest.hexdigest()
            if self._output is not None:
                try:
                    self._output.flush()
                    self._output.close()
                except OSError as exc:
                    self.read_error = f"output artifact close failed: {type(exc).__name__}: {exc}"
                    self._storage_failed = True
                self._output = None
            storage_failed = self._storage_failed
            overflowed = self._overflowed
        if self.destination is None or storage_failed or overflowed or not path.exists():
            try:
                path.write_bytes(retained)
            except OSError as exc:
                self.mark_read_error(exc)
        try:
            stored_bytes = path.stat().st_size
            stored_sha256 = _sha256_file(path)
        except OSError as exc:
            self.mark_read_error(exc)
            stored_bytes = 0
            stored_sha256 = _sha256(b"")
        with self._lock:
            read_error = self.read_error
        return {
            "path": path.name,
            "bytes": stored_bytes,
            "total_bytes": total_bytes,
            "sha256": stored_sha256,
            "stream_sha256": stream_digest,
            "truncated": total_bytes > stored_bytes,
            "retention": "last_bytes" if storage_failed or overflowed else "full",
            "read_error": read_error,
        }


def _drain_pipe(pipe, capture: _CaptureBuffer) -> None:
    try:
        while True:
            chunk = pipe.read(OUTPUT_CHUNK_BYTES)
            if not chunk:
                break
            capture.append(chunk)
    except (OSError, ValueError) as exc:
        capture.mark_read_error(exc)
    finally:
        try:
            pipe.close()
        except OSError as exc:
            capture.mark_read_error(exc)


def _process_group_exists(process_id: int) -> bool:
    if os.name != "posix":
        return False
    try:
        os.killpg(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate_process_group(process: subprocess.Popen, grace_seconds: int = PROCESS_TERMINATION_GRACE_SECONDS) -> bool:
    """Terminate a timed-out/cancelled check and confirm its process group is gone."""
    process_id = process.pid
    if os.name == "posix":
        try:
            os.killpg(process_id, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline:
            if process.poll() is None:
                try:
                    process.wait(timeout=min(0.1, max(0.01, deadline - time.monotonic())))
                except subprocess.TimeoutExpired:
                    pass
            if not _process_group_exists(process_id):
                return True
            time.sleep(0.05)
        if _process_group_exists(process_id):
            try:
                os.killpg(process_id, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            return False
        return not _process_group_exists(process_id)

    # GitHub's runner is POSIX, but preserve process-tree cleanup on Windows
    # hosts too. If taskkill is unavailable, fail closed: terminating only the
    # immediate process does not prove its descendants stopped.
    try:
        terminated = subprocess.run(
            ["taskkill", "/PID", str(process_id), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=grace_seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        return False
    return terminated.returncode == 0 and process.poll() is not None


@contextmanager
def _cancellation_watch():
    """Record SIGINT/SIGTERM so the active child can be stopped and reconciled."""
    state: dict[str, int | None] = {"signal": None}
    previous: dict[int, object] = {}
    if threading.current_thread() is threading.main_thread():
        def record_signal(signum, _frame) -> None:
            if state["signal"] is None:
                state["signal"] = signum

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, record_signal)
    try:
        yield state
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def foundation_checks(python_executable: str | Path = sys.executable) -> list[Check]:
    py = str(python_executable)

    def check(name: str, *argv: str, cwd: str = ".") -> Check:
        return Check(name=name, argv=(py, *argv), cwd=cwd)

    return [
        Check("lean-foundation", ("lake", "env", "lean", "Foundation.lean"), "formal/lean"),
        check("adjudicate-core", "tools/foundation/adjudicate_core.py", "--check"),
        check("migrate-legacy", "tools/foundation/migrate_legacy.py", "--check"),
        check("validate-foundation", "tools/foundation/validate_foundation.py"),
        check("build-function-asset-census", "tools/foundation/build_function_asset_census.py", "--check"),
        check("adjudicate-function-assets", "tools/foundation/adjudicate_function_assets.py", "--check"),
        check("validate-claim-governance", "tools/foundation/validate_claim_governance.py"),
        check("validate-function-asset-closure", "tools/foundation/validate_function_asset_closure.py"),
        check("function-asset-math-checks", "tools/foundation/run_function_asset_math_checks.py", "--check"),
        check("adjudicate-nonfunction-claims", "tools/foundation/adjudicate_nonfunction_claims.py", "--check"),
        check("validate-nonfunction-claim-closure", "tools/foundation/validate_nonfunction_claim_closure.py"),
        check("build-human-results", "tools/governance/build_human_results.py", "--check"),
        check("run-self-correction", "tools/governance/run_self_correction.py", "--check"),
        check("build-knowledge-experience", "tools/governance/build_knowledge_experience.py", "--check"),
        check("validate-human-visibility", "tools/governance/validate_human_visibility.py"),
        check("validate-knowledge-experience", "tools/governance/validate_knowledge_experience.py"),
        check("validate-fire-seeds", "tools/publication/validate_fire_seeds.py", "--check"),
        check("build-claim-browsers", "tools/governance/build_claim_browsers.py", "--check"),
        check("validate-overall-architecture", "tools/generate_overall_architecture.py", "--check"),
        check("knowledge-experience-determinism", "tools/governance/check_knowledge_experience_determinism.py"),
        check("verify-core-claims", "tools/foundation/verify_core_claims.py", "--check"),
        check("verify-079", "tools/foundation/verify_079.py", "--check"),
        check("validate-080-adjudications", "tools/foundation/validate_080_adjudications.py"),
        check("validate-iteration-sync", "tools/validate_iteration_sync.py"),
        check("validate-phase-d-closeout", "tools/operations/validate_phase_d_closeout.py", "--check"),
        check(
            "compute-q32i-change-propagation",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/121Q32I-request.json",
            "--output", "data/operations/propagation/121Q32I-closure.json",
            "--report", "reports/operations/121Q32I-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/121Q32I-system-map-delta.json",
            "--residue", "data/operations/propagation/121Q32I-residue.json",
            "--era-ref", "0a13c246172c0338bf8dda5dc08db5a574a8b23f",
            "--check",
        ),
        check(
            "compute-method-1-4-continuous-stage-snapshot",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-request.json",
            "--output", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-closure.json",
            "--report", "reports/operations/IGNITION-ITERATION-METHOD-1.4-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-system-map-delta.json",
            "--residue", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-residue.json",
            "--era-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--head-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--check",
        ),
        check(
            "compute-method-1-4-actor-gate-repair",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-request.json",
            "--output", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-closure.json",
            "--report", "reports/operations/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-system-map-delta.json",
            "--residue", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-residue.json",
            "--era-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--head-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--check",
        ),
        check(
            "compute-method-1-4-actor-normalized-schema-repair",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-request.json",
            "--output", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-closure.json",
            "--report", "reports/operations/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-system-map-delta.json",
            "--residue", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-residue.json",
            "--era-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--head-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--check",
        ),
        check("validate-phase-e-candidate", "tools/operations/validate_phase_e_candidate.py", "--check"),
        check("validate-system-map", "tools/generate_interactive_system_map.py", "--check"),
        check("validate-homepage-architecture-projection", "tools/validate_homepage_architecture_projection.py", "--check"),
        check("validate-stage-snapshot-actor-contract", "tools/operations/generate_stage_snapshot_actor_contract.py", "--check"),
        check("validate-stage-snapshots", "tools/operations/validate_stage_snapshots.py", "--check"),
        check("stage-snapshot-responsibility-cases", "tools/operations/run_stage_snapshot_responsibility_cases.py"),
        check("validate-human-front-door", "tools/validate_human_front_door.py"),
        check("validate-language-thought", "tools/language_thought/validate_language_thought.py"),
        check("test-language-thought-plane", "-m", "unittest", "tests.test_language_thought_plane"),
        check(
            "validate-epistemic-governance-relationships",
            "tools/validate_epistemic_governance_relationships.py",
            "data/governance/epistemic-governance-relationships.json",
            "--repo-root", ".",
        ),
        check("test-epistemic-governance-relationships", "-m", "unittest", "tests.test_epistemic_governance_relationships", "-v"),
        check("validate-state-changelog", "tools/validate_state_changelog.py"),
        check("test-state-changelog", "-m", "unittest", "tests.test_state_changelog", "-v"),
        check(
            "test-foundation",
            "-m", "unittest",
            "tests.foundation.test_foundation", "tests.foundation.test_trigger_coverage",
        ),
        check("test-claim-governance", "-m", "unittest", "tests.foundation.test_claim_governance"),
        check("test-function-asset-closure", "-m", "unittest", "tests.foundation.test_function_asset_closure"),
        check("test-nonfunction-claim-closure", "-m", "unittest", "tests.foundation.test_nonfunction_claim_closure", "-v"),
        check("test-iteration-sync", "-m", "unittest", "tests.test_iteration_sync", "-v"),
        check("test-human-front-door", "-m", "unittest", "tests.test_human_front_door", "-v"),
        check("test-change-propagation", "-m", "unittest", "tests.test_change_propagation", "-v"),
        check("test-human-visibility-self-correction-knowledge-experience", "-m", "unittest",
              "tests.test_human_visibility_gate", "tests.test_self_correction_engine", "tests.test_knowledge_experience", "-v"),
        check("test-stage-snapshot-publication", "-m", "unittest", "tests.test_stage_snapshot_publication", "-v"),
        check("test-era-resolver-and-generated-output-authority", "-m", "unittest",
              "tests.test_era_resolver_generalization", "tests.test_generated_output_authority",
              "tests.test_generated_output_authority_negative", "-v"),
        check("test-phase-e-candidate", "-m", "unittest", "tests.test_phase_e_candidate", "-v"),
        check("test-production-execution-authority", "-m", "unittest", "tests.test_production_execution_authority", "-v"),
        check("test-generator-reconciliation-staleness", "-m", "unittest",
              "tests.foundation.test_generator_reconciliation_staleness", "-v"),
        check("test-propagation-reconciliation", "-m", "unittest", "tests.test_propagation_reconciliation", "-v"),
        check("validate-propagation-reconciliation", "tools/propagation/validate_reconciliation.py", "--check"),
    ]


def default_evidence_dir() -> Path:
    runner_temp = os.environ.get("RUNNER_TEMP")
    if runner_temp:
        return Path(runner_temp) / "foundation-ci-evidence"
    return Path(tempfile.mkdtemp(prefix="foundation-ci-evidence-")) / "results"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(OUTPUT_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decode(value: bytes | str) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def _tail(value: bytes | str, max_lines: int = 100) -> str:
    lines = _decode(value).splitlines()
    return "\n".join(lines[-max_lines:])


def execute_checks(
    checks: Sequence[Check],
    *,
    repo_root: Path = REPO_ROOT,
    app_root: Path = APP_ROOT,
    evidence_dir: Path,
    env: dict[str, str] | None = None,
) -> dict:
    root = repo_root.resolve()
    app = app_root.resolve()
    output = evidence_dir.expanduser().resolve()
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("Foundation CI evidence directory must be outside the repository")
    output.mkdir(parents=True, exist_ok=False)

    command_env = dict(os.environ if env is None else env)
    python_paths = [str(app), str(app / "tests"), str(app / "tools/foundation")]
    python_paths.extend(item for item in command_env.get("PYTHONPATH", "").split(os.pathsep) if item)
    command_env["PYTHONPATH"] = os.pathsep.join(python_paths)

    ledger_path = output / "command-ledger.jsonl"
    records: list[dict] = []
    failures: list[str] = []
    started_at = datetime.now(timezone.utc).isoformat()
    stop_reason: str | None = None

    def append_record(ledger, record: dict) -> None:
        records.append(record)
        ledger.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        ledger.flush()

    def record_not_run(ledger, number: int, item: Check, reason: str) -> None:
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", item.name).strip("-") or f"check-{number}"
        stdout_path = output / f"{number:03d}-{slug}.stdout"
        stderr_path = output / f"{number:03d}-{slug}.stderr"
        empty_stdout = _CaptureBuffer(stdout_path).record(stdout_path)
        empty_stderr = _CaptureBuffer(stderr_path).record(stderr_path)
        record = {
            "index": number,
            "name": item.name,
            "argv": list(item.argv),
            "cwd": str(app / item.cwd),
            "started_at_utc": None,
            "duration_seconds": 0,
            "timeout_seconds": item.timeout_seconds,
            "returncode": None,
            "status": reason,
            "reason": stop_reason,
            "process_group_terminated": None,
            "output_readers_complete": True,
            "stdout": empty_stdout,
            "stderr": empty_stderr,
        }
        failures.append(item.name)
        append_record(ledger, record)

    with _cancellation_watch() as cancel_state, ledger_path.open("w", encoding="utf-8") as ledger:
        for number, item in enumerate(checks, 1):
            if cancel_state["signal"] is not None:
                stop_reason = f"runner received signal {cancel_state['signal']} before starting {item.name}"
                for pending_number, pending in enumerate(checks[number - 1 :], number):
                    record_not_run(ledger, pending_number, pending, "NOT_RUN_CANCELLED")
                break

            slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", item.name).strip("-") or f"check-{number}"
            stdout_path = output / f"{number:03d}-{slug}.stdout"
            stderr_path = output / f"{number:03d}-{slug}.stderr"
            command_cwd = app / item.cwd
            wall_start = time.monotonic()
            started = datetime.now(timezone.utc).isoformat()
            stdout_capture = _CaptureBuffer(stdout_path)
            stderr_capture = _CaptureBuffer(stderr_path)
            process: subprocess.Popen | None = None
            stdout_reader: threading.Thread | None = None
            stderr_reader: threading.Thread | None = None
            status = "FAIL"
            returncode: int | None = 127
            process_group_terminated: bool | None = None
            output_readers_complete = True
            termination_reason = "NONE"

            try:
                popen_options = {"start_new_session": True} if os.name == "posix" else {
                    "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                }
                process = subprocess.Popen(
                    list(item.argv),
                    cwd=command_cwd,
                    env=command_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    **popen_options,
                )
                assert process.stdout is not None and process.stderr is not None
                stdout_reader = threading.Thread(target=_drain_pipe, args=(process.stdout, stdout_capture), daemon=True)
                stderr_reader = threading.Thread(target=_drain_pipe, args=(process.stderr, stderr_capture), daemon=True)
                stdout_reader.start()
                stderr_reader.start()
                deadline = wall_start + item.timeout_seconds
                print(
                    f"FOUNDATION_CHECK_STARTED {number}/{len(checks)} {item.name} "
                    f"timeout={item.timeout_seconds:g}s",
                    flush=True,
                )

                while True:
                    if cancel_state["signal"] is not None:
                        termination_reason = f"SIGNAL_{cancel_state['signal']}"
                        process_group_terminated = _terminate_process_group(process)
                        status = "CANCELLED" if process_group_terminated else "CANCELLED_UNRECONCILED"
                        try:
                            process.wait(timeout=PROCESS_TERMINATION_GRACE_SECONDS)
                        except subprocess.TimeoutExpired:
                            pass
                        returncode = process.poll()
                        break

                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        termination_reason = "TIMEOUT"
                        process_group_terminated = _terminate_process_group(process)
                        status = "TIMEOUT" if process_group_terminated else "TIMEOUT_UNRECONCILED"
                        try:
                            process.wait(timeout=PROCESS_TERMINATION_GRACE_SECONDS)
                        except subprocess.TimeoutExpired:
                            pass
                        returncode = process.poll()
                        break

                    try:
                        returncode = process.wait(timeout=min(0.2, remaining))
                    except subprocess.TimeoutExpired:
                        continue
                    status = "PASS" if returncode == 0 else "FAIL"
                    break
            except OSError as exc:
                stderr_capture.append(str(exc).encode("utf-8", errors="replace"))
                returncode = 127
                status = "FAIL"

            for reader in (stdout_reader, stderr_reader):
                if reader is not None:
                    reader.join(timeout=PROCESS_TERMINATION_GRACE_SECONDS + 1)
                    output_readers_complete = output_readers_complete and not reader.is_alive()

            if (
                os.name == "posix"
                and process is not None
                and process.poll() is not None
                and process_group_terminated is None
                and _process_group_exists(process.pid)
            ):
                # A child may close both pipes and keep running. Check the
                # process group as well as pipe EOF before starting another
                # check, so an apparently clean command cannot overlap it.
                termination_reason = "PROCESS_GROUP_CLEANUP"
                process_group_terminated = _terminate_process_group(process)
                for reader in (stdout_reader, stderr_reader):
                    if reader is not None:
                        reader.join(timeout=PROCESS_TERMINATION_GRACE_SECONDS + 1)
                output_readers_complete = all(
                    reader is None or not reader.is_alive()
                    for reader in (stdout_reader, stderr_reader)
                )
                if process_group_terminated and status in {"PASS", "FAIL"}:
                    status = "PROCESS_GROUP_CLEANED"
                elif not process_group_terminated:
                    status = "PROCESS_UNRECONCILED"

            if not output_readers_complete and process is not None and process_group_terminated is None:
                # A completed command may have left a descendant holding one of
                # the pipes open. Stop that process group before deciding whether
                # the next Foundation check can safely start.
                if termination_reason == "NONE":
                    termination_reason = "PROCESS_GROUP_CLEANUP"
                process_group_terminated = _terminate_process_group(process)
                for reader in (stdout_reader, stderr_reader):
                    if reader is not None:
                        reader.join(timeout=PROCESS_TERMINATION_GRACE_SECONDS + 1)
                output_readers_complete = all(
                    reader is None or not reader.is_alive()
                    for reader in (stdout_reader, stderr_reader)
                )

            capture_read_error = any(
                capture.read_error is not None for capture in (stdout_capture, stderr_capture)
            )
            if not output_readers_complete and status in {"PASS", "FAIL", "TIMEOUT", "CANCELLED"}:
                status = "OUTPUT_UNRECONCILED"
            if capture_read_error and status in {"PASS", "FAIL", "TIMEOUT", "CANCELLED"}:
                status = "OUTPUT_UNRECONCILED"

            duration = round(time.monotonic() - wall_start, 3)
            stdout_record = stdout_capture.record(stdout_path)
            stderr_record = stderr_capture.record(stderr_path)
            record = {
                "index": number,
                "name": item.name,
                "argv": list(item.argv),
                "cwd": str(command_cwd),
                "started_at_utc": started,
                "duration_seconds": duration,
                "timeout_seconds": item.timeout_seconds,
                "returncode": returncode,
                "status": status,
                "termination_reason": termination_reason,
                "process_group_terminated": process_group_terminated,
                "output_readers_complete": output_readers_complete,
                "stdout": stdout_record,
                "stderr": stderr_record,
            }
            append_record(ledger, record)
            print(
                f"FOUNDATION_CHECK {number}/{len(checks)} {item.name} "
                f"status={status} exit={returncode} duration={duration}s "
                f"group_terminated={process_group_terminated} "
                f"stdout_bytes={stdout_record['total_bytes']} stderr_bytes={stderr_record['total_bytes']} "
                f"stdout_sha256={stdout_record['sha256']} stderr_sha256={stderr_record['sha256']}",
                flush=True,
            )
            if status != "PASS":
                failures.append(item.name)
                if stdout_capture.tail:
                    print(f"--- {item.name} stdout (retained tail) ---\n{_tail(bytes(stdout_capture.tail))}", flush=True)
                if stderr_capture.tail:
                    print(f"--- {item.name} stderr (retained tail) ---\n{_tail(bytes(stderr_capture.tail))}", flush=True)

            if termination_reason.startswith("SIGNAL_"):
                stop_reason = f"runner cancelled by {termination_reason}"
                for pending_number, pending in enumerate(checks[number:], number + 1):
                    record_not_run(ledger, pending_number, pending, "NOT_RUN_CANCELLED")
                break
            if status in {"TIMEOUT_UNRECONCILED", "OUTPUT_UNRECONCILED", "PROCESS_UNRECONCILED"}:
                stop_reason = f"{item.name} did not close its process/output group"
                for pending_number, pending in enumerate(checks[number:], number + 1):
                    record_not_run(ledger, pending_number, pending, "NOT_RUN_PREVIOUS_PROCESS_UNRECONCILED")
                break

        if cancel_state["signal"] is not None and stop_reason is None:
            stop_reason = f"runner cancelled by SIGNAL_{cancel_state['signal']} after the final check"

    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        head_sha = _decode(head.stdout).strip() if head.returncode == 0 else None
    except OSError:
        head_sha = None
    cancelled = stop_reason is not None and "cancelled" in stop_reason
    cancellation_unreconciled = cancelled and any(
        row["status"] in {"CANCELLED_UNRECONCILED", "OUTPUT_UNRECONCILED"}
        for row in records
    )
    summary = {
        "schema_version": "foundation-ci-evidence-r1",
        "repository_head": head_sha,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks_total": len(checks),
        "checks_passed": sum(row["status"] == "PASS" for row in records),
        "checks_failed": len(failures),
        "failed_checks": failures,
        "status": (
            "CANCELLED_UNRECONCILED"
            if cancellation_unreconciled
            else ("CANCELLED" if cancelled else ("PASS" if not failures else "FAIL"))
        ),
        "stop_reason": stop_reason,
        "command_ledger": ledger_path.name,
        "command_ledger_sha256": _sha256(ledger_path.read_bytes()),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"FOUNDATION_CI_RESULT={summary['status']} checks={summary['checks_passed']}/{summary['checks_total']} "
        f"failed={summary['checks_failed']} evidence_dir={output}",
        flush=True,
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    summary = execute_checks(foundation_checks(), evidence_dir=args.evidence_dir or default_evidence_dir())
    if summary["status"].startswith("CANCELLED"):
        return 130
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
