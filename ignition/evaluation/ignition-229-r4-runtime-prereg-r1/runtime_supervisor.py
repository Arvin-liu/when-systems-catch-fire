#!/usr/bin/env python3
"""External hard-timeout and process-group cleanup for one R4 runtime worker."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SUPERVISOR_TIMEOUT_SECONDS = 300
TERM_GRACE_SECONDS = 1.0


def _signal_process_group(pgid: int, sig: int) -> str:
    try:
        os.killpg(pgid, sig)
        return "sent"
    except ProcessLookupError:
        return "absent"
    except PermissionError:
        return "permission_denied"


def _group_state(pgid: int) -> str:
    try:
        os.killpg(pgid, 0)
        return "present"
    except ProcessLookupError:
        return "absent"
    except PermissionError:
        return "inaccessible"


def _stop_group(pgid: int, child: subprocess.Popen[bytes] | None = None) -> tuple[bool, str]:
    term_result = _signal_process_group(pgid, signal.SIGTERM)
    if term_result == "permission_denied":
        if child is not None and child.poll() is None:
            child.kill()
            child.wait()
        return False, "SIGTERM_PERMISSION_DENIED"

    if child is not None and child.poll() is None:
        try:
            child.wait(timeout=TERM_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            kill_result = _signal_process_group(pgid, signal.SIGKILL)
            if kill_result == "permission_denied" and child.poll() is None:
                child.kill()
            child.wait()

    deadline = time.monotonic() + TERM_GRACE_SECONDS
    while time.monotonic() < deadline:
        state = _group_state(pgid)
        if state == "absent":
            return True, "SIGTERM_GROUP_EXITED"
        if state == "inaccessible":
            return False, "PROCESS_GROUP_INACCESSIBLE"
        time.sleep(0.05)

    kill_result = _signal_process_group(pgid, signal.SIGKILL)
    if kill_result == "permission_denied":
        return False, "SIGKILL_PERMISSION_DENIED"
    deadline = time.monotonic() + TERM_GRACE_SECONDS
    while time.monotonic() < deadline:
        state = _group_state(pgid)
        if state == "absent":
            return True, "SIGKILL_GROUP_EXITED"
        if state == "inaccessible":
            return False, "PROCESS_GROUP_INACCESSIBLE"
        time.sleep(0.05)
    return False, "PROCESS_GROUP_STILL_PRESENT"


def run_supervised(argv: list[str], *, timeout_seconds: float = SUPERVISOR_TIMEOUT_SECONDS,
                   cwd: str | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    if not argv or timeout_seconds <= 0:
        raise ValueError("nonempty argv and positive timeout required")
    started = time.monotonic()
    child = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    timed_out = False
    cleanup_complete = True
    cleanup_result = "NO_ORPHAN_PROCESS_GROUP"
    try:
        child.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        cleanup_complete, cleanup_result = _stop_group(child.pid, child)
    else:
        # A successful worker must not leave a subprocess behind in its session.
        if _group_state(child.pid) != "absent":
            cleanup_complete, cleanup_result = _stop_group(child.pid)
    try:
        source_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError:
        source_digest = None
    return {
        "argv_sha256": hashlib.sha256(
            json.dumps(argv, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "pid": child.pid,
        "process_group_id": child.pid,
        "session_id": child.pid,
        "new_session_requested": True,
        "timeout_seconds": timeout_seconds,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "timed_out": timed_out,
        "exit_code": child.returncode,
        "retry_count": 0,
        "process_group_cleanup": cleanup_result,
        "cleanup_complete": cleanup_complete,
        "supervisor_source_sha256": source_digest,
        "status": "EXTERNAL_TIMEOUT" if timed_out else ("EXITED_ZERO" if child.returncode == 0 else "EXITED_NONZERO"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=float, default=SUPERVISOR_TIMEOUT_SECONDS)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide one worker command after --")
    result = run_supervised(command, timeout_seconds=args.timeout_seconds)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if not result["cleanup_complete"]:
        return 2
    return 124 if result["timed_out"] else (0 if result["exit_code"] == 0 else 1)


if __name__ == "__main__":
    raise SystemExit(main())
