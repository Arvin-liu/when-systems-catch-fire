#!/usr/bin/env python3
"""Run Foundation CI checks sequentially and retain per-command evidence.

Every declared check runs even after an earlier check fails. The aggregate
process exits nonzero if any check fails, so diagnostic continuation never
turns a failed run green. Checks run in one process at a time to keep the
memory-heavy Foundation generators from overlapping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import selectors
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
CHECK_TIMEOUT_SECONDS = 45 * 60
MAX_OUTPUT_BYTES_PER_STREAM = 256 * 1024
STREAM_READ_CHUNK_BYTES = 64 * 1024
PROCESS_TERMINATION_GRACE_SECONDS = 2.0
PROCESS_REAP_GRACE_SECONDS = 2.0
SELECT_POLL_SECONDS = 0.05


@dataclass(frozen=True)
class Check:
    name: str
    argv: tuple[str, ...]
    cwd: str = "."
    timeout_seconds: float = CHECK_TIMEOUT_SECONDS
    output_limit_bytes: int = MAX_OUTPUT_BYTES_PER_STREAM


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
        check("test-foundation", "-m", "unittest", "tests.foundation.test_foundation"),
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


def _decode(value: bytes | str) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


class _StreamCapture:
    """Persist a bounded prefix while hashing every byte read from a child pipe."""

    def __init__(self, path: Path, limit_bytes: int) -> None:
        self.path = path
        self.limit_bytes = limit_bytes
        self.stored_bytes = 0
        self.observed_bytes = 0
        self.stored_hash = hashlib.sha256()
        self.observed_hash = hashlib.sha256()
        self.truncated = False
        self.eof_reached = False
        self.handle = None

    def open(self) -> None:
        self.handle = self.path.open("wb")

    def consume(self, chunk: bytes) -> None:
        self.observed_bytes += len(chunk)
        self.observed_hash.update(chunk)
        available = max(0, self.limit_bytes - self.stored_bytes)
        stored = chunk[:available]
        if stored:
            if self.handle is None:
                raise OSError(f"capture file is not open: {self.path.name}")
            self.handle.write(stored)
            self.handle.flush()
            self.stored_hash.update(stored)
            self.stored_bytes += len(stored)
        if len(stored) != len(chunk):
            self.truncated = True

    def close(self, *, eof_reached: bool | None = None) -> None:
        if eof_reached is not None:
            self.eof_reached = eof_reached
        if self.handle is not None:
            self.handle.flush()
            os.fsync(self.handle.fileno())
            self.handle.close()
            self.handle = None

    def metadata(self) -> dict:
        return {
            "path": self.path.name,
            "bytes": self.stored_bytes,
            "sha256": self.stored_hash.hexdigest(),
            "observed_bytes": self.observed_bytes,
            "observed_sha256": self.observed_hash.hexdigest(),
            "truncated": self.truncated,
            "eof_reached": self.eof_reached,
        }


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return _decode(result.stdout).strip() if result.returncode == 0 else None


def _process_group_exists(process: subprocess.Popen) -> bool | None:
    if os.name != "posix":
        return None
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _signal_process_tree(process: subprocess.Popen, signum: int) -> bool:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signum)
        elif signum == signal.SIGTERM:
            process.terminate()
        else:
            process.kill()
    except ProcessLookupError:
        return False
    except OSError:
        if process.poll() is not None:
            return False
        raise
    return True


def _terminate_process_tree(process: subprocess.Popen) -> tuple[list[str], bool]:
    """Terminate the isolated process group and reap it within two bounded waits."""
    signals_sent: list[str] = []
    if _signal_process_tree(process, signal.SIGTERM):
        signals_sent.append("SIGTERM")
    term_deadline = time.monotonic() + PROCESS_TERMINATION_GRACE_SECONDS
    while time.monotonic() < term_deadline:
        process.poll()
        group_exists = _process_group_exists(process)
        if process.returncode is not None and group_exists is False:
            return signals_sent, True
        time.sleep(min(SELECT_POLL_SECONDS, max(0.0, term_deadline - time.monotonic())))

    group_exists = _process_group_exists(process)
    if process.returncode is None or group_exists is True:
        if _signal_process_tree(process, signal.SIGKILL):
            signals_sent.append("SIGKILL")
    kill_deadline = time.monotonic() + PROCESS_REAP_GRACE_SECONDS
    while time.monotonic() < kill_deadline:
        process.poll()
        group_exists = _process_group_exists(process)
        if process.returncode is not None and group_exists is False:
            return signals_sent, True
        time.sleep(min(SELECT_POLL_SECONDS, max(0.0, kill_deadline - time.monotonic())))
    process.poll()
    group_exists = _process_group_exists(process)
    if os.name != "posix":
        return signals_sent, False
    return signals_sent, process.returncode is not None and group_exists is False


def install_cancellation_handlers(cancel_event: threading.Event) -> None:
    """Convert cooperative runner signals into a bounded cancellation request."""
    def request_cancel(_signum, _frame) -> None:
        cancel_event.set()

    signal.signal(signal.SIGINT, request_cancel)
    signal.signal(signal.SIGTERM, request_cancel)


def _not_executed_record(index: int, item: Check, app_root: Path, head: str | None) -> dict:
    empty = _sha256(b"")
    return {
        "index": index,
        "name": item.name,
        "argv": list(item.argv),
        "cwd": str(app_root / item.cwd),
        "repository_head": head,
        "started_at_utc": None,
        "duration_seconds": 0.0,
        "returncode": None,
        "status": "NOT_EXECUTED",
        "termination_reason": "CANCELLED_BEFORE_START",
        "stdout": {"path": None, "bytes": 0, "sha256": empty, "observed_bytes": 0,
                   "observed_sha256": empty, "truncated": False, "eof_reached": False},
        "stderr": {"path": None, "bytes": 0, "sha256": empty, "observed_bytes": 0,
                   "observed_sha256": empty, "truncated": False, "eof_reached": False},
        "process_tree_cleanup_complete": True,
    }


def _execute_one_check(
    *,
    index: int,
    total: int,
    item: Check,
    command_env: dict[str, str],
    command_cwd: Path,
    output: Path,
    repository_head: str | None,
    cancel_event: threading.Event,
) -> dict:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", item.name).strip("-") or f"check-{index}"
    stdout_capture = _StreamCapture(output / f"{index:03d}-{slug}.stdout", item.output_limit_bytes)
    stderr_capture = _StreamCapture(output / f"{index:03d}-{slug}.stderr", item.output_limit_bytes)
    started = datetime.now(timezone.utc).isoformat()
    wall_start = time.monotonic()
    process = None
    selector = selectors.DefaultSelector()
    stream_captures = {"stdout": stdout_capture, "stderr": stderr_capture}
    termination_reason = None
    termination_attempted = False
    signals_sent: list[str] = []
    cleanup_complete = True
    runner_error = None
    returncode = None
    opened = []
    try:
        if item.timeout_seconds <= 0:
            raise ValueError("check timeout_seconds must be positive")
        if item.output_limit_bytes < 0:
            raise ValueError("check output_limit_bytes must be nonnegative")
        for capture in (stdout_capture, stderr_capture):
            capture.open()
            opened.append(capture)
        if cancel_event.is_set():
            termination_reason = "CANCELLED_BEFORE_START"
            returncode = None
        else:
            process = subprocess.Popen(
                list(item.argv),
                cwd=command_cwd,
                env=command_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                close_fds=True,
                start_new_session=(os.name == "posix"),
            )
            for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr)):
                if pipe is None:
                    raise OSError(f"child {name} pipe was not created")
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)

            while selector.get_map() or process.poll() is None:
                if process.poll() is not None and os.name == "posix" and _process_group_exists(process) is True and termination_reason is None:
                    termination_reason = "PROCESS_TREE_LEAK"
                if termination_reason is None:
                    if cancel_event.is_set():
                        termination_reason = "CANCELLED"
                    elif stdout_capture.truncated or stderr_capture.truncated:
                        termination_reason = "OUTPUT_LIMIT_EXCEEDED"
                    elif time.monotonic() - wall_start >= item.timeout_seconds:
                        termination_reason = "TIMEOUT"
                if termination_reason is not None and not termination_attempted:
                    termination_attempted = True
                    sent, cleanup_complete = _terminate_process_tree(process)
                    signals_sent.extend(sent)
                    if not cleanup_complete:
                        runner_error = "process tree did not disappear within bounded termination/reap grace"
                events = selector.select(SELECT_POLL_SECONDS)
                for key, _mask in events:
                    name = key.data
                    pipe = key.fileobj
                    try:
                        chunk = os.read(pipe.fileno(), STREAM_READ_CHUNK_BYTES)
                    except BlockingIOError:
                        continue
                    capture = stream_captures[name]
                    if chunk:
                        capture.consume(chunk)
                    else:
                        selector.unregister(pipe)
                        pipe.close()
                        capture.close(eof_reached=True)
                if termination_reason is not None and runner_error is not None:
                    break
            if process.poll() is None:
                process.wait(timeout=PROCESS_REAP_GRACE_SECONDS)
            returncode = process.returncode
    except OSError as exc:
        runner_error = f"{type(exc).__name__}: {exc}"
        if process is None:
            termination_reason = "LAUNCH_ERROR"
            returncode = 127
        else:
            termination_reason = "RUNNER_EXCEPTION"
            sent, cleanup_complete = _terminate_process_tree(process)
            signals_sent.extend(sent)
            try:
                returncode = process.wait(timeout=PROCESS_REAP_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                cleanup_complete = False
    except (ValueError, OSError) as exc:
        runner_error = f"{type(exc).__name__}: {exc}"
        termination_reason = "RUNNER_EXCEPTION"
        if process is not None:
            sent, cleanup_complete = _terminate_process_tree(process)
            signals_sent.extend(sent)
            returncode = process.poll()
    except BaseException as exc:
        runner_error = f"{type(exc).__name__}: {exc}"
        termination_reason = "CANCELLED" if isinstance(exc, KeyboardInterrupt) else "RUNNER_EXCEPTION"
        if process is not None:
            sent, cleanup_complete = _terminate_process_tree(process)
            signals_sent.extend(sent)
            returncode = process.poll()
    finally:
        for key in list(selector.get_map().values()):
            try:
                selector.unregister(key.fileobj)
                key.fileobj.close()
            except (OSError, ValueError):
                pass
        selector.close()
        for capture in opened:
            if capture.handle is not None:
                try:
                    capture.close()
                except OSError as exc:
                    runner_error = runner_error or f"capture close failed: {exc}"

    duration = round(time.monotonic() - wall_start, 3)
    if termination_reason == "CANCELLED_BEFORE_START":
        status = "NOT_EXECUTED"
    elif termination_reason == "TIMEOUT":
        status = "TIMEOUT"
    elif termination_reason == "OUTPUT_LIMIT_EXCEEDED":
        status = "OUTPUT_LIMIT_EXCEEDED"
    elif termination_reason == "CANCELLED":
        status = "CANCELLED"
    elif termination_reason == "PROCESS_TREE_LEAK":
        status = "FAIL"
    elif termination_reason == "RUNNER_EXCEPTION" or runner_error and termination_reason != "LAUNCH_ERROR":
        status = "ABORTED"
    else:
        status = "PASS" if returncode == 0 else "FAIL"
    if not cleanup_complete and status != "NOT_EXECUTED":
        status = "ABORTED"
    return {
        "index": index,
        "name": item.name,
        "argv": list(item.argv),
        "cwd": str(command_cwd),
        "repository_head": repository_head,
        "started_at_utc": started,
        "duration_seconds": duration,
        "returncode": returncode,
        "status": status,
        "termination_reason": termination_reason,
        "timeout_seconds": item.timeout_seconds,
        "output_limit_bytes_per_stream": item.output_limit_bytes,
        "stdout": stdout_capture.metadata(),
        "stderr": stderr_capture.metadata(),
        "signals_sent": signals_sent,
        "termination_grace_seconds": PROCESS_TERMINATION_GRACE_SECONDS,
        "reap_grace_seconds": PROCESS_REAP_GRACE_SECONDS,
        "process_tree_cleanup_complete": cleanup_complete,
        "runner_error": runner_error,
    }


def execute_checks(
    checks: Sequence[Check],
    *,
    repo_root: Path = REPO_ROOT,
    app_root: Path = APP_ROOT,
    evidence_dir: Path,
    env: dict[str, str] | None = None,
    cancel_event: threading.Event | None = None,
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
    failures: list[dict] = []
    cancel_event = cancel_event or threading.Event()
    started_at = datetime.now(timezone.utc).isoformat()
    head_sha = _git_head(root)
    aborted = False
    cancelled = False
    with ledger_path.open("w", encoding="utf-8") as ledger:
        for number, item in enumerate(checks, 1):
            if cancel_event.is_set():
                cancelled = True
                record = _not_executed_record(number, item, app, head_sha)
            else:
                try:
                    record = _execute_one_check(
                        index=number,
                        total=len(checks),
                        item=item,
                        command_env=command_env,
                        command_cwd=app / item.cwd,
                        output=output,
                        repository_head=head_sha,
                        cancel_event=cancel_event,
                    )
                except BaseException as exc:
                    record = _not_executed_record(number, item, app, head_sha)
                    record["status"] = "ABORTED"
                    record["termination_reason"] = "RUNNER_EXCEPTION"
                    record["runner_error"] = f"{type(exc).__name__}: {exc}"
                    aborted = True
            records.append(record)
            ledger.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())
            print(
                f"FOUNDATION_CHECK {number}/{len(checks)} {item.name} "
                f"status={record['status']} exit={record['returncode']} duration={record['duration_seconds']}s",
                flush=True,
            )
            if record["status"] not in {"PASS", "NOT_EXECUTED"}:
                failures.append({"name": item.name, "status": record["status"]})
            if record["termination_reason"] == "CANCELLED_BEFORE_START":
                cancelled = True
            if record["status"] in {"CANCELLED", "ABORTED"}:
                cancelled = record["status"] == "CANCELLED"
                aborted = record["status"] == "ABORTED"
            if cancelled or aborted:
                for future_index, future in enumerate(checks[number:], number + 1):
                    future_record = _not_executed_record(future_index, future, app, head_sha)
                    records.append(future_record)
                    ledger.write(json.dumps(future_record, ensure_ascii=False, sort_keys=True) + "\n")
                    ledger.flush()
                    os.fsync(ledger.fileno())
                break

    head_after = _git_head(root)
    if head_sha is not None and head_after != head_sha:
        aborted = True
        failures.append({"name": "repository-head-stability", "status": "ABORTED"})
    checks_not_executed = sum(
        row["status"] == "NOT_EXECUTED" or row["started_at_utc"] is None for row in records
    )
    checks_passed = sum(row["status"] == "PASS" for row in records)
    checks_failed = sum(row["status"] not in {"PASS", "NOT_EXECUTED"} for row in records)
    if cancelled:
        run_status = "CANCELLED"
    elif aborted or checks_not_executed:
        run_status = "ABORTED"
    elif failures:
        run_status = "FAIL"
    else:
        run_status = "PASS"
    summary = {
        "schema_version": "foundation-ci-evidence-r2",
        "repository_head": head_sha,
        "repository_head_after": head_after,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "os_name": os.name,
        "stream_read_chunk_bytes": STREAM_READ_CHUNK_BYTES,
        "default_timeout_seconds": CHECK_TIMEOUT_SECONDS,
        "default_output_limit_bytes_per_stream": MAX_OUTPUT_BYTES_PER_STREAM,
        "termination_grace_seconds": PROCESS_TERMINATION_GRACE_SECONDS,
        "reap_grace_seconds": PROCESS_REAP_GRACE_SECONDS,
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks_total": len(checks),
        "checks_executed": len(records) - checks_not_executed,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "checks_not_executed": checks_not_executed,
        "failed_checks": failures,
        "full_suite_completed": checks_not_executed == 0 and len(records) == len(checks),
        "status": run_status,
        "command_ledger": ledger_path.name,
        "command_ledger_sha256": _sha256(ledger_path.read_bytes()),
    }
    summary_tmp = output / "summary.json.tmp"
    with summary_tmp.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    summary_tmp.replace(output / "summary.json")
    print(
        f"FOUNDATION_CI_RESULT={summary['status']} checks={summary['checks_passed']}/{summary['checks_total']} "
        f"failed={summary['checks_failed']} not_executed={summary['checks_not_executed']} evidence_dir={output}",
        flush=True,
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    cancel_event = threading.Event()
    install_cancellation_handlers(cancel_event)
    summary = execute_checks(
        foundation_checks(),
        evidence_dir=args.evidence_dir or default_evidence_dir(),
        cancel_event=cancel_event,
    )
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
